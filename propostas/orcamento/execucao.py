"""
HH de execução de obra, equipe, prazo por frentes e preço no motor.

Fórmulas (caso de referência: plano T1, preço R$ 44.921,49):
    fator    = Π fatores (altura, acesso, ocupação, turno)
    hh_base  = quantidade × hh_por_unidade × fator
    hh       = hh_base × fator_calibracao
    equipe   = ⌈HH ÷ (horas_dia × prazo × eficiência)⌉ por função
    dias da frente = máx. por função de ⌈HH ÷ (horas_dia × pessoas × eficiência)⌉; frentes em sequência
    dias corridos  = ⌈dias úteis × 7 ÷ 5⌉
    custo-hora = custo_hora × params["execucao"]["encargos"] (opcional, padrão 1,0)
Cada item pode trazer "base" ("sinapi"|"propria", padrão "propria") e "material" (R$/unid, padrão 0),
repassados sem cálculo; "material" vale como custo de material quando "custo_material_unit" não vem.
"""
import copy
import math

from . import motor
from . import proposta as pp
from .erros import ErroEntrada

FUNCOES_PADRAO = {"encarregado": "Encarregado", "mecanico_refrigeracao": "Mecânico de refrigeração",
                  "ajudante": "Ajudante", "soldador": "Soldador", "eletricista": "Eletricista",
                  "tecnico_tab": "Técnico de TAB"}
UNIDADES_ITEM = ("m2", "m", "un", "kW")
ITENS_SUGERIDOS = {"duto_m2": "m2", "linha_frigorifica_m": "m", "evaporadora_un": "un", "condensadora_un": "un",
                   "capacidade_kw": "kW", "ponto_eletrico_un": "un", "difusor_un": "un"}
FATORES_PADRAO = {
    "altura": {"ate_3m": 1.0, "de_3_a_6m": 1.15, "acima_6m": 1.3},
    "acesso": {"livre": 1.0, "restrito": 1.15, "confinado": 1.3},
    "ocupacao": {"desocupado": 1.0, "ocupado": 1.2},
    "turno": {"diurno": 1.0, "noturno": 1.25},
}


def config_padrao(fase="F1"):
    return {"fase": fase, "modo": "prazo", "prazo_alvo_dias": 20, "equipe": {}, "horas_dia": 8.0,
            "eficiencia": 0.8, "fatores": copy.deepcopy(FATORES_PADRAO)}


def fator_item(fatores, item):
    det = {}
    for nome in FATORES_PADRAO:
        valor = item.get(nome)
        tabela = fatores.get(nome, {})
        if valor not in tabela:
            raise ErroEntrada("fator_desconhecido", f"Fator '{nome}' desconhecido: {valor!r}.",
                              {"fator": nome, "valor": valor})
        det[nome] = tabela[valor]
    total = 1.0
    for v in det.values():
        total *= v
    return total, det


def hh_execucao(itens, produtividade, fatores):
    prod = {}
    for p in produtividade:
        prod.setdefault(p["item"], []).append(p)
    linhas, frentes = [], []
    hh_f, hh_fb, hh_ff = {}, {}, {}
    for it in itens:
        if it["item"] not in prod:
            raise ErroEntrada("item_sem_produtividade", f"O item '{it['item']}' não tem produtividade cadastrada.",
                              {"item": it["item"]})
        if float(it["quantidade"]) < 0:
            raise ErroEntrada("quantidade_negativa", "A quantidade do item não pode ser negativa.",
                              {"item_id": it["id"]})
        fator, _ = fator_item(fatores, it)
        if it["frente"] not in frentes:
            frentes.append(it["frente"])
        for p in prod[it["item"]]:
            cal = float(p.get("fator_calibracao", 1.0))
            base = float(it["quantidade"]) * float(p["hh_por_unidade"]) * fator
            hh = base * cal
            f = p["funcao"]
            linhas.append({"item_id": it["id"], "frente": it["frente"], "item": it["item"], "funcao": f,
                           "quantidade": float(it["quantidade"]), "hh_por_unidade": float(p["hh_por_unidade"]),
                           "fator": fator, "fator_calibracao": cal, "hh_base": base, "hh": hh})
            hh_f[f] = hh_f.get(f, 0.0) + hh
            hh_fb[f] = hh_fb.get(f, 0.0) + base
            d = hh_ff.setdefault(it["frente"], {})
            d[f] = d.get(f, 0.0) + hh
    return {"linhas": linhas, "hh_funcao": hh_f, "hh_funcao_base": hh_fb, "hh_frente_funcao": hh_ff,
            "frentes": frentes, "total_hh": sum(hh_f.values())}


def _dias(hh, horas_dia, pessoas, eficiencia):
    return math.ceil(round(hh / (horas_dia * pessoas * eficiencia), 9))


def dimensionar_equipe(hh_funcao, horas_dia, prazo_dias, eficiencia):
    return {f: (_dias(hh, horas_dia, prazo_dias, eficiencia) if hh > 0 else 0) for f, hh in hh_funcao.items()}


