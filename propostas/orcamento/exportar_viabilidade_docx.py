"""
Relatório de viabilidade em DOCX para o cliente (spec B5).

Premissas, tabela comparativa (VPL, TIR, payback simples, breakeven descontado, LCC), dois gráficos
feitos com matplotlib (custo acumulado e sensibilidade do VPL à economia) e conclusão gerada dos
números. Os estilos (moeda, percentual) vêm de exportar_docx.py. Sem matplotlib, só as tabelas.

Os termos seguem o estudo: "breakeven" = contas empatam (sem desconto), "payback" = devolve o
investimento descontado pela TMA. Os rótulos pedidos para a tabela são mantidos abaixo.
"""

import io
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

from . import viabilidade as vb
from .exportar_docx import RAIZ, moeda, pct_br

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:          # pragma: no cover
    plt = None

MODELO = os.path.join(RAIZ, "modelos", "proposta.docx")
AZUL, CINZA = "1B3A5C", "3E4448"
CORES = ["#1f4e79", "#c0504d", "#4f9a3f", "#e08a1e", "#7a4fa3", "#2a9d9d"]


def _anos(v):
    return "—" if v is None else f"{v:.1f}".replace(".", ",") + " anos"


def _pct(v):
    return "—" if v is None else pct_br(v)


def series_custo_acumulado(dados, res):
    """Custo acumulado (sem desconto) do sistema atual e de cada alternativa, anos 0..horizonte."""
    fin = vb.completar(dados)["financeiro"]
    ge, gm = float(fin["reajuste_energia"]), float(fin["reajuste_manutencao"])
    h = res["horizonte"]
    atual, acum = [0.0], 0.0
    for t in range(1, h + 1):
        acum += res["custo_energia_base"] * (1 + ge) ** (t - 1) + res["manutencao_base"] * (1 + gm) ** (t - 1)
        atual.append(acum)
    alts = []
    for a in res["alternativas"]:
        ac, s = [], 0.0
        for t, f in enumerate(a["fluxo"]):
            s += f
            ac.append(atual[t] - s)       # custo atual evitado vira economia; o CAPEX entra no ano 0
        alts.append(ac)
    return atual, alts


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def grafico_custo_acumulado(dados, res):
    atual, alts = series_custo_acumulado(dados, res)
    anos = list(range(len(atual)))
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(anos, atual, color="#444444", linewidth=2.4, label="Sistema atual")
    for i, (a, ac) in enumerate(zip(res["alternativas"], alts)):
        cor = CORES[i % len(CORES)]
        ax.plot(anos, ac, color=cor, linewidth=1.8, label=a["nome"])
        if a["breakeven"] is not None:
            ax.axvline(a["breakeven"], color=cor, linestyle="--", linewidth=0.9, alpha=0.8)
        if a["payback"] is not None:
            ax.axvline(a["payback"], color=cor, linestyle=":", linewidth=1.2, alpha=0.8)
    ax.plot([], [], color="grey", linestyle="--", label="Breakeven (sem desconto)")
    ax.plot([], [], color="grey", linestyle=":", label="Payback (descontado pela TMA)")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Custo acumulado (R$)")
    ax.set_title("Custo acumulado: sistema atual × alternativas")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x / 1000:,.0f} mil".replace(",", "."))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left")
    return _png(fig)


def grafico_sensibilidade(res):
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for i, a in enumerate(res["alternativas"]):
        sens = a["sensibilidade"]["economia"]
        ks = sorted(sens)
        ax.plot([k * 100 for k in ks], [sens[k] for k in ks], marker="o", color=CORES[i % len(CORES)],
                label=a["nome"])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Variação da economia (%)")
    ax.set_ylabel("VPL (R$)")
    ax.set_title("Sensibilidade do VPL à economia")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x / 1000:,.0f} mil".replace(",", "."))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)
    return _png(fig)


