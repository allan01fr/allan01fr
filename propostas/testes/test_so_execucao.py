"""Proposta só de execução: fase sem serviços, só com fornecimentos (materiais e mão de obra), é uma fase com preço."""
import io

import pytest
from docx import Document
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
