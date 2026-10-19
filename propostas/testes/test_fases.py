import copy

import pytest

from orcamento import catalogo as ct
from orcamento import cobranca as cb
from orcamento import motor
from orcamento import parametros as pm
from orcamento import proposta as pp


def item(cat, sid, fase, **dados):
    it = pp.novo_item(ct.servico(cat, sid), fase)
    it["dados"].update(dados)
    return it


@pytest.fixture
def p(cat, params):
    """Laudo e projeto em escopo fechado + assessoria de obra por % sobre a estimativa interna."""
    p = pp.completar(pp.padrao(copy.deepcopy(params)), cat, params)
    A = p["opcoes"][0]
    A["fases"] = [pp.nova_fase("F1", params, "Laudo técnico"), pp.nova_fase("F2", params, "Projeto"),
                  pp.nova_fase("F3", params, "Assessoria de obra", "percentual")]
    A["itens"] = [item(cat, "hvac.asbuilt", "F1"), item(cat, "hvac.projeto", "F2"),
                  item(cat, "geral.acompanhamento_obra", "F3", meses=4)]
    A["fases"][2]["percentual"]["pct"] = 0.04
    A["fases"][2]["obra"].update(base_modo="opcao", base_opcao="E", base_parte="obra", meses=4)
    E = pp.nova_opcao("E", params, "Estimativa do valor global")
    E["modalidade"] = "estimativa"
    E["fornecimentos"] = [pp.novo_fornecimento("Condensadoras VRF", "equipamento", "un", 5, 52000.0),
                          pp.novo_fornecimento("Instalação (subempreiteira)", "subcontrato", "vb", 1, 120000.0)]
    p["opcoes"].append(E)
    return p


def calc(cat, p):
    res = motor.precificar(cat, p)
    return {r["id"]: r for r in res["opcoes"]}, res["avisos"]


def fase(r, fid):
    return next(f for f in r["fases"] if f["id"] == fid)


# ----------------------------------------------------------------------------- soma das fases
def test_opcao_e_a_soma_das_fases(cat, p):
    r = calc(cat, p)[0]["A"]
    for k in ("preco", "preco_fixo", "preco_estimado", "custo_servicos", "total_h", "art"):
        assert r[k] == pytest.approx(sum(f[k] for f in r["fases"])), k
    assert r["preco"] == pytest.approx(r["preco_fixo"] + r["preco_estimado"])
    assert r["art"] == pytest.approx(sum(motor.valor_art(p["parametros"], f["preco_fechado"]) for f in r["fases"]))


def test_fases_correm_em_sequencia(cat, p):
    r = calc(cat, p)[0]["A"]
    cron = r["cronograma"]
    assert [e["fase"] for e in cron] == sorted([e["fase"] for e in cron])
    for a, b in zip(cron, cron[1:]):
        assert b["inicio"] == a["fim"] + 1
    obra = [e for e in cron if e["fase"] == "F3"]
    assert len(obra) == 1 and obra[0]["dias_uteis"] == 4 * 21 and obra[0]["dias_corridos"] == 4 * 30
    assert r["prazo_dias_corridos"] == sum(e["dias_corridos"] for e in cron)


def test_fase_fechada_e_precificada_sozinha(cat, params, p):
    f1 = fase(calc(cat, p)[0]["A"], "F1")
    so = pp.completar(pp.padrao(copy.deepcopy(params)), cat, params)
    so["opcoes"][0]["itens"] = [item(cat, "hvac.asbuilt", "F1")]
    r = motor.precificar(cat, so)["opcoes"][0]
    assert f1["preco"] == pytest.approx(r["preco"]) and f1["preco"] == pytest.approx(f1["preco_servicos"] + f1["preco_fornec"])
    assert f1["pagamento"] == r["fases"][0]["pagamento"]


# ----------------------------------------------------------------------------- % da obra
def test_percentual_sobre_medicoes_usa_a_estimativa(cat, p):
    res = calc(cat, p)[0]
    e, f3 = res["E"], fase(res["A"], "F3")
    assert e["interno"] and e["valor_obra"] == pytest.approx(e["preco_fornec"])
    assert f3["base"] == pytest.approx(e["preco_fornec"]) and "estimativa E" in f3["base_origem"]
    assert f3["preco_estimado"] == pytest.approx(0.04 * f3["base"]) and f3["preco_fixo"] == 0
    fat = f3["percentual"]["faturamento"]
    assert len(fat) == 4 and sum(m["medicao"] for m in fat) == pytest.approx(f3["base"])
    assert sum(m["honorario"] for m in fat) == pytest.approx(f3["preco"])
    assert len(f3["pagamento"]) == 1 and f3["pagamento"][0]["pct"] == 1.0
    assert "4% sobre o valor de cada medição" in f3["pagamento"][0]["marco"]
    assert f3["pct_minimo"] == pytest.approx(f3["preco_minimo_servicos"] / f3["base"])
    assert f3["margem_efetiva"] == pytest.approx((f3["preco"] * (1 - f3["imp_pct"]) - f3["custo_servicos"]) / f3["preco"])


