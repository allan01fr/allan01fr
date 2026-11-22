import pytest

from app.nucleo.documentos import (
    somente_digitos,
    validar_cnpj,
    validar_cpf,
    validar_cpf_cnpj,
)


def test_somente_digitos_remove_pontuacao_e_espacos():
    assert somente_digitos(" 529.982.247-25 ") == "52998224725"
    assert somente_digitos("11.222.333/0001-81") == "11222333000181"


@pytest.mark.parametrize(
    "entrada,saida",
    [
        ("529.982.247-25", "52998224725"),
        (" 111.444.777-35 ", "11144477735"),
        ("52998224725", "52998224725"),
    ],
)
def test_cpf_valido(entrada, saida):
    assert validar_cpf(entrada) == saida


@pytest.mark.parametrize(
    "ruim",
    ["529.982.247-24", "111.111.111-11", "00000000000", "5299822472", "52998224725a"],
)
def test_cpf_invalido(ruim):
    with pytest.raises(ValueError, match="CPF inválido."):
        validar_cpf(ruim)


@pytest.mark.parametrize(
    "entrada,saida",
    [
        ("11.222.333/0001-81", "11222333000181"),
        ("11444777000161", "11444777000161"),
    ],
)
def test_cnpj_valido(entrada, saida):
    assert validar_cnpj(entrada) == saida


@pytest.mark.parametrize(
    "ruim",
    ["11.222.333/0001-82", "11.111.111/1111-11", "1122233300018"],
)
def test_cnpj_invalido(ruim):
    with pytest.raises(ValueError, match="CNPJ inválido."):
        validar_cnpj(ruim)


def test_cpf_cnpj_escolhe_pelo_tamanho():
    assert validar_cpf_cnpj("529.982.247-25") == "52998224725"
    assert validar_cpf_cnpj("11.222.333/0001-81") == "11222333000181"
    with pytest.raises(ValueError, match="Informe um CPF"):
        validar_cpf_cnpj("123")
