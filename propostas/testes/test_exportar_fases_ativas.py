"""Exportações (planilha, proposta, CLI) ignoram fases desligadas: equivalem a uma proposta sem a fase."""
import copy
import io
import os
import re
import shutil
import subprocess

import pytest
from docx import Document
from openpyxl import load_workbook

from conftest import abrir_exemplo
from orcamento import cli, exportar_docx, exportar_xlsx, motor

RETROFIT = os.path.join(os.path.dirname(__file__), "..", "exemplos", "hvac_retrofit_fases.json")
ROTULOS = {"Horas técnicas": "total_h", "Prazo (dias corridos)": "prazo_dias_corridos",
           "Preço — parcela fixa": "preco_fixo", "Preço — parcela estimada": "preco_estimado",
           "PREÇO TOTAL (FIXO + ESTIMADO)": "preco", "Referência: tudo em escopo fechado": "preco_fechado",
           "Preço mínimo dos serviços (margem zero)": "preco_minimo_servicos"}


def _pares(cat, params, idx=1):
    """(proposta com a fase desligada, cópia com a fase, seus itens e fornecimentos removidos)."""
    p = abrir_exemplo(RETROFIT, cat, params)
    A = next(o for o in p["opcoes"] if o["id"] == "A")
    fid = A["fases"][idx]["id"]
    assert any(x["fase"] == fid for x in A["itens"]) or any(x["fase"] == fid for x in A["fornecimentos"])
    rem = copy.deepcopy(p)
    RA = next(o for o in rem["opcoes"] if o["id"] == "A")
    RA["fases"] = [f for f in RA["fases"] if f["id"] != fid]
    RA["itens"] = [x for x in RA["itens"] if x["fase"] != fid]
    RA["fornecimentos"] = [x for x in RA["fornecimentos"] if x["fase"] != fid]
    A["fases"][idx]["ativa"], A["fases"][idx]["modulo"] = False, "m1"
    return p, rem, A["fases"][idx]


def _celulas(conteudo):
    wb = load_workbook(io.BytesIO(conteudo))
    return {ws.title: [[c.value for c in row] for row in ws.iter_rows()] for ws in wb}


def _texto_docx(conteudo):
    d = Document(io.BytesIO(conteudo))
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            partes += [c.text for c in row.cells]
    return "\n".join(partes)


def test_xlsx_sem_vestigio_da_fase_desligada(cat, params):
    p, rem, f2 = _pares(cat, params)
    nomes_itens = {x.get("descricao") for x in p["opcoes"][0]["fornecimentos"] if x["fase"] == f2["id"]}
    cel = _celulas(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p)))
    plano = "\n".join(str(v) for linhas in cel["Opção A"] for v in linhas if v is not None)
    assert f2["nome"] not in plano
    for n in nomes_itens - {None, ""}:
        assert n not in "\n".join(str(v) for linhas in cel["Fornecimentos"] for v in linhas if v is not None) or \
            any(x.get("descricao") == n and x["fase"] != f2["id"] for x in p["opcoes"][0]["fornecimentos"])


def test_xlsx_equivale_a_proposta_sem_a_fase(cat, params):
    p, rem, _ = _pares(cat, params)
    a = _celulas(exportar_xlsx.gerar(cat, p, motor.precificar(cat, p)))
    b = _celulas(exportar_xlsx.gerar(cat, rem, motor.precificar(cat, rem)))
    assert a.keys() == b.keys()
    for aba in a:
        assert a[aba] == b[aba], aba


def test_docx_sem_a_fase_desligada(cat, params):
    p, rem, f2 = _pares(cat, params)
    da = exportar_docx.gerar(cat, p, motor.precificar(cat, p))
    db = exportar_docx.gerar(cat, rem, motor.precificar(cat, rem))
    assert len(da) == len(db)
    for (ca, na, _), (cb, nb, _) in zip(da, db):
        ta, tb = _texto_docx(ca), _texto_docx(cb)
        if "-opA-" in na:
            assert f2["nome"] not in ta     # a opção B também tem uma "Fase 2" com esse nome
        assert ta == tb
        fases = [int(n) for n in re.findall(r"Fase (\d+)", ta)]
        assert fases == [] or set(fases) == set(range(1, max(fases) + 1))


