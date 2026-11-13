from orcamento import arts
from orcamento import catalogo as ct
from orcamento import proposta as pp


def _opcao(params, cat, fases, fornec=()):
    """fases: [(id, [servicos])]; fornec: [(fase, dict extra)]."""
    o = pp.padrao(params)["opcoes"][0]
    o["fases"], o["itens"], o["fornecimentos"] = [], [], []
    for fid, servs in fases:
        o["fases"].append(pp.nova_fase(fid, params))
        o["itens"] += [pp.novo_item(ct.servico(cat, s), fid) for s in servs]
    for fid, extra in fornec:
        f = pp.novo_fornecimento("x", fase=fid)
        f.update(extra)
        o["fornecimentos"].append(f)
    return o


def test_projeto_e_execucao_geram_duas_arts(cat, params):
    o = _opcao(params, cat, [("F1", ["hvac.projeto"]), ("F2", [])], [("F2", {"categoria": "material"})])
    plano = arts.planejar_arts(o, cat, params, {"F1": 10000, "F2": 50000})
    assert sorted(a["atividades"][0] for a in plano) == ["execucao", "projeto"]
    assert all(a["tipo"] == "obra_servico" and a["no_preco"] for a in plano)
    assert next(a for a in plano if a["fases"] == ["F2"])["valor_base"] == 50000


def test_desligar_fase_remove_art(cat, params):
    o = _opcao(params, cat, [("F1", ["hvac.projeto"]), ("F2", ["geral.acompanhamento_obra"])])
    o["fases"][1]["ativa"] = False
    plano = arts.planejar_arts(o, cat, params)
    assert [a["atividades"] for a in plano] == [["projeto"]]


def test_agrupar_por_profissional_junta(cat, params):
    o = _opcao(params, cat, [("F1", ["hvac.projeto"]), ("F2", ["geral.acompanhamento_obra"])])
    params = {**params, "art": {**params["art"], "regras": {"agrupar_por_profissional": True}}}
    plano = arts.planejar_arts(o, cat, params, {"F1": 1000, "F2": 2000})
    assert len(plano) == 1 and plano[0]["fases"] == ["F1", "F2"] and plano[0]["valor_base"] == 3000


def test_eletricista_gera_art_extra(cat, params):
    o = _opcao(params, cat, [("F1", [])], [("F1", {"categoria": "mo_execucao"}),
                                           ("F1", {"categoria": "mo_execucao", "funcao": "Eletricista"})])
    plano = arts.planejar_arts(o, cat, params)
    assert sorted(a["modalidade"] for a in plano) == ["eletrica", "mecanica"]


def test_subcontratado_fora_do_preco(cat, params):
    o = _opcao(params, cat, [("F1", ["hvac.projeto"])], [("F1", {"categoria": "subcontrato", "art_propria": True})])
    plano = arts.planejar_arts(o, cat, params)
    sub = next(a for a in plano if a["tipo"] == "subcontratado")
    assert sub["no_preco"] is False
    p2 = {**params, "art": {**params["art"], "regras": {"subcontratado_no_preco": True}}}
    assert next(a for a in arts.planejar_arts(o, cat, p2) if a["tipo"] == "subcontratado")["no_preco"] is True


def test_total_arts_soma_so_no_preco():
    lista = [{"taxa": 100.0, "no_preco": True}, {"taxa": 50.0, "no_preco": False}, {"taxa": 20.0, "no_preco": True}]
    assert arts.total_arts(lista) == 120.0
    assert arts.total_arts([]) == 0.0
