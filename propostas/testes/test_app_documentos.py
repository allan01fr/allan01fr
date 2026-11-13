import os

import pytest

from conftest import RAIZ

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = os.path.join(RAIZ, "app", "app.py")


def test_app_carrega_com_modulos_de_documentos():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    assert len(at.tabs) >= 10
