import json
import os

import pytest

from orcamento import ajustes_honorario as aj
from orcamento import honorario_abrava as ha
from orcamento.erros import ErroEntrada

EXEMPLO = os.path.join(os.path.dirname(__file__), "..", "dados", "abrava_parametros.exemplo.json")
PARAMS = json.load(open(EXEMPLO, encoding="utf-8"))  # FICTÍCIO

CASO1 = {"climatizados": [{"tipo": "auditorio", "area_m2": 160, "repeticoes": 1},
                          {"tipo": "cpd", "area_m2": 48, "repeticoes": 2}],
         "ventilados": [{"tipo": "exaustao", "area_m2": 32}]}
AJ = {"nivel_rt": "senior", "inclui_planilha": True, "adicional_planilha_pct": None, "adicional_pct": 0.05,
      "desconto_pct": 0.03, "custos_extras": [{"descricao": "deslocamento", "valor": 800},
                                              {"descricao": "hospedagem", "valor": 450}],
      "valor_final_manual": None}


def test_exemplo_marcado_provisorio():
    assert PARAMS["provisorio"] is True and "conferir" in PARAMS["nota"]


def test_metodo_casos_1_2_e_piso():
    a, det = ha.area_corrigida(PARAMS, CASO1["climatizados"], CASO1["ventilados"])
    assert a == pytest.approx(309.6) and [d["area_corrigida"] for d in det] == pytest.approx([192, 108, 9.6])
    r = ha.calcular_abrava(PARAMS, {**CASO1, "tipo_instalacao": "vrf", "escopo": "nova_em_novo"}, 1500.0)
    assert (r["custo_base"], r["pct"], r["honorario_metodo"]) == pytest.approx((102168, 0.0598916, 6119.0049888))
    r = ha.calcular_abrava(PARAMS, {**CASO1, "tipo_instalacao": "agua_gelada", "escopo": "retrofit"}, 1500.0)
    assert r["honorario_metodo"] == pytest.approx(9512.0533094)
    p = {"tipo_instalacao": "expansao_direta", "escopo": "nova_em_novo", "ventilados": [],
         "climatizados": [{"tipo": "escritorio", "area_m2": 20, "repeticoes": 1}]}
    r = ha.calcular_abrava(PARAMS, p, 1500.0)
    assert (r["honorario_bruto"], r["honorario_metodo"]) == pytest.approx((348.128, 4500))
    assert "piso de 3 salários mínimos" in r["avisos"][0]


@pytest.mark.parametrize("clim, codigo", [
    ([{"tipo": "garagem", "area_m2": 10, "repeticoes": 1}], "ambiente_desconhecido"),
    ([{"tipo": "cpd", "area_m2": 10, "repeticoes": 0}], "repeticoes_invalida"),
    ([{"tipo": "cpd", "area_m2": 0, "repeticoes": 1}], "area_invalida"),
    ([], "sem_ambientes"),
])
def test_erros(clim, codigo):
    with pytest.raises(ErroEntrada) as e:
        ha.calcular_abrava(PARAMS, {"tipo_instalacao": "vrf", "escopo": "retrofit", "climatizados": clim}, None)
    assert e.value.codigo == codigo


def test_ajustes_rotulados_e_manual():
    r = aj.aplicar_ajustes(6119.0049888, aj.AJUSTES_PADRAO, AJ)
    assert [l["subtotal"] for l in r["linhas"]] == pytest.approx(
        [8566.60698, 9423.26768, 9894.43107, 9597.59813, 10397.59813, 10847.59813])
    assert all(l["rotulo"].startswith("Ajuste da empresa — ") for l in r["linhas"])
    assert r["referencial_licitacao"] == pytest.approx(9220.458, abs=0.01)
    m = aj.aplicar_ajustes(6119.0049888, aj.AJUSTES_PADRAO, {**AJ, "valor_final_manual": 9000})
    assert (m["honorario_final"], m["diferenca_manual"]) == pytest.approx((9000, -1847.598), abs=0.01)
    with pytest.raises(ErroEntrada) as e:
        aj.aplicar_ajustes(1000, aj.AJUSTES_PADRAO, {**AJ, "desconto_pct": 1.0})
    assert e.value.codigo == "desconto_invalido"


def test_aplicar_na_proposta_devolve_copia():
    pa = {"ativo": True, "fase": "F1", "adotar": True, "tipo_instalacao": "vrf", "escopo": "nova_em_novo",
          **CASO1, "prazo_dias": 30, "ajustes": AJ}
    p = {"opcoes": [{"id": "A", "fases": [{"id": "F1", "cobranca": "fechado"}], "projeto_abrava": pa}]}
    p2, info = ha.aplicar_na_proposta(p, PARAMS, aj.AJUSTES_PADRAO, 1500.0)
    f1 = p2["opcoes"][0]["fases"][0]
    assert f1["cobranca"] == "valor" and f1["valor_definido"]["valor"] == pytest.approx(10847.598, abs=0.01)
    assert info["A"]["adotado"] and p["opcoes"][0]["fases"][0]["cobranca"] == "fechado"
    with pytest.raises(ErroEntrada) as e:
        ha.aplicar_na_proposta(p, None, aj.AJUSTES_PADRAO, 1500.0)
    assert e.value.codigo == "sem_parametros_abrava"
