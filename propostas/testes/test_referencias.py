import copy
import io
import shutil
import subprocess

import pytest
from openpyxl import Workbook
from openpyxl.styles import Border, Side

from orcamento import catalogo as ct
from orcamento import motor
from orcamento import proposta as pp
from orcamento import referencias as rf


@pytest.fixture
def con(tmp_path):
    c = rf.conectar(str(tmp_path / "ref.sqlite"))
    yield c
    c.close()


def xlsx(linhas, bordas=False):
    wb = Workbook()
    ws = wb.active
    if bordas:          # vai virar PDF: colunas largas para o texto não ser cortado na impressão
        for col in "ABC":
            ws.column_dimensions[col].width = 32
    fino = Side(style="thin")
    for r, linha in enumerate(linhas, 1):
        for c, v in enumerate(linha, 1):
            cel = ws.cell(r, c, v)
            if bordas and v is not None:
                cel.border = Border(left=fino, right=fino, top=fino, bottom=fino)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# layout típico: títulos e data-base acima do cabeçalho, linhas de grupo sem preço
EMOP = [
    ["EMOP — Empresa de Obras Públicas do Estado do Rio de Janeiro"],
    ["Catálogo de custos unitários — data-base: mar/2026"],
    [],
    ["Código", "Descrição", "Unidade", "Custo unitário (R$)", "Preço unitário (R$)"],
    ["15", "AR CONDICIONADO E VENTILAÇÃO", None, None, None],
    ["15.020.0010-A", "Instalação de condicionador split hi-wall até 12.000 BTU/h", "un", "580,00", "742,40"],
    ["15.020.0050-A", "Rede frigorígena em cobre 1/4\" e 3/8\" com isolamento", "m", "98,10", "125,57"],
]

SINAPI = [
    ["SINAPI — PREÇOS DE INSUMOS"],
    ["LOCALIDADE: RIO DE JANEIRO", None, "DATA DE PREÇO: 06/2026"],
    ["CODIGO", "DESCRICAO DO INSUMO", "UNIDADE", "ORIGEM DE PRECO", "PRECO MEDIANO R$"],
    ["39421", "CONDICIONADOR DE AR SPLIT HI-WALL 12000 BTU/H", "UN", "C", 2350.75],
    ["2436", "ELETRICISTA (HORISTA)", "H", "CR", 28.4],
]


# ----------------------------------------------------------------------------- utilitários
@pytest.mark.parametrize("texto, esperado", [
    ("R$ 1.234,56", 1234.56), ("1234.56", 1234.56), ("1,234.56", 1234.56), ("742,40", 742.40),
    (98.1, 98.1), ("", None), ("—", None), (None, None)])
def test_converter_valor(texto, esperado):
    assert rf.converter_valor(texto) == esperado


def test_info_do_nome():
    assert rf.info_do_nome("SINAPI_Preco_Ref_Insumos_RJ_202606_Desonerado.xlsx") == \
        {"uf": "RJ", "data_base": "2026-06", "desonerado": True}
    assert rf.info_do_nome("SINAPI_RJ_06-2026_NaoDesonerado.xlsx")["desonerado"] is False
    assert rf.info_do_nome("catalogo emop.xlsx") == {"uf": "", "data_base": "", "desonerado": None}


@pytest.mark.parametrize("texto, esperado", [
    ("2026-03", "2026-03"), ("03/2026", "2026-03"), ("mar/2026", "2026-03"), ("mar/26", "2026-03"), ("março 2026", "2026-03"),
    ("x", "")])
def test_converter_mes(texto, esperado):
    assert rf.converter_mes(texto) == esperado


# ----------------------------------------------------------------------------- importação
def test_cabecalho_emop_abaixo_dos_titulos_e_coluna_de_preco():
    linhas = rf.ler_tabela(xlsx(EMOP), "EMOP_RJ_2026-03.xlsx")
    ini, mapa = rf.detectar_cabecalho(linhas, "EMOP-RJ")
    assert ini == 3
    assert mapa == {"codigo": 0, "descricao": 1, "unidade": 2, "valor": 4}   # preço, não custo
    itens = rf.extrair_itens(linhas, ini, mapa)
    assert [i["codigo"] for i in itens] == ["15.020.0010-A", "15.020.0050-A"]   # linha de grupo ignorada
    assert itens[0]["valor"] == pytest.approx(742.40)


