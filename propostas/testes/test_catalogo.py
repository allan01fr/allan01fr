import copy

import pytest

from orcamento import catalogo as ct
from orcamento import motor
from orcamento import proposta as pp


def test_catalogo_valido_e_cobre_as_quatro_disciplinas(cat):
    assert ct.validar(cat) == []
    disc = set(ct.disciplinas(cat))
    assert {"HVAC-R", "Mecânica e utilidades", "Segurança do trabalho", "Hidráulica e incêndio"} <= disc
    tipos = {s["tipo"] for s in cat["servicos"]}
    assert {"calculo", "projeto", "simulacao", "obra", "comissionamento", "ensaio"} <= tipos


def test_todo_servico_gera_horas_com_o_formulario_padrao(cat, params):
    p = pp.padrao(params)
    for s in cat["servicos"]:
        linhas, _ = motor.linhas_item(cat, p, pp.novo_item(s), 0)
        assert sum(l["total_h"] for l in linhas) > 0, s["id"]


def test_validacao_aponta_erros(cat):
    ruim = copy.deepcopy(cat)
    s = ruim["servicos"][0]
    s["atividades"][0]["driver"] = "campo_que_nao_existe*2"
    s["atividades"][1]["etapa"] = "etapa_inventada"
    s["exclusoes"].append({"texto": "x", "exceto_se": ["servico.fantasma"]})
    erros = "\n".join(ct.validar(ruim))
    assert "campo_que_nao_existe" in erros
    assert "etapa_inventada" in erros
    assert "servico.fantasma" in erros


def test_exclusoes_condicionais(cat):
    so_cx = ct.exclusoes_validas(cat, ["hvac.comissionamento"], False)
    assert "TAB, salvo se contratado em item próprio." in so_cx
    com_tab = ct.exclusoes_validas(cat, ["hvac.comissionamento", "hvac.tab"], False)
    assert "TAB, salvo se contratado em item próprio." not in com_tab
    turnkey = ct.exclusoes_validas(cat, ["hvac.projeto", "hvac.comissionamento"], True)
    assert not any(t.startswith("Execução de obras") or t.startswith("Correção de defeitos") for t in turnkey)


def test_contexto_gera_flags_de_opcoes(cat):
    s = ct.servico(cat, "hvac.asbuilt")
    ctx = ct.contexto(s, {"nivel": "bim"}, {"dist_km": 10})
    assert ctx["nivel__bim"] == 1.0 and ctx["nivel__2d"] == 0.0 and ctx["dist_km"] == 10.0


@pytest.mark.parametrize("estrago", [
    lambda s: s.pop("descricao"), lambda s: s.update(nome=""), lambda s: s.update(dados="area"),
    lambda s: s["dados"][0].pop("rotulo"), lambda s: s["atividades"][0].pop("etapa"),
    lambda s: s["dados"].append({"id": "x", "rotulo": "X", "tipo": "opcoes", "padrao": "a", "opcoes": [{"valor": "a"}]}),
])
def test_servico_sem_as_chaves_que_o_app_le_e_recusado(cat, estrago):
    """Na prévia online o catálogo é compartilhado: um serviço incompleto salvo derrubaria o app para todos."""
    ruim = copy.deepcopy(cat)
    estrago(ruim["servicos"][0])
    assert ct.estrutura_servico(ruim["servicos"][0])
    assert ct.validar(ruim)


def test_servico_que_nao_e_objeto_nao_quebra_a_validacao(cat):
    ruim = copy.deepcopy(cat)
    ruim["servicos"].append("texto solto")
    assert "o serviço precisa ser um objeto JSON ({...})" in ct.validar(ruim)


@pytest.mark.parametrize("estrago", [
    lambda s: s["atividades"][0].update(b="abc"), lambda s: s["atividades"][0].update(fixo="10"),
    lambda s: s["atividades"][0].update(fatores=3), lambda s: s["atividades"][0].update(driver=["x"]),
    lambda s: s["dados"][0].update(padrao="abc", tipo="float"),
    lambda s: s["atividades"][0].update(driver="round(1, 0-15000000)"),
    lambda s: s["atividades"][0].update(driver="+".join(["1"] * 60000)),
])
def test_valor_de_tipo_errado_vira_erro_sem_excecao(cat, estrago):
    ruim = copy.deepcopy(cat)
    estrago(ruim["servicos"][0])
    assert ct.validar(ruim)


def test_divisao_por_zero_no_padrao_nao_trava_o_catalogo(cat):
    ok = copy.deepcopy(cat)
    s = ok["servicos"][0]
    s["atividades"][0]["driver"] = f"1/({s['dados'][0]['id']}*0)"
    assert ct.validar(ok) == []


def test_exemplos_continuam_validos(cat, params):
    from conftest import EXEMPLOS, abrir_exemplo
    for caminho in EXEMPLOS:
        abrir_exemplo(caminho, cat, params)
    assert ct.validar(cat) == []