def test_percentual_fixo_e_parte_fixa(cat, p):
    cfg = p["opcoes"][0]["fases"][2]
    cfg["percentual"]["forma"] = "fixo_global"
    f3 = fase(calc(cat, p)[0]["A"], "F3")
    assert f3["preco_fixo"] == pytest.approx(0.04 * f3["base"]) and f3["preco_estimado"] == 0
    cfg["percentual"].update(forma="fixo_mais_medicoes", parcela_fixa=5000.0)
    f3 = fase(calc(cat, p)[0]["A"], "F3")
    assert f3["preco"] == pytest.approx(5000 + 0.04 * f3["base"])
    assert f3["preco_fixo"] == pytest.approx(5000) and f3["percentual"]["faturamento"][0]["honorario"] > 5000
    assert sum(m["pct"] for m in f3["pagamento"]) == pytest.approx(1.0)
    assert f3["pagamento"][0]["pct"] == pytest.approx(round(5000 / f3["preco"], 4))


def test_base_global_e_base_ausente(cat, p):
    cfg = p["opcoes"][0]["fases"][2]["obra"]
    cfg["base_parte"] = "global"
    res = calc(cat, p)[0]
    assert fase(res["A"], "F3")["base"] == pytest.approx(res["E"]["preco_fechado"])
    cfg.update(base_modo="informado", base_valor=0.0)
    r, avisos = calc(cat, p)
    assert fase(r["A"], "F3")["preco"] == 0
    assert any("sem base" in a for a in avisos)
    cfg.update(base_modo="opcao", base_opcao="A")
    assert any("não é uma estimativa interna" in a for a in calc(cat, p)[1])


@pytest.mark.parametrize("curva", ["s", "linear"])
def test_curva_de_medicoes_fecha_o_total(curva):
    v = cb.curva_medicoes(1_000_000.0, 6, curva)
    assert sum(v) == pytest.approx(1_000_000.0) and len(v) == 6
    if curva == "linear":
        assert v == pytest.approx([1_000_000.0 / 6] * 6)
    else:   # curva S: simétrica, cresce até o meio e depois cai
        assert v[0] < v[1] < v[2] and v[0] == pytest.approx(v[-1]) and v[2] == pytest.approx(v[3])


# ----------------------------------------------------------------------------- pacote de horas
def _pacote(p, **cfg):
    f3 = p["opcoes"][0]["fases"][2]
    f3["cobranca"] = "pacote"
    f3["pacote"].update(cfg)
    return f3


def test_pacote_mensal(cat, p):
    _pacote(p, forma="mensal", horas_mes=40.0, meses=4, desconto=0.10)
    r = calc(cat, p)[0]["A"]
    f3 = fase(r, "F3")
    pk = f3["pacote"]
    perf = p["parametros"]["perfis"]
    mix = cb.mix_perfis(f3["horas_servicos"], {})
    taxa_cheia = sum(mix[k] * perf[k]["taxa_venda_h"] for k in mix)
    assert pk["horas"] == 160 and pk["taxa"] == pytest.approx(taxa_cheia * 0.9)
    assert f3["preco"] == pytest.approx(160 * taxa_cheia * 0.9 + f3["reembolso"])
    assert f3["total_h"] == 160 and sum(f3["horas_perfil"].values()) == pytest.approx(160)
    custo_mo = sum(160 * mix[k] * perf[k]["custo_h"] for k in mix)
    assert f3["custo_mo"] == pytest.approx(custo_mo)        # custo das horas vendidas
    assert f3["pagamento"][0]["pct"] == 1.0 and "4 parcelas mensais" in f3["pagamento"][0]["marco"]
    assert r["cronograma"][-1]["dias_uteis"] == 4 * 21


def test_pacote_total_sem_servicos_usa_mix_padrao(cat, p):
    _pacote(p, forma="total", horas=200.0, validade_meses=10, parcelas=4, desconto=0.0, excedente_pct=0.2)
    p["opcoes"][0]["itens"] = [it for it in p["opcoes"][0]["itens"] if it["fase"] != "F3"]
    f3 = fase(calc(cat, p)[0]["A"], "F3")
    pk = f3["pacote"]
    mix = p["parametros"]["cobranca"]["pacote"]["mix_padrao"]
    perf = p["parametros"]["perfis"]
    taxa = sum(v * perf[k]["taxa_venda_h"] for k, v in mix.items()) / sum(mix.values())
    assert pk["taxa"] == pytest.approx(taxa) and pk["parcela"] == pytest.approx((200 * taxa + f3["reembolso"]) / 4)
    assert pk["taxa_excedente"] == pytest.approx(taxa * 1.2)
    assert f3["art"] > 0                                    # fiscalização exige ART mesmo sem serviços listados


def test_pacote_sem_horas_avisa(cat, p):
    _pacote(p, forma="mensal", horas_mes=0.0)
    p["opcoes"][0]["itens"] = [it for it in p["opcoes"][0]["itens"] if it["fase"] != "F3"]
    assert any("pacote sem horas" in a for a in calc(cat, p)[1])


