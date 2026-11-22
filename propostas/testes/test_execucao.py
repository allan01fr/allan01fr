import pytest

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import execucao as ex
from orcamento import motor
from orcamento import proposta as pp
from orcamento.erros import ErroEntrada

PRODUTIVIDADE_REF = [
    {"item": i, "funcao": f, "hh_por_unidade": h, "fator_calibracao": 1.0, "fonte": "caso de referência T1"}
    for i, (e, m) in {"duto_m2": (0.05, 0.40), "linha_frigorifica_m": (0.02, 0.30), "evaporadora_un": (0.50, 4.00)}.items()
    for f, h in (("encarregado", e), ("mecanico_refrigeracao", m), ("ajudante", m))]


def _it(id, frente, item, un, q, alt, ace, ocu, tur, mat, cat):
    return {"id": id, "frente": frente, "item": item, "unidade": un, "descricao": "", "quantidade": q, "altura": alt,
            "acesso": ace, "ocupacao": ocu, "turno": tur, "custo_material_unit": mat, "categoria_material": cat}


ITENS_REF = [_it("1", "Térreo", "duto_m2", "m2", 100, "de_3_a_6m", "livre", "ocupado", "diurno", 120.0, "material"),
             _it("2", "Térreo", "linha_frigorifica_m", "m", 50, "ate_3m", "livre", "ocupado", "noturno", 85.0, "material"),
             _it("3", "Cobertura", "evaporadora_un", "un", 4, "ate_3m", "restrito", "desocupado", "diurno", 3500.0,
                 "equipamento")]
FUNCOES_REF = {"encarregado": {"nome": "Encarregado", "custo_hora": 72.0},
               "mecanico_refrigeracao": {"nome": "Mecânico de refrigeração", "custo_hora": 54.0},
               "ajudante": {"nome": "Ajudante", "custo_hora": 27.0}}


def test_hh_do_caso_de_referencia_e_fatores():
    fator, det = ex.fator_item(ex.FATORES_PADRAO, ITENS_REF[0])
    assert fator == pytest.approx(1.38) and det == {"altura": 1.15, "acesso": 1.0, "ocupacao": 1.2, "turno": 1.0}
    r = ex.hh_execucao(ITENS_REF, PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert r["hh_funcao"] == pytest.approx({"encarregado": 10.7, "mecanico_refrigeracao": 96.1, "ajudante": 96.1})
    assert r["total_hh"] == pytest.approx(202.9) and r["frentes"] == ["Térreo", "Cobertura"] and len(r["linhas"]) == 9
    prod = [{**p, "fator_calibracao": 1.1} if p["funcao"] == "ajudante" else p for p in PRODUTIVIDADE_REF]
    c = ex.hh_execucao(ITENS_REF, prod, ex.FATORES_PADRAO)
    assert (c["hh_funcao"]["ajudante"], c["hh_funcao_base"]["ajudante"]) == pytest.approx((105.71, 96.1))


@pytest.mark.parametrize("alteracao, codigo", [({"item": "inexistente"}, "item_sem_produtividade"),
                                               ({"quantidade": -1}, "quantidade_negativa"),
                                               ({"altura": "no_teto"}, "fator_desconhecido")])
def test_entradas_invalidas(alteracao, codigo):
    with pytest.raises(ErroEntrada) as e:
        ex.hh_execucao([{**ITENS_REF[0], **alteracao}], PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert e.value.codigo == codigo


def test_equipe_e_cronograma():
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), "prazo_alvo_dias": 10})
    assert p["equipe"] == {"encarregado": 1, "mecanico_refrigeracao": 2, "ajudante": 2}
    assert [(c["frente"], c["dias_uteis"], c["inicio"], c["fim"]) for c in p["cronograma"]] == [("Térreo", 7, 1, 7), ("Cobertura", 2, 8, 9)]
    assert (p["prazo_dias_uteis"], p["prazo_dias_corridos"], p["avisos"]) == (9, 13, [])
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3, "ajudante": 3}}
    assert ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)["prazo_dias_uteis"] == 6
    assert ex.dimensionar_equipe({"ajudante": 64.0, "soldador": 0.0}, 8, 10, 0.8) == {"ajudante": 1, "soldador": 0}
    a = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), "prazo_alvo_dias": 8})
    assert a["prazo_dias_uteis"] == 9 and "acima do prazo-alvo de 8" in a["avisos"][0]


def test_equipe_incompleta_e_parametros_invalidos():
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3}}
    with pytest.raises(ErroEntrada) as e:
        ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert (e.value.codigo, e.value.detalhes) == ("equipe_incompleta", {"funcao": "ajudante"})
    for campo, valor in [("eficiencia", 0), ("eficiencia", 1.2), ("horas_dia", 0), ("prazo_alvo_dias", 0)]:
        with pytest.raises(ErroEntrada) as e:
            ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), campo: valor})
        assert (e.value.codigo, e.value.detalhes) == ("parametro_invalido", {"campo": campo})


def _proposta_obra(cat, params):
    p = pp.completar(pp.padrao(params), cat, params)
    p["opcoes"][0]["execucao"] = {**ex.config_padrao("F1"), "prazo_alvo_dias": 10}
    return p


def test_preco_de_obra_do_caso_de_referencia(cat, params):
    p = _proposta_obra(cat, params)
    r = ex.precificar_com_execucao(cat, p, {"A": ITENS_REF}, PRODUTIVIDADE_REF, FUNCOES_REF)
    o = r["orcamento"]["opcoes"][0]
    mo = [f for f in o["fornecimentos"] if f["categoria"] == "mo_execucao"]
    assert (sum(f["custo"] for f in mo), sum(f["preco"] for f in mo)) == pytest.approx((8554.50, 10436.49))
    assert o["preco"] == pytest.approx(44921.49) and (o["prazo_dias_uteis"], o["prazo_dias_corridos"]) == (9, 13)
    assert [a for a in r["orcamento"]["avisos"] if "sem ART" not in a] == [] and p["opcoes"][0]["fornecimentos"] == []
    with pytest.raises(ErroEntrada) as e:
        ex.precificar_com_execucao(cat, p, {"A": ITENS_REF}, PRODUTIVIDADE_REF,
                                   {**FUNCOES_REF, "ajudante": {"nome": "Ajudante", "custo_hora": 0.0}})
    assert e.value.codigo == "funcao_sem_custo"
    for caminho in EXEMPLOS:
        q = abrir_exemplo(caminho, cat, params)
        esperado = [x["preco"] for x in motor.precificar(cat, q)["opcoes"]]
        assert [x["preco"] for x in ex.precificar_com_execucao(cat, q, {}, [], {})["orcamento"]["opcoes"]] == pytest.approx(esperado)
