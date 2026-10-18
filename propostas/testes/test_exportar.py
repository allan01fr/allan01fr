import io
import shutil
import subprocess

import pytest
from docx import Document
from openpyxl import load_workbook

from conftest import EXEMPLOS, abrir_exemplo
from orcamento import exportar_docx, exportar_xlsx, motor

ROTULOS = {"Horas técnicas": "total_h", "Prazo (dias corridos)": "prazo_dias_corridos",
           "Preço — escopo fechado": "preco_fechado", "Preço — hora técnica (estimado)": "preco_hora",
           "Preço mínimo dos serviços (margem zero)": "preco_minimo_servicos", "PREÇO DA PROPOSTA": "preco"}


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_xlsx_tem_formulas_e_abas(caminho, cat, params):
    p = abrir_exemplo(caminho, cat, params)
    res = motor.precificar(cat, p)
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, res)))
    esperadas = {"Resumo", "Parametros", "Fornecimentos", "Cronograma", "Pagamento"}
    esperadas |= {f"Opção {o['id']}" for o in p["opcoes"]}
    assert esperadas <= set(wb.sheetnames)
    formulas = sum(1 for ws in wb for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("="))
    assert formulas > 50


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_xlsx_recalculado_bate_com_o_motor(caminho, cat, params, tmp_path):
    p = abrir_exemplo(caminho, cat, params)
    res = motor.precificar(cat, p)
    arq = tmp_path / "proposta.xlsx"
    arq.write_bytes(exportar_xlsx.gerar(cat, p, res))
    saida = tmp_path / "rec"
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(saida), str(arq)],
                   check=True, capture_output=True, timeout=180)
    wb = load_workbook(saida / "proposta.xlsx", data_only=True)
    codigos = ("#NAME?", "#VALUE!", "#REF!", "#DIV/0!", "#N/A", "#NUM!", "#NULL!", "Err:")
    erros = [f"{ws.title}!{c.coordinate}" for ws in wb for row in ws.iter_rows() for c in row
             if isinstance(c.value, str) and c.value.startswith(codigos)]
    assert not erros
    ws = wb["Resumo"]
    linha = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
    for i, r in enumerate(res["opcoes"]):
        for rot, chave in ROTULOS.items():
            assert float(ws.cell(linha[rot], 3 + i).value or 0) == pytest.approx(r[chave], abs=1.0), (r["nome"], rot)


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_docx_preenche_o_template(caminho, cat, params):
    p = abrir_exemplo(caminho, cat, params)
    res = motor.precificar(cat, p)
    docs = exportar_docx.gerar(cat, p, res)
    assert len(docs) == len(p["opcoes"])
    for (conteudo, nome, pend), r in zip(docs, res["opcoes"]):
        assert nome.startswith("KAPTEK-proposta-") and nome.endswith(".docx")
        assert exportar_docx.verificar(conteudo) == {"margem_sup_cm": 3.2, "margem_esq_cm": 3.0, "logo": True}
        assert set(pend) <= {"[Nome e cargo do signatário]"}
        d = Document(io.BytesIO(conteudo))
        escopo, prazos, honor = d.tables[2], d.tables[3], d.tables[4]
        servicos = len({l["item"] for l in r["linhas"]})
        assert len(escopo.rows) - 1 == servicos
        assert len(prazos.rows) - 1 == len(r["cronograma"]) + 1
        assert honor.rows[-1].cells[-1].text == exportar_docx.moeda(r["preco"])
        texto = "\n".join(par.text for par in d.paragraphs)
        assert p["numero"] in "\n".join(c.text for row in d.tables[0].rows for c in row.cells)
        assert "[" not in texto.replace("[Nome e cargo do signatário]", "")
