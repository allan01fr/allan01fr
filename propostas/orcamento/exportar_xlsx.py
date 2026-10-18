"""
Planilha de escopo e preços, no padrão visual KAPTEK, com fórmulas vivas.

Toda conta do motor é refeita em fórmula: mudar uma produtividade, um custo/h,
a margem ou uma quantidade na planilha recalcula horas, preço, prazo e parcelas.
Só usa funções compatíveis com o Excel 2007 (SUM, SUMIF, INDEX/MATCH, ROUNDUP, IF).

Convenção de cores: fundo amarelo e texto azul = entrada; texto verde = vínculo
com outra aba; grafite = fórmula.
"""

import io
import json
import math
import os

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

from . import motor
from . import parametros as pm

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGO = os.path.join(RAIZ, "modelos", "logo-horizontal.png")
ORG = os.path.join(RAIZ, "dados", "kaptek_org.json")

AZUL, GRAFITE, COBRE, CINZA = "1B3A5C", "3E4448", "C18E6D", "8A8A8A"
FUNDO_CAB, FILETE, AMARELO, AZUL_ENTRADA, VERDE = "F2F4F6", "D8D8D8", "FFF2CC", "0000FF", "008000"
FONTE = "Arial"

MOEDA = '"R$" #,##0.00;("R$" #,##0.00);"-"'
HORAS = '#,##0.0;(#,##0.0);"-"'
NUM = '#,##0.00;(#,##0.00);"-"'
PCT = '0.0%;(0.0%);"-"'
INT = '0;(0);"-"'

_fino = Side(style="thin", color=FILETE)
BORDA = Border(left=_fino, right=_fino, top=_fino, bottom=_fino)


def _fill(cor):
    return PatternFill("solid", start_color=cor, end_color=cor)


class Folha:
    """Atalhos de escrita com o estilo da marca."""

    def __init__(self, ws):
        self.ws = ws

    def c(self, linha, col, valor=None, fmt=None, negrito=False, cor=GRAFITE, fundo=None, alinhar=None,
          quebra=False, tam=10, borda=True):
        cel = self.ws.cell(linha, col, valor)
        cel.font = Font(name=FONTE, size=tam, bold=negrito, color=cor)
        if fmt:
            cel.number_format = fmt
        if fundo:
            cel.fill = _fill(fundo)
        if alinhar or quebra:
            cel.alignment = Alignment(horizontal=alinhar, vertical="center", wrap_text=quebra)
        if borda:
            cel.border = BORDA
        return cel

    def entrada(self, linha, col, valor, fmt=None):
        return self.c(linha, col, valor, fmt, cor=AZUL_ENTRADA, fundo=AMARELO)

    def vinculo(self, linha, col, formula, fmt=None, negrito=False):
        return self.c(linha, col, formula, fmt, negrito=negrito, cor=VERDE)

    def titulo(self, linha, texto, ate_col):
        self.ws.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=ate_col)
        cel = self.c(linha, 1, texto, negrito=True, cor="FFFFFF", fundo=AZUL, tam=13, borda=False)
        cel.alignment = Alignment(vertical="center", indent=1)
        self.ws.row_dimensions[linha].height = 26
        cobre = Side(style="medium", color=COBRE)
        for col in range(1, ate_col + 1):
            self.ws.cell(linha, col).border = Border(bottom=cobre)

    def secao(self, linha, texto, ate_col):
        self.ws.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=ate_col)
        cel = self.c(linha, 1, texto, negrito=True, cor=AZUL, tam=11, borda=False)
        cel.border = Border(bottom=Side(style="thin", color=COBRE))
        self.ws.row_dimensions[linha].height = 20

    def cabecalho(self, linha, rotulos, col=1):
        for i, r in enumerate(rotulos):
            self.c(linha, col + i, r, negrito=True, cor=AZUL, fundo=FUNDO_CAB, alinhar="center", quebra=True)
        self.ws.row_dimensions[linha].height = 30

    def nota(self, linha, texto, ate_col, col=1):
        self.ws.merge_cells(start_row=linha, start_column=col, end_row=linha, end_column=ate_col)
        cel = self.c(linha, col, texto, cor=CINZA, tam=8, borda=False)
        cel.alignment = Alignment(wrap_text=True, vertical="top")

    def larguras(self, mapa):
        for col, w in mapa.items():
            self.ws.column_dimensions[col].width = w


def _q(nome):
    """Nome de aba entre aspas para uso em fórmula."""
    return "'" + nome.replace("'", "''") + "'"


