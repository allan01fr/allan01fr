import json
import os

from conftest import RAIZ
from docx import Document

from orcamento import exportar_viabilidade_docx as ev
from orcamento import viabilidade as vb

CAMINHO = os.path.join(RAIZ, "exemplos", "hvac_retrofit_fases.json")


def _dados():
    with open(CAMINHO, encoding="utf-8") as f:
        return json.load(f)["viabilidade"]


def test_relatorio_tem_tabelas_graficos_e_conclusao(tmp_path):
    out = tmp_path / "v.docx"
    ev.gerar_relatorio_viabilidade(_dados(), str(out), cliente="Cliente Teste")
    d = Document(str(out))
    assert len(d.tables) == 2
    assert len(d.tables[1].rows) == 1 + len(_dados()["alternativas"])
    assert "VPL" in [c.text for c in d.tables[1].rows[0].cells]
    if ev.plt is not None:
        assert len(d.inline_shapes) == 3   # logo da capa + 2 gráficos
    assert any(p.text.startswith("Foram comparadas") for p in d.paragraphs)
    assert any("Cliente Teste" in p.text for p in d.paragraphs)


def test_custo_acumulado_fecha_com_vpl_e_economia():
    res = vb.calcular(_dados(), {"E": 1000000.0})
    atual, alts = ev.series_custo_acumulado(_dados(), res)
    assert atual[0] == 0 and len(atual) == res["horizonte"] + 1
    for a, ac in zip(res["alternativas"], alts):
        assert abs(ac[0] - a["capex"]) < 1e-6
        assert abs((atual[-1] - ac[-1]) - sum(a["fluxo"])) < 1e-6


def test_sem_alternativas_nao_quebra(tmp_path):
    out = tmp_path / "v.docx"
    ev.gerar_relatorio_viabilidade({"ativo": True}, str(out))
    assert "Nenhuma alternativa" in " ".join(p.text for p in Document(str(out)).paragraphs)


def test_alternativa_sem_preco_da_opcao_vira_traco_e_nota(tmp_path):
    dados = _dados()
    dados["alternativas"][0]["capex_opcao"], dados["alternativas"][0]["capex"] = "ZZ", 0
    out = tmp_path / "v.docx"
    ev.gerar_relatorio_viabilidade(dados, str(out))
    d = Document(str(out))
    assert [c.text for c in d.tables[1].rows[1].cells][1:7] == ["—"] * 6
    assert any("vincule o preço da opção ZZ" in p.text for p in d.paragraphs)
