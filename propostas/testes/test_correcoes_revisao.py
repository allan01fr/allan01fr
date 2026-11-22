"""Regressões da revisão do motor/execução/ARTs."""
import copy

import pytest

from orcamento import arts, escopos, modelos, motor, tabela_referencia as tr
from orcamento import catalogo as ct
from orcamento import execucao as ex
from orcamento import execucao_itens as ei
from orcamento import indices_bcb as bcb
from orcamento import proposta as pp
from orcamento import referencias as rf


def _kit_opcao(params, cat, plano=False):
    prop = pp.padrao(params)
    o = prop["opcoes"][0]
    o["fases"], o["itens"], o["fornecimentos"] = [], [], []
    escopos.incluir(o, "execucao", cat, params)
    kit = next(k for k in modelos.carregar_kits() if k["id"] == "split_12k_padrao")
    modelos.aplicar_kit(o, kit)
    ei.sincronizar_fornecimentos(o, params)
    escopos.incluir(o, "acompanhamento", cat, params)
    o["plano_arts"] = plano
    return prop, o


def test_precificar_com_execucao_nao_duplica(cat, params):
    prop, o = _kit_opcao(params, cat)
    n = len(o["fornecimentos"])
    res = ex.precificar_com_execucao(cat, prop, {o["id"]: ei.itens_da_opcao(o)}, ei.produtividade_da_opcao(o),
                                     ei._funcoes(params))
    assert len(res["proposta"]["opcoes"][0]["fornecimentos"]) == n


def test_base_global_inclui_art_da_execucao(cat, params):
    prop, o = _kit_opcao(params, cat, plano=True)
    o["fases"][1]["obra"]["base_parte"] = "global"
    r = motor.precificar_opcao(cat, prop, o)
    assert r["fases"][1]["base"] == pytest.approx(r["fases"][0]["preco"])


def test_art_percentual_entra_no_preco(cat, params):
    prop, o = _kit_opcao(params, cat, plano=False)
    sem = motor.precificar_opcao(cat, prop, o)["fases"][1]["preco"]
    o["plano_arts"] = True
    r = motor.precificar_opcao(cat, prop, o)
    f2 = r["fases"][1]
    assert f2["art"] > 0 and f2["preco"] > sem


def test_arts_fase_invalida_e_eletricista(cat, params):
    o = pp.padrao(params)["opcoes"][0]
    o["fases"] = [pp.nova_fase("F1", params), pp.nova_fase("F2", params)]
    o["itens"] = [pp.novo_item(ct.servico(cat, "hvac.projeto"), "F1")]
    o["fornecimentos"] = [pp.novo_fornecimento("x", fase="ZZ", qtd=1, custo_unit=1000)]
    plano = arts.planejar_arts(o, cat, params, {"F1": 1000})
    assert any(a["atividades"] == ["execucao"] for a in plano)
    p = ex.planejar_execucao([{"id": "1", "frente": "a", "item": "k", "quantidade": 1, "altura": "ate_3m",
                               "acesso": "livre", "ocupacao": "desocupado", "turno": "diurno", "unidade": "un"}],
                             [{"item": "k", "funcao": "eletricista", "hh_por_unidade": 1}], ex.config_padrao())
    fo = ex.fornecimentos_execucao(p, [], {"eletricista": {"nome": "Eletricista", "custo_hora": 58}}, "F1")
    assert arts._eletrico(fo[0])


def test_pacote_obra_ignora_plano_com_execucao_desligada(cat, params):
    prop, o = _kit_opcao(params, cat)
    f = o["fases"][1]
    f["cobranca"], f["pacote"]["forma"], f["pacote"]["dias_obra"] = "pacote", "obra", 30
    o["fases"][0]["ativa"] = False
    r = motor.precificar_opcao(cat, prop, o)
    assert r["fases"][0]["pacote"]["dias_obra"] == 30


def test_tabela_acima_da_ultima_faixa():
    item = {"unidade": "m2", "modo": "cheia", "faixas": [{"ate": 100, "valor": 10}, {"ate": 200, "valor": 9}]}
    assert tr._base(item, 500, []) == pytest.approx(4500)


def test_serie_vazia_nao_apaga_indice(tmp_path):
    con = rf.conectar(str(tmp_path / "r.sqlite"))
    rf.importar_indices(con, "IGP-M", rf.indice_de_variacoes([("2024-01", 1.0)]))
    orig = bcb.baixar_serie
    bcb.baixar_serie = lambda *a, **k: []
    try:
        bcb.atualizar_banco(con, "IGP-M")
    finally:
        bcb.baixar_serie = orig
    assert con.execute("SELECT COUNT(*) FROM indices WHERE nome='IGP-M'").fetchone()[0] > 0


def test_fator_padrao_nao_hashavel_ignorado(cat, params):
    prop, o = _kit_opcao(params, cat)
    o["execucao"]["fator_padrao"] = {"altura": ["x"]}
    assert ei.calcular_execucao(o, params)["plano"] is not None


def test_config_parcial_sem_fase_e_item_sem_unidade(cat, params):
    prop, o = _kit_opcao(params, cat)
    o["execucao"].pop("fase")
    assert ei.sincronizar_fornecimentos(o, params) > 0
    p = ex.planejar_execucao([{"id": "1", "frente": "a", "item": "k", "quantidade": 1, "altura": "ate_3m",
                               "acesso": "livre", "ocupacao": "desocupado", "turno": "diurno"}],
                             [{"item": "k", "funcao": "eletricista", "hh_por_unidade": 1}], ex.config_padrao())
    ex.fornecimentos_execucao(p, [{"item": "k", "quantidade": 1, "material": 10}],
                              {"eletricista": {"nome": "E", "custo_hora": 58}}, "F1")


def test_acompanhamento_fase_invalida_dimensionado(cat, params):
    prop, o = _kit_opcao(params, cat)
    for i in o["itens"]:
        if i.get("servico") == "geral.acompanhamento_obra":
            i["fase"] = "ZZ"
    o["fases"].reverse()          # a primeira fase passa a ser a de acompanhamento
    assert escopos.dimensionar_acompanhamento(o, params) > 0
