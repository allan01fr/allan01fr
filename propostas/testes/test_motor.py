import math

import pytest

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import calibracao as cb
from orcamento import catalogo as ct
from orcamento import motor
from orcamento import parametros as pm
from orcamento import proposta as pp


def _proposta(params, cat, *itens, **contexto):
    p = pp.padrao(params)
    p["contexto"].update(contexto)
    for sid, dados in itens:
        it = pp.novo_item(ct.servico(cat, sid))
        it["dados"].update(dados)
        p["opcoes"][0]["itens"].append(it)
    return p


def test_formula_de_horas(cat, params):
    p = _proposta(params, cat, ("hvac.tab", {"terminais": 40, "amostragem": "completo"}), acesso="restrito")
    linhas, _ = motor.linhas_item(cat, p, p["opcoes"][0]["itens"][0], 0)
    ativ = next(l for l in linhas if l["atividade"] == "terminais")
    # fixo TC 4 + 0,35 h/terminal × 40, com acesso restrito ×1,15 (complexidade e urgência = 1)
    assert ativ["q"] == 40
    assert ativ["horas"]["TC"] == pytest.approx((4 + 0.35 * 40) * 1.15)
    assert ativ["horas"]["PL"] == pytest.approx(0.08 * 40 * 1.15)


def test_cadeia_de_preco_fecha_exatamente(cat, params):
    p = _proposta(params, cat, ("hvac.projeto", {}), ("hvac.tab", {}))
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["custo_servicos"] == pytest.approx(r["custo_mo"] + r["overhead"] + r["diretos_total"])
    assert r["custo_servicos"] + r["contingencia"] + r["impostos"] + r["margem"] == pytest.approx(r["preco_servicos"])
    assert r["overhead"] == pytest.approx(r["custo_mo"] * params["overhead"]["pct"])
    imp = pm.aliquota_impostos(params)
    honor = sum(r["horas_perfil"][k] * params["perfis"][k]["taxa_venda_h"] for k in cat["perfis"])
    assert r["preco_hora"] == pytest.approx(honor + r["diretos_total"] * (1 + params["reembolsaveis_adm"]) / (1 - imp))
    assert r["preco"] == pytest.approx(r["preco_fechado"])
    assert r["margem_efetiva"] == pytest.approx(
        (r["preco_servicos"] * (1 - imp) - r["custo_servicos"]) / r["preco_servicos"])


def test_impostos_lucro_presumido_e_simples(params):
    assert pm.aliquota_impostos(params) == pytest.approx(0.0065 + 0.03 + 0.048 + 0.0288 + 0.05)
    simples = pm.mesclar(params, {"impostos": {"regime": "simples", "simples_aliquota": 0.112}})
    assert pm.aliquota_impostos(simples) == pytest.approx(0.112)


def test_fornecimento_com_bdi_e_percentual(cat, params):
    p = _proposta(params, cat, ("geral.gestao_obra", {}))
    o = p["opcoes"][0]
    o["fornecimentos"] = [{"descricao": "Condensadora", "categoria": "equipamento", "unid": "un", "qtd": 2, "custo_unit": 10000.0}]
    r = motor.precificar(cat, p)["opcoes"][0]
    bdi = params["bdi_fornecimento"]["equipamento"]
    assert r["preco_fornec"] == pytest.approx(20000 * (1 + bdi))      # sem fase: fica na primeira
    assert r["preco_fechado"] == pytest.approx(r["preco_servicos"] + r["preco_fornec"])
    f = o["fases"][0]
    f["cobranca"] = "percentual"
    f["percentual"].update(pct=0.08, forma="fixo_global")
    f["obra"].update(base_modo="fornecimentos", meses=0)
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["fases"][0]["base"] == pytest.approx(20000)
    assert r["preco"] == pytest.approx(0.08 * 20000 + r["preco_fornec"])


def test_deslocamento_por_faixa(params):
    d = params["deslocamento"]
    assert motor.deslocamento(params, d["raio_isento_km"] - 1, 3)[0] == 0
    v, _ = motor.deslocamento(params, 100, 3)
    assert v == pytest.approx(3 * 2 * 100 * d["rs_km"])
    v, _ = motor.deslocamento(params, 400, 3)
    assert v == pytest.approx(2 * 400 * d["rs_km"] + 3 * d["pessoas_campo"] * d["diaria"])


def test_cronograma_e_pagamento(cat, params):
    p = _proposta(params, cat, ("hvac.asbuilt", {}), ("hvac.tab", {}))
    r = motor.precificar(cat, p)["opcoes"][0]
    cr = r["cronograma"]
    assert [e["inicio"] for e in cr][0] == 1
    for a, b in zip(cr, cr[1:]):
        assert b["inicio"] == a["fim"] + 1
    for e in cr:
        assert e["dias_uteis"] == max(1, math.ceil(e["horas"] / (8 * params["cronograma"]["equipe"])))
    pag = r["fases"][0]["pagamento"]
    assert sum(m["pct"] for m in pag) == pytest.approx(1)
    assert pag[0]["pct"] == params["pagamento"]["sinal"]


def test_aviso_de_visto_fora_de_rj_sp(cat, params):
    p = _proposta(params, cat, ("geral.visita", {}))
    p["cliente"]["uf"] = "MG"
    assert any("CREA-MG" in a for a in motor.precificar(cat, p)["avisos"])


def test_duplicar_opcao_trocando_nivel(cat, params):
    p = _proposta(params, cat, ("hvac.asbuilt", {"nivel": "2d"}), ("hvac.tab", {}))
    nova = pp.duplicar_opcao(p, 0, nivel="bim")
    assert nova["id"] == "B" and nova["itens"][0]["dados"]["nivel"] == "bim"
    r = motor.precificar(cat, p)["opcoes"]
    assert r[1]["total_h"] > r[0]["total_h"]
    assert r[1]["diretos_total"] > r[0]["diretos_total"]     # escaneamento a laser


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_exemplos_precificam(caminho, cat, params):
    p = abrir_exemplo(caminho, cat, params)
    res = motor.precificar(cat, p)
    for r in res["opcoes"]:
        assert r["linhas"] and r["preco"] > 0
        for f in r["fases"]:
            assert f["preco"] > 0
            if not r["interno"]:
                assert sum(m["pct"] for m in f["pagamento"]) == pytest.approx(1)


def test_calibracao_nao_acumula(cat, params, tmp_path):
    cat_local = __import__("copy").deepcopy(cat)
    p = _proposta(params, cat_local, ("hvac.tab", {}))
    r = motor.precificar(cat_local, p)["opcoes"][0]
    hist = []
    cb.registrar(hist, cat_local, p, r, {i: l["total_h"] * 1.2 for i, l in enumerate(r["linhas"])})
    sug = cb.fatores_sugeridos(cat_local, hist)
    assert all(s["fator_sugerido"] == pytest.approx(1.2) for s in sug)
    cb.aplicar(cat_local, sug)
    cb.aplicar(cat_local, cb.fatores_sugeridos(cat_local, hist))
    assert all(a["calibracao"] == pytest.approx(1.2) for a in ct.servico(cat_local, "hvac.tab")["atividades"]
               if any(s["atividade"] == a["id"] for s in sug))
    r2 = motor.precificar(cat_local, p)["opcoes"][0]
    assert r2["total_h"] == pytest.approx(r["total_h"] * 1.2)
