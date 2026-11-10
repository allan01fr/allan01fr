"""Os exemplos devem produzir exatamente os mesmos preços, células do XLSX e texto do DOCX."""
import json
import os

import pytest
from conftest import EXEMPLOS, abrir_exemplo
from golden import impressao

GOLDEN = os.path.join(os.path.dirname(__file__), "golden_exemplos.json")


@pytest.mark.parametrize("caminho", EXEMPLOS, ids=[os.path.basename(c) for c in EXEMPLOS])
def test_exemplo_nao_mudou(caminho, cat, params):
    with open(GOLDEN, encoding="utf-8") as f:
        esperado = json.load(f)
    assert impressao(cat, abrir_exemplo(caminho, cat, params)) == esperado[os.path.basename(caminho)]
