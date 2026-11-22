import os

import pytest

from conftest import RAIZ

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = os.path.join(RAIZ, "app", "app.py")


def test_aba_bases_mostra_indices_e_tabelas_json():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, at.exception
    assert any(b.label == "Baixar/atualizar do Banco Central" for b in at.button)
    assert any(m.key == "bcb_sel" for m in at.multiselect)
