"""Textos da proposta e da planilha quando há fase de execução (só fornecimentos, sem ART no preço)."""
import io
import shutil

import pytest
from conftest import erros_xlsx, recalcular_xlsx
from docx import Document
from openpyxl import load_workbook
from test_so_execucao import projeto_e_execucao, so_execucao

from orcamento import exportar_docx, exportar_xlsx, motor
from orcamento import proposta as pp
from orcamento import escopos

ART_NEUTRA = ("A Anotação de Responsabilidade Técnica (ART) de execução não está incluída neste preço; "
              "quando exigida, será recolhida e cobrada à parte.")
ART_PADRAO = "Os serviços serão acompanhados da devida Anotação de Responsabilidade Técnica (ART)"
FRASE_MISTA = "A ART cobre as fases de serviços de engenharia e não inclui a execução."


def _doc(cat, p):
    res = motor.precificar(cat, p)
    return res, Document(io.BytesIO(exportar_docx.gerar(cat, p, res)[0][0]))


def _paragrafos(d):
    return [x.text for x in d.paragraphs]


def _tabela(d, *cab):
    for t in d.tables:
        if [c.text for c in t.rows[0].cells][:len(cab)] == list(cab):
            return [[c.text for c in r.cells] for r in t.rows[1:]]
    raise AssertionError(cab)


# ---- 1. honorários e seção 7
def test_multifase_sem_linha_zerada_de_escopo_fechado(cat, params):
    _, d = _doc(cat, projeto_e_execucao(cat, params))
    descricoes = [l[0] for l in _tabela(d, "Descrição", "Qtd.")]
    assert "Fase 2 — Execução: escopo fechado" not in descricoes
    assert not any("R$ 0,00" == l[3] for l in _tabela(d, "Descrição", "Qtd."))
    assert "Fase 1 — Projeto: escopo fechado" in descricoes


def test_multifase_lista_fornecimentos_item_a_item(cat, params):
    _, d = _doc(cat, projeto_e_execucao(cat, params))
    linhas = _tabela(d, "Descrição", "Qtd.")
    assert not any(l[0].endswith(": fornecimentos") for l in linhas)
    tub = next(l for l in linhas if "Tubulação de cobre" in l[0])
    ins = next(l for l in linhas if "Instalação do sistema" in l[0])
    assert tub[1:] == ["120 m", "R$ 96,90", "R$ 11.628,00"]
    assert ins[1:] == ["20 dia", "R$ 793,00", "R$ 15.860,00"]
    assert linhas[-1][3] == "R$ 64.145,18"


def test_multifase_com_servicos_e_fornecimentos_mantem_linha_vb(cat, params):
    p = projeto_e_execucao(cat, params)
    p["opcoes"][0]["fornecimentos"].append(pp.novo_fornecimento("Cabo de comando", "material", "m", 10, 5.0, fase="F1"))
    _, d = _doc(cat, p)
    assert "Fase 1 — Projeto: fornecimentos" in [l[0] for l in _tabela(d, "Descrição", "Qtd.")]


# ---- 2. ART
def test_so_execucao_art_neutra_no_docx(cat, params):
    _, d = _doc(cat, so_execucao(cat, params))
    pars = _paragrafos(d)
    assert ART_NEUTRA in pars
    assert not any(t.startswith(ART_PADRAO) for t in pars)


def test_art_padrao_quando_todas_as_fases_tem_servicos(cat, params):
    p = pp.completar(pp.padrao(params), cat, params)
    escopos.incluir(p["opcoes"][0], "projeto", cat, p["parametros"])
    _, d = _doc(cat, p)
    pars = _paragrafos(d)
    assert any(t.startswith(ART_PADRAO) and FRASE_MISTA not in t for t in pars)
    assert ART_NEUTRA not in pars


def test_projeto_mais_execucao_mantem_texto_e_acrescenta_frase(cat, params):
    _, d = _doc(cat, projeto_e_execucao(cat, params))
    art = [t for t in _paragrafos(d) if t.startswith(ART_PADRAO)]
    assert len(art) == 1 and art[0].endswith(FRASE_MISTA) and "somente produz efeitos" in art[0]


def test_aviso_fase_sem_art_no_preco(cat, params):
    aviso = "Opção A / Execução: fase sem ART no preço — confirme se a execução exige ART própria."
    assert aviso in motor.precificar(cat, so_execucao(cat, params))["avisos"]
    assert aviso in motor.precificar(cat, projeto_e_execucao(cat, params))["avisos"]
    p = pp.completar(pp.padrao(params), cat, params)
    escopos.incluir(p["opcoes"][0], "projeto", cat, p["parametros"])
    assert not any("sem ART" in a for a in motor.precificar(cat, p)["avisos"])


