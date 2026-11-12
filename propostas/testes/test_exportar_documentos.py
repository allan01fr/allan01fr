import os

import pytest
from docx import Document

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import exportar_documentos as ed
from orcamento import motor

RETROFIT = next(e for e in EXEMPLOS if e.endswith("hvac_retrofit_fases.json"))


def _texto(caminho):
    d = Document(caminho)
    return "\n".join([p.text for p in d.paragraphs] + [c.text for t in d.tables for r in t.rows for c in r.cells])


@pytest.fixture(scope="module")
def caso(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    r = motor.precificar(cat, p)
    return p, r["opcoes"][0]


def test_extenso():
    assert ed.extenso(1234.56) == "mil duzentos e trinta e quatro reais e cinquenta e seis centavos"
    assert ed.extenso(1) == "um real"
    assert ed.extenso(1_000_000) == "um milhão de reais"
    assert ed.extenso(0.01) == "um centavo"


def test_contrato(caso, tmp_path):
    p, res = caso
    c = str(tmp_path / "c.docx")
    ed.gerar_contrato(p, res, c, revisao=2)
    t = _texto(c)
    assert p["cliente"]["razao"] in t and ed.moeda(res["preco"]) in t
    assert "Rev. 02" in t and ed.AVISO in t and "[foro]" in t


def test_recibo(caso, tmp_path):
    p, res = caso
    c = str(tmp_path / "r.docx")
    ed.gerar_recibo(p, res["preco"], "sinal", c, data="2026-11-12", numero="001")
    t = _texto(c)
    assert p["cliente"]["razao"] in t and ed.moeda(res["preco"]) in t and "12/11/2026" in t
