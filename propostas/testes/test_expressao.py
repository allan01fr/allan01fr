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


@pytest.mark.parametrize("enorme", ["9**9**9", "10**400", "ceil(1e308)*ceil(1e308)", "1e308*10", "sqrt(0-1)", "(0-8)**0.5"])
def test_conta_enorme_ou_impossivel_vira_erro_na_hora(enorme):
    """O catálogo é editável por quem usa a prévia online: uma potência gigante não pode travar o servidor."""
    import time
    t = time.perf_counter()
    with pytest.raises(ErroExpressao):
        avaliar(enorme, {})
    assert time.perf_counter() - t < 1


def test_potencia_e_inteiros_comuns_continuam_exatos():
    assert avaliar("area**0.5 + 2**3", {"area": 100}) == pytest.approx(18.0)
    assert avaliar("ceil(terminais/7)*1000000", {"terminais": 60}) == 9000000
