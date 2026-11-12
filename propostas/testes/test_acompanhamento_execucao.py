"""Acompanhamento de obra ligado à execução: % sobre o valor da execução e pacote pelas horas da obra."""
import pytest

from orcamento import escopos, modelos, motor
from orcamento import execucao_itens as ei
from orcamento import proposta as pp

KIT = next(k for k in modelos.carregar_kits() if k["id"] == "split_12k_padrao")


def _proposta(cat, params, ordem=("execucao", "acompanhamento")):
    p = pp.completar(pp.padrao(params), cat, params)
    o = p["opcoes"][0]
    modelos.aplicar_kit(o, KIT)      # itens de execução antes dos módulos: a ligação só vale com execução a precificar
    for m in ordem:
        escopos.incluir(o, m, cat, p["parametros"])
    ei.sincronizar_fornecimentos(o, p["parametros"])
    return p, o


def _fases(p, cat):
    r = motor.precificar_opcao(cat, p, p["opcoes"][0])
    return r, {f["nome"]: f for f in r["fases"]}


@pytest.mark.parametrize("ordem", [("execucao", "acompanhamento"), ("acompanhamento", "execucao")])
def test_base_execucao_e_percentual(cat, params, ordem):
    p, o = _proposta(cat, params, ordem)
    ac = next(f for f in o["fases"] if f["modulo"] == "acompanhamento")
    assert ac["cobranca"] == "percentual" and ac["obra"]["base_modo"] == "execucao" and ac["pacote"]["forma"] == "obra"
    r, fs = _fases(p, cat)
    ex, a = fs["Execução"], fs["Acompanhamento de obra"]
    assert ex["preco_fornec"] > 0 and a["base"] == pytest.approx(ex["preco_fornec"])
    assert a["base_origem"] == "valor da execução desta opção"
    assert a["honorarios"] == pytest.approx(ac["percentual"]["pct"] * ex["preco_fornec"])


def test_base_global_e_sem_execucao(cat, params):
    p, o = _proposta(cat, params)
    ac = next(f for f in o["fases"] if f["modulo"] == "acompanhamento")
    ac["obra"]["base_parte"] = "global"
    _, fs = _fases(p, cat)
    assert fs["Acompanhamento de obra"]["base"] == pytest.approx(fs["Execução"]["preco"])
    ex = next(f for f in o["fases"] if f["modulo"] == "execucao")
    ex["ativa"] = False
    res = motor.precificar(cat, p)
    assert res["opcoes"][0]["fases"][0]["base"] == 0
    assert any("sem base" in a for a in motor.avisos(p, res["opcoes"]))


def test_pacote_obra_horas(cat, params):
    p, o = _proposta(cat, params)
    ac = next(f for f in o["fases"] if f["modulo"] == "acompanhamento")
    ac["cobranca"] = "pacote"
    ac["pacote"].update(horas_dia_obra=3.0, horas_fixas=10.0, desconto=0.0)
    dias = ei.calcular_execucao(o, p["parametros"])["plano"]["prazo_dias_uteis"]
    _, fs = _fases(p, cat)
    pk = fs["Acompanhamento de obra"]["pacote"]
    assert pk["dias_obra"] == dias and pk["horas"] == pytest.approx(dias * 3.0 + 10.0)
    assert pk["honorarios"] == pytest.approx(pk["horas"] * pk["taxa"])


def test_obra_pequena_reduz_horas_do_acompanhamento():
    import json
    from orcamento import motor, proposta as pp, escopos, modelos, execucao_itens as ei
    P = pp.padrao(json.load(open("dados/parametros.json")))
    cat = json.load(open("dados/catalogo.json"))
    O = P["opcoes"][0]
    for m in ("projeto", "acompanhamento", "execucao"):
        escopos.incluir(O, m, cat, P["parametros"])
    kit = {k["id"]: k for k in modelos.carregar_kits()}["split_12k_padrao"]
    for _ in range(10):
        modelos.aplicar_kit(O, kit, ei.config_da_opcao(O)["fase"])
    ei.config_da_opcao(O)["prazo_alvo_dias"] = 10
    ei.sincronizar_fornecimentos(O, P["parametros"])
    antes = motor.precificar(cat, P)["opcoes"][0]["fases"][1]["total_h"]
    assert escopos.dimensionar_acompanhamento(O, P["parametros"]) == 1
    depois = motor.precificar(cat, P)["opcoes"][0]["fases"][1]["total_h"]
    assert depois < antes / 2
