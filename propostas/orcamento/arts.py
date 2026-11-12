"""Plano de ARTs (B7): quantas ARTs o orçamento exige, quais e a taxa de cada uma.

Funções puras. As regras são provisórias (confirmar com o CREA-RJ) e editáveis em
`parametros["art"]["regras"]`.
"""
from . import motor

ATIVIDADES = ("projeto", "execucao", "fiscalizacao", "laudo", "manutencao", "consultoria")

# Serviço do catálogo → atividade. Vale o id exato; senão, o prefixo mais longo; senão, "consultoria".
ATIVIDADE_POR_SERVICO = {
    "hvac.carga_termica": "projeto", "hvac.projeto": "projeto", "hvac.asbuilt": "projeto",
    "hvac.energetica": "consultoria", "hvac.viabilidade": "consultoria", "hvac.cfd": "consultoria",
    "hvac.inspecao_conformidade": "laudo", "hvac.desempenho": "laudo", "hvac.qai": "laudo",
    "hvac.tab": "laudo", "hvac.comissionamento": "laudo",
    "hvac.pmoc": "manutencao", "hvac.emergencial": "manutencao",
    "geral.acompanhamento_obra": "fiscalizacao", "geral.gestao_obra": "fiscalizacao",
    "geral.planejamento_obra": "consultoria",
    "mec.nr13_inspecao": "laudo", "inc.vistoria": "laudo", "st.": "laudo",
}

# Módulo de escopo (orcamento/escopos.py) → atividade.
ATIVIDADE_POR_MODULO = {
    "projeto": "projeto", "acompanhamento": "fiscalizacao", "execucao": "execucao",
    "inspecao_laudo": "laudo", "desempenho": "laudo",
}

MODALIDADE_PADRAO = "mecanica"

REGRAS_PADRAO = {
    "agrupar_por_profissional": False,
    "separar_modalidade": True,
    "subcontratado_no_preco": False,
    "provisorio": True,
    "nota": "Regras provisórias — confirmar com o CREA-RJ.",
}


def regras(params):
    """Regras efetivas: padrão sobrescrito por `params["art"]["regras"]`."""
    r = dict(REGRAS_PADRAO)
    r.update((params.get("art") or {}).get("regras") or {})
    return r


def _atividade_servico(sid):
    if sid in ATIVIDADE_POR_SERVICO:
        return ATIVIDADE_POR_SERVICO[sid]
    achados = [p for p in ATIVIDADE_POR_SERVICO if p.endswith(".") or p.endswith("_") if sid.startswith(p)]
    if achados:
        return ATIVIDADE_POR_SERVICO[max(achados, key=len)]
    return "consultoria"


def _art_servico(cat, sid):
    """(atividade, modalidade) de um serviço; `art` no catálogo sobrescreve o padrão."""
    serv = next((s for s in cat.get("servicos", []) if s["id"] == sid), {})
    art = serv.get("art") or {}
    return art.get("atividade") or _atividade_servico(sid), art.get("modalidade") or MODALIDADE_PADRAO


def _eletrico(x):
    return x.get("funcao") == "Eletricista" or x.get("modalidade") == "eletrica"


def _necessidades(opcao, cat, fase):
    """Lista de (atividade, modalidade, tipo) exigidas por uma fase, pelos serviços e fornecimentos."""
    fid, nec = fase["id"], []
    for it in opcao.get("itens", []):
        if it.get("fase") == fid:
            a, m = _art_servico(cat, it["servico"])
            nec.append((a, m, "obra_servico"))
    for f in opcao.get("fornecimentos", []):
        if f.get("fase") != fid:
            continue
        if f.get("categoria") == "subcontrato" and f.get("art_propria"):
            nec.append(("execucao", f.get("modalidade") or MODALIDADE_PADRAO, "subcontratado"))
        else:
            nec.append(("execucao", "eletrica" if _eletrico(f) else MODALIDADE_PADRAO, "obra_servico"))
    if not nec:
        return []  # fase sem serviço nem item: sem ART
    return nec


def planejar_arts(opcao, cat, params, valores_fase=None):
    """Plano de ARTs da opção: uma por (atividade, modalidade) nas fases ativas.

    `valores_fase`: {fase_id: preço}; o valor base da ART é a soma das suas fases.
    Com `agrupar_por_profissional`, uma ART por modalidade. Subcontratado com ART própria
    gera ART do tipo "subcontratado", dentro do preço só se `subcontratado_no_preco`.
    """
    rg, vf = regras(params), valores_fase or {}
    grupos = {}  # chave → ART
    for fase in opcao.get("fases", []):
        if not fase.get("ativa", True):
            continue
        for ativ, mod, tipo in _necessidades(opcao, cat, fase):
            if not rg["separar_modalidade"]:
                mod = MODALIDADE_PADRAO if tipo != "subcontratado" else mod
            if tipo == "subcontratado":
                chave = (tipo, "-", mod)
            elif rg["agrupar_por_profissional"]:
                chave = (tipo, "-", mod)
            else:
                chave = (tipo, ativ, mod)
            art = grupos.get(chave)
            if art is None:
                art = grupos[chave] = {"tipo": tipo, "modalidade": mod, "atividades": [], "fases": [],
                                       "valor_base": 0.0, "taxa": 0.0, "no_preco": True, "motivo": ""}
            if ativ not in art["atividades"]:
                art["atividades"].append(ativ)
            if fase["id"] not in art["fases"]:
                art["fases"].append(fase["id"])
                art["valor_base"] += float(vf.get(fase["id"], 0) or 0)
    saida = []
    for art in grupos.values():
        art["taxa"] = motor.valor_art(params, art["valor_base"])
        ativs = ", ".join(art["atividades"])
        if art["tipo"] == "subcontratado":
            art["no_preco"] = bool(rg["subcontratado_no_preco"])
            art["motivo"] = "ART própria do subcontratado" + ("" if art["no_preco"] else " (fora do preço)")
        elif art["modalidade"] == "eletrica":
            art["motivo"] = f"Modalidade elétrica exige profissional próprio ({ativs})"
        else:
            art["motivo"] = f"Atividade: {ativs}"
        saida.append(art)
    return saida


def total_arts(arts):
    """Soma das taxas das ARTs que entram no preço."""
    return float(sum(a["taxa"] for a in arts if a.get("no_preco")))
