from orcamento import tabela_referencia as tr
from orcamento import unidades as un


def test_escalonada_1200_m2():
    t = tr.carregar()
    t["itens"][0].update(modo="escalonada", minimo=0)
    r = tr.calcular(t, t["itens"][0]["id"], 1200)
    assert r["valor"] == round(500 * 4.83 + 700 * 4.11, 2)
    assert r["provisorio"] and r["data_base"] == "2023-01"


def test_cheia_usa_taxa_da_faixa_para_toda_area():
    t = tr.carregar()
    assert tr.calcular(t, "clim_projeto_basico", 1200)["valor"] == round(1200 * 4.11, 2)
    assert tr.calcular(t, "clim_projeto_basico", 800)["valor"] == round(800 * 4.11, 2)


def test_minimo():
    t = tr.carregar()
    r = tr.calcular(t, "clim_projeto_basico", 10)
    assert r["valor"] == 2500.00 and any("mínimo" in l for l in r["memoria"])


def test_acrescimo_deslocamento_e_indice():
    t = tr.carregar()
    base = 1200 * 4.11
    r = tr.calcular(t, "clim_projeto_basico", 1200, acrescimos=("reforma",), km=10, fator_indice=1.1)
    esperado = (base * 1.2 + 2 * 10 * t["deslocamento_rs_km"]) * 1.1
    assert r["valor"] == round(esperado, 2)


def test_unidades():
    assert round(un.tr_para_kw(10), 2) == 35.17
    assert round(un.kw_para_tr(3.517), 6) == 1
    assert un.capacidade_de_area(100, 20) == {"valor": 5, "estimado": True,
                                              "premissa": un.capacidade_de_area(100, 20)["premissa"]}
