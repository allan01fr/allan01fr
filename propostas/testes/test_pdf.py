import pytest
from docx import Document

from orcamento import pdf

pytestmark = pytest.mark.skipif(not pdf.disponivel(), reason="LibreOffice não instalado")


def _docx_minimo() -> bytes:
    import io

    doc = Document()
    doc.add_paragraph("Teste de conversão para PDF")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_bytes_docx_para_pdf_gera_pdf():
    saida = pdf.bytes_docx_para_pdf(_docx_minimo(), nome="teste.docx")
    assert saida.startswith(b"%PDF")


def test_docx_para_pdf_grava_arquivo(tmp_path):
    origem = tmp_path / "entrada.docx"
    origem.write_bytes(_docx_minimo())
    destino = pdf.docx_para_pdf(origem, pasta_saida=tmp_path / "saida")
    assert destino.endswith("entrada.pdf")
    with open(destino, "rb") as f:
        assert f.read(5) == b"%PDF-"
