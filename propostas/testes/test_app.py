import os

import pytest

from conftest import EXEMPLOS, RAIZ

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = os.path.join(RAIZ, "app", "app.py")


def _rodar():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_abre_vazio():
    at = _rodar()
    assert len(at.tabs) >= 8


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_app_carrega_exemplo_e_gera_arquivos(caminho):
    at = _rodar()
    at.sidebar.selectbox(key="exemplo_sel").select(os.path.basename(caminho)).run()
    next(b for b in at.sidebar.button if b.label == "Carregar exemplo").click().run()
    assert not at.exception, at.exception
    assert at.session_state.proposta["opcoes"][0]["itens"]
    next(b for b in at.button if b.label == "Gerar planilha e propostas").click().run()
    assert not at.exception, at.exception
    arquivos = at.session_state.arquivos
    assert arquivos["xlsx"][0][:2] == b"PK"
    assert len(arquivos["docx"]) == len(at.session_state.proposta["opcoes"])


def test_app_adiciona_servico_e_duplica_opcao():
    at = _rodar()
    at.selectbox(key="0|f_disc").select("Segurança do trabalho").run()
    next(b for b in at.button if b.label == "Adicionar à opção").click().run()
    assert not at.exception, at.exception
    p = at.session_state.proposta
    assert len(p["opcoes"][0]["itens"]) == 1
    next(b for b in at.button if b.label == "⧉ Duplicar").click().run()
    assert not at.exception, at.exception
    assert len(at.session_state.proposta["opcoes"]) == 2


def _carregar(nome, tmp_path, monkeypatch):
    monkeypatch.setenv("KAPTEK_REFERENCIAS", str(tmp_path / "ref.sqlite"))   # nunca toca a base real
    at = _rodar()
    at.sidebar.selectbox(key="exemplo_sel").select(nome).run()
    next(b for b in at.sidebar.button if b.label == "Carregar exemplo").click().run()
    assert not at.exception, at.exception
    return at


def test_app_turnkey_mostra_etapas_e_exporta_viabilidade(tmp_path, monkeypatch):
    at = _carregar("hvac_turnkey.json", tmp_path, monkeypatch)
    textos = [m.value for m in at.markdown]
    assert "**Turnkey — etapas do produto final**" in textos
    assert any("Projeto executivo" in t for t in textos)
    next(b for b in at.button if b.label == "Gerar planilha do estudo (.xlsx)").click().run()
    assert not at.exception, at.exception
    assert at.session_state.arquivo_viab[0][:2] == b"PK"


def test_app_piso_de_engenheiro_vira_custo_do_perfil(tmp_path, monkeypatch):
    from orcamento import referencias as rf
    at = _carregar("hvac_consultoria_2d_3d_bim.json", tmp_path, monkeypatch)
    at.radio(key="piso_modo").set_value("Engenheiro — Lei 4.950-A").run()
    perfil = at.selectbox(key="piso_perfil").value
    at.button(key="piso_apl_prop").click().run()
    assert not at.exception, at.exception
    esperado = rf.custo_hora_piso(rf.piso_lei_4950a(rf.SALARIO_MINIMO_2026, 8), 0.0, 0.70, 1200.0, 140.0)
    perfis = at.session_state.proposta["parametros"]["perfis"]
    assert perfis[perfil]["custo_h"] == pytest.approx(round(esperado, 2))
    assert perfis[perfil]["origem"]["fonte"] == "Lei 4.950-A/1966"


def test_app_busca_na_base_importada(tmp_path, monkeypatch):
    from orcamento import referencias as rf
    con = rf.conectar(str(tmp_path / "ref.sqlite"))
    rf.importar_itens(con, [{"codigo": "15.020.0010-A", "descricao": "Instalação de split hi-wall 12.000 BTU/h", "unidade": "un",
                             "valor": 742.40}], "EMOP-RJ", "2026-03", "RJ")
    con.close()
    at = _carregar("hvac_turnkey.json", tmp_path, monkeypatch)
    at.text_input(key="busca_termo").input("split").run()
    assert not at.exception, at.exception
    tabela = next(d for d in at.dataframe if {"descricao", "uf"} <= set(d.value.columns))
    assert list(tabela.value["fonte"]) == ["EMOP-RJ"]