def test_cabecalho_sinapi_usa_preco_mediano():
    linhas = rf.ler_tabela(xlsx(SINAPI), "SINAPI.xlsx")
    ini, mapa = rf.detectar_cabecalho(linhas, "SINAPI")
    assert ini == 2 and mapa["valor"] == 4 and mapa["descricao"] == 1
    itens = rf.extrair_itens(linhas, ini, mapa)
    assert itens[0] == {"codigo": "39421", "descricao": "CONDICIONADOR DE AR SPLIT HI-WALL 12000 BTU/H",
                        "unidade": "UN", "valor": 2350.75}


def test_csv_generico_com_numero_brasileiro():
    texto = "Tabela de referência ABRAVA\n\nItem;Serviço;Unid;Valor\nA1;Limpeza de fancoil;un;1.250,00\nA2;Medição de vazão;ponto;85,5\n"
    linhas = rf.ler_tabela(texto.encode("utf-8"), "abrava.csv")
    ini, mapa = rf.detectar_cabecalho(linhas, "ABRAVA")
    itens = rf.extrair_itens(linhas, ini, mapa)
    assert [(i["codigo"], i["valor"]) for i in itens] == [("A1", 1250.0), ("A2", 85.5)]


def test_sem_cabecalho_reconhecivel():
    assert rf.detectar_cabecalho([["a", "b"], [1, 2]]) == (None, {})


def test_formato_nao_suportado():
    with pytest.raises(ValueError):
        rf.ler_tabela(b"", "tabela.doc")


def test_importar_substitui_mesma_fonte_uf_e_data_base(con):
    itens = rf.extrair_itens(*(lambda l: (l, *rf.detectar_cabecalho(l, "EMOP-RJ")))(rf.ler_tabela(xlsx(EMOP), "e.xlsx")))
    assert rf.importar_itens(con, itens, "EMOP-RJ", "2026-03", "RJ") == 2
    rf.importar_itens(con, itens, "EMOP-RJ", "2026-03", "RJ")           # reimportação não duplica
    rf.importar_itens(con, itens[:1], "EMOP-RJ", "2025-09", "RJ")       # outra data-base convive
    resumo = {(f["data_base"], f["itens"]) for f in rf.fontes_importadas(con)}
    assert resumo == {("2026-03", 2), ("2025-09", 1)}
    rf.apagar_fonte(con, "EMOP-RJ", "RJ", "2025-09")
    assert [f["data_base"] for f in rf.fontes_importadas(con)] == ["2026-03"]


# ----------------------------------------------------------------------------- busca e hierarquia
def test_busca_segue_a_hierarquia_rj(con, params):
    item = [{"codigo": "X", "descricao": "Split hi-wall 12000 BTU/h instalado", "unidade": "un", "valor": 1000.0}]
    for fonte in ("SICRO", "SINAPI", "ORSE", "SCO-RIO", "EMOP-RJ"):
        rf.importar_itens(con, item, fonte, "2026-06", "RJ")
    rf.importar_itens(con, item, "SINAPI", "2026-06", "SP")
    achados = rf.buscar(con, "split 12000", "RJ", hierarquia=params["hierarquia_fontes"])
    assert [a["fonte"] for a in achados] == ["EMOP-RJ", "SCO-RIO", "SINAPI", "SICRO", "ORSE"]
    assert achados[-1]["prioridade"] is None                 # fonte fora da hierarquia vai para o fim
    assert all(a["uf"] == "RJ" for a in achados)
    # outra UF usa a hierarquia padrão
    assert [a["fonte"] for a in rf.buscar(con, "split", "SP", hierarquia=params["hierarquia_fontes"])] == ["SINAPI"]


def test_busca_exige_todas_as_palavras_sem_acento(con):
    rf.importar_itens(con, [{"codigo": "1", "descricao": "Válvula de expansão eletrônica", "unidade": "un", "valor": 1.0},
                            {"codigo": "2", "descricao": "Válvula de esfera", "unidade": "un", "valor": 1.0}], "SINAPI", "2026-06", "RJ")
    assert [a["codigo"] for a in rf.buscar(con, "valvula expansao")] == ["1"]
    assert rf.buscar(con, "   ") == []


def test_busca_prefere_data_base_mais_recente(con):
    item = [{"codigo": "1", "descricao": "Fancoil 5 TR", "unidade": "un", "valor": 1.0}]
    rf.importar_itens(con, item, "SINAPI", "2025-12", "RJ")
    rf.importar_itens(con, item, "SINAPI", "2026-06", "RJ")
    assert [a["data_base"] for a in rf.buscar(con, "fancoil", "RJ")] == ["2026-06", "2025-12"]