def _org():
    try:
        with open(ORG, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


def _logo(ws, ancora):
    if os.path.exists(LOGO):
        img = XLImage(LOGO)
        img.width, img.height = 200, round(200 * img.height / img.width)
        ws.add_image(img, ancora)


def _impressao(ws, paisagem=True):
    ws.page_setup.orientation = "landscape" if paisagem else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True


# ----------------------------------------------------------------------------- Parâmetros
def _aba_parametros(wb, cat, proposta):
    params = proposta["parametros"]
    ws = wb.create_sheet("Parametros")
    f = Folha(ws)
    f.larguras({"A": 10, "B": 40, "C": 18, "D": 18, "E": 60})
    f.titulo(1, "PARÂMETROS COMERCIAIS DESTA PROPOSTA", 5)
    ref = {}

    f.secao(3, "Custo e taxa de venda por perfil", 5)
    f.cabecalho(4, ["Código", "Perfil", "Custo/h (R$)", "Taxa de venda/h (R$)", "Observação"])
    ref["custo"], ref["taxa"] = {}, {}
    for i, (cod, nome) in enumerate(cat["perfis"].items()):
        r = 5 + i
        f.c(r, 1, cod, alinhar="center")
        f.c(r, 2, nome)
        f.entrada(r, 3, float(params["perfis"][cod]["custo_h"]), MOEDA)
        f.entrada(r, 4, float(params["perfis"][cod]["taxa_venda_h"]), MOEDA)
        f.c(r, 5, "Salário + encargos + benefícios ÷ horas produtivas" if i == 0 else None, cor=CINZA, tam=8)
        ref["custo"][cod] = f"Parametros!$C${r}"
        ref["taxa"][cod] = f"Parametros!$D${r}"
    r = 5 + len(cat["perfis"]) + 1

    f.secao(r, "Formação do preço", 5)
    r += 1
    imp = pm.aliquota_impostos(params)
    regime = params["impostos"]["regime"]
    nota_imp = ("Simples Nacional — alíquota efetiva informada" if regime == "simples"
                else "Lucro Presumido: PIS + COFINS + IRPJ/CSLL presumidos + ISS")
    linhas = [
        ("overhead_metodo", "Método de overhead (percentual | hora)", params["overhead"]["metodo"], None, "percentual = % sobre a MO; hora = custo fixo ÷ horas faturáveis × horas da proposta"),
        ("overhead_pct", "Overhead sobre a mão de obra", float(params["overhead"]["pct"]), PCT, "Estrutura, aluguel, administrativo, software"),
        ("custo_fixo", "Custo fixo mensal do escritório", float(params["overhead"]["custo_fixo_mensal"]), MOEDA, "Usado no método hora"),
        ("horas_fat", "Horas faturáveis por mês", float(params["overhead"]["horas_faturaveis_mes"]), NUM, "Usado no método hora"),
        ("imp", "Impostos sobre o faturamento", imp, PCT, nota_imp),
        ("margem", "Margem-alvo sobre o preço", float(params["margem"]), PCT, "Lucro desejado"),
        ("cont", f"Contingência (risco {proposta['contexto']['risco']})", float(params["contingencia"][proposta["contexto"]["risco"]]), PCT, "Reserva de risco do escopo fechado"),
        ("adm", "Administração sobre reembolsáveis (hora técnica)", float(params["reembolsaveis_adm"]), PCT, "Aplicada aos custos diretos no modelo hora técnica"),
        ("horas_dia", "Horas por dia de trabalho", float(params["cronograma"]["horas_dia"]), NUM, "Base do cronograma"),
        ("area", "Área de referência", float(proposta["contexto"].get("area_ref") or 0), NUM, "m² — usada nos indicadores R$/m² e CUB (0 = não calcular)"),
        ("cub_valor", f"CUB/m² ({params['cub'].get('padrao', '')} {params['cub'].get('mes', '')})".strip(), float(params["cub"].get("valor") or 0), MOEDA,
         f"{params['cub'].get('fonte', 'SINDUSCON')} — 0 = sem referência de CUB"),
        ("cub_pct", "% do CUB × área para honorários de referência", float(params["cub"].get("pct_honorarios") or 0), PCT, "Faixa usual 2% a 11%"),
        ("garantia_pct", f"Provisão de garantia — turnkey ({params['turnkey']['garantia_meses']} meses)", float(params["turnkey"]["garantia_pct"]), PCT,
         "Sobre o custo de fornecimento e execução"),
        ("cesta_faixa", "Cesta de preços: faixa aceita em torno da mediana", float(params["cesta"]["faixa_alerta"]), PCT,
         "Referências fora da faixa ficam marcadas e saem do valor adotado (aba Pesquisa de preços)"),
    ]
    for chave, rot, val, fmt, obs in linhas:
        f.c(r, 2, rot)
        f.entrada(r, 3, val, fmt)
        f.c(r, 5, obs, cor=CINZA, tam=8)
        ref[chave] = f"Parametros!$C${r}"
        r += 1
    f.c(r, 2, "Overhead por hora (método hora)", negrito=True)
    f.c(r, 3, f"=IF({ref['horas_fat']}>0,{ref['custo_fixo']}/{ref['horas_fat']},0)", MOEDA, fundo=FUNDO_CAB)
    ref["overhead_h"] = f"Parametros!$C${r}"
    r += 2

    f.secao(r, "BDI de fornecimento e execução (turnkey)", 5)
    r += 1
    f.cabecalho(r, ["Código", "Categoria", "BDI", "", "Observação"])
    r += 1
    rot_cat = {"material": "Material", "equipamento": "Equipamento", "mo_execucao": "Mão de obra de execução", "subcontrato": "Subcontrato"}
    ini = r
    for k, v in params["bdi_fornecimento"].items():
        f.c(r, 1, k, alinhar="center")
        f.c(r, 2, rot_cat.get(k, k))
        f.entrada(r, 3, float(v), PCT)
        r += 1
    ref["bdi_chaves"] = f"Parametros!$A${ini}:$A${r - 1}"
    ref["bdi_valores"] = f"Parametros!$C${ini}:$C${r - 1}"
    f.nota(r, params.get("notas", {}).get("bdi_fornecimento", ""), 5)
    r += 2
    for k in ("impostos", "custos", "art"):
        if params.get("notas", {}).get(k):
            f.nota(r, params["notas"][k], 5)
            r += 1
    ws.freeze_panes = "A5"
    _impressao(ws, paisagem=False)
    return ref


# ----------------------------------------------------------------------------- Opção
COL_PERFIL = 9     # I: primeira coluna de horas por perfil


def _aba_opcao(wb, cat, proposta, opcao, res, ref):
    perfis = list(cat["perfis"])
    n_p = len(perfis)
    nome = f"Opção {opcao['id']}"[:31]
    ws = wb.create_sheet(nome)
    f = Folha(ws)
    c_tot = COL_PERFIL + n_p          # total h
    c_mo = c_tot + 1                  # custo MO
    c_fixo = c_mo + 2                 # bloco de produtividade (deixa uma coluna de folga)
    c_unid = c_fixo + n_p
    ultima = c_unid + n_p - 1
    turnkey = res.get("modalidade") == "turnkey"
    f.titulo(1, f"{opcao['nome'].upper()} — " + ("TURNKEY (PREÇO GLOBAL)" if turnkey else "ESCOPO, HORAS E PREÇO"), c_mo)
    f.nota(2, "Horas por perfil = (fixo + unid × qtd^b) × fator. Edite as células amarelas: quantidade, expoente, "
              "fator e a produtividade (fixo/unid) à direita.", c_mo)

    cab = ["#", "Serviço", "Atividade", "Entregável", "Etapa", "Qtd (driver)", "b", "Fator"]
    cab += [f"h {p}" for p in perfis] + ["Total (h)", "Custo MO (R$)", ""]
    cab += [f"Fixo {p}" for p in perfis] + [f"Unid {p}" for p in perfis]
    f.cabecalho(3, cab)
    ws.cell(3, c_mo + 1).fill = PatternFill()
    rot_etapa = {e["id"]: e["rotulo"] for e in cat["etapas"]}

    r0 = 4
    for i, l in enumerate(res["linhas"]):
        r = r0 + i
        f.c(r, 1, l["item"] + 1, INT, alinhar="center")
        f.c(r, 2, l["servico_nome"], quebra=True, tam=9)
        f.c(r, 3, l["nome"], quebra=True, tam=9)
        f.c(r, 4, l["entregavel"], quebra=True, tam=9)
        f.c(r, 5, rot_etapa[l["etapa"]], quebra=True, tam=9)
        f.entrada(r, 6, round(l["q"], 6), NUM)
        f.entrada(r, 7, l["b"], NUM)
        f.entrada(r, 8, round(l["fator"], 6), "0.000")
        for k, p in enumerate(perfis):
            cf, cu = L(c_fixo + k), L(c_unid + k)
            f.entrada(r, c_fixo + k, l["fixo"][p], HORAS)
            f.entrada(r, c_unid + k, l["unid"][p], "0.0000")
            f.c(r, COL_PERFIL + k, f"=({cf}{r}+{cu}{r}*$F{r}^$G{r})*$H{r}", HORAS)
        f.c(r, c_tot, f"=SUM({L(COL_PERFIL)}{r}:{L(COL_PERFIL + n_p - 1)}{r})", HORAS, negrito=True)
        mo = "+".join(f"{L(COL_PERFIL + k)}{r}*{ref['custo'][p]}" for k, p in enumerate(perfis))
        f.c(r, c_mo, "=" + mo, MOEDA)
        ws.row_dimensions[r].height = 30
    r_fim = r0 + max(len(res["linhas"]), 1) - 1
    rt = r_fim + 1
    f.c(rt, 2, "TOTAL", negrito=True, fundo=FUNDO_CAB)
    for col in range(3, COL_PERFIL):
        f.c(rt, col, None, fundo=FUNDO_CAB)
    for col in range(COL_PERFIL, c_mo + 1):
        letra = L(col)
        f.c(rt, col, f"=SUM({letra}{r0}:{letra}{r_fim})", MOEDA if col == c_mo else HORAS, negrito=True, fundo=FUNDO_CAB)
    cel = {"total_h": f"${L(c_tot)}${rt}", "mo": f"${L(c_mo)}${rt}",
           "etapas": f"$E${r0}:$E${r_fim}", "horas": f"${L(c_tot)}${r0}:${L(c_tot)}${r_fim}"}
    cel["h_perfil"] = {p: f"${L(COL_PERFIL + k)}${rt}" for k, p in enumerate(perfis)}

    # custos diretos
    r = rt + 2
    f.secao(r, "Custos diretos (instrumentos, terceiros, deslocamento, ART)", 8)
    r += 1
    f.cabecalho(r, ["", "Descrição", "Serviço / memória", "Unid", "Qtd", "Valor unit. (R$)", "Valor (R$)"])
    r += 1
    d0 = r
    for d in res["diretos"]:
        f.c(r, 2, d["descricao"], quebra=True, tam=9)
        f.c(r, 3, d["servico_nome"], quebra=True, tam=9)
        f.c(r, 4, d["unid"], alinhar="center")
        if d.get("garantia"):
            f.vinculo(r, 5, f"=SUMIF(Fornecimentos!$A:$A,\"{opcao['id']}\",Fornecimentos!$G:$G)", MOEDA)
            f.vinculo(r, 6, f"={ref['garantia_pct']}", PCT)
        else:
            f.entrada(r, 5, round(d["qtd"], 6), NUM)
            f.entrada(r, 6, round(d["valor_unit"], 2), MOEDA)
        f.c(r, 7, f"=E{r}*F{r}", MOEDA)
        r += 1
    d_fim = max(r - 1, d0)
    if r == d0:
        r += 1
    f.c(r, 2, "TOTAL DE CUSTOS DIRETOS", negrito=True, fundo=FUNDO_CAB)
    f.c(r, 7, f"=SUM(G{d0}:G{d_fim})", MOEDA, negrito=True, fundo=FUNDO_CAB)
    cel["diretos"] = f"$G${r}"

    # formação do preço
    r += 2
    f.secao(r, "Formação do preço — escopo fechado", 4)
    r += 1
    q_forn = "Fornecimentos"
    oid = opcao["id"]
    cadeia = [
        ("mo", "Custo de mão de obra", f"={cel['mo']}", MOEDA, "Horas × custo/h de cada perfil"),
        ("overhead", "Overhead", f"=IF({ref['overhead_metodo']}=\"hora\",{cel['total_h']}*{ref['overhead_h']},{cel['mo']}*{ref['overhead_pct']})", MOEDA, "Conforme o método da aba Parametros"),
        ("dir", "Custos diretos", f"={cel['diretos']}", MOEDA, ""),
        ("custo", "CUSTO DOS SERVIÇOS", None, MOEDA, "MO + overhead + diretos"),
        ("cont", "Contingência", None, MOEDA, "Custo × contingência"),
        ("preco_serv", "PREÇO DOS SERVIÇOS", None, MOEDA, "(Custo + contingência) ÷ (1 − impostos − margem)"),
        ("impostos", "  Impostos", None, MOEDA, "Preço × alíquota"),
        ("margem", "  Margem", None, MOEDA, "Preço × margem-alvo"),
        ("custo_forn", "Custo dos fornecimentos", f"=SUMIF({q_forn}!$A:$A,\"{oid}\",{q_forn}!$G:$G)", MOEDA, "Aba Fornecimentos"),
        ("preco_forn", "Preço dos fornecimentos (com BDI)", f"=SUMIF({q_forn}!$A:$A,\"{oid}\",{q_forn}!$I:$I)", MOEDA, "Custo × (1 + BDI da categoria)"),
        ("fechado", "PREÇO — ESCOPO FECHADO", None, MOEDA, "Serviços + fornecimentos"),
    ]
    pos = {}
    for chave, rot, formula, fmt, obs in cadeia:
        pos[chave] = r
        r += 1
    linhas_f = {
        "custo": f"=C{pos['mo']}+C{pos['overhead']}+C{pos['dir']}",
        "cont": f"=C{pos['custo']}*{ref['cont']}",
        "preco_serv": f"=(C{pos['custo']}+C{pos['cont']})/(1-{ref['imp']}-{ref['margem']})",
        "impostos": f"=C{pos['preco_serv']}*{ref['imp']}",
        "margem": f"=C{pos['preco_serv']}*{ref['margem']}",
        "fechado": f"=C{pos['preco_serv']}+C{pos['preco_forn']}",
    }
    for chave, rot, formula, fmt, obs in cadeia:
        rr = pos[chave]
        forte = rot.isupper()
        f.c(rr, 2, rot, negrito=forte, fundo=FUNDO_CAB if forte else None)
        formula = formula or linhas_f[chave]
        if chave in ("custo_forn", "preco_forn"):
            f.vinculo(rr, 3, formula, fmt, negrito=forte)
        else:
            f.c(rr, 3, formula, fmt, negrito=forte, fundo=FUNDO_CAB if forte else None)
        f.c(rr, 4, obs, cor=CINZA, tam=8, fundo=FUNDO_CAB if forte else None)
    F = {k: f"$C${v}" for k, v in pos.items()}

    # outros modelos
    r += 1
    f.secao(r, "Outros modelos de preço e indicadores", 4)
    r += 1
    honor = "+".join(f"{cel['h_perfil'][p]}*{ref['taxa'][p]}" for p in perfis)
    modelos = [
        ("honor", "Hora técnica — honorários (horas × taxa de venda)", "=" + honor, MOEDA, "Taxas por perfil na aba Parametros"),
        ("reemb", "Hora técnica — reembolsáveis", f"={cel['diretos']}*(1+{ref['adm']})/(1-{ref['imp']})", MOEDA, "Diretos × (1 + administração) ÷ (1 − impostos)"),
        ("hora", "PREÇO — HORA TÉCNICA (estimado)", None, MOEDA, "Honorários + reembolsáveis + fornecimentos"),
        ("hora_teto", "Hora técnica — teto (horas + contingência)", None, MOEDA, "Limite máximo a faturar"),
        ("fee_pct", "% sobre o valor da obra / CAPEX", float(opcao.get("fee_pct") or 0), PCT, "Entrada"),
        ("fee_base_inf", "Valor da obra / CAPEX informado", float(opcao.get("fee_base") or 0), MOEDA, "0 = usar o custo dos fornecimentos"),
        ("fee_base", "Base usada", None, MOEDA, ""),
        ("fee_hon", "Honorários no modelo %", None, MOEDA, "% × base"),
        ("fee", "PREÇO — % SOBRE OBRA", None, MOEDA, "Honorários % + fornecimentos (zero se não houver base)"),
        ("minimo", "Preço mínimo dos serviços (margem zero)", None, MOEDA, "Custo ÷ (1 − impostos)"),
        ("me_fechado", "Margem efetiva — escopo fechado", None, PCT, "Inclui a contingência não consumida"),
        ("me_hora", "Margem efetiva — hora técnica", None, PCT, ""),
        ("me_fee", "Margem efetiva — % sobre obra", None, PCT, ""),
        ("capex_min", "Valor de obra mínimo para o % igualar o escopo fechado", None, MOEDA, "Preço dos serviços ÷ %"),
        ("rs_h", "Preço por hora técnica (R$/h)", None, MOEDA, "Preço dos serviços ÷ horas"),
        ("rs_m2", "Preço por m² (R$/m²)", None, MOEDA, "Escopo fechado ÷ área de referência"),
        ("ref_cub", "Referência: % do CUB × área", None, MOEDA, "Comparação com honorários usuais (aba Parametros)"),
        ("modelo", "Modelo escolhido (fechado | hora | fee)", res["modelo_preco"], None,
         "Turnkey: sempre preço global (fechado)" if turnkey else "Entrada"),
        ("preco", "PREÇO DA OPÇÃO", None, MOEDA, "Conforme o modelo escolhido"),
    ]
    for chave, *_ in modelos:
        pos[chave] = r
        r += 1
    F = {k: f"$C${v}" for k, v in pos.items()}
    calc = {
        "hora": f"={F['honor']}+{F['reemb']}+{F['preco_forn']}",
        "hora_teto": f"={F['honor']}*(1+{ref['cont']})+{F['reemb']}+{F['preco_forn']}",
        "fee_base": f"=IF({F['fee_base_inf']}>0,{F['fee_base_inf']},{F['custo_forn']})",
        "fee_hon": f"={F['fee_pct']}*{F['fee_base']}",
        "fee": f"=IF({F['fee_base']}>0,{F['fee_hon']}+{F['preco_forn']},0)",
        "minimo": f"={F['custo']}/(1-{ref['imp']})",
        "me_fechado": f"=IF({F['preco_serv']}>0,({F['preco_serv']}*(1-{ref['imp']})-{F['custo']})/{F['preco_serv']},0)",
        "me_hora": f"=IF({F['honor']}+{F['reemb']}>0,(({F['honor']}+{F['reemb']})*(1-{ref['imp']})-{F['custo']})/({F['honor']}+{F['reemb']}),0)",
        "me_fee": f"=IF({F['fee_hon']}>0,({F['fee_hon']}*(1-{ref['imp']})-{F['custo']})/{F['fee_hon']},0)",
        "capex_min": f"=IF({F['fee_pct']}>0,{F['preco_serv']}/{F['fee_pct']},0)",
        "rs_h": f"=IF({cel['total_h']}>0,{F['preco_serv']}/{cel['total_h']},0)",
        "rs_m2": f"=IF({ref['area']}>0,{F['fechado']}/{ref['area']},0)",
        "ref_cub": f"={ref['cub_pct']}*{ref['cub_valor']}*{ref['area']}",
        "preco": f"=IF({F['modelo']}=\"hora\",{F['hora']},IF(AND({F['modelo']}=\"fee\",{F['fee_base']}>0),{F['fee']},{F['fechado']}))",
    }
    for chave, rot, val, fmt, obs in modelos:
        rr = pos[chave]
        forte = rot.isupper()
        f.c(rr, 2, rot, negrito=forte, fundo=FUNDO_CAB if forte else None)
        if val is not None and chave not in calc:
            f.entrada(rr, 3, val, fmt)
        else:
            f.c(rr, 3, calc[chave] if chave in calc else val, fmt, negrito=forte, fundo=FUNDO_CAB if forte else None)
        f.c(rr, 4, obs, cor=CINZA, tam=8, fundo=FUNDO_CAB if forte else None)

    if res.get("checklist_turnkey"):
        r += 1
        f.secao(r, "Turnkey — etapas do produto final", 4)
        r += 1
        rot_status = {"atendida": "Incluída", "dispensada": "A cargo do contratante", "opcional": "Opcional — não incluída",
                      "faltando": "FALTANDO"}
        for e in res["checklist_turnkey"]:
            f.c(r, 2, e["rotulo"])
            f.c(r, 3, rot_status[e["status"]], negrito=e["status"] == "faltando",
                cor="C00000" if e["status"] == "faltando" else GRAFITE)
            r += 1

    larg = {"A": 5, "B": 44, "C": 38, "D": 30, "E": 20, "F": 14, "G": 14, "H": 9}
    for k in range(n_p):
        larg[L(COL_PERFIL + k)] = 9
        larg[L(c_fixo + k)] = 8
        larg[L(c_unid + k)] = 8
    larg[L(c_tot)] = 10
    larg[L(c_mo)] = 15
    larg[L(c_mo + 1)] = 3
    f.larguras(larg)
    # o bloco de produtividade fica agrupado (recolhível) para não poluir a impressão
    ws.column_dimensions.group(L(c_fixo), L(ultima), outline_level=1, hidden=False)
    ws.freeze_panes = "C4"
    _impressao(ws)
    ws.print_area = f"A1:{L(c_mo)}{r}"
    cel.update({k: f"{_q(nome)}!$C${v}" for k, v in pos.items()})
    cel["total_h_ext"] = f"{_q(nome)}!{cel['total_h']}"
    cel["etapas_ext"] = f"{_q(nome)}!{cel['etapas']}"
    cel["horas_ext"] = f"{_q(nome)}!{cel['horas']}"
    cel["aba"] = nome
    return cel


# ----------------------------------------------------------------------------- Fornecimentos
def _aba_fornecimentos(wb, proposta, resultados, ref):
    ws = wb.create_sheet("Fornecimentos")
    f = Folha(ws)
    f.larguras({"A": 8, "B": 46, "C": 16, "D": 8, "E": 10, "F": 16, "G": 16, "H": 9, "I": 16, "J": 16, "K": 14, "L": 11})
    f.titulo(1, "FORNECIMENTOS E SUBCONTRATAÇÕES", 12)
    f.cabecalho(3, ["Opção", "Descrição", "Categoria", "Unid", "Qtd", "Custo unit. (R$)", "Custo (R$)", "BDI", "Preço (R$)",
                    "Fonte", "Código", "Data-base"])
    r = 4
    linhas = {}
    for o, res in zip(proposta["opcoes"], resultados):
        for it in res["fornecimentos"]:
            linhas[(o["id"], it.get("uid"))] = r
            f.c(r, 1, o["id"], alinhar="center")
            f.c(r, 2, it.get("descricao", ""), quebra=True, tam=9)
            f.entrada(r, 3, it["categoria"])
            f.c(r, 4, it.get("unid", ""), alinhar="center")
            f.entrada(r, 5, float(it.get("qtd") or 0), NUM)
            f.entrada(r, 6, float(it.get("custo_unit") or 0), MOEDA)
            f.c(r, 7, f"=E{r}*F{r}", MOEDA)
            f.vinculo(r, 8, f"=INDEX({ref['bdi_valores']},MATCH(C{r},{ref['bdi_chaves']},0))", PCT)
            f.c(r, 9, f"=G{r}*(1+H{r})", MOEDA)
            f.c(r, 10, it.get("fonte", ""), tam=9)
            f.c(r, 11, it.get("codigo", ""), tam=9)
            f.c(r, 12, it.get("data_base", ""), tam=9, alinhar="center")
            r += 1
    if r == 4:
        f.nota(4, "Sem fornecimentos nesta proposta. Para incluir, use a aba 'Fornecimentos e subcontratações' do app "
                  "(categorias: material, equipamento, mo_execucao, subcontrato).", 12)
    ws.freeze_panes = "A4"
    _impressao(ws)
    return linhas


# ----------------------------------------------------------------------------- Pesquisa de preços
CRITERIOS = {"mediana": ("Mediana", "MEDIAN"), "media": ("Média", "AVERAGE"), "menor": ("Menor valor", "MIN")}


def _aba_pesquisa(wb, proposta, resultados, ref, linhas_forn):
    """Cesta de preços de cada item com referências: valores, atualização, desvio da mediana e valor adotado."""
    itens = [(o, it) for o, res in zip(proposta["opcoes"], resultados) for it in res["fornecimentos"] if it.get("referencias")]
    if not itens:
        return
    cfg = proposta["parametros"]["cesta"]
    rot_crit, func = CRITERIOS.get(cfg["criterio"], CRITERIOS["mediana"])
    ws = wb.create_sheet("Pesquisa de preços")
    f = Folha(ws)
    f.larguras({"A": 30, "B": 14, "C": 11, "D": 15, "E": 11, "F": 15, "G": 12, "H": 14, "I": 15})
    f.titulo(1, "PESQUISA DE PREÇOS (CESTA)", 9)
    f.nota(2, f"Critério: {rot_crit.lower()} das referências dentro da faixa em torno da mediana (Parametros). Recomenda-se "
              f"no mínimo {cfg['minimo_fontes']} referências por item. O fator de atualização é o do índice no momento em que a "
              "cesta foi aplicada (1 = sem atualização).", 9)
    faixa = ref["cesta_faixa"]
    r = 4
    for o, it in itens:
        f.secao(r, f"Opção {o['id']} — {it.get('descricao', '')}", 9)
        r += 1
        f.cabecalho(r, ["Fonte / fornecedor", "Código", "Data-base", "Valor (R$)", "Fator", "Atualizado (R$)",
                        "Desvio", "Situação", "Na cesta (R$)"])
        ini = r + 1
        fim = ini + len(it["referencias"]) - 1
        for k, rf_ in enumerate(it["referencias"]):
            r = ini + k
            f.c(r, 1, rf_.get("fonte", ""), tam=9)
            f.c(r, 2, rf_.get("codigo", ""), tam=9)
            f.c(r, 3, rf_.get("data_base", ""), tam=9, alinhar="center")
            f.entrada(r, 4, float(rf_.get("valor") or 0), MOEDA)
            f.entrada(r, 5, float(rf_.get("fator") or 1.0), '0.0000')
            f.c(r, 6, f"=D{r}*E{r}", MOEDA)
            f.c(r, 7, f"=IF(MEDIAN($F${ini}:$F${fim})=0,0,F{r}/MEDIAN($F${ini}:$F${fim})-1)", PCT)
            f.c(r, 8, f'=IF(ABS(G{r})>{faixa},"fora da faixa","ok")', alinhar="center")
            # MEDIAN, AVERAGE e MIN ignoram o texto vazio: só os valores dentro da faixa entram no adotado
            f.c(r, 9, f'=IF(H{r}="ok",F{r},"")', MOEDA)
        r = fim + 1
        rotulos = [("Mediana", f"=MEDIAN(F{ini}:F{fim})"), ("Média", f"=AVERAGE(F{ini}:F{fim})"), ("Menor", f"=MIN(F{ini}:F{fim})"),
                   ("Referências / dentro da faixa", f'=COUNT(F{ini}:F{fim})&" / "&COUNT(I{ini}:I{fim})')]
        for rot, form in rotulos:
            f.c(r, 8, rot, alinhar="right", tam=9)
            f.c(r, 9, form, MOEDA if rot != rotulos[-1][0] else None, alinhar="right")
            r += 1
        f.c(r, 8, f"Valor adotado ({rot_crit.lower()})", negrito=True, alinhar="right")
        adotado = f"I{r}"
        f.c(r, 9, f"=IF(COUNT(I{ini}:I{fim})=0,{func}(F{ini}:F{fim}),{func}(I{ini}:I{fim}))", MOEDA, negrito=True, fundo=FUNDO_CAB)
        r += 1
        lf = linhas_forn.get((o["id"], it.get("uid")))
        if lf:
            f.c(r, 8, "Custo unit. em Fornecimentos", alinhar="right", tam=9)
            f.vinculo(r, 9, f"=Fornecimentos!F{lf}", MOEDA)
            f.c(r + 1, 8, "Diferença para o adotado", alinhar="right", tam=9)
            f.c(r + 1, 9, f"=IF({adotado}=0,0,I{r}/{adotado}-1)", PCT)
            r += 2
        r += 1
    ws.freeze_panes = "A4"
    _impressao(ws)


# ----------------------------------------------------------------------------- Cronograma
def _aba_cronograma(wb, cat, proposta, resultados, celulas, ref):
    ws = wb.create_sheet("Cronograma")
    f = Folha(ws)
    semanas = max([math.ceil(r["prazo_dias_uteis"] / 5) for r in resultados] + [1]) + 1
    ultima = 9 + semanas
    f.larguras({"A": 34, "B": 10, "C": 8, "D": 10, "E": 8, "F": 8, "G": 10, "H": 26, "I": 2})
    for k in range(semanas):
        ws.column_dimensions[L(10 + k)].width = 3.6
    f.titulo(1, "CRONOGRAMA (DIAS ÚTEIS) E GANTT SEMANAL", min(ultima, 30))
    f.nota(2, "Dias úteis = horas da etapa ÷ (horas/dia × equipe), no mínimo 1. Etapas em sequência; atividades da "
              "mesma etapa em paralelo. Dias corridos = dias úteis × 7/5.", min(ultima, 30))
    r = 4
    for o, res in zip(proposta["opcoes"], resultados):
        cel = celulas[o["id"]]
        f.secao(r, o["nome"], 8)
        r += 1
        f.cabecalho(r, ["Etapa", "Horas", "Equipe", "Dias úteis", "Início", "Fim", "Dias corridos", "Marco de conclusão"])
        for k in range(semanas):
            f.c(r, 10 + k, k + 1, INT, negrito=True, cor=AZUL, fundo=FUNDO_CAB, alinhar="center", tam=8)
        r += 1
        r_ini = r
        minimos = motor.prazos_minimos(o, res)
        for i, e in enumerate(res["cronograma"]):
            f.c(r, 1, e["rotulo"])
            f.vinculo(r, 2, f"=SUMIF({cel['etapas_ext']},A{r},{cel['horas_ext']})", HORAS)
            f.entrada(r, 3, proposta["parametros"]["cronograma"].get("equipe_etapa", {}).get(e["etapa"], proposta["parametros"]["cronograma"]["equipe"]), INT)
            base = f"IF(B{r}>0,MAX(1,ROUNDUP(B{r}/({ref['horas_dia']}*C{r}),0)),0)"
            if minimos.get(e["etapa"]):     # lead time dos equipamentos / prazo de execução da obra
                f.c(r, 4, f"=MAX({base},{minimos[e['etapa']]})", INT)
            else:
                f.c(r, 4, "=" + base, INT)
            f.c(r, 5, 1 if i == 0 else f"=F{r - 1}+1", INT, alinhar="center")
            f.c(r, 6, f"=E{r}+D{r}-1", INT, alinhar="center")
            f.c(r, 7, f"=ROUNDUP(D{r}*7/5,0)", INT, alinhar="center")
            f.c(r, 8, e["marco"], tam=9)
            for k in range(semanas):
                f.c(r, 10 + k, None, borda=True)
            r += 1
        r_fim = r - 1
        if res["cronograma"]:
            faixa = f"{L(10)}{r_ini}:{L(9 + semanas)}{r_fim}"
            ws.conditional_formatting.add(faixa, FormulaRule(
                formula=[f"AND({L(10)}${r_ini - 1}*5>=$E{r_ini},({L(10)}${r_ini - 1}-1)*5+1<=$F{r_ini})"],
                fill=_fill(AZUL), stopIfTrue=False))
        f.c(r, 1, "PRAZO TOTAL", negrito=True, fundo=FUNDO_CAB)
        f.c(r, 4, f"=SUM(D{r_ini}:D{max(r_fim, r_ini)})", INT, negrito=True, fundo=FUNDO_CAB)
        f.c(r, 7, f"=SUM(G{r_ini}:G{max(r_fim, r_ini)})", INT, negrito=True, fundo=FUNDO_CAB)
        cel["prazo_uteis"] = f"Cronograma!$D${r}"
        cel["prazo_corridos"] = f"Cronograma!$G${r}"
        r += 2
    ws.freeze_panes = "B4"
    _impressao(ws)


# ----------------------------------------------------------------------------- Pagamento
def _aba_pagamento(wb, proposta, resultados, celulas):
    ws = wb.create_sheet("Pagamento")
    f = Folha(ws)
    f.larguras({"A": 70, "B": 10, "C": 18})
    f.titulo(1, "FORMA DE PAGAMENTO", 3)
    r = 3
    for o, res in zip(proposta["opcoes"], resultados):
        cel = celulas[o["id"]]
        f.secao(r, o["nome"], 3)
        r += 1
        f.cabecalho(r, ["Marco", "%", "Valor (R$)"])
        r += 1
        r_ini = r
        for m in res["pagamento"]:
            f.c(r, 1, m["marco"], quebra=True)
            f.entrada(r, 2, float(m["pct"]), PCT)
            f.c(r, 3, f"=B{r}*{cel['preco']}", MOEDA)
            r += 1
        f.c(r, 1, "TOTAL (deve somar 100%)", negrito=True, fundo=FUNDO_CAB)
        f.c(r, 2, f"=SUM(B{r_ini}:B{max(r - 1, r_ini)})", PCT, negrito=True, fundo=FUNDO_CAB)
        f.c(r, 3, f"=SUM(C{r_ini}:C{max(r - 1, r_ini)})", MOEDA, negrito=True, fundo=FUNDO_CAB)
        ws.conditional_formatting.add(f"B{r}", FormulaRule(formula=[f"ABS(B{r}-1)>0.0001"], fill=_fill("F8CBAD")))
        r += 2
    _impressao(ws, paisagem=False)


# ----------------------------------------------------------------------------- Resumo
def _aba_resumo(ws, cat, proposta, resultados, celulas):
    f = Folha(ws)
    n = len(resultados)
    ate = 2 + n
    f.larguras({"A": 44, "B": 4, **{L(3 + i): 22 for i in range(n)}})
    _logo(ws, "A1")
    for linha in range(1, 5):
        ws.row_dimensions[linha].height = 18
    org = _org()
    f.titulo(6, f"PROPOSTA COMERCIAL {proposta['numero']} — RESUMO DAS OPÇÕES", ate)
    cl = proposta["cliente"]
    info = [
        ("Cliente", cl.get("razao", "")),
        ("Objeto", proposta.get("objeto", "")),
        ("Endereço do objeto", cl.get("endereco", "")),
        ("Data de emissão / validade", f"{_data_br(proposta['data'])} — {proposta['validade_dias']} dias corridos"),
        ("Responsável técnico", f"{org.get('resp', '').title()} — {org.get('registros', '')}"),
        ("Empresa", f"{org.get('fantasia', '')} — CNPJ {org.get('cnpj', '')}"),
    ]
    r = 7
    for rot, val in info:
        f.c(r, 1, rot, negrito=True, borda=False)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=ate)
        f.c(r, 3, val, borda=False, quebra=True)
        r += 1
    r += 1
    f.cabecalho(r, ["Indicador", ""] + [o["nome"] for o in proposta["opcoes"]])
    r += 1
    f.c(r, 1, "Modalidade")
    f.c(r, 2, None)
    for i, res in enumerate(resultados):
        f.c(r, 3 + i, "Turnkey (preço global)" if res.get("modalidade") == "turnkey" else "Serviços de engenharia",
            alinhar="right")
    r += 1
    linhas = [
        ("Horas técnicas", "total_h_ext", HORAS),
        ("Prazo (dias úteis)", "prazo_uteis", INT),
        ("Prazo (dias corridos)", "prazo_corridos", INT),
        ("Custo dos serviços", "custo", MOEDA),
        ("Preço — escopo fechado", "fechado", MOEDA),
        ("Preço — hora técnica (estimado)", "hora", MOEDA),
        ("Preço — hora técnica (teto)", "hora_teto", MOEDA),
        ("Preço — % sobre obra", "fee", MOEDA),
        ("Preço mínimo dos serviços (margem zero)", "minimo", MOEDA),
        ("Margem efetiva — escopo fechado", "me_fechado", PCT),
        ("Preço por hora técnica (R$/h)", "rs_h", MOEDA),
        ("Preço por m² (R$/m²)", "rs_m2", MOEDA),
        ("Referência: % do CUB × área", "ref_cub", MOEDA),
        ("Modelo escolhido", "modelo", None),
        ("PREÇO DA PROPOSTA", "preco", MOEDA),
    ]
    for rot, chave, fmt in linhas:
        forte = rot.isupper()
        f.c(r, 1, rot, negrito=forte, fundo=FUNDO_CAB if forte else None)
        f.c(r, 2, None, fundo=FUNDO_CAB if forte else None)
        for i, o in enumerate(proposta["opcoes"]):
            f.vinculo(r, 3 + i, "=" + celulas[o["id"]][chave], fmt, negrito=forte)
            ws.cell(r, 3 + i).alignment = Alignment(horizontal="right")
        r += 1
    r += 1
    f.nota(r, cat.get("nota", ""), ate)
    f.nota(r + 1, "Valores com tributos incidentes. Fundo amarelo = entrada editável; verde = vínculo com outra aba. "
                  "O documento técnico só produz efeito acompanhado da ART registrada e quitada (Lei 6.496/1977).", ate)
    ws.freeze_panes = "A7"
    _impressao(ws, paisagem=n > 2)
    ws.page_setup.fitToHeight = 1


