"""Proposta só de execução: fase sem serviços, só com fornecimentos (materiais e mão de obra), é uma fase com preço."""
import io
import shutil

import pytest
from docx import Document
from conftest import erros_xlsx, recalcular_xlsx
from openpyxl import load_workbook

from orcamento import escopos, exportar_docx, exportar_xlsx, motor
from orcamento import catalogo as ct
from orcamento import proposta as pp

AVISO_SEM_ITENS = "Opção A / Execução: fase sem itens — lance materiais e mão de obra na aba Fornecimentos."


def _base(cat, params):
    return pp.completar(pp.padrao(params), cat, params)


def so_execucao(cat, params, com_fornecimentos=True):
    p = _base(cat, params)
    o = p["opcoes"][0]
    escopos.incluir(o, "execucao", cat, p["parametros"])
    if com_fornecimentos:
        o["fornecimentos"] += [
            pp.novo_fornecimento("Tubulação de cobre", "material", "m", 120, 85.0, fase="F1"),
            pp.novo_fornecimento("Instalação do sistema", "mo_execucao", "dia", 20, 650.0, fase="F1")]
    return p


def projeto_e_execucao(cat, params):
    p = _base(cat, params)
    o = p["opcoes"][0]
    escopos.incluir(o, "projeto", cat, p["parametros"])
    escopos.incluir(o, "execucao", cat, p["parametros"])
    o["fornecimentos"] += [
        pp.novo_fornecimento("Tubulação de cobre", "material", "m", 120, 85.0, fase="F2"),
        pp.novo_fornecimento("Instalação do sistema", "mo_execucao", "dia", 20, 650.0, fase="F2")]
    return p


def test_so_execucao_tem_preco_e_nenhum_aviso_de_servicos(cat, params):
    p = so_execucao(cat, params)
    res = motor.precificar(cat, p)
    r = res["opcoes"][0]
    assert r["linhas"] == [] and r["preco"] > 0 and r["total_h"] == 0
    assert not [a for a in res["avisos"] if "nenhum serviço com horas" in a or "fase sem serviços" in a
                or "fase sem itens" in a]


def test_execucao_sem_nada_avisa_fase_sem_itens(cat, params):
    res = motor.precificar(cat, so_execucao(cat, params, com_fornecimentos=False))
    assert AVISO_SEM_ITENS in res["avisos"]
    assert not any("fase sem serviços" in a for a in res["avisos"])


def test_fase_comum_sem_nada_continua_com_o_aviso_de_servicos(cat, params):
    p = _base(cat, params)
    res = motor.precificar(cat, p)
    assert any("fase sem serviços" in a for a in res["avisos"])
    assert any("nenhum serviço com horas" in a for a in res["avisos"])


def test_projeto_mais_execucao_sem_aviso_de_servicos(cat, params):
    res = motor.precificar(cat, projeto_e_execucao(cat, params))
    assert not [a for a in res["avisos"] if "sem serviços" in a or "sem itens" in a or "nenhum serviço" in a]


def _texto_docx(conteudo):
    d = Document(io.BytesIO(conteudo))
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            partes += [c.text for c in row.cells]
    return "\n".join(partes)


CASOS = {"so_execucao": lambda cat, params: so_execucao(cat, params), "projeto_e_execucao": projeto_e_execucao}


@pytest.mark.parametrize("caso", CASOS)
def test_exporta_sem_linhas_de_servico(caso, cat, params):
    p = CASOS[caso](cat, params)
    res = motor.precificar(cat, p)
    if caso == "so_execucao":
        assert res["opcoes"][0]["linhas"] == []
    xlsx = exportar_xlsx.gerar(cat, p, res)
    assert load_workbook(io.BytesIO(xlsx)).sheetnames
    docs = exportar_docx.gerar(cat, p, res)
    assert docs
    for conteudo, nome, pend in docs:
        texto = _texto_docx(conteudo)
        assert "nan" not in texto.lower().split() and "inf" not in texto.lower().split()
        assert "Tubulação de cobre" in texto or "execução" in texto.lower()


ROTULOS = {"Horas técnicas": "total_h", "Prazo (dias corridos)": "prazo_dias_corridos",
           "Preço — parcela fixa": "preco_fixo", "Preço — parcela estimada": "preco_estimado",
           "PREÇO TOTAL (FIXO + ESTIMADO)": "preco", "Referência: tudo em escopo fechado": "preco_fechado",
           "Preço mínimo dos serviços (margem zero)": "preco_minimo_servicos"}


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
@pytest.mark.parametrize("caso", CASOS)
def test_xlsx_recalculado_bate_com_o_motor(caso, cat, params, tmp_path):
    p = CASOS[caso](cat, params)
    res = motor.precificar(cat, p)
    wb = recalcular_xlsx(exportar_xlsx.gerar(cat, p, res), tmp_path)
    assert not erros_xlsx(wb)
    ws = wb["Resumo"]
    linha = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
    r = res["opcoes"][0]
    for rot, chave in ROTULOS.items():
        valor = ws.cell(linha[rot], 3).value
        if valor == "a definir":        # opção sem horas nem cronograma: o prazo é "a definir", não 0
            assert chave == "prazo_dias_corridos" and r[chave] == 0 and not r["cronograma"]
            continue
        assert float(valor or 0) == pytest.approx(r[chave], abs=0.01), rot
    wo = wb["Opção A"]
    rot_o = {wo.cell(k, 2).value: k for k in range(1, wo.max_row + 1) if wo.cell(k, 2).value}
    for k, fr in enumerate(r["fases"]):
        for rot, chave in (("PREÇO DA FASE", "preco"), ("Custo da fase", "custo_servicos"), ("Horas da fase", "total_h")):
            assert float(wo.cell(rot_o[rot], 3 + k).value or 0) == pytest.approx(fr[chave], abs=0.01), (fr["id"], rot)


def _docx_unico(cat, params, p):
    res = motor.precificar(cat, p)
    return _texto_docx(exportar_docx.gerar(cat, p, res)[0][0])


def test_docx_so_execucao_objeto_escopo_prazo_e_pagamento(cat, params):
    texto = _docx_unico(cat, params, so_execucao(cat, params))
    assert "Compreende: ," not in texto and "Compreende: Execução" in texto
    assert "fornecimento de materiais e mão de obra" in texto
    assert "Prazo total estimado\na definir" in texto and "0 dias" not in texto
    assert "na conclusão da execução" in texto and "atividades de campo" not in texto


def test_docx_projeto_e_execucao_prazo_da_execucao_a_definir(cat, params):
    texto = _docx_unico(cat, params, projeto_e_execucao(cat, params))
    assert "Fase 2 — Execução\na definir" in texto and "0 dias" not in texto
