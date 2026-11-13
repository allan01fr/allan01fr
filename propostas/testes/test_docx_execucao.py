"""Proposta DOCX com projeto + acompanhamento (pacote por horas da obra) + execução por itens de kit."""
import io
import os

import pytest
from docx import Document

from orcamento import escopos, modelos, motor
from orcamento import execucao_itens as ei
from orcamento import exportar_docx
from orcamento import proposta as pp


@pytest.fixture(scope="module")
def textos(cat, params):
    p = pp.completar(pp.padrao(params), cat, params)
    O = p["opcoes"][0]
    for m in ("projeto", "acompanhamento", "execucao"):
        escopos.incluir(O, m, cat, p["parametros"])
    kit = next(k for k in modelos.carregar_kits() if k["id"] == "split_12k_padrao")
    for _ in range(10):
        modelos.aplicar_kit(O, kit, ei.config_da_opcao(O)["fase"])
    ei.config_da_opcao(O)["prazo_alvo_dias"] = 10
    ei.sincronizar_fornecimentos(O, p["parametros"])
    escopos.ligar_acompanhamento_execucao(O)
    escopos.dimensionar_acompanhamento(O, p["parametros"])
    next(f for f in O["fases"] if f["modulo"] == "acompanhamento")["cobranca"] = "pacote"
    conteudo = exportar_docx.gerar(cat, p, motor.precificar(cat, p))[0][0]
    d = Document(io.BytesIO(conteudo))
    partes = [x.text for x in d.paragraphs] + [c.text for t in d.tables for r in t.rows for c in r.cells]
    amostra = os.environ.get("KAPTEK_SALVAR_DOCX")
    if amostra:
        open(amostra, "wb").write(conteudo)
    return "\n".join(partes)


def test_secao_execucao(textos):
    assert "Itens de execução:" in textos and "Prazo de execução estimado:" in textos and "dias úteis" in textos
    assert "Equipe prevista:" in textos and "materiais e equipamentos listados" in textos
    assert "Tubulação frigorífica de cobre" in textos


def test_acompanhamento_pacote_obra(textos):
    assert "acompanhamento estimado em 20 h (6 dias úteis de obra × 2 h/dia + 8 h de mobilização e relatório)" in textos
    assert "horas excedentes a R$ 192,17/h" in textos


def test_revisao_validade_e_sem_vazamento(textos):
    assert "Rev." in textos and "15 dias corridos" in textos
    for proibido in ("HH", "margem", "Margem", "custo-hora", "overhead"):
        assert proibido not in textos
