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


def _fases_de_exemplos():
    """(arquivo, opção, índice da fase) de cada fase de cada opção "fases" com mais de uma fase dos exemplos."""
    casos = []
    for caminho in EXEMPLOS:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        for o in dados["opcoes"]:
            fases = o.get("fases") or []
            if o.get("modalidade", "fases") == "fases" and len(fases) > 1:
                casos += [pytest.param(caminho, o["id"], i, id=f"{os.path.basename(caminho)[:-5]}-{o['id']}-F{i + 1}")
                          for i in range(len(fases))]
    return casos


@pytest.mark.parametrize("caminho,oid,idx", _fases_de_exemplos())
def test_desligar_fase_equivale_a_remove_la(caminho, oid, idx, cat, params):
    p = abrir_exemplo(caminho, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == oid)
    fid = A["fases"][idx]["id"]

    removida = copy.deepcopy(p)
    RA = next(o for o in removida["opcoes"] if o["id"] == oid)
    RA["fases"] = [f for f in RA["fases"] if f["id"] != fid]
    RA["itens"] = [x for x in RA["itens"] if x["fase"] != fid]
    RA["fornecimentos"] = [x for x in RA["fornecimentos"] if x["fase"] != fid]

    A["fases"][idx]["ativa"] = False
    A["fases"][idx]["modulo"] = "m1"
    ligada = motor.precificar(cat, p)
    esperada = motor.precificar(cat, removida)
    a, e = opcao(ligada, oid), opcao(esperada, oid)
    assert a["preco"] == pytest.approx(e["preco"])
    assert a["total_h"] == pytest.approx(e["total_h"])
    assert len(a["cronograma"]) == len(e["cronograma"])
    assert a["prazo_dias_uteis"] == e["prazo_dias_uteis"]
    assert [x["id"] for x in a["fases"]] == [x["id"] for x in e["fases"]]
    assert [x for x in ligada["avisos"] if "fases desligadas" not in x] == esperada["avisos"]
    assert (any("fases desligadas" in x for x in ligada["avisos"])) == bool(
        any(x["fase"] == fid for x in A["itens"] + A["fornecimentos"]))
    for o in p["opcoes"]:       # as outras opções não mudam
        if o["id"] != oid:
            assert opcao(ligada, o["id"])["preco"] == pytest.approx(opcao(esperada, o["id"])["preco"])


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


# ----------------------------------------------------------------------------- aviso de itens em fase desligada
def _aviso(res, texto="fases desligadas"):
    return [a for a in res["avisos"] if texto in a]


def test_aviso_itens_em_fase_desligada(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    fid = A["fases"][1]["id"]
    n_it = sum(1 for x in A["itens"] if x["fase"] == fid)
    n_fo = sum(1 for x in A["fornecimentos"] if x["fase"] == fid)
    assert n_it + n_fo
    A["fases"][1]["ativa"] = False
    av = _aviso(motor.precificar(cat, p))
    assert f"Opção {A['id']}: {n_it} serviço(s) e {n_fo} fornecimento(s) estão em fases desligadas e ficaram fora do preço." in av


def test_aviso_sem_itens_em_fase_desligada_nao_aparece(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    A["fases"].append(pp.nova_fase(pp.proxima_fase(A), params))
    A["fases"][-1]["ativa"] = False
    assert _aviso(motor.precificar(cat, p)) == []


def test_aviso_item_orfao_cai_na_primeira_fase_desligada(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    A["itens"][-1]["fase"] = "F99"            # fase inexistente: o item cai na primeira fase
    A["fases"][0]["ativa"] = False
    av = _aviso(motor.precificar(cat, p))
    n_it = sum(1 for x in A["itens"] if x["fase"] == A["fases"][0]["id"] or x["fase"] == "F99")
    assert av and f"{n_it} serviço(s)" in av[0]


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_exemplos_sem_aviso_de_fase_desligada(caminho, cat, params):
    assert _aviso(motor.precificar(cat, abrir_exemplo(caminho, cat, params))) == []
