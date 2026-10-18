import pytest

from orcamento.expressao import ErroExpressao, avaliar, nomes


def test_aritmetica_funcoes_e_condicional():
    ctx = {"area": 1500.0, "nivel__bim": 1.0, "nivel__2d": 0.0, "terminais": 60.0, "amostragem": 0.3}
    assert avaliar("terminais*amostragem", ctx) == pytest.approx(18.0)
    assert avaliar("area*(0.0055*nivel__2d + 0.037*nivel__bim)", ctx) == pytest.approx(55.5)
    assert avaliar("ceil(terminais/7)", ctx) == 9
    assert avaliar("max(1, min(3, terminais))", ctx) == 3
    assert avaliar("2 if area > 1000 else 1", ctx) == 2
    assert avaliar("", ctx) == 0.0


def test_nomes_ignora_funcoes():
    assert nomes("ceil(a/b) + max(c, 1)") == {"a", "b", "c"}


@pytest.mark.parametrize("perigosa", [
    "__import__('os')", "a.__class__", "x[0]", "(lambda: 1)()", "'texto'", "open('f')", "[i for i in x]", "True",
])
def test_recusa_codigo_fora_da_aritmetica(perigosa):
    with pytest.raises(ErroExpressao):
        avaliar(perigosa, {"a": 1, "x": [1]})


def test_variavel_desconhecida_e_divisao_por_zero():
    with pytest.raises(ErroExpressao, match="desconhecida"):
        avaliar("area*2", {})
    with pytest.raises(ErroExpressao, match="zero"):
        avaliar("1/a", {"a": 0})
