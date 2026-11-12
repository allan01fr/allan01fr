"""Tabelas e gráficos da execução de obra e da curva ABC.

Funções puras: não usam Streamlit e retornam DataFrames ou gráficos Altair.
"""

import altair as alt
import pandas as pd

from orcamento.execucao import FUNCOES_PADRAO

CORES_CLASSE = {"A": "#1f4e79", "B": "#5b9bd5", "C": "#bdd7ee"}


def _nome_funcao(chave):
    return FUNCOES_PADRAO.get(chave, chave)


def tabela_equipe(plano):
    """Equipe por função: HH, número de pessoas e dias de trabalho somados das frentes."""
    dias = {}
    for c in plano.get("cronograma", []):
        for f, d in c.get("dias_funcao", {}).items():
            dias[f] = dias.get(f, 0) + d
    funcoes = list(plano.get("hh_funcao", {}))
    funcoes += [f for f in plano.get("equipe", {}) if f not in funcoes]
    linhas = [{"Função": _nome_funcao(f),
               "HH": round(float(plano.get("hh_funcao", {}).get(f, 0.0)), 2),
               "Pessoas": int(plano.get("equipe", {}).get(f, 0)),
               "Dias": int(dias.get(f, 0))}
              for f in funcoes]
    return pd.DataFrame(linhas, columns=["Função", "HH", "Pessoas", "Dias"])


def grafico_frentes(plano):
    """Gantt horizontal: uma barra por frente, de início a fim, em sequência."""
    cron = plano.get("cronograma", [])
    if not cron:
        return None
    df = pd.DataFrame([{"Frente": c["frente"], "Início": c["inicio"], "Fim": c["fim"] + 1,
                        "Dias úteis": c["dias_uteis"],
                        "Dia inicial": c["inicio"], "Dia final": c["fim"]} for c in cron])
    ordem = list(df["Frente"])
    return (
        alt.Chart(df)
        .mark_bar(color=CORES_CLASSE["A"], cornerRadius=2)
        .encode(
            y=alt.Y("Frente:N", sort=ordem, title=None),
            x=alt.X("Início:Q", title="Dia útil"),
            x2="Fim:Q",
            tooltip=[alt.Tooltip("Frente:N", title="Frente"),
                     alt.Tooltip("Dia inicial:Q", title="Dia inicial"),
                     alt.Tooltip("Dia final:Q", title="Dia final"),
                     alt.Tooltip("Dias úteis:Q", title="Dias úteis")],
        )
        .properties(title="Cronograma por frentes", height=max(60, 40 * len(df)))
    )


def grafico_abc(curva):
    """Barras de custo por item (desc.) coloridas pela classe, com linha de acumulado (%) no eixo direito."""
    df = pd.DataFrame([{"Item": it["descricao"], "Custo (R$)": float(it["custo"]),
                        "Classe": it["classe"], "Acumulado (%)": round(float(it["acumulado"]) * 100, 2)}
                       for it in curva], columns=["Item", "Custo (R$)", "Classe", "Acumulado (%)"])
    ordem = list(df["Item"])
    escala_cor = alt.Scale(domain=["A", "B", "C"], range=[CORES_CLASSE[k] for k in ("A", "B", "C")])
    base = alt.Chart(df).encode(x=alt.X("Item:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=-45)))
    barras = base.mark_bar().encode(
        y=alt.Y("Custo (R$):Q", title="Custo (R$)"),
        color=alt.Color("Classe:N", scale=escala_cor, legend=alt.Legend(title="Classe")),
        tooltip=[alt.Tooltip("Item:N"), alt.Tooltip("Custo (R$):Q", format=",.2f"),
                 alt.Tooltip("Classe:N"), alt.Tooltip("Acumulado (%):Q", format=".1f")],
    )
    linha = base.mark_line(color="#c00000", point=True).encode(
        y=alt.Y("Acumulado (%):Q", title="Acumulado (%)", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(orient="right")),
    )
    return alt.layer(barras, linha).resolve_scale(y="independent").properties(title="Curva ABC")


def tabela_abc(curva):
    """Tabela da curva ABC com custo em R$ e participação e acumulado em %."""
    linhas = [{"Item": it["descricao"],
               "Custo (R$)": round(float(it["custo"]), 2),
               "Participação (%)": round(float(it["participacao"]) * 100, 2),
               "Acumulado (%)": round(float(it["acumulado"]) * 100, 2),
               "Classe": it["classe"]}
              for it in curva]
    return pd.DataFrame(linhas, columns=["Item", "Custo (R$)", "Participação (%)", "Acumulado (%)", "Classe"])