def conclusao(res):
    """Texto neutro, gerado dos números."""
    todas = res["alternativas"]
    alts = [a for a in todas if not a.get("sem_preco")]
    if not todas:
        return "Nenhuma alternativa foi avaliada neste estudo."
    if not alts:
        return ("Nenhuma alternativa pôde ser avaliada: falta informar o investimento (preço da opção) de todas elas.")
    n = len(alts)
    pos = [a for a in alts if a["vpl"] > 0]
    partes = [f"Foram comparadas {n} alternativa{'s' if n > 1 else ''} em horizonte de {res['horizonte']} anos, "
              f"com taxa mínima de atratividade de {_pct(res['tma'])}."]
    if pos:
        m = max(pos, key=lambda a: a["vpl"])
        partes.append(f"{len(pos)} de {n} apresenta{'m' if len(pos) > 1 else ''} VPL positivo. "
                      f"O maior VPL é o de \"{m['nome']}\": {moeda(m['vpl'])}, com investimento de {moeda(m['capex'])}, "
                      f"breakeven em {_anos(m['breakeven'])} e payback descontado em {_anos(m['payback'])}.")
    else:
        partes.append("Nenhuma alternativa apresenta VPL positivo nas premissas adotadas.")
    lcc = min(alts, key=lambda a: a["lcc"])
    partes.append(f"O menor custo de ciclo de vida (LCC) é o de \"{lcc['nome']}\", {moeda(lcc['lcc'])}, "
                  f"contra {moeda(res['lcc_base'])} para manter o sistema atual.")
    fragil = [a["nome"] for a in alts if a["vpl"] > 0 and a["sensibilidade"]["economia"].get(-0.3, 1) < 0]
    if fragil:
        partes.append("Com economia 30% menor que a prevista, o VPL fica negativo em: " + "; ".join(fragil) + ".")
    if len(alts) < len(todas):
        partes.append("As alternativas sem investimento informado ficaram fora desta conclusão.")
    partes.append("Os resultados dependem das premissas informadas e devem ser revistos se elas mudarem.")
    return " ".join(partes)


def _fmt(run, tam, negrito=False, cor=CINZA):
    run.font.name = "Arial"
    run._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Arial")
    run.font.size, run.bold = Pt(tam), negrito
    run.font.color.rgb = RGBColor.from_string(cor)


def _par(doc, texto, tam=9.5, negrito=False, cor=CINZA, depois=7, italico=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after, p.paragraph_format.space_before = Pt(depois), Pt(0)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(texto)
    _fmt(r, tam, negrito, cor)
    r.italic = italico
    return p


def _titulo(doc, texto):
    p = doc.add_paragraph()
    p._p.get_or_add_pPr().get_or_add_pStyle().val = "Heading1"      # estilo de seção da proposta
    p.paragraph_format.keep_with_next = True
    _fmt(p.add_run(texto), 12, True, AZUL)
    return p


def _celula(c, texto, larg_cm, tam, cabecalho=False, dir_=False):
    tcPr = c._tc.get_or_add_tcPr()
    for el in list(tcPr):
        tcPr.remove(el)
    ns = nsdecls("w")
    tcPr.append(parse_xml(f'<w:tcW {ns} w:type="dxa" w:w="{int(larg_cm * 567)}"/>'))
    tcPr.append(parse_xml(f'<w:tcBorders {ns}>' + "".join(
        f'<w:{l} w:val="single" w:color="D8D8D8" w:sz="4"/>' for l in ("top", "left", "bottom", "right"))
        + '</w:tcBorders>'))
    tcPr.append(parse_xml(f'<w:shd {ns} w:val="clear" w:color="auto" w:fill="{AZUL if cabecalho else "FFFFFF"}"/>'))
    tcPr.append(parse_xml(f'<w:tcMar {ns}><w:top w:type="dxa" w:w="60"/><w:left w:type="dxa" w:w="45"/>'
                          f'<w:bottom w:type="dxa" w:w="60"/><w:right w:type="dxa" w:w="45"/></w:tcMar>'))
    p = c.paragraphs[0]
    p.paragraph_format.space_after = p.paragraph_format.space_before = Pt(0)
    if dir_:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _fmt(p.add_run(str(texto).replace("R$ ", "R$\u00a0")), tam, cabecalho, "FFFFFF" if cabecalho else CINZA)


def _tabela(doc, cabecalho, linhas, larguras, tam=9, dir_cols=()):
    """Tabela no padrão da proposta: cabeçalho azul-marinho, bordas cinza claras, larguras fixas (cm)."""
    t = doc.add_table(rows=1, cols=len(cabecalho))
    t.autofit = False
    tblPr = t._tbl.tblPr
    for el in tblPr.findall(qn("w:tblStyle")):
        tblPr.remove(el)
    tblPr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))
    for g, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), larguras):
        g.set(qn("w:w"), str(int(w * 567)))
    for j, (c, txt) in enumerate(zip(t.rows[0].cells, cabecalho)):
        _celula(c, txt, larguras[j], tam, cabecalho=True, dir_=j in dir_cols)
    t.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for ln in linhas:
        for j, (c, txt) in enumerate(zip(t.add_row().cells, ln)):
            _celula(c, txt, larguras[j], tam, dir_=j in dir_cols)
    return t


