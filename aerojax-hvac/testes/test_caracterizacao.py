"""Caracterização: congela o relatório e os indicadores do app atual antes de qualquer refatoração."""

import base64
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from clima2d import projeto as pj
from referencia import RAIZ, PROJETO_EXEMPLO, PASTA_REFERENCIAS, normalizar_relatorio


@pytest.fixture(scope="module")
def caso():
    projeto = pj.carregar_json(PROJETO_EXEMPLO.read_text(encoding="utf-8"))
    r = pj.simular_projeto(projeto)
    return projeto, r, pj.relatorio_html(projeto, r)   # mesma chamada do app (aba 5), sem estudo de malha


def test_relatorio_igual_a_referencia(caso):
    _, _, html = caso
    esperado = (PASTA_REFERENCIAS / "relatorio_escritorio_rapido.html").read_text(encoding="utf-8")
    assert normalizar_relatorio(html) == esperado
    png = base64.b64decode(re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", html).group(1))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_indicadores_iguais_a_referencia(caso):
    _, r, _ = caso
    esperado = json.loads((PASTA_REFERENCIAS / "indicadores_escritorio_rapido.json").read_text(encoding="utf-8"))
    assert r["indicadores"].keys() == esperado.keys()
    for k, v in esperado.items():
        assert r["indicadores"][k] == pytest.approx(v, rel=1e-6, abs=1e-9), k


def test_app_abre_sem_erro():
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    at = AppTest.from_file(str(RAIZ / "app" / "app.py"), default_timeout=120).run()
    assert not at.exception
    assert len(at.error) == 0