def test_cli_so_lista_fases_ativas(cat, params, tmp_path, capsys):
    import json
    p, rem, f2 = _pares(cat, params)
    saidas = []
    for nome, prop in (("off", p), ("rem", rem)):
        arq = tmp_path / f"{nome}.json"
        arq.write_text(json.dumps(prop), encoding="utf-8")
        cli.main([str(arq), "--saida", str(tmp_path / nome)])
        saidas.append(capsys.readouterr().out)
    aviso = "estão em fases desligadas e ficaram fora do preço."
    com_aviso = [l for l in saidas[0].splitlines() if aviso in l]
    assert len(com_aviso) == 1 and com_aviso[0].startswith("AVISO: Opção A:")      # o CLI continua avisando
    assert aviso not in saidas[1]
    sem_aviso = "\n".join(l for l in saidas[0].splitlines() if aviso not in l)
    assert sem_aviso.strip() == saidas[1].strip()
    bloco_a = saidas[0].split("Opção B")[0] if "Opção B" in saidas[0] else saidas[0]
    assert f2["nome"] not in bloco_a


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
def test_xlsx_recalculado_com_fase_desligada(cat, params, tmp_path):
    p, rem, _ = _pares(cat, params)
    res = motor.precificar(cat, p)
    arq = tmp_path / "f.xlsx"
    arq.write_bytes(exportar_xlsx.gerar(cat, p, res))
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(tmp_path / "rec"), str(arq)],
                   check=True, capture_output=True, timeout=180)
    wb = load_workbook(tmp_path / "rec" / "f.xlsx", data_only=True)
    codigos = ("#NAME?", "#VALUE!", "#REF!", "#DIV/0!", "#N/A", "#NUM!", "#NULL!", "Err:")
    assert not [c.coordinate for ws in wb for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith(codigos)]
    ws = wb["Resumo"]
    linha = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
    for i, r in enumerate(res["opcoes"]):
        for rot, chave in ROTULOS.items():
            assert float(ws.cell(linha[rot], 3 + i).value or 0) == pytest.approx(r[chave], abs=0.01), (r["nome"], rot)
        wo = wb[f"Opção {r['id']}"]
        rot_o = {wo.cell(k, 2).value: k for k in range(1, wo.max_row + 1) if wo.cell(k, 2).value}
        for k, fr in enumerate(r["fases"]):
            for rot, chave in (("PREÇO DA FASE", "preco"), ("Custo da fase", "custo_servicos"), ("Horas da fase", "total_h")):
                assert float(wo.cell(rot_o[rot], 3 + k).value or 0) == pytest.approx(fr[chave], abs=0.01), (r["id"], fr["id"], rot)


def test_cli_sem_fase_incluida_da_erro_sem_traceback(cat, params, tmp_path, capsys):
    import json
    p, _, _ = _pares(cat, params)
    for o in p["opcoes"]:
        for f in o["fases"]:
            f["ativa"] = False
    arq = tmp_path / "off.json"
    arq.write_text(json.dumps(p), encoding="utf-8")
    assert cli.main([str(arq), "--saida", str(tmp_path / "s")]) == 2
    err = capsys.readouterr().err
    assert err.startswith("Erro: ") and "nenhuma fase incluída" in err and "Traceback" not in err


def _opcao_cfd_tab(cat, params, tab_ligada, fase_item="F2"):
    """F1: CFD; F2: TAB. O CFD exclui a validação em campo, salvo se o TAB estiver na proposta."""
    import copy as _c
    from orcamento import catalogo as ct
    from orcamento import proposta as pp
    p = pp.completar(pp.padrao(_c.deepcopy(params)), cat, params)
    o = p["opcoes"][0]
    o["fases"] = [pp.nova_fase("F1", params, "Simulação"), pp.nova_fase("F2", params, "Medições")]
    o["itens"] = [pp.novo_item(ct.servico(cat, "hvac.cfd"), "F1"), pp.novo_item(ct.servico(cat, "hvac.tab"), fase_item)]
    o["fornecimentos"] = []
    o["fases"][1]["ativa"] = tab_ligada
    return p, o


EXCL_CFD = "Validação experimental em campo, salvo se contratada (TAB)."


@pytest.mark.parametrize("tab_ligada", [True, False])
def test_exclusao_exceto_se_segue_a_fase_ligada(cat, params, tab_ligada):
    p, o = _opcao_cfd_tab(cat, params, tab_ligada)
    res = motor.precificar(cat, p)["opcoes"][0]
    assert (EXCL_CFD in exportar_docx._exclusoes(cat, o, res)) is (not tab_ligada)


def test_item_sem_fase_valida_segue_o_mesmo_destino_do_motor(cat, params):
    # F1 desligada + item sem "fase": o motor o põe na primeira fase (desligada), então ele sai do preço e dos textos.
    p, o = _opcao_cfd_tab(cat, params, True)
    o["fases"][0]["ativa"] = False
    del o["itens"][0]["fase"]
    res = motor.precificar(cat, p)["opcoes"][0]
    assert [f["id"] for f in res["fases"]] == ["F2"]
    assert exportar_docx._servicos_ativos(o, res) == ["hvac.tab"]
    assert EXCL_CFD not in exportar_docx._exclusoes(cat, o, res)
    from orcamento import catalogo as ct
    textos = exportar_docx._exclusoes(cat, o, res) + exportar_docx._premissas(cat, p, o, res)
    proprios_tab = {ct.texto_condicional(t)["texto"] for t in
                    ct.servico(cat, "hvac.tab").get("exclusoes", []) + ct.servico(cat, "hvac.tab").get("premissas", [])}
    cfd = ct.servico(cat, "hvac.cfd")
    so_cfd = [ct.texto_condicional(t)["texto"] for t in cfd.get("exclusoes", []) + cfd.get("premissas", [])
              if ct.texto_condicional(t)["texto"] not in proprios_tab]
    assert so_cfd and not any(t in textos for t in so_cfd)