# ----------------------------------------------------------------------------- cesta e atualização
REFS = [{"fonte": "EMOP-RJ", "valor": 100.0}, {"fonte": "SINAPI", "valor": 104.0}, {"fonte": "Cotação A", "valor": 96.0},
        {"fonte": "Cotação B", "valor": 160.0}]


def test_cesta_mediana_e_valores_fora_da_faixa():
    c = rf.cesta(REFS, "mediana", 0.25, 3)
    assert c["mediana"] == pytest.approx(102.0)
    assert [l["fora_da_faixa"] for l in c["linhas"]] == [False, False, False, True]
    assert c["valor"] == pytest.approx(100.0)                # mediana de 96, 100 e 104
    assert c["n"] == 4 and c["n_validos"] == 3
    assert any("Cotação B" in a for a in c["avisos"])


@pytest.mark.parametrize("criterio, esperado", [("media", 100.0), ("menor", 96.0)])
def test_cesta_outros_criterios(criterio, esperado):
    assert rf.cesta(REFS, criterio)["valor"] == pytest.approx(esperado)


def test_cesta_avisa_poucas_fontes_e_vazia():
    assert any("mínimo 3" in a for a in rf.cesta(REFS[:2])["avisos"])
    assert rf.cesta([{"fonte": "x", "valor": ""}])["valor"] is None


def test_atualizacao_por_indice(con):
    rf.importar_indices(con, "INCC-M", [("2026-01", 1000.0), ("2026-06", 1030.0)])
    assert rf.atualizar(con, 200.0, "2026-01", "2026-06", "INCC-M") == (pytest.approx(206.0), pytest.approx(1.03))
    assert rf.atualizar(con, 200.0, "2025-01", "2026-06", "INCC-M") == (200.0, None)      # mês sem índice
    assert rf.atualizar(con, 200.0, "2026-06", "2026-06", "INCC-M") == (200.0, 1.0)
    refs = [{"fonte": "EMOP-RJ", "valor": 100.0, "data_base": "2026-01"}, {"fonte": "SINAPI", "valor": 103.0, "data_base": "2026-06"},
            {"fonte": "SCO-RIO", "valor": 99.0, "data_base": "2025-11"}]
    c = rf.cesta(refs, "mediana", con=con, data_alvo="2026-06", indice="INCC-M")
    assert c["linhas"][0]["valor_atualizado"] == pytest.approx(103.0)
    assert c["linhas"][2]["fator"] is None
    assert any("Sem índice INCC-M" in a and "SCO-RIO" in a for a in c["avisos"])
    assert rf.indices_disponiveis(con) == [{"nome": "INCC-M", "de": "2026-01", "ate": "2026-06", "meses": 2}]


def test_meses():
    assert rf.mes_anterior("2026-02", 3) == "2025-11"
    assert rf.meses_entre("2025-11", "2026-02") == 3


# ----------------------------------------------------------------------------- convenções → custo/h
def test_piso_lei_4950a_nas_duas_bases():
    # 6 SM para 6 h; 8 h = 6 + 2 × 1,25 = 8,5 SM
    assert rf.piso_lei_4950a(rf.SALARIO_MINIMO_2026, 8) == pytest.approx(1621.00 * 8.5)
    assert rf.piso_lei_4950a(rf.BASE_CONGELADA_STF, 8) == pytest.approx(1212.00 * 8.5)
    assert rf.piso_lei_4950a(1000, 6) == pytest.approx(6000)
    assert rf.piso_lei_4950a(1000, 4) == pytest.approx(6000)      # abaixo de 6 h não reduz


def test_custo_hora_do_piso():
    assert rf.custo_hora_piso(3000, 0.30, 0.80, 600, 140) == pytest.approx((3000 * 1.3 * 1.8 + 600) / 140)
    assert rf.custo_hora_piso(3000, horas_produtivas=0) == 0.0


