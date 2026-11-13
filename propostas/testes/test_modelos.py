import os

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import modelos as md
from orcamento import motor


def _retrofit(cat, params):
    caminho = next(e for e in EXEMPLOS if e.endswith("hvac_retrofit_fases.json"))
    return abrir_exemplo(caminho, cat, params)


def test_duplicar_gera_ids_novos_e_mesmo_preco(cat, params):
    p = _retrofit(cat, params)
    d = md.duplicar_proposta(p)
    assert d["origem"] == p["numero"]
    assert d["numero"] == "" and d["data"] == ""
    assert [o["id"] for o in d["opcoes"]] == [o["id"] for o in p["opcoes"]]  # ids A/B mantidos
    ids_fases_orig = {f["id"] for o in p["opcoes"] for f in o["fases"]}
    ids_fases_dup = {f["id"] for o in d["opcoes"] for f in o["fases"]}
    assert ids_fases_orig.isdisjoint(ids_fases_dup)
    fases_dup = {f["id"] for o in d["opcoes"] for f in o["fases"]}
    for o in d["opcoes"]:
        for x in o["itens"] + o["fornecimentos"]:
            assert x["fase"] in fases_dup
    precos_orig = [r["preco"] for r in motor.precificar(cat, p)["opcoes"]]
    precos_dup = [r["preco"] for r in motor.precificar(cat, d)["opcoes"]]
    assert precos_orig == precos_dup


def test_kits_carregam_com_fonte_provisoria():
    kits = md.carregar_kits()
    assert [k["id"] for k in kits] == ["split_12k_padrao", "split_24k_padrao", "pmoc_visita_mensal"]
    assert all(k["itens"] and k["fonte"].startswith("provisório") for k in kits)


def test_aplicar_kit_acrescenta_itens_na_fase():
    kit = md.carregar_kits()[0]
    opcao = {"id": "A", "fases": [{"id": "F1"}, {"id": "F2"}], "fornecimentos": []}
    devolvida = md.aplicar_kit(opcao, kit, fase_id="F2")
    assert devolvida is opcao
    assert len(opcao["itens_execucao"]) == len(kit["itens"])
    assert {i["fase"] for i in opcao["itens_execucao"]} == {"F2"}
    assert opcao["fornecimentos"] == []
