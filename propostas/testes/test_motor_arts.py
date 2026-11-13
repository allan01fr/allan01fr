import copy

from orcamento import catalogo as ct
from orcamento import motor
from orcamento import proposta as pp


def _proposta(cat, params, plano):
    prop = pp.padrao(params)
    o = prop["opcoes"][0]
    o["fases"], o["itens"], o["fornecimentos"] = [pp.nova_fase("F1", params), pp.nova_fase("F2", params)], [], []
    o["itens"].append(pp.novo_item(ct.servico(cat, "hvac.projeto"), "F1"))
    f = pp.novo_fornecimento("x", fase="F2")
    f["categoria"] = "material"
    f.update({"custo": 20000} if "custo" in f else {})
    o["fornecimentos"].append(f)
    if plano:
        o["plano_arts"] = True
    return prop, o


def test_sem_plano_preco_identico(cat, params):
    prop, o = _proposta(cat, params, False)
    antes = motor.precificar_opcao(cat, prop, o)
    assert "arts" not in antes
    o2 = copy.deepcopy(o)
    o2["plano_arts"] = False
    assert motor.precificar_opcao(cat, prop, o2)["preco"] == antes["preco"]


def test_com_plano_duas_arts_e_total(cat, params):
    prop, o = _proposta(cat, params, True)
    r = motor.precificar_opcao(cat, prop, o)
    assert len(r["arts"]) == 2
    total = sum(a["taxa"] for a in r["arts"] if a["no_preco"])
    assert abs(r["art"] - total) < 1e-6
    assert abs(sum(f["art"] for f in r["fases"]) - total) < 1e-6


def test_plano_art_entra_no_preco(cat, params):
    prop, o = _proposta(cat, params, True)
    r = motor.precificar_opcao(cat, prop, o)
    assert r["preco"] > 0 and any(d["descricao"].startswith("Taxa de ART") for d in r["diretos"])
