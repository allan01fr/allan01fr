"""
Modelo de dados da proposta (salvo e aberto como JSON pela barra lateral do app).

Uma proposta tem dados gerais, o contexto que gera os fatores (complexidade,
documentação, acesso, urgência, risco), uma cópia dos parâmetros comerciais e
N opções. Cada opção é uma lista de serviços do catálogo com o formulário
preenchido, mais fornecimentos.

Modalidades da opção:
- "fases": a proposta para o cliente, em fases sequenciais (ex.: laudo, estudo de viabilidade,
  projeto, assessoria de obra). Cada fase tem a sua forma de cobrança: escopo fechado, hora
  técnica, % da obra (sobre as medições, fixo pelo valor global ou parcela fixa + medições) ou
  pacote de horas (mensal ou total), com taxa de desempenho opcional nas fases de obra.
- "estimativa": estimativa interna do valor global da obra (equipamentos, execução, BDI,
  garantia). Não gera proposta; é a base do % da assessoria e do CAPEX da viabilidade.
"""

import copy
import datetime as dt
import json
import string
import uuid

from . import catalogo as ct
from . import parametros as pm
from . import viabilidade as vb

CONTEXTO_PADRAO = {
    "dist_km": 20.0,
    "area_ref": 0.0,
    "complexidade": "media",
    "documentacao": "parcial",
    "acesso": "livre",
    "urgencia": "normal",
    "risco": "medio",
}
CATEGORIAS_FORNECIMENTO = ("material", "equipamento", "mo_execucao", "subcontrato")
MODALIDADES = ("fases", "estimativa")
COBRANCAS = ("fechado", "hora", "percentual", "pacote")
FORMAS_PERCENTUAL = ("medicoes", "fixo_global", "fixo_mais_medicoes")
FORMAS_PACOTE = ("mensal", "total")


def nova_fase(fid, params, nome=None, cobranca="fechado"):
    """Fase da proposta com os parâmetros de todas as formas de cobrança (só a escolhida é usada)."""
    cb = params.get("cobranca", {})
    pc, pk, de = cb.get("percentual", {}), cb.get("pacote", {}), cb.get("desempenho", {})
    return {
        "id": fid,
        "nome": nome or f"Fase {fid.lstrip('F')}",
        "cobranca": cobranca,
        # obra acompanhada: base do % e da taxa de desempenho, duração e curva das medições.
        # base_modo: valor informado, estimativa interna de outra opção (parte "obra" = fornecimentos e
        # execução com BDI, ou "global") ou custo dos fornecimentos da própria fase
        "obra": {"base_modo": "informado", "base_valor": 0.0, "base_opcao": "", "base_parte": "obra",
                 "meses": int(pc.get("meses", 6)), "curva": pc.get("curva", "s")},
        "percentual": {"pct": float(params.get("fee_pct_padrao", 0.06)), "forma": pc.get("forma", "medicoes"),
                       "parcela_fixa": 0.0},
        "pacote": {
            "forma": "mensal", "horas_mes": 0.0, "meses": int(pk.get("meses", 6)), "acumula_saldo": False,
            "horas": 0.0, "validade_meses": int(pk.get("validade_meses", 12)), "parcelas": int(pk.get("parcelas", 3)),
            "desconto": float(pk.get("desconto", 0.10)), "excedente_pct": float(pk.get("excedente_pct", 0.0)),
        },
        "desempenho": {
            "ativo": False,
            "economia_pct": float(de.get("economia_pct", 0.10)), "prazo_pct_semana": float(de.get("prazo_pct_semana", 0.02)),
            "retrabalho_meta": float(de.get("retrabalho_meta", 0.02)),
            "retrabalho_bonus_pct": float(de.get("retrabalho_bonus_pct", 0.05)), "teto_pct": float(de.get("teto_pct", 0.30)),
            "cenario": {"economia": 0.05, "dias_antecipados": 15, "retrabalho_ok": True},
        },
        "pagamento": [],        # marcos manuais (escopo fechado); vazio = padrão calculado
    }


def proxima_fase(opcao):
    usados = {f["id"] for f in opcao.get("fases", [])}
    n = 1
    while f"F{n}" in usados:
        n += 1
    return f"F{n}"


def nova_opcao(letra, params, nome=None):
    return {
        "id": letra,
        "nome": nome or f"Opção {letra}",
        "modalidade": "fases",
        "fases": [nova_fase("F1", params)],
        "itens": [],
        "fornecimentos": [],
        "prazo_execucao_dias": 0,
        "prazo_fornecimento_dias": 0,   # lead time dos equipamentos (estimativa)
        "turnkey_dispensas": [],        # etapas fora da estimativa do valor global
    }


def novo_fornecimento(descricao="", categoria="material", unid="un", qtd=1.0, custo_unit=0.0, fonte="", codigo="",
                      data_base="", fase="F1"):
    """Item de fornecimento ou subcontratação; `referencias` guarda a cesta de preços do item."""
    return {"uid": uuid.uuid4().hex[:8], "descricao": descricao, "categoria": categoria, "unid": unid, "qtd": float(qtd),
            "custo_unit": float(custo_unit), "fonte": fonte, "codigo": codigo, "data_base": data_base, "referencias": [],
            "fase": fase}


