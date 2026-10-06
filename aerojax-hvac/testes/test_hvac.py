"""
Testes de verificação. Rodar com:  python -m pytest testes -q

Cada teste compara com uma referência independente (tabela de norma, solução
analítica ou lei de conservação). Se algum falhar depois de você alterar o código,
o resultado das simulações não é mais confiável.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jax
import jax.numpy as jnp
import pytest

from hvac import psicrometria as psi
from hvac import conforto
from hvac.sala2d import (Sala, Abertura, FonteCalor, Insuflamento, montar_geometria,
                         estado_inicial, simular, indicadores, passo)


# ------------------------------------------------------------- psicrometria
@pytest.mark.parametrize("t, pws_ref", [(-10.0, 259.90), (0.0, 611.21), (20.0, 2339.3), (25.0, 3169.9),
                                        (40.0, 7384.9)])
def test_pressao_saturacao_ashrae(t, pws_ref):
    """ASHRAE Fundamentals 2017, cap. 1, tabela 3."""
    assert float(psi.pressao_saturacao(t)) == pytest.approx(pws_ref, rel=2e-3)


def test_ida_e_volta_umidade():
    w = psi.umidade_absoluta(27.0, 0.55)
    assert float(psi.umidade_relativa(27.0, w)) == pytest.approx(0.55, rel=1e-5)
    td = psi.ponto_orvalho(w)
    assert float(psi.umidade_relativa(td, w)) == pytest.approx(1.0, rel=1e-4)


def test_bulbo_umido_consistente():
    w = psi.umidade_absoluta_tbu(35.0, 26.0)
    assert float(psi.bulbo_umido(35.0, w)) == pytest.approx(26.0, abs=0.02)


def test_adp_serpentina():
    t_adp, bf = 11.0, 0.15
    w_ent = psi.umidade_absoluta(26.0, 0.55)
    t_sai, w_sai = psi.serpentina_resfriamento(26.0, w_ent, t_adp, bf)
    t_adp2, bf2 = psi.adp_serpentina(26.0, w_ent, t_sai, w_sai)
    assert float(t_adp2) == pytest.approx(t_adp, abs=0.05)
    assert float(bf2) == pytest.approx(bf, abs=0.005)


# ------------------------------------------------------------- conforto
@pytest.mark.parametrize("ta, tr, var, ur, met, clo, pmv_ref", [
    # ISO 7730:2005, tabela D.1
    (22.0, 22.0, 0.1, 0.60, 1.2, 0.5, -0.75),
    (27.0, 27.0, 0.1, 0.60, 1.2, 0.5, 0.77),
    (27.0, 27.0, 0.3, 0.60, 1.2, 0.5, 0.44),
    (23.5, 25.5, 0.1, 0.60, 1.2, 0.5, -0.01),
    (23.5, 25.5, 0.3, 0.60, 1.2, 0.5, -0.55),
])
def test_pmv_iso7730(ta, tr, var, ur, met, clo, pmv_ref):
    assert float(conforto.pmv(ta, tr, var, ur, met, clo)) == pytest.approx(pmv_ref, abs=0.015)


def test_ppd_minimo():
    assert float(conforto.ppd(0.0)) == pytest.approx(5.0)


# ------------------------------------------------------------- CFD
@pytest.fixture(scope="module")
def caso_pequeno():
    sala = Sala(nx=25, ny=14,
                aberturas=(Abertura("esquerda", 2.2, 2.4, "insuflamento"),
                           Abertura("esquerda", 2.6, 2.8, "retorno")),
                fontes=(FonteCalor(2.8, 3.2, 0.0, 1.2, 200.0, 100.0),),
                fluxo_direita=30.0)
    geo = montar_geometria(sala)
    ins = Insuflamento(jnp.asarray(500.0), jnp.asarray(20.0), jnp.asarray(18.0),
                       psi.umidade_absoluta(18.0, 0.9))
    return sala, geo, ins


def test_aberturas_na_mesma_face_sao_rejeitadas():
    with pytest.raises(ValueError):
        montar_geometria(Sala(nx=25, ny=14))      # aberturas padrão não cabem em células de 20 cm


def test_divergencia_nula(caso_pequeno):
    sala, geo, ins = caso_pequeno
    e = estado_inicial(sala, 24.0, 0.010)
    for _ in range(20):
        e = passo(e, sala, geo, ins, 0.05)
    div = (e.u[1:] - e.u[:-1]) / sala.dx + (e.v[:, 1:] - e.v[:, :-1]) / sala.dy
    assert float(jnp.abs(div).max()) < 1e-4


def test_balanco_energia_e_umidade(caso_pequeno):
    """Em regime permanente, o ar insuflado retira exatamente as cargas impostas."""
    sala, geo, ins = caso_pequeno
    carga_sens = 200.0 + 30.0 * sala.altura * sala.profundidade
    e0 = estado_inicial(sala, 21.0, 0.0105)
    _, med = jax.jit(lambda e: simular(sala, geo, ins, e, 2500.0, 0.08, 500.0))(e0)
    ind = indicadores(sala, geo, ins, med)
    assert float(ind["capacidade_sensivel_W"]) == pytest.approx(carga_sens, rel=0.02)
    assert float(ind["capacidade_latente_W"]) == pytest.approx(100.0, rel=0.03)


def test_gradiente_confere_com_diferencas_finitas(caso_pequeno):
    sala, geo, _ = caso_pequeno
    e0 = estado_inicial(sala, 22.0, 0.0105)

    def f(x):
        ins = Insuflamento(x[0], x[1], x[2], psi.umidade_absoluta(x[2], 0.9))
        _, med = simular(sala, geo, ins, e0, 120.0, 0.08, 40.0, passos_por_bloco=50)
        return indicadores(sala, geo, ins, med)["PMV_medio"]

    x = jnp.array([500.0, 20.0, 18.0])
    g = jax.jit(jax.grad(f))(x)
    fj = jax.jit(f)
    for i, h in enumerate([10.0, 2.0, 0.2]):
        e = jnp.zeros(3).at[i].set(h)
        fd = (float(fj(x + e)) - float(fj(x - e))) / (2 * h)
        assert float(g[i]) == pytest.approx(fd, rel=0.1, abs=1e-5)


# ------------------------------------------------------------- projeto / interface
from hvac import projeto as pj
from hvac import importar_dxf as idxf

PASTA_DXF = os.path.join(os.path.dirname(__file__), "..", "exemplos", "dxf")


def test_importar_corte_dxf():
    dados, _ = idxf.importar_corte(os.path.join(PASTA_DXF, "corte_escritorio.dxf"))
    assert dados["sala"]["largura"] == pytest.approx(5.0)
    assert dados["sala"]["altura"] == pytest.approx(2.8)
    tipos = {(a["tipo"], a["parede"]) for a in dados["aberturas"]}
    assert tipos == {("insuflamento", "esquerda"), ("retorno", "esquerda")}
    assert len(dados["obstaculos"]) == 1


def test_importar_planta_dxf_em_milimetros():
    dados, avisos, _ = idxf.importar_planta(os.path.join(PASTA_DXF, "planta_escritorio.dxf"), eixo="x")
    assert dados["sala"]["largura"] == pytest.approx(5.0)        # 5000 mm
    assert dados["sala"]["profundidade"] == pytest.approx(4.0)
    pessoas = [f for f in dados["fontes"] if "pessoa" in f["nome"]]
    assert sum(f["sensivel_w"] for f in pessoas) == pytest.approx(140.0)   # 2 pessoas
    projeto = pj.completar(dict(pj.projeto_padrao(), **dados))
    assert pj.validar(projeto) == []


def test_projeto_json_ida_e_volta():
    p = pj.projeto_padrao()
    assert pj.carregar_json(pj.salvar_json(p)) == p


def test_cargas_totais_e_dimensionamento():
    p = pj.projeto_padrao()
    cg = pj.cargas_totais(p)
    assert cg["sensivel"] == pytest.approx(150 + 100 + 40 * 2.8 * 4 + 10 * 5 * 4)
    assert cg["latente"] == pytest.approx(110)
    d = pj.dimensionar_insuflamento(p)
    assert d["temperatura"] == pytest.approx(19.6, abs=0.1)


def test_validacao_aponta_erros():
    p = pj.projeto_padrao()
    p["aberturas"] = [a for a in p["aberturas"] if a["tipo"] == "insuflamento"]
    assert any("retorno" in e for e in pj.validar(p))
