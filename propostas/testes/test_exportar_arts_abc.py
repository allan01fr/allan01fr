"""ARTs e Curva ABC nas exportações: aparecem só quando os dados existem."""
import copy
import io
import os

from docx import Document
from openpyxl import load_workbook

from conftest import abrir_exemplo
from orcamento import exportar_docx, exportar_xlsx, motor

RETROFIT = os.path.join(os.path.dirname(__file__), "..", "exemplos", "hvac_retrofit_fases.json")
ARTS = [
    {"tipo": "execucao", "modalidade": "Projeto", "atividades": ["Projeto HVAC"], "fases": ["F1"],
     "valor_base": 10000.0, "taxa": 99.64, "no_preco": True, "motivo": "ART da fase"},
    {"tipo": "subcontratado", "modalidade": "Execução", "atividades": ["Montagem"], "fases": ["F2"],
     "valor_base": 5000.0, "taxa": 88.78, "no_preco": False, "motivo": "ART própria do subcontratado (fora do preço)"},
]


def _res(cat, params):
    p = abrir_exemplo(RETROFIT, cat, params)
    r = motor.precificar(cat, p)
    return p, r


def test_sem_dados_nao_cria_abas(cat, params):
    p, r = _res(cat, params)
    nomes = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, r))).sheetnames
    assert "ARTs" not in nomes and "Curva ABC" not in nomes


def test_arts_no_xlsx_e_docx(cat, params):
    p, r = _res(cat, params)
    r = copy.deepcopy(r)
    for res in r["opcoes"]:
        res["arts"] = ARTS
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, r)))
    ws = wb["ARTs"]
    valores = [[c.value for c in row] for row in ws.iter_rows()]
    assert any("SUMIF" in str(c) for row in valores for c in row)
    assert any(row[3] == "Montagem" for row in valores)
    for conteudo, _, _ in exportar_docx.gerar(cat, p, r):
        txt = "\n".join(x.text for x in Document(io.BytesIO(conteudo)).paragraphs)
        assert "ARTs previstas" in txt and "inclusa no preço" in txt and "do subcontratado" in txt


def test_curva_abc_no_xlsx(cat, params):
    p, r = _res(cat, params)
    p["opcoes"][0]["itens_execucao"] = [{"descricao": "A", "custo": 900.0}, {"descricao": "B", "custo": 100.0}]
    ws = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, r)))["Curva ABC"]
    assert [row[1].value for row in ws.iter_rows(min_row=4, max_row=5)] == ["A", "B"]
    assert ws["G4"].value == "A"