def cronograma_frentes(hh_frente_funcao, frentes, equipe, horas_dia, eficiencia):
    cron, inicio = [], 1
    for fr in frentes:
        dias_f = {}
        for f, hh in hh_frente_funcao.get(fr, {}).items():
            if hh <= 0:
                continue
            n = equipe.get(f, 0)
            if n <= 0:
                raise ErroEntrada("equipe_incompleta", f"A equipe não tem a função '{f}', que tem horas a executar.",
                                  {"funcao": f})
            dias_f[f] = _dias(hh, horas_dia, n, eficiencia)
        dias = max(dias_f.values(), default=0)
        cron.append({"frente": fr, "dias_uteis": dias, "inicio": inicio, "fim": inicio + dias - 1,
                     "dias_funcao": dias_f})
        inicio += dias
    return cron


def _invalido(campo):
    return ErroEntrada("parametro_invalido", f"Parâmetro inválido: {campo}.", {"campo": campo})


def planejar_execucao(itens, produtividade, config):
    horas_dia, ef = config.get("horas_dia"), config.get("eficiencia")
    if not isinstance(horas_dia, (int, float)) or horas_dia <= 0:
        raise _invalido("horas_dia")
    if not isinstance(ef, (int, float)) or not 0 < ef <= 1:
        raise _invalido("eficiencia")
    modo = config.get("modo", "prazo")
    alvo = config.get("prazo_alvo_dias")
    if modo == "prazo" and (not isinstance(alvo, (int, float)) or alvo < 1):
        raise _invalido("prazo_alvo_dias")
    if modo == "equipe":
        for n in config.get("equipe", {}).values():
            if not isinstance(n, int) or n < 0:
                raise _invalido("equipe")
    r = hh_execucao(itens, produtividade, config.get("fatores") or FATORES_PADRAO)
    avisos = []
    if modo == "prazo":
        equipe = dimensionar_equipe(r["hh_funcao"], horas_dia, int(alvo), ef)
    else:
        equipe = dict(config.get("equipe", {}))
    cron = cronograma_frentes(r["hh_frente_funcao"], r["frentes"], equipe, horas_dia, ef)
    uteis = sum(c["dias_uteis"] for c in cron)
    if modo == "prazo" and uteis > alvo:
        avisos.append(f"O cronograma por frentes dá {uteis} dias úteis, acima do prazo-alvo de {int(alvo)}, "
                      "pelo arredondamento de cada frente.")
    r.update({"modo": modo, "equipe": equipe, "cronograma": cron, "prazo_dias_uteis": uteis,
              "prazo_dias_corridos": math.ceil(uteis * 7 / 5), "avisos": avisos})
    return r


def _material_unit(it):
    return float(it.get("custo_material_unit") or it.get("material") or 0)


def fornecimentos_execucao(plano, itens, funcoes, fase, encargos=1.0):
    out = []
    for f, hh in plano["hh_funcao"].items():
        if hh <= 0:
            continue
        info = funcoes.get(f)
        if not info or float(info.get("custo_hora", 0)) <= 0:
            raise ErroEntrada("funcao_sem_custo", f"A função '{f}' não tem custo-hora.", {"funcao": f})
        out.append(pp.novo_fornecimento(descricao=f"Mão de obra de execução — {info['nome']}",
                                        categoria="mo_execucao", unid="h", qtd=hh,
                                        custo_unit=float(info["custo_hora"]) * encargos,
                                        fonte="HH de execução", fase=fase))
    for it in itens:
        mat = _material_unit(it)
        if mat > 0:
            out.append(pp.novo_fornecimento(descricao=it.get("descricao") or it["item"],
                                            categoria=it.get("categoria_material", "material"),
                                            unid=it["unidade"], qtd=it["quantidade"], custo_unit=mat,
                                            fonte="item de execução", fase=fase))
    return out


def precificar_com_execucao(cat, proposta, itens_por_opcao, produtividade, funcoes):
    prop = copy.deepcopy(proposta)
    encargos = float((prop["parametros"].get("execucao") or {}).get("encargos", 1.0))
    planos, remover = {}, set()
    for o in prop["opcoes"]:
        itens = itens_por_opcao.get(o["id"])
        if not itens:
            continue
        cfg = o.get("execucao") or config_padrao(o["fases"][0]["id"])
        fase = next((f for f in o["fases"] if f["id"] == cfg["fase"]), None)
        if fase is None:
            raise ErroEntrada("fase_inexistente", f"A fase de execução '{cfg['fase']}' não existe na opção {o['id']}.",
                              {"opcao": o["id"], "fase": cfg["fase"]})
        plano = planejar_execucao(itens, produtividade, cfg)
        o["fornecimentos"].extend(fornecimentos_execucao(plano, itens, funcoes, cfg["fase"], encargos))
        o["prazo_execucao_dias"] = plano["prazo_dias_uteis"]
        planos[o["id"]] = plano
        remover.add(f"{o['nome']}: nenhum serviço com horas — adicione serviços na aba Escopo.")
        remover.add(f"{o['nome']} / {fase['nome']}: fase sem serviços.")
    orc = motor.precificar(cat, prop)
    orc["avisos"] = [a for a in orc["avisos"] if a not in remover]
    for o in prop["opcoes"]:
        if o["id"] in planos:
            orc["avisos"] += [f"{o['nome']}: {a}" for a in planos[o["id"]]["avisos"]]
    return {"proposta": prop, "orcamento": orc, "execucao": planos}
