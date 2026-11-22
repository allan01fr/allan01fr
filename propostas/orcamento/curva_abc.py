"""Curva ABC (Pareto) para classificar itens de orçamento pelo custo."""

from __future__ import annotations


def curva_abc(itens: list[dict], limite_a: float = 0.80, limite_b: float = 0.95) -> list[dict]:
    """Ordena os itens por custo decrescente e classifica-os em A, B ou C.

    Cada item retornado é uma cópia do original acrescida de:
    - ``participacao``: fração do custo total representada pelo item;
    - ``acumulado``: soma das participações até o item, inclusive;
    - ``classe``: "A" se o acumulado for <= ``limite_a`` (o primeiro item é
      sempre A), "B" se for <= ``limite_b`` e "C" nos demais casos.

    Se o total for zero (ou a lista estiver vazia), cada item recebe
    ``participacao`` e ``acumulado`` iguais a 0 e classe "C".

    Args:
        itens: lista de dicionários com as chaves "descricao" e "custo".
        limite_a: acumulado máximo da classe A.
        limite_b: acumulado máximo da classe B.

    Returns:
        Nova lista de dicionários, ordenada por custo decrescente.
    """
    ordenados = sorted(itens, key=lambda item: item["custo"], reverse=True)
    total = sum(item["custo"] for item in ordenados)

    if not total:
        return [
            {**item, "participacao": 0.0, "acumulado": 0.0, "classe": "C"}
            for item in ordenados
        ]

    resultado = []
    acumulado = 0.0
    for indice, item in enumerate(ordenados):
        participacao = item["custo"] / total
        acumulado += participacao
        if indice == 0 or acumulado <= limite_a:
            classe = "A"
        elif acumulado <= limite_b:
            classe = "B"
        else:
            classe = "C"
        resultado.append(
            {**item, "participacao": participacao, "acumulado": acumulado, "classe": classe}
        )
    return resultado


def resumo_abc(curva: list[dict]) -> dict:
    """Agrega uma curva ABC por classe.

    Args:
        curva: lista retornada por ``curva_abc``.

    Returns:
        Dicionário com as chaves "A", "B" e "C", cada uma com ``itens``
        (quantidade), ``custo`` (soma dos custos) e ``participacao`` (soma
        das participações). Classes sem itens aparecem zeradas.
    """
    resumo = {classe: {"itens": 0, "custo": 0.0, "participacao": 0.0} for classe in ("A", "B", "C")}
    for item in curva:
        dados = resumo[item["classe"]]
        dados["itens"] += 1
        dados["custo"] += item["custo"]
        dados["participacao"] += item["participacao"]
    return resumo