def novo_item(serv, fase="F1"):
    return {
        "servico": serv["id"],
        "fase": fase,
        "dados": ct.valores_padrao(serv),
        "ajustes": {},          # sobrescreve fatores globais só neste serviço: {"complexidade": "alta"}
        "fator_manual": 1.0,
        "descricao": "",        # nome do serviço na proposta; vazio = nome do catálogo
    }


def _migrar_fases(o, params):
    """Arquivos anteriores às fases: a opção vira uma fase única com a cobrança do antigo modelo de preço,
    reproduzindo exatamente a conta antiga (o % antigo era fixo sobre a obra informada ou sobre o custo
    dos fornecimentos)."""
    o["modalidade"] = {"turnkey": "estimativa", "servicos": "fases"}.get(o.get("modalidade"), o.get("modalidade") or "fases")
    if not o.get("fases"):
        modelo = o.get("modelo_preco", "fechado")
        fase = nova_fase("F1", params, "Fase única" if o["modalidade"] == "fases" else "Obra",
                         {"hora": "hora", "fee": "percentual"}.get(modelo, "fechado"))
        if modelo == "fee":
            base = float(o.get("fee_base") or 0)
            fase["percentual"].update(pct=float(o.get("fee_pct") or 0), forma="fixo_global")
            fase["obra"].update(base_valor=base, base_modo="informado" if base > 0 else "fornecimentos", meses=0)
        fase["pagamento"] = list(o.get("pagamento") or [])
        o["fases"] = [fase]
    for k in ("modelo_preco", "fee_pct", "fee_base", "pagamento"):
        o.pop(k, None)
    for i, f in enumerate(o["fases"]):
        base = nova_fase(f.get("id") or f"F{i + 1}", params)
        for k, v in base.items():
            if isinstance(v, dict):
                f[k] = {**v, **f.get(k, {})}
            else:
                f.setdefault(k, v)
        f["desempenho"]["cenario"] = {**base["desempenho"]["cenario"], **f["desempenho"].get("cenario", {})}
    ids = [f["id"] for f in o["fases"]]
    for x in o["itens"] + o["fornecimentos"]:
        if x.get("fase") not in ids:
            x["fase"] = ids[0]


def padrao(params, numero=None):
    hoje = dt.date.today()
    return {
        "versao": 1,
        "numero": numero or f"PC-KTK-001/{hoje.year}",
        "revisao": "00",
        "data": hoje.isoformat(),
        "validade_dias": 15,
        "prazo_pagamento_dias": 15,
        "cliente": {"razao": "", "contato": "", "signatario": "", "endereco": "", "cidade": "Rio de Janeiro", "uf": "RJ"},
        "objeto": "",
        "contexto": dict(CONTEXTO_PADRAO),
        "parametros": copy.deepcopy(params),
        "opcoes": [nova_opcao("A", params)],
        "viabilidade": vb.padrao(),
    }


def completar(p, cat, params):
    """Preenche chaves ausentes (arquivos antigos ou feitos à mão) sem mexer no que existe."""
    base = padrao(params, p.get("numero"))
    for k, v in base.items():
        if k not in p:
            p[k] = copy.deepcopy(v)
    p["cliente"] = {**base["cliente"], **p.get("cliente", {})}
    p["contexto"] = {**CONTEXTO_PADRAO, **p.get("contexto", {})}
    p["parametros"] = pm.mesclar(params, p.get("parametros"))
    p["viabilidade"] = vb.completar(p.get("viabilidade"))
    if not p["opcoes"]:
        p["opcoes"] = [nova_opcao("A", params)]
    for o in p["opcoes"]:
        o.setdefault("itens", [])
        o["fornecimentos"] = [{**novo_fornecimento(), **f} for f in o.get("fornecimentos", [])]
        _migrar_fases(o, p["parametros"])       # antes dos padrões: precisa ver o modelo de preço antigo
        for k, v in nova_opcao(o.get("id", "A"), params).items():
            o.setdefault(k, copy.deepcopy(v))
        for it in o["itens"]:
            serv = ct.servico(cat, it["servico"])
            dados = ct.valores_padrao(serv)
            dados.update({k: v for k, v in it.get("dados", {}).items() if k in dados})
            it["dados"] = dados
            it.setdefault("ajustes", {})
            it.setdefault("fator_manual", 1.0)
            it.setdefault("descricao", "")
    return p


def salvar_json(p):
    return json.dumps(p, ensure_ascii=False, indent=1)


def carregar_json(texto):
    p = json.loads(texto)
    if not isinstance(p, dict) or "opcoes" not in p:
        raise ValueError("o arquivo não é uma proposta (falta a lista 'opcoes')")
    return p


def proxima_letra(p):
    usadas = {o["id"] for o in p["opcoes"]}
    for letra in string.ascii_uppercase:
        if letra not in usadas:
            return letra
    raise ValueError("limite de 26 opções")


def duplicar_opcao(p, indice, nivel=None, nome=None):
    """Copia uma opção; com `nivel`, troca o campo 'nivel' (2D/3D/BIM) de todos os serviços que o têm."""
    nova = copy.deepcopy(p["opcoes"][indice])
    nova["id"] = proxima_letra(p)
    nova["nome"] = nome or f"Opção {nova['id']}"
    for f in nova.get("fases", []):
        f["pagamento"] = []
    if nivel:
        for it in nova["itens"]:
            if "nivel" in it["dados"]:
                it["dados"]["nivel"] = nivel
    p["opcoes"].append(nova)
    return nova
