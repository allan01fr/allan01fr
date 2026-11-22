"""Honorário de projeto pelo método ABRAVA/DNPC.

ATENÇÃO: a forma das fórmulas é PROVISÓRIA e só vale depois de conferida no documento oficial
("Metodologia para Avaliação dos Honorários de Projetos de HVAC", ABRAVA/DNPC, Rev. 01/2014).
Nenhum valor de tabela fica no código: os parâmetros vêm de arquivo local, fora do git
(`dados/abrava_parametros.json`; veja `dados/abrava_parametros.exemplo.json`).
"""
import copy
import json
import os

from .ajustes_honorario import aplicar_ajustes
from .erros import ErroEntrada

TIPOS_INSTALACAO = ("expansao_direta", "vrf", "agua_gelada")
ESCOPOS = ("planilha_orcamento", "nova_em_existente", "nova_em_novo", "retrofit")
TIPOS_VENTILACAO = ("insuflacao_exaustao", "exaustao", "insuflacao", "cozinha", "estacionamento")

CAMINHO_PADRAO = os.path.join(os.path.dirname(__file__), "..", "dados", "abrava_parametros.json")


def carregar_parametros(caminho: str | None = None) -> dict | None:
    """Lê o arquivo local não versionado; devolve None se não existir."""
    caminho = caminho or CAMINHO_PADRAO
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def area_corrigida(parametros, climatizados, ventilados):
    if not climatizados:
        raise ErroEntrada("sem_ambientes", "Informe ao menos um ambiente climatizado.")
    detalhe, total = [], 0.0
    for c in climatizados:
        tipo = c["tipo"]
        if tipo not in parametros["tipos_ambiente"]:
            raise ErroEntrada("ambiente_desconhecido", f"Tipo de ambiente desconhecido: {tipo}.", {"tipo": tipo})
        _area(c["area_m2"])
        rep = c.get("repeticoes", 1)
        if isinstance(rep, bool) or not isinstance(rep, int) or rep < 1:
            raise ErroEntrada("repeticoes_invalida", "Repetições deve ser inteiro ≥ 1.", {"tipo": tipo})
        peso = parametros["tipos_ambiente"][tipo]["peso"]
        ac = c["area_m2"] * peso * (1 + (rep - 1) * parametros["fator_repeticao"])
        total += ac
        detalhe.append({"origem": "climatizado", "tipo": tipo, "area_m2": c["area_m2"], "repeticoes": rep,
                        "peso": peso, "area_corrigida": ac})
    for v in ventilados or []:
        tipo = v["tipo"]
        if tipo not in parametros["peso_ventilacao"]:
            raise ErroEntrada("ventilacao_desconhecida", f"Tipo de ventilação desconhecido: {tipo}.", {"tipo": tipo})
        _area(v["area_m2"])
        peso = parametros["peso_ventilacao"][tipo]
        ac = v["area_m2"] * peso
        total += ac
        detalhe.append({"origem": "ventilado", "tipo": tipo, "area_m2": v["area_m2"], "repeticoes": 1,
                        "peso": peso, "area_corrigida": ac})
    return total, detalhe


def _area(a):
    if a is None or a <= 0:
        raise ErroEntrada("area_invalida", "A área deve ser maior que zero.", {"area_m2": a})


def percentual_curva(curva, custo_base):
    if not curva:
        raise ErroEntrada("curva_vazia", "A curva de percentual está vazia.")
    pts = sorted(curva, key=lambda p: p["custo_base"])
    if custo_base <= pts[0]["custo_base"]:
        return pts[0]["pct"]
    if custo_base >= pts[-1]["custo_base"]:
        return pts[-1]["pct"]
    for a, b in zip(pts, pts[1:]):
        if a["custo_base"] <= custo_base <= b["custo_base"]:
            t = (custo_base - a["custo_base"]) / (b["custo_base"] - a["custo_base"])
            return a["pct"] + t * (b["pct"] - a["pct"])


