import pytest

from orcamento.bdi import bdi, bdi_implicito, fora_da_faixa


def test_bdi_formula_tcu():
    valor = bdi(0.04, 0.008, 0.0127, 0.0123, 0.074, 0.0615)
    assert valor == pytest.approx(0.2288, abs=1e-3)


def test_bdi_implicito():
    assert bdi_implicito(122.88, 100) == pytest.approx(0.2288, abs=1e-3)


def test_bdi_rejeita_impostos_iguais_a_um():
    with pytest.raises(ValueError):
        bdi(0.04, 0.008, 0.0127, 0.0123, 0.074, 1)


def test_fora_da_faixa():
    faixa = {"min": 0.20, "max": 0.25, "fonte": "Acórdão TCU 2622/2013"}
    assert fora_da_faixa(0.2288, faixa) is None
    assert fora_da_faixa(0.20, faixa) is None
    assert fora_da_faixa(0.25, faixa) is None

    abaixo = fora_da_faixa(0.15, faixa)
    assert abaixo is not None and "abaixo" in abaixo and "Acórdão TCU 2622/2013" in abaixo

    acima = fora_da_faixa(0.30, faixa)
    assert acima is not None and "acima" in acima and "Acórdão TCU 2622/2013" in acima
