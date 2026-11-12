"""
Relatório de viabilidade em DOCX para o cliente (spec B5).

Premissas, tabela comparativa (VPL, TIR, payback simples, breakeven descontado, LCC), dois gráficos
feitos com matplotlib (custo acumulado e sensibilidade do VPL à economia) e conclusão gerada dos
números. Os estilos (moeda, percentual) vêm de exportar_docx.py. Sem matplotlib, só as tabelas.

Os termos seguem o estudo: "breakeven" = contas empatam (sem desconto), "payback" = devolve o
investimento descontado pela TMA. Os rótulos pedidos para a tabela são mantidos abaixo.
"""

import io

from docx import Document
from docx.shared import Cm, Pt

from . import viabilidade as vb
from .exportar_docx import moeda, pct_br

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:          # pragma: no cover
    plt = None

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
    alts = res["alternativas"]
    if not alts:
        return "Nenhuma alternativa foi avaliada neste estudo."
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
    partes.append("Os resultados dependem das premissas informadas e devem ser revistos se elas mudarem.")
    return " ".join(partes)


def _tabela(doc, cabecalho, linhas):
    t = doc.add_table(rows=1, cols=len(cabecalho))
    t.style = "Table Grid"
    for c, txt in zip(t.rows[0].cells, cabecalho):
        c.text = ""
        c.paragraphs[0].add_run(txt).bold = True
    for ln in linhas:
        for c, txt in zip(t.add_row().cells, ln):
            c.text = str(txt)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    return t


def gerar_relatorio_viabilidade(dados_viabilidade, caminho, cliente=None, precos_opcoes=None):
    """Grava o relatório DOCX em `caminho` e devolve o caminho."""
    v = vb.completar(dados_viabilidade)
    res = vb.calcular(v, precos_opcoes)
    b, fin = v["base"], v["financeiro"]
    doc = Document()
    doc.add_heading(res["titulo"], level=0)
    if cliente:
        doc.add_paragraph(f"Cliente: {cliente}")

    doc.add_heading("Premissas", level=1)
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
    _tabela(doc, ["Premissa", "Valor"], premissas)

    doc.add_heading("Comparativo das alternativas", level=1)
    linhas = [[a["nome"], moeda(a["capex"]), moeda(a["vpl"]), _pct(a["tir"]), _anos(a["breakeven"]),
               _anos(a["payback"]), moeda(a["lcc"]), a["classificacao"]] for a in res["alternativas"]]
    _tabela(doc, ["Alternativa", "Investimento", "VPL", "TIR", "Payback simples", "Breakeven descontado",
                  "LCC", "Classificação"], linhas)
    doc.add_paragraph(f"LCC do sistema atual (manter como está): {moeda(res['lcc_base'])}. "
                      "Payback simples: economia acumulada sem desconto iguala o investimento. "
                      "Breakeven descontado: o mesmo, com a economia descontada pela TMA.")

    if res["alternativas"]:
        if plt is not None:
            doc.add_heading("Gráficos", level=1)
            doc.add_picture(grafico_custo_acumulado(v, res), width=Cm(16))
            doc.add_picture(grafico_sensibilidade(res), width=Cm(16))
        else:
            doc.add_paragraph("Gráficos indisponíveis: matplotlib não está instalado.")

    doc.add_heading("Conclusão", level=1)
    doc.add_paragraph(conclusao(res))
    doc.save(caminho)
    return caminho