def calcular_abrava(parametros, projeto, salario_minimo):
    tipo, escopo = projeto.get("tipo_instalacao"), projeto.get("escopo")
    if tipo not in parametros["custo_tr"]:
        raise ErroEntrada("parametro_abrava_ausente", f"Sem custo por TR para {tipo}.", {"campo": "tipo_instalacao", "valor": tipo})
    if escopo not in parametros["fator_escopo"]:
        raise ErroEntrada("parametro_abrava_ausente", f"Sem fator para o escopo {escopo}.", {"campo": "escopo", "valor": escopo})
    area, detalhe = area_corrigida(parametros, projeto.get("climatizados"), projeto.get("ventilados"))
    tr = area * parametros["densidade_tr_m2"] * parametros["fs"]
    custo_tr = parametros["custo_tr"][tipo]
    custo_base = tr * custo_tr
    pct = percentual_curva(parametros["curva_percentual"], custo_base)
    f_escopo = parametros["fator_escopo"][escopo]
    fatores = parametros.get("fatores_metodo") or {}
    bruto = custo_base * pct * f_escopo
    for f in fatores.values():
        bruto *= f
    avisos, piso = [], None
    n = parametros.get("piso_salarios_minimos")
    if n is not None and salario_minimo is not None:
        piso = n * salario_minimo
    metodo = max(bruto, piso) if piso is not None else bruto
    if piso is not None and piso > bruto:
        avisos.append(f"Honorário pelo piso de {n:g} salários mínimos.")
    if parametros.get("edicao_superada"):
        avisos.append(f"Parâmetros ABRAVA/DNPC de edição superada ({parametros.get('edicao')}): confira a tabela vigente.")
    return {"area_corrigida": area, "detalhe_areas": detalhe, "tr_estimada": tr, "custo_tr": custo_tr,
            "fs": parametros["fs"], "custo_base": custo_base, "pct": pct, "fator_escopo": f_escopo,
            "fatores_metodo": fatores, "honorario_bruto": bruto, "piso": piso, "honorario_metodo": metodo,
            "avisos": avisos, "fonte": parametros.get("fonte"), "edicao": parametros.get("edicao"),
            "secao_tabela": parametros.get("secao_tabela")}


def comparar_com_hh(preco_hh, honorario_final):
    return {"preco_hh": preco_hh, "honorario_final": honorario_final, "diferenca": honorario_final - preco_hh,
            "razao": honorario_final / preco_hh if preco_hh else None}


def aplicar_na_proposta(proposta, parametros, ajustes_empresa, salario_minimo):
    """Devolve (cópia da proposta, {opcao_id: {abrava, ajustes, fase, adotado}}); a original fica intacta.

    Com `adotar`, a fase recebe cobranca="valor" e valor_definido. NOTA: a cobrança "valor" ainda não
    existe no motor (cobranca.py); até ser implementada, o motor não usará este valor no preço.
    """
    nova, info = copy.deepcopy(proposta), {}
    for op in nova.get("opcoes", []):
        pa = op.get("projeto_abrava")
        if not pa or not pa.get("ativo"):
            continue
        if parametros is None:
            raise ErroEntrada("sem_parametros_abrava", "Parâmetros ABRAVA não encontrados (arquivo local ausente).")
        fase = next((f for f in op.get("fases", []) if f.get("id") == pa.get("fase")), None)
        if fase is None:
            raise ErroEntrada("fase_inexistente", f"Fase inexistente: {pa.get('fase')}.", {"fase": pa.get("fase")})
        abrava = calcular_abrava(parametros, pa, salario_minimo)
        ajustes = aplicar_ajustes(abrava["honorario_metodo"], ajustes_empresa, pa.get("ajustes") or {})
        adotado = bool(pa.get("adotar"))
        if adotado:
            fase["cobranca"] = "valor"
            fase["valor_definido"] = {"valor": ajustes["honorario_final"],
                                      "origem": "Método ABRAVA/DNPC com ajustes da empresa",
                                      "prazo_dias": pa.get("prazo_dias")}
        info[op["id"]] = {"abrava": abrava, "ajustes": ajustes, "fase": pa["fase"], "adotado": adotado}
    return nova, info