def test_pisos_e_encargos_no_banco(con):
    rf.importar_pisos(con, [{"funcao": "Mecânico de refrigeração", "piso": 2890.0},
                            {"funcao": "Ajudante", "piso": 1780.0, "carga_semanal": 44}], "SINDRATAR-RJ", "CCT 2026/2027", "2026-05", "RJ")
    pisos = rf.listar_pisos(con, "SINDRATAR-RJ")
    assert [p["funcao"] for p in pisos] == ["Ajudante", "Mecânico de refrigeração"]
    assert pisos[1]["carga_semanal"] == 44
    rf.importar_encargos(con, [{"uf": "RJ", "regime": "mensalista", "desonerado": False, "pct": 0.7123, "data_base": "2026-01"},
                               {"uf": "RJ", "regime": "mensalista", "desonerado": False, "pct": 0.7189, "data_base": "2026-06"},
                               {"uf": "RJ", "regime": "horista", "desonerado": True, "pct": 0.8455, "data_base": "2026-06"}])
    assert rf.encargos(con, "RJ") == pytest.approx(0.7189)              # data-base mais recente
    assert rf.encargos(con, "RJ", "horista", True) == pytest.approx(0.8455)
    assert rf.encargos(con, "SP") is None


def test_cub_no_banco(con):
    rf.importar_cub(con, [{"uf": "RJ", "padrao": "CSL-8N", "mes": "2026-08", "valor": 2310.5},
                          {"uf": "RJ", "padrao": "R8-N", "mes": "2026-09", "valor": 2601.2}])
    assert [c["mes"] for c in rf.listar_cub(con, "RJ")] == ["2026-09", "2026-08"]


def test_registro_de_entidades():
    fontes = rf.carregar_fontes()
    ids = {e["id"] for e in fontes["entidades"]}
    assert {"EMOP-RJ", "SCO-RIO", "SINAPI", "SENGE-RJ", "SINDRATAR-RJ", "SINDUSCON-RIO", "ABRAVA", "CBIC-CUB"} <= ids
    assert all(e["preset"] in rf.PRESETS for e in fontes["entidades"])


# ----------------------------------------------------------------------------- ART por faixa e CUB no preço
def test_art_por_faixa(params):
    pr = copy.deepcopy(params)
    assert motor.valor_art(pr, 10000) == pytest.approx(108.39)
    assert motor.valor_art(pr, 15000) == pytest.approx(108.39)
    assert motor.valor_art(pr, 15000.01) == pytest.approx(285.59)
    pr["art"]["modo"] = "fixo"
    assert motor.valor_art(pr, 1e6) == pytest.approx(pr["art"]["valor"])


def _proposta_simples(cat, params, area=0.0):
    p = pp.completar(pp.padrao(copy.deepcopy(params)), cat, params)
    p["contexto"]["area_ref"] = area
    p["opcoes"][0]["itens"] = [pp.novo_item(ct.servico(cat, "hvac.projeto"))]
    return p


def test_art_do_preco_cai_na_faixa_do_valor_do_contrato(cat, params):
    p = _proposta_simples(cat, params)
    r = motor.precificar(cat, p)["opcoes"][0]
    assert r["art"] == pytest.approx(motor.valor_art(p["parametros"], r["preco_fechado"]))
    p["parametros"]["art"]["faixas"] = [{"ate": r["preco_fechado"] * 10, "valor": 50.0}, {"ate": None, "valor": 999.0}]
    assert motor.precificar(cat, p)["opcoes"][0]["art"] == pytest.approx(50.0)


def test_indicador_cub(cat, params):
    p = _proposta_simples(cat, params, area=1500.0)
    p["parametros"]["cub"].update({"valor": 2500.0, "pct_honorarios": 0.04})
    assert motor.precificar(cat, p)["opcoes"][0]["ref_cub"] == pytest.approx(0.04 * 2500.0 * 1500.0)
    p["parametros"]["cub"]["valor"] = 0
    assert motor.precificar(cat, p)["opcoes"][0]["ref_cub"] is None


# ----------------------------------------------------------------------------- PDF
@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
def test_extracao_de_pdf(tmp_path):
    pytest.importorskip("pdfplumber")
    origem = tmp_path / "cct.xlsx"
    origem.write_bytes(xlsx([["Função", "Piso salarial (R$)", "Unidade"],
                             ["Mecânico de refrigeração", "2.890,00", "mês"],
                             ["Ajudante de refrigeração", "1.780,00", "mês"]], bordas=True))
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(origem)],
                   check=True, capture_output=True, timeout=180)
    linhas = rf.ler_tabela((tmp_path / "cct.pdf").read_bytes(), "cct.pdf")
    ini, mapa = rf.detectar_cabecalho(linhas)
    itens = rf.extrair_itens(linhas, ini, mapa)
    assert [(i["descricao"], i["valor"]) for i in itens] == [("Mecânico de refrigeração", 2890.0), ("Ajudante de refrigeração", 1780.0)]