def _data_br(iso):
    try:
        a, m, d = iso.split("-")
        return f"{d}/{m}/{a}"
    except (ValueError, AttributeError):
        return str(iso)


# ----------------------------------------------------------------------------- API
def gerar(cat, proposta, resultado):
    """Bytes do .xlsx com todas as opções da proposta."""
    resultados = resultado["opcoes"]
    wb = Workbook()
    resumo = wb.active
    resumo.title = "Resumo"
    ref = _aba_parametros(wb, cat, proposta)
    celulas = {}
    for o, res in zip(proposta["opcoes"], resultados):
        celulas[o["id"]] = _aba_opcao(wb, cat, proposta, o, res, ref)
    linhas_forn = _aba_fornecimentos(wb, proposta, resultados, ref)
    _aba_pesquisa(wb, proposta, resultados, ref, linhas_forn)
    _aba_cronograma(wb, cat, proposta, resultados, celulas, ref)
    _aba_pagamento(wb, proposta, resultados, celulas)
    _aba_resumo(resumo, cat, proposta, resultados, celulas)
    wb.move_sheet("Parametros", offset=len(wb.sheetnames))
    wb.properties.title = f"Proposta {proposta['numero']}"
    wb.properties.creator = _org().get("fantasia", "KAPTEK")
    wb.calculation.fullCalcOnLoad = True
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
