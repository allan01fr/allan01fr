"""Impressão digital dos exemplos (preços, células do XLSX, texto do DOCX): guarda que as saídas não mudam."""
import hashlib
import io
import json

from docx import Document
from openpyxl import load_workbook

from orcamento import exportar_docx, exportar_xlsx, motor


def _texto_docx(conteudo):
    d = Document(io.BytesIO(conteudo))
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            partes += [c.text for c in row.cells]
    return "\n".join(partes)


def _celulas_xlsx(conteudo):
    wb = load_workbook(io.BytesIO(conteudo))
    return [[ws.title, [[c.coordinate, repr(c.value)] for row in ws.iter_rows() for c in row if c.value is not None]]
            for ws in wb]


def _h(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def impressao(cat, proposta):
    res = motor.precificar(cat, proposta)
    return {
        "precos": [[o["id"], round(o["preco"], 6)] for o in res["opcoes"]],
        "avisos": _h(res["avisos"]),
        "xlsx": _h(_celulas_xlsx(exportar_xlsx.gerar(cat, proposta, res))),
        "docx": _h([_texto_docx(c) for c, _, _ in exportar_docx.gerar(cat, proposta, res)]),
    }