# ----------------------------------------------------------------------------- taxa de desempenho
def test_taxa_de_desempenho_fica_fora_do_preco(cat, p):
    de = p["opcoes"][0]["fases"][2]["desempenho"]
    de.update(ativo=True, economia_pct=0.10, prazo_pct_semana=0.02, retrabalho_bonus_pct=0.05, teto_pct=0.30,
              cenario={"economia": 0.05, "dias_antecipados": 14, "retrabalho_ok": True})
    r = calc(cat, p)[0]["A"]
    f3 = fase(r, "F3")
    d = f3["desempenho"]
    hon = f3["honorarios"]
    assert d["economia"] == pytest.approx(0.10 * 0.05 * f3["base"])
    assert d["prazo"] == pytest.approx(0.02 * hon * 2) and d["retrabalho"] == pytest.approx(0.05 * hon)
    assert d["potencial"] == pytest.approx(min(d["economia"] + d["prazo"] + d["retrabalho"], 0.30 * hon))
    assert r["potencial_desempenho"] == pytest.approx(d["potencial"]) and r["teto_desempenho"] == pytest.approx(0.30 * hon)
    assert f3["preco"] == pytest.approx(f3["preco_estimado"])        # não entra no preço


def test_teto_limita_a_taxa_de_desempenho():
    d = cb.taxa_desempenho({"economia_pct": 0.2, "prazo_pct_semana": 0.0, "retrabalho_bonus_pct": 0.0, "teto_pct": 0.1,
                            "cenario": {"economia": 0.1, "dias_antecipados": 0, "retrabalho_ok": False}}, 10000.0, 1e6)
    assert d["bruto"] == pytest.approx(20000) and d["potencial"] == pytest.approx(1000) and d["limitado"]


def test_fase_fechada_ignora_taxa_de_desempenho(cat, p):
    p["opcoes"][0]["fases"][0]["desempenho"]["ativo"] = True
    assert fase(calc(cat, p)[0]["A"], "F1")["desempenho"] is None


# ----------------------------------------------------------------------------- migração de arquivos antigos
def _antiga(cat, params, modelo, **extra):
    p = pp.completar(pp.padrao(copy.deepcopy(params)), cat, params)
    o = p["opcoes"][0]
    del o["fases"]
    o.update({"modalidade": "servicos", "modelo_preco": modelo, **extra})
    o["itens"] = [item(cat, "inc.spci", "?")]
    o["fornecimentos"] = [pp.novo_fornecimento("Hidrantes", "material", "vb", 1, 20000.0)]
    for it in o["itens"] + o["fornecimentos"]:
        it.pop("fase", None)
    return pp.completar(p, cat, params)


def test_migracao_do_modelo_fee(cat, params):
    p = _antiga(cat, params, "fee", fee_pct=0.05, fee_base=900000.0)
    o = p["opcoes"][0]
    assert o["modalidade"] == "fases" and "modelo_preco" not in o
    assert o["fases"][0]["cobranca"] == "percentual" and o["fases"][0]["percentual"]["forma"] == "fixo_global"
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["preco"] == pytest.approx(0.05 * 900000 + r["preco_fornec"])        # conta antiga: % × base + fornecimentos
    p = _antiga(cat, params, "fee", fee_pct=0.05, fee_base=0.0)
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["preco"] == pytest.approx(0.05 * r["custo_fornec"] + r["preco_fornec"])


def test_migracao_hora_e_turnkey(cat, params):
    r = motor.precificar(cat, _antiga(cat, params, "hora"))["opcoes"][0]
    assert r["preco"] == pytest.approx(r["honorarios_hora"] + r["reembolso"] + r["preco_fornec"])
    p = _antiga(cat, params, "fechado")
    p["opcoes"][0]["modalidade"] = "turnkey"
    p["opcoes"][0].pop("fases")
    p = pp.completar(p, cat, params)
    assert p["opcoes"][0]["modalidade"] == "estimativa"
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["interno"] and any(d.get("garantia") for d in r["diretos"])


def test_duplicar_opcao_copia_as_fases(cat, p):
    nova = pp.duplicar_opcao(p, 0, nome="Opção B")
    assert [f["id"] for f in nova["fases"]] == ["F1", "F2", "F3"]
    assert pp.proxima_fase(nova) == "F4"
    nova["fases"][2]["cobranca"] = "pacote"
    assert p["opcoes"][0]["fases"][2]["cobranca"] == "percentual"


def test_parametros_tem_os_padroes_de_cobranca(params):
    cb_ = pm.mesclar(params, {})["cobranca"]
    assert set(cb_) == {"percentual", "pacote", "desempenho"}


def test_estimativa_e_sempre_preco_fechado(cat, p):
    e = p["opcoes"][1]
    e["fases"][0]["cobranca"] = "percentual"        # resto de quando a opção era uma proposta em fases
    r = calc(cat, p)[0]["E"]
    assert r["fases"][0]["cobranca"] == "fechado" and r["preco"] == pytest.approx(r["preco_fechado"])
