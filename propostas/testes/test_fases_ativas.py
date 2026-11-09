"""Fases ligadas e desligadas: a fase desligada sai do preço, das horas, do cronograma e dos avisos."""
import copy
import glob
import json
import os

import pytest

from orcamento import motor
from orcamento import proposta as pp
from conftest import abrir_exemplo

RAIZ = os.path.join(os.path.dirname(__file__), "..")
EXEMPLOS = sorted(glob.glob(os.path.join(RAIZ, "exemplos", "*.json")))
RETROFIT = os.path.join(RAIZ, "exemplos", "hvac_retrofit_fases.json")


def opcao(res, oid):
    return next(r for r in res["opcoes"] if r["id"] == oid)


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_exemplos_sem_fase_desligada(caminho, cat, params):
    p = abrir_exemplo(caminho, cat, params)
    assert all(f["ativa"] is True and f["modulo"] == "" for o in p["opcoes"] for f in o["fases"])
    assert all(r["fases_desligadas"] == [] for r in motor.precificar(cat, p)["opcoes"])


def test_nova_fase_ativa_e_sem_modulo(params):
    f = pp.nova_fase("F1", params)
    assert f["ativa"] is True
    assert f["modulo"] == ""


def test_desligar_fase_equivale_a_remove_la(cat, params):
    # Opção A do retrofit tem 4 fases; a estimativa E (base da F4) não depende da F2, então é seguro desligá-la.
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    assert len(A["fases"]) >= 2
    fid = A["fases"][1]["id"]
    assert any(x["fase"] == fid for x in A["itens"] + A["fornecimentos"])

    removida = copy.deepcopy(p)
    RA = next(o for o in removida["opcoes"] if o["id"] == "A")
    RA["fases"] = [f for f in RA["fases"] if f["id"] != fid]
    RA["itens"] = [x for x in RA["itens"] if x["fase"] != fid]
    RA["fornecimentos"] = [x for x in RA["fornecimentos"] if x["fase"] != fid]

    A["fases"][1]["ativa"] = False
    A["fases"][1]["modulo"] = "m1"
    ligada = motor.precificar(cat, p)
    esperada = motor.precificar(cat, removida)
    a, e = opcao(ligada, "A"), opcao(esperada, "A")
    assert a["preco"] == pytest.approx(e["preco"])
    assert a["total_h"] == pytest.approx(e["total_h"])
    assert len(a["cronograma"]) == len(e["cronograma"])
    assert a["prazo_dias_uteis"] == e["prazo_dias_uteis"]
    assert ligada["avisos"] == esperada["avisos"]
    # a outra opção não muda
    assert opcao(ligada, "B")["preco"] == pytest.approx(opcao(esperada, "B")["preco"])


def test_fase_desligada_listada(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    f2 = A["fases"][1]
    f2["ativa"], f2["modulo"] = False, "m1"
    a = opcao(motor.precificar(cat, p), "A")
    assert a["fases_desligadas"] == [{"id": f2["id"], "nome": f2["nome"], "modulo": "m1"}]
    assert f2["id"] not in [f["id"] for f in a["fases"]]


def test_fase_sem_chave_ativa_e_precificada(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    antes = motor.precificar(cat, p)
    for o in p["opcoes"]:
        for f in o["fases"]:
            del f["ativa"]
            del f["modulo"]
    depois = motor.precificar(cat, p)
    assert [r["preco"] for r in depois["opcoes"]] == [r["preco"] for r in antes["opcoes"]]
    pp.completar(p, cat, p["parametros"])
    assert all(f["ativa"] is True and f["modulo"] == "" for o in p["opcoes"] for f in o["fases"])


def test_ativa_false_sobrevive_ao_json(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    p["opcoes"][0]["fases"][1]["ativa"] = False
    p2 = pp.completar(json.loads(pp.salvar_json(p)), cat, params)
    assert p2["opcoes"][0]["fases"][1]["ativa"] is False
    assert p2["opcoes"][0]["fases"][0]["ativa"] is True


def test_todas_desligadas_levanta_erro(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    B = next(o for o in p["opcoes"] if o["id"] == "B")
    for f in B["fases"]:
        f["ativa"] = False
    with pytest.raises(ValueError, match="A opção B não tem nenhuma fase incluída na proposta."):
        motor.precificar(cat, p)


def test_estimativa_ignora_ativa(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    antes = opcao(motor.precificar(cat, p), "E")["preco"]
    E = next(o for o in p["opcoes"] if o["id"] == "E")
    E["fases"][0]["ativa"] = False
    r = opcao(motor.precificar(cat, p), "E")
    assert r["preco"] == antes
    assert r["fases_desligadas"] == []
