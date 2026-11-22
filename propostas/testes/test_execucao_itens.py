import copy

import pytest

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import execucao_itens as ei
from orcamento import modelos, motor

KIT = next(k for k in modelos.carregar_kits() if k["id"] == "split_12k_padrao")


def _opcao():
    o = {"id": "A", "nome": "Opção A", "fases": [{"id": "F1", "ativa": True}], "fornecimentos": []}
    return modelos.aplicar_kit(o, KIT)


def test_itens_e_produtividade_do_kit():
    o = _opcao()
    itens, prod = ei.itens_da_opcao(o), ei.produtividade_da_opcao(o)
    assert len(itens) == len(prod) == 4 and itens[1]["custo_material_unit"] == 38.0
    assert {p["funcao"] for p in prod} == {"mecanico_refrigeracao", "ajudante"}
    assert ei.config_da_opcao(o)["fase"] == "F1" and o["execucao"]["modo"] == "prazo"


def test_calcular_execucao_custos():
    o = _opcao()
    r = ei.calcular_execucao(o, {})
    assert r["erro"] is None and r["plano"]["total_hh"] == pytest.approx(2.5 + 0.75 + 0.45 + 0.5)
    assert r["material"] == pytest.approx(3 * 38 + 3 * 9 + 65)
    assert sum(c["custo"] for c in r["custo_itens"]) == pytest.approx(r["mao_obra"] + r["material"])
    o["execucao"]["horas_dia"] = 0
    assert ei.calcular_execucao(o, {})["erro"]


def test_sincronizar_idempotente_e_sem_itens():
    o = _opcao()
    n = ei.sincronizar_fornecimentos(o, {})
    assert n > 0 and ei.sincronizar_fornecimentos(o, {}) == n
    assert sum(f.get("origem") == "execucao" for f in o["fornecimentos"]) == n
    assert ei.sincronizar_fornecimentos({"fornecimentos": []}, {}) == 0


def test_preco_aumenta_apos_sincronizar(cat, params):
    caminho = next(c for c in EXEMPLOS if c.endswith("hvac_retrofit_fases.json"))
    prop = abrir_exemplo(caminho, cat, params)
    antes = motor.precificar(cat, prop)
    novo = copy.deepcopy(prop)
    op = novo["opcoes"][0]
    modelos.aplicar_kit(op, KIT, op["fases"][0]["id"])
    assert ei.sincronizar_fornecimentos(op, novo["parametros"]) > 0
    depois = motor.precificar(cat, novo)
    assert depois["opcoes"][0]["preco_fornec"] > antes["opcoes"][0]["preco_fornec"]