def _base_kaptek():
    """Abre modelos/proposta.docx (cabeçalho, rodapé, estilos) e esvazia o corpo, preservando sectPr."""
    doc = Document(MODELO) if os.path.exists(MODELO) else Document()
    corpo = doc.element.body
    logo = corpo[0] if corpo[0].xpath(".//w:drawing") else None      # logo da capa (a 1ª página não tem cabeçalho)
    for el in list(corpo):
        if el.tag != qn("w:sectPr") and el is not logo:
            corpo.remove(el)
    if logo is not None:
        for ext in logo.xpath(".//wp:extent | .//a:ext"):
            ext.set("cx", str(int(ext.get("cx")) * 55 // 100))
            ext.set("cy", str(int(ext.get("cy")) * 55 // 100))
        sp = logo.xpath("./w:pPr/w:spacing")[0]
        sp.set(qn("w:before"), "0")
        sp.set(qn("w:line"), "240")
        sp.set(qn("w:lineRule"), "auto")                              # espaçamento simples: não corta o topo do logo
    return doc


def _imagem(doc, buf):
    doc.add_picture(buf, width=Cm(15.5))
    p = doc.paragraphs[-1]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE   # evita corte do topo no LibreOffice


def _marcar_sem_preco(dados, res, precos_opcoes):
    """Marca em res as alternativas cujo CAPEX vem de uma opção sem preço informado."""
    for alt, a in zip(dados.get("alternativas", []), res["alternativas"]):
        oid = alt.get("capex_opcao") or ""
        if oid and not (precos_opcoes and oid in precos_opcoes) and not float(alt.get("capex") or 0):
            a["sem_preco"] = oid


def gerar_relatorio_viabilidade(dados_viabilidade, caminho, cliente=None, precos_opcoes=None):
    """Grava o relatório DOCX em `caminho` e devolve o caminho."""
    v = vb.completar(dados_viabilidade)
    res = vb.calcular(v, precos_opcoes)
    _marcar_sem_preco(v, res, precos_opcoes)
    b, fin = v["base"], v["financeiro"]
    todas = res["alternativas"]
    ok = [a for a in todas if not a.get("sem_preco")]
    res_ok = dict(res, alternativas=ok)
    doc = _base_kaptek()
    p = doc.add_paragraph()
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(16), Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    _fmt(p.add_run(res["titulo"]), 20, True, AZUL)
    if cliente:
        _par(doc, f"Cliente: {cliente}")

    _titulo(doc, "Premissas")
    premissas = [
        ("Consumo anual do sistema atual", f"{res['consumo_base']:,.0f} kWh".replace(",", ".")),
        ("Tarifa de energia", f"{moeda(res['tarifa'])}/kWh"),
        ("Manutenção anual do sistema atual", moeda(res["manutencao_base"])),
        ("Taxa mínima de atratividade (TMA)", _pct(res["tma"])),
        ("Horizonte", f"{res['horizonte']} anos"),
        ("Reajuste da energia", _pct(float(fin["reajuste_energia"]))),
        ("Reajuste da manutenção", _pct(float(fin["reajuste_manutencao"]))),
    ]
    if res["paliativos"]:
        premissas.append(("Paliativos (comuns a todas as alternativas)", moeda(res["paliativos"])))
    _tabela(doc, ["Premissa", "Valor"], premissas, [9.5, 6.5], dir_cols=(1,))

    _titulo(doc, "Comparativo das alternativas")
    linhas = []
    for a in todas:
        if a.get("sem_preco"):
            linhas.append([a["nome"], "—", "—", "—", "—", "—", "—", "Investimento não informado"])
        else:
            linhas.append([a["nome"], moeda(a["capex"]), moeda(a["vpl"]), _pct(a["tir"]), _anos(a["breakeven"]),
                           _anos(a["payback"]), moeda(a["lcc"]), a["classificacao"]])
    _tabela(doc, ["Alternativa", "Investimento", "VPL", "TIR", "Payback simples", "Breakeven descontado",
                  "LCC", "Classificação"], linhas, [2.6, 2.2, 2.2, 1.0, 1.45, 1.95, 2.2, 2.4], tam=7.5,
            dir_cols=(1, 2, 3, 4, 5, 6))
    _par(doc, f"LCC do sistema atual (manter como está): {moeda(res['lcc_base'])}. "
              "Payback simples: economia acumulada sem desconto iguala o investimento. "
              "Breakeven descontado: o mesmo, com a economia descontada pela TMA.", 8.5, depois=4).paragraph_format.space_before = Pt(6)
    faltam = [a for a in todas if a.get("sem_preco")]
    if faltam:
        _par(doc, "Investimento não informado: " + "; ".join(
            f"\"{a['nome']}\" (vincule o preço da opção {a['sem_preco']})" for a in faltam)
            + ". Essas alternativas não entram na conclusão nem nos gráficos.", 8.5, True, AZUL)

    if ok:
        if plt is not None:
            _titulo(doc, "Gráficos")
            _imagem(doc, grafico_custo_acumulado(v, res_ok))
            _imagem(doc, grafico_sensibilidade(res_ok))
        else:
            _par(doc, "Gráficos indisponíveis: matplotlib não está instalado.")

    _titulo(doc, "Conclusão")
    _par(doc, conclusao(res))
    doc.save(caminho)
    return caminho
