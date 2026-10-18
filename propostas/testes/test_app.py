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