def _rodape(wb):
    ws = wb["Resumo"]
    return [str(ws.cell(r, 1).value) for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value]


def test_rodape_do_resumo_neutro_so_execucao(cat, params):
    p = so_execucao(cat, params)
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p))))
    nota = next(t for t in _rodape(wb) if t.startswith("Valores com tributos"))
    assert "ART de execução não está incluída neste preço" in nota
    assert "ART registrada e quitada" not in nota


def test_rodape_do_resumo_misto_acrescenta_frase(cat, params):
    p = projeto_e_execucao(cat, params)
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p))))
    nota = next(t for t in _rodape(wb) if t.startswith("Valores com tributos"))
    assert "ART registrada e quitada (Lei 6.496/1977)" in nota and FRASE_MISTA in nota


# ---- 3. objeto
def test_objeto_vazio_so_execucao(cat, params):
    p = so_execucao(cat, params)
    p["objeto"] = ""
    _, d = _doc(cat, p)
    obj = next(t for t in _paragrafos(d) if "Compreende:" in t)
    assert obj.startswith("Fornecimento e execução de instalações. Compreende: Execução")
    assert "serviços técnicos de engenharia: serviços" not in obj


def test_objeto_vazio_multifase_sem_clausula_duplicada(cat, params):
    p = projeto_e_execucao(cat, params)
    p["objeto"] = ""
    _, d = _doc(cat, p)
    obj = next(t for t in _paragrafos(d) if "Compreende:" in t)
    assert obj.startswith("Prestação de serviços técnicos de engenharia, em 2 fases. Compreende: Fase 1 — projeto;")
    assert "serviços técnicos de engenharia: serviços" not in obj


def test_objeto_vazio_fase_unica_com_servicos(cat, params):
    p = pp.completar(pp.padrao(params), cat, params)
    escopos.incluir(p["opcoes"][0], "projeto", cat, p["parametros"])
    p["objeto"] = ""
    _, d = _doc(cat, p)
    obj = next(t for t in _paragrafos(d) if "Compreende:" in t)
    assert obj.startswith("Prestação de serviços técnicos de engenharia. Compreende: ")


def test_objeto_preenchido_so_execucao_comeca_por_fornecimento(cat, params):
    p = so_execucao(cat, params)
    p["objeto"] = "Climatização do 2º andar"
    _, d = _doc(cat, p)
    obj = next(t for t in _paragrafos(d) if "Compreende:" in t)
    assert obj.startswith("Fornecimento e execução de instalações: Climatização do 2º andar. Compreende:")


# ---- 4. Resumo sem horas
def _resumo(wb):
    ws = wb["Resumo"]
    return {ws.cell(r, 1).value: ws.cell(r, 3) for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value}


def test_resumo_sem_horas_mostra_a_definir_e_travessao(cat, params):
    p = so_execucao(cat, params)
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p))))
    c = _resumo(wb)
    assert c["Prazo (dias úteis)"].value == "a definir" and c["Prazo (dias corridos)"].value == "a definir"
    assert c["Margem efetiva"].value == "—" and c["Preço dos serviços por hora (R$/h)"].value == "—"


def test_resumo_com_horas_continua_numerico(cat, params):
    p = projeto_e_execucao(cat, params)
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p))))
    c = _resumo(wb)
    for rot in ("Prazo (dias úteis)", "Prazo (dias corridos)", "Margem efetiva", "Preço dos serviços por hora (R$/h)"):
        assert str(c[rot].value).startswith("="), rot


def test_resumo_so_execucao_com_prazo_de_execucao_tem_prazo_numerico(cat, params):
    p = so_execucao(cat, params)
    p["opcoes"][0]["prazo_execucao_dias"] = 30
    res = motor.precificar(cat, p)
    assert res["opcoes"][0]["cronograma"]
    wb = load_workbook(io.BytesIO(exportar_xlsx.gerar(cat, p, res)))
    assert str(_resumo(wb)["Prazo (dias corridos)"].value).startswith("=")


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
@pytest.mark.parametrize("caso", ["so", "misto"])
def test_resumo_recalculado_sem_erros(caso, cat, params, tmp_path):
    p = so_execucao(cat, params) if caso == "so" else projeto_e_execucao(cat, params)
    wb = recalcular_xlsx(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p)), tmp_path)
    assert not erros_xlsx(wb)
    c = _resumo(wb)
    if caso == "so":
        assert c["Prazo (dias corridos)"].value == "a definir" and c["Margem efetiva"].value == "—"
    else:
        assert float(c["Prazo (dias corridos)"].value) == 22
