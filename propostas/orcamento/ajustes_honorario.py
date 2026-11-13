"""Ajustes da empresa sobre o honorário do método ABRAVA/DNPC.

Todas as linhas levam o rótulo "Ajuste da empresa — ...": não fazem parte do método.
"""
from .erros import ErroEntrada

NIVEIS_RT = ("junior", "pleno", "senior", "expert")

# padrões da empresa (requisitos do usuário), não da ABRAVA
AJUSTES_PADRAO = {
    "fator_nivel_rt": {"junior": 0.70, "pleno": 1.00, "senior": 1.40, "expert": 1.80},
    "nivel_rt_padrao": "pleno",
    "adicional_planilha_pct": 0.10,
    "fator_licitacao": 0.85,
}

_P = "Ajuste da empresa — "


def aplicar_ajustes(honorario_metodo: float, ajustes_empresa: dict, ajustes_projeto: dict) -> dict:
    a = ajustes_projeto or {}
    nivel = a.get("nivel_rt") or ajustes_empresa["nivel_rt_padrao"]
    if nivel not in NIVEIS_RT or nivel not in ajustes_empresa["fator_nivel_rt"]:
        raise ErroEntrada("nivel_rt_desconhecido", f"Nível de RT desconhecido: {nivel}.", {"nivel": nivel})
    adicional = float(a.get("adicional_pct") or 0.0)
    desconto = float(a.get("desconto_pct") or 0.0)
    if not 0.0 <= desconto < 1.0:
        raise ErroEntrada("desconto_invalido", "O desconto deve estar entre 0 e 100%.", {"valor": desconto})
    if adicional < 0:
        raise ErroEntrada("percentual_invalido", "O adicional não pode ser negativo.", {"valor": adicional})
    extras = a.get("custos_extras") or []
    for e in extras:
        if float(e["valor"]) < 0:
            raise ErroEntrada("custo_extra_invalido", "Custo extra negativo.", {"descricao": e.get("descricao")})
    manual = a.get("valor_final_manual")
    if manual is not None and manual <= 0:
        raise ErroEntrada("valor_manual_invalido", "O valor final manual deve ser maior que zero.", {"valor": manual})

    fator_rt = ajustes_empresa["fator_nivel_rt"][nivel]
    linhas, sub = [], float(honorario_metodo)

    def add(rotulo, op, valor):
        nonlocal sub
        sub = sub * valor if op == "×" else sub + valor
        linhas.append({"rotulo": _P + rotulo, "operacao": op, "valor": valor, "subtotal": sub})

    add(f"nível do RT ({nivel})", "×", fator_rt)
    if a.get("inclui_planilha"):
        pct = a.get("adicional_planilha_pct")
        pct = ajustes_empresa["adicional_planilha_pct"] if pct is None else pct
        add("planilha quantitativa e orçamento", "×", 1 + pct)
    if adicional > 0:
        add("adicional", "×", 1 + adicional)
    if desconto > 0:
        add("desconto", "×", 1 - desconto)
    for e in extras:
        add(e["descricao"], "+", float(e["valor"]))

    final = manual or sub
    return {"honorario_metodo": honorario_metodo, "linhas": linhas, "honorario_calculado": sub,
            "valor_final_manual": manual, "honorario_final": final,
            "diferenca_manual": (final - sub) if manual else 0.0,
            "referencial_licitacao": sub * ajustes_empresa["fator_licitacao"],
            "nivel_rt": nivel, "fator_rt": fator_rt}
