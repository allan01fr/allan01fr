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


def test_modelo_preenche_tudo(caso, tmp_path):
    p, res = caso
    c, r = str(tmp_path / "c.docx"), str(tmp_path / "r.docx")
    assert os.path.exists(ed.MODELO_CONTRATO) and "fases" in ed.listar_placeholders(ed.MODELO_CONTRATO)
    ed.gerar_contrato(p, res, c, revisao=1)
    ed.gerar_recibo(p, res["preco"], "sinal", r, data="2026-11-12", numero="001")
    for caminho in (c, r):
        assert "{{" not in _texto(caminho)
    t = _texto(c)
    assert ed.AVISO in t and "Rev. 01" in t and "escopo fechado" in t
    assert "CREA-RJ" in "".join(c.text for s in Document(c).sections for tb in s.header.tables for r in tb.rows for c in r.cells) and "sobre o valor da execução" in t


def test_modelo_proprio(caso, tmp_path):
    p, res = caso
    m = Document()
    m.add_paragraph("Ola {{cliente_nome}} — total {{valor_t")  # run partido
    m.paragraphs[0].add_run("otal}} / {{valor_extenso}}")
    m.add_paragraph("{{fases}}", style="List Bullet")
    m.save(tmp_path / "m.docx")
    assert ed.listar_placeholders(str(tmp_path / "m.docx")) == {"cliente_nome", "valor_total", "valor_extenso", "fases"}
    c = str(tmp_path / "c.docx")
    ed.gerar_contrato(p, res, c, modelo=str(tmp_path / "m.docx"))
    t = _texto(c)
    assert "{{" not in t and p["cliente"]["razao"] in t and ed.moeda(res["preco"]) in t
    assert t.count("Fase ") == len(res["fases"])


def test_extenso_inalterado():
    assert ed.extenso(2_500_000.5) == "dois milhões e quinhentos mil reais e cinquenta centavos"
