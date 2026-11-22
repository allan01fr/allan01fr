"""Testes da curva ABC."""

import pytest

from orcamento.curva_abc import curva_abc, resumo_abc

# Total 1000; acumulados 0.40, 0.60, 0.70, 0.78, 0.84, 0.89, 0.93, 0.96, 0.985, 1.0
CUSTOS_EXEMPLO = [400, 200, 100, 80, 60, 50, 40, 30, 25, 15]
CLASSES_ESPERADAS = ["A", "A", "A", "A", "B", "B", "B", "C", "C", "C"]


def _itens(custos):
    return [{"descricao": f"item {i}", "custo": float(c)} for i, c in enumerate(custos)]


def test_ordenacao_por_custo_decrescente():
    curva = curva_abc(_itens([10, 30, 20]))

    assert [item["custo"] for item in curva] == [30.0, 20.0, 10.0]
    assert [item["descricao"] for item in curva] == ["item 1", "item 2", "item 0"]


def test_classes_no_exemplo_de_10_itens():
    curva = curva_abc(_itens(CUSTOS_EXEMPLO))

    assert [item["classe"] for item in curva] == CLASSES_ESPERADAS
    assert curva[0]["participacao"] == pytest.approx(0.40)
    assert curva[3]["acumulado"] == pytest.approx(0.78)
    assert curva[-1]["acumulado"] == pytest.approx(1.0)


def test_lista_vazia_e_total_zero():
    assert curva_abc([]) == []

    curva = curva_abc(_itens([0, 0]))
    assert all(item["classe"] == "C" for item in curva)
    assert all(item["participacao"] == 0 for item in curva)


def test_resumo_soma_participacao_igual_a_1():
    curva = curva_abc(_itens(CUSTOS_EXEMPLO))
    resumo = resumo_abc(curva)

    assert sum(dados["participacao"] for dados in resumo.values()) == pytest.approx(1.0)
    assert sum(dados["itens"] for dados in resumo.values()) == 10
    assert sum(dados["custo"] for dados in resumo.values()) == pytest.approx(1000.0)
    assert resumo["A"]["itens"] == 4
    assert resumo["B"]["itens"] == 3
    assert resumo["C"]["itens"] == 3
