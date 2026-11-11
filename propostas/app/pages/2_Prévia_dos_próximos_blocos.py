"""Prévia visual dos próximos blocos. Mockup: valores fictícios, sem lógica real."""

import math

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Prévia — próximos blocos", layout="wide")
st.title("Prévia dos próximos blocos")
st.info("Prévia visual: valores fictícios e botões ainda sem função.")


def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def pct(v):
    return f"{v * 100:.2f}".replace(".", ",") + "%"


def anos_fmt(v):
    return "n/d" if v is None else f"{v:.1f} anos".replace(".", ",")


def em_construcao():
    st.toast("Em construção")


def cruzamento(acum, alvo):
    """Ano fracionário em que o acumulado atinge o alvo; None se não atinge."""
    for t in range(1, len(acum)):
        if acum[t] >= alvo:
            return (t - 1) + (alvo - acum[t - 1]) / (acum[t] - acum[t - 1])
    return None


b1, b2, b3, _ = st.columns([1, 1, 1, 3])
b1.button("Duplicar proposta", on_click=em_construcao)
b2.button("Usar modelo (kit)", on_click=em_construcao)
b3.button("Importar do Excel", on_click=em_construcao)

t1, t2, t4, t5 = st.tabs(["Execução de obra", "Preço, comparação e ARTs", "Viabilidade", "Documentos"])

# ---------------------------------------------------------------- 1. Execução de obra
with t1:
    funcoes = ["Mecânico", "Auxiliar", "Eletricista"]
    custo_h = {"Mecânico": 37.61, "Auxiliar": 24.81, "Eletricista": 33.25}
    itens = pd.DataFrame([
        {"Base": "SINAPI (fictício)", "Item": "Instalação de split 12.000 BTU/h", "Unid": "un", "Qtd": 8.0, "HH/unid": 6.0, "Função": "Mecânico", "Material (R$)": 1450.0},
        {"Base": "SINAPI (fictício)", "Item": "Rede frigorígena cobre 3/8–5/8", "Unid": "m", "Qtd": 120.0, "HH/unid": 0.25, "Função": "Mecânico", "Material (R$)": 96.0},
        {"Base": "SINAPI (fictício)", "Item": "Dreno PVC 25 mm", "Unid": "m", "Qtd": 60.0, "HH/unid": 0.15, "Função": "Auxiliar", "Material (R$)": 9.5},
        {"Base": "Própria", "Item": "Instalação condensadora VRF 28 HP", "Unid": "un", "Qtd": 2.0, "HH/unid": 24.0, "Função": "Mecânico", "Material (R$)": 2800.0},
        {"Base": "Própria", "Item": "Startup e comissionamento", "Unid": "vb", "Qtd": 1.0, "HH/unid": 16.0, "Função": "Eletricista", "Material (R$)": 0.0},
    ])

    with st.container(border=True):
        st.markdown("**Base de composições e fatores de produtividade**")
        g1, g2 = st.columns(2)
        g1.selectbox("Base de composições", ["SINAPI-RJ (mês de referência fictício)", "Própria da empresa"])
        g2.radio("Encargos sociais", ["Com desoneração", "Sem desoneração"], horizontal=True, index=1)
        f1, f2, f3, f4 = st.columns(4)
        altura = f1.selectbox("Altura", ["até 3 m", "3–6 m", "acima de 6 m"], index=1)
        acesso = f2.selectbox("Acesso", ["livre", "restrito", "difícil"], index=1)
        ocupado = f3.checkbox("Ambiente ocupado", value=True)
        noturno = f4.checkbox("Trabalho noturno")
    fator = (
        {"até 3 m": 1.0, "3–6 m": 1.15, "acima de 6 m": 1.30}[altura]
        * {"livre": 1.0, "restrito": 1.15, "difícil": 1.30}[acesso]
        * (1.10 if ocupado else 1.0)
        * (1.20 if noturno else 1.0)
    )

    col_tab, col_eq = st.columns([3, 2])
    with col_tab:
        with st.container(border=True):
            st.markdown("**Serviços e quantitativos**")
            itens_ed = st.data_editor(
                itens,
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "Qtd": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                    "HH/unid": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                    "Função": st.column_config.SelectboxColumn(options=funcoes),
                },
            )
    hh = (
        (itens_ed["Qtd"] * itens_ed["HH/unid"] * fator)
        .groupby(itens_ed["Função"])
        .sum()
        .reindex(funcoes, fill_value=0.0)
    )

    with col_eq:
        with st.container(border=True):
            st.markdown("**Equipe e HH por função**")
            prazo = st.number_input("Prazo-alvo (dias úteis)", min_value=1, value=15, step=1)
            horas = prazo * 8
            equipe = pd.DataFrame({
                "Função": funcoes,
                "HH": hh.values,
                "Pessoas": [math.ceil(v / horas) if v > 0 else 0 for v in hh.values],
                "Custo/h (R$)": [custo_h[f] for f in funcoes],
                "Mão de obra (R$)": [v * custo_h[f] for f, v in zip(funcoes, hh.values)],
            })
            mo = equipe["Mão de obra (R$)"].sum()
            st.dataframe(
                equipe,
                hide_index=True,
                column_config={
                    "HH": st.column_config.NumberColumn(format="%.1f"),
                    "Custo/h (R$)": st.column_config.NumberColumn(format="%.2f"),
                    "Mão de obra (R$)": st.column_config.NumberColumn(format="%.2f"),
                },
            )

    with st.container(border=True):
        st.markdown("**Cronograma — 3 frentes**")
        frentes = pd.DataFrame([
            {"Frente": "Casa de máquinas", "Início": 0, "Fim": round(prazo * 0.30)},
            {"Frente": "Distribuição de rede", "Início": round(prazo * 0.20), "Fim": round(prazo * 0.80)},
            {"Frente": "Comissionamento", "Início": round(prazo * 0.75), "Fim": prazo},
        ])
        st.altair_chart(
            alt.Chart(frentes).mark_bar(cornerRadius=3).encode(
                y=alt.Y("Frente:N", sort=None, title=None),
                x=alt.X("Início:Q", title="Dia útil"),
                x2="Fim:Q",
                color=alt.Color("Frente:N", legend=None),
            ).properties(height=150)
        )

    with st.expander("Calculadora de BDI"):
        b = st.columns(6)
        ac = b[0].number_input("AC (%)", value=4.0, step=0.1, format="%.2f")
        seg = b[1].number_input("Seguro + garantia (%)", value=0.8, step=0.1, format="%.2f")
        risco = b[2].number_input("Risco (%)", value=1.27, step=0.01, format="%.2f")
        dfin = b[3].number_input("Despesas financeiras (%)", value=1.23, step=0.01, format="%.2f")
        lucro = b[4].number_input("Lucro (%)", value=7.4, step=0.1, format="%.2f")
        imp = b[5].number_input("Impostos (%)", value=6.15, step=0.01, format="%.2f")
        bdi = (1 + (ac + seg + risco) / 100) * (1 + dfin / 100) * (1 + lucro / 100) / (1 - imp / 100) - 1
        k1, k2 = st.columns([1, 3])
        k1.metric("BDI calculado", pct(bdi))
        k2.caption("Faixa de referência informada pelo usuário")
        st.code("BDI = (1 + AC + S + R + G) × (1 + DF) × (1 + L) / (1 − I) − 1   (S + G = seguro + garantia)")

    material = st.number_input("Material (R$)", min_value=0.0, value=48700.0, step=500.0)
    direto = mo + material
    total = direto * (1 + bdi)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mão de obra", brl(mo))
    m2.metric("Material", brl(material))
    m3.metric("Custo direto", brl(direto))
    m4.metric("Total com BDI", brl(total))
    st.caption(f"BDI aplicado sobre o custo direto: {pct(bdi)}")

    with st.container(border=True):
        st.markdown("**Curva ABC (custo por item)**")
        abc = itens_ed.assign(**{"Custo (R$)": itens_ed["Qtd"] * (itens_ed["HH/unid"] * fator * itens_ed["Função"].map(custo_h).fillna(30.0) + itens_ed["Material (R$)"].fillna(0.0))})
        abc = abc.sort_values("Custo (R$)", ascending=False)
        abc["% acumulado"] = abc["Custo (R$)"].cumsum() / abc["Custo (R$)"].sum() * 100
        abc["Classe"] = abc["% acumulado"].map(lambda v: "A" if v <= 80 else ("B" if v <= 95 else "C"))
        st.altair_chart(
            alt.Chart(abc).mark_bar().encode(
                x=alt.X("Item:N", sort=None, title=None), y=alt.Y("Custo (R$):Q"),
                color=alt.Color("Classe:N", scale=alt.Scale(domain=["A", "B", "C"], range=["#1f4e79", "#5b9bd5", "#bdd7ee"])),
            ).properties(height=220),
            use_container_width=True,
        )

# ---------------------------------------------------------------- 2. Preço por tabela
with t2:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 3, 1, 2])
        tabela = c1.selectbox("Tabela", ["CEHOP-SE jan/2023", "CEHOP-SE jul/2023"])
        item = c2.text_input("Item", "Projeto de climatização — complexo")
        area = c3.number_input("Área (m²)", min_value=1, value=1200, step=10)
        indice = c4.radio("Índice de correção", ["INCC", "IPCA", "IGP-M"], horizontal=True)
    fator_idx = {"INCC": 1.048, "IPCA": 1.041, "IGP-M": 1.057}[indice]
    tab_base = min(area, 500) * 4.83 + max(area - 500, 0) * 4.11
    tab_corr = tab_base * fator_idx
    st.caption(f"{tabela} · {item} · índice {indice} (fator fictício {fator_idx:.3f})")

    esq, dir_ = st.columns([3, 2])
    with esq:
        with st.container(border=True):
            adotado = st.number_input("Preço adotado (R$)", min_value=0.0, value=36657.0, step=100.0)
            ref = [
                ("Preço por horas", 36657.0),
                ("Preço pela tabela", tab_corr),
                ("Mercado — média", 52000.0),
                ("Mercado — mediana", 48500.0),
                ("Mercado — menor", 41000.0),
            ]
            linhas = [
                {"Referência": n, "Valor (R$)": brl(v), "Δ vs adotado": f"{(v / adotado - 1) * 100:+.1f}%".replace(".", ",")}
                for n, v in ref
            ]
            linhas.append({"Referência": "ABRAVA", "Valor (R$)": "não configurado", "Δ vs adotado": "—"})
            st.dataframe(pd.DataFrame(linhas), hide_index=True)
            desvio = adotado / 48500.0 - 1
            txt = f"{desvio * 100:+.1f}% da mediana".replace(".", ",")
            if abs(desvio) > 0.25:
                st.markdown(f":red-badge[Acima de 25% da mediana ({txt})]")
            else:
                st.markdown(f":green-badge[Dentro de 25% da mediana ({txt})]")

    with dir_:
        with st.container(border=True):
            st.markdown("**Cotações**")
            cot = st.data_editor(
                pd.DataFrame([
                    {"Fornecedor": "Cotação A (fictícia)", "Valor (R$)": 49800.0, "Comparável": True, "Motivo": ""},
                    {"Fornecedor": "Cotação B (fictícia)", "Valor (R$)": 47200.0, "Comparável": True, "Motivo": ""},
                    {"Fornecedor": "Cotação C (fictícia)", "Valor (R$)": 39900.0, "Comparável": False, "Motivo": "modelo diferente"},
                    {"Fornecedor": "Cotação D (fictícia)", "Valor (R$)": 51300.0, "Comparável": True, "Motivo": ""},
                ]),
                hide_index=True,
                column_config={
                    "Valor (R$)": st.column_config.NumberColumn(format="%.2f"),
                    "Comparável": st.column_config.CheckboxColumn(),
                },
            )
            if st.button("Adotar este valor", type="primary"):
                em_construcao()

# ---------------------------------------------------------------- ABRAVA (coluna do painel, dentro da aba de preço)
with t2:
    with st.expander("Honorário ABRAVA — detalhe da coluna do painel"):
        st.warning("Parâmetros provisórios — conferir com o documento oficial.")
        esq, dir_ = st.columns([3, 2])
        with esq:
            with st.container(border=True):
                st.markdown("**Ambientes**")
                amb = st.data_editor(
                    pd.DataFrame([
                        {"Tipo": "Sala de reuniões", "Área m²": 45.0, "Repetições": 2},
                        {"Tipo": "Escritório", "Área m²": 30.0, "Repetições": 6},
                        {"Tipo": "Auditório", "Área m²": 120.0, "Repetições": 1},
                        {"Tipo": "Recepção", "Área m²": 60.0, "Repetições": 1},
                    ]),
                    num_rows="dynamic",
                    hide_index=True,
                )
        with dir_:
            with st.container(border=True):
                st.markdown("**Parâmetros**")
                tipo_inst = st.selectbox("Tipo de instalação", ["Split", "VRF", "Água gelada"], index=1)
                custo_tr = st.number_input("Custo por TR (R$)", min_value=0.0, value=1850.0, step=50.0)
                dific = st.selectbox(
                    "Fator de dificuldade",
                    [1.00, 1.15, 1.30],
                    index=1,
                    format_func=lambda x: f"{x:.2f}".replace(".", ","),
                )

        fator_inst = {"Split": 1.00, "VRF": 1.20, "Água gelada": 1.35}[tipo_inst]
        area_corr = (amb["Área m²"] * amb["Repetições"]).sum() * fator_inst
        custo_base = area_corr / 30 * custo_tr * dific
        curva = 0.045
        honor = custo_base * curva
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Área corrigida", f"{area_corr:,.1f} m²".replace(",", "X").replace(".", ",").replace("X", "."))
        o2.metric("Custo base", brl(custo_base))
        o3.metric("Percentual da curva", pct(curva))
        o4.metric("Honorário calculado", brl(honor))

        with st.container(border=True):
            st.markdown("**Ajustes da empresa**")
            a1, a2, a3 = st.columns(3)
            nivel = a1.selectbox("Nível do RT", ["Júnior", "Pleno", "Sênior"], index=1)
            planilha = a2.checkbox("Planilha +10 %")
            desc = a3.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.5)
            f_nivel = {"Júnior": 0.90, "Pleno": 1.00, "Sênior": 1.10}[nivel]
            aj_nivel = honor * (f_nivel - 1)
            aj_plan = honor * 0.10 if planilha else 0.0
            base_aj = honor + aj_nivel + aj_plan
            aj_desc = -base_aj * desc / 100
            final = base_aj + aj_desc
            st.dataframe(
                pd.DataFrame([
                    {"Linha": "Ajuste da empresa — nível do RT", "Valor (R$)": aj_nivel},
                    {"Linha": "Ajuste da empresa — planilha +10 %", "Valor (R$)": aj_plan},
                    {"Linha": "Ajuste da empresa — desconto", "Valor (R$)": aj_desc},
                ]),
                hide_index=True,
                column_config={"Valor (R$)": st.column_config.NumberColumn(format="%.2f")},
            )
            st.metric("Valor final do honorário", brl(final))

# ---------------------------------------------------------------- 4. Viabilidade
with t4:
    with st.container(border=True):
        c = st.columns(5)
        capex = c[0].number_input("CAPEX (R$)", min_value=0.0, value=850000.0, step=10000.0)
        economia = c[1].number_input("Economia anual (R$)", min_value=0.0, value=210000.0, step=5000.0)
        tma = c[2].number_input("TMA (% a.a.)", min_value=0.0, value=12.0, step=0.5)
        horiz = c[3].number_input("Horizonte (anos)", min_value=1, max_value=30, value=15, step=1)
        reaj = c[4].number_input("Reajuste energia (% a.a.)", min_value=0.0, value=5.0, step=0.5)

    i_, g = tma / 100, reaj / 100
    custo_atual_ano1 = 300000.0
    anos = list(range(0, horiz + 1))
    custo_t = [0.0] + [custo_atual_ano1 * (1 + g) ** (t - 1) for t in range(1, horiz + 1)]
    econ_t = [0.0] + [economia * (1 + g) ** (t - 1) for t in range(1, horiz + 1)]
    atual_acum, alt_acum = [0.0], [capex]
    for t in range(1, horiz + 1):
        atual_acum.append(atual_acum[-1] + custo_t[t])
        alt_acum.append(alt_acum[-1] + custo_t[t] - econ_t[t])
    sav_acum, desc_acum = [0.0], [0.0]
    for t in range(1, horiz + 1):
        sav_acum.append(sav_acum[-1] + econ_t[t])
        desc_acum.append(desc_acum[-1] + econ_t[t] / (1 + i_) ** t)

    payback = cruzamento(sav_acum, capex)
    breakeven = cruzamento(desc_acum, capex)
    vpl = desc_acum[-1] - capex

    def vpl_taxa(r):
        return -capex + sum(econ_t[t] / (1 + r) ** t for t in range(1, horiz + 1))

    tir = None
    lo, hi = 0.0001, 1.0
    if vpl_taxa(lo) * vpl_taxa(hi) < 0:
        for _ in range(60):
            mid = (lo + hi) / 2
            if vpl_taxa(lo) * vpl_taxa(mid) <= 0:
                hi = mid
            else:
                lo = mid
        tir = (lo + hi) / 2

    curvas = pd.DataFrame({
        "Ano": anos * 2,
        "Custo acumulado (R$)": atual_acum + alt_acum,
        "Cenário": ["Sistema atual"] * len(anos) + ["Alternativa"] * len(anos),
    })
    marcas = pd.DataFrame(
        [{"Ano": x, "Rótulo": r} for x, r in [(payback, "Payback"), (breakeven, "Breakeven")] if x is not None],
        columns=["Ano", "Rótulo"],
    ).astype({"Ano": float})
    linha = alt.Chart(curvas).mark_line(point=True).encode(
        x=alt.X("Ano:Q"),
        y=alt.Y("Custo acumulado (R$):Q"),
        color="Cenário:N",
    )
    regras = alt.Chart(marcas).mark_rule(strokeDash=[4, 4]).encode(x="Ano:Q")
    rotulos = alt.Chart(marcas).mark_text(align="left", dx=4, dy=-6).encode(
        x="Ano:Q", y=alt.value(20), text="Rótulo:N"
    )
    st.altair_chart(linha + regras + rotulos)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("VPL", brl(vpl))
    m2.metric("TIR", "n/d" if tir is None else pct(tir))
    m3.metric("Breakeven (descontado)", anos_fmt(breakeven))
    m4.metric("Payback (simples)", anos_fmt(payback))

    sens = []
    for d in [-30, -20, -10, 0, 10, 20, 30]:
        e_mod = economia * (1 + d / 100)
        v = -capex + sum(e_mod * (1 + g) ** (t - 1) / (1 + i_) ** t for t in range(1, horiz + 1))
        sens.append({"Variação da economia": f"{d:+d}%", "VPL (R$)": v, "Sinal": "Positivo" if v >= 0 else "Negativo"})
    with st.container(border=True):
        st.markdown("**Sensibilidade do VPL à economia anual**")
        st.altair_chart(
            alt.Chart(pd.DataFrame(sens)).mark_bar().encode(
                x=alt.X("Variação da economia:N", sort=None),
                y=alt.Y("VPL (R$):Q"),
                color=alt.Color(
                    "Sinal:N",
                    scale=alt.Scale(domain=["Positivo", "Negativo"], range=["#2E7D32", "#C62828"]),
                    legend=None,
                ),
            )
        )
    if st.button("Gerar relatório para o cliente (DOCX)"):
        em_construcao()

# ---------------------------------------------------------------- 5. Documentos
with t5:
    c1, c2 = st.columns(2)
    rev = c1.number_input("Revisão", min_value=0, value=1, step=1)
    validade = c2.number_input("Validade (dias)", min_value=1, value=15, step=1)
    b1, b2, b3 = st.columns(3)
    if b1.button("Gerar proposta"):
        em_construcao()
    if b2.button("Gerar contrato"):
        em_construcao()
    if b3.button("Gerar recibo"):
        em_construcao()

    with st.container(border=True):
        st.markdown(
            f"""
#### KAPTEK Engenharia e Tecnologia

**Proposta PC-KTK-001/2026 Rev. {rev:02d}**

**Cliente:** Cliente Exemplo Ltda. (fictício)

**Objeto:** Projeto e instalação de climatização VRF para edifício comercial (dados fictícios)

**Valor total:** {brl(total)}

**Validade:** {validade} dias a partir da emissão
"""
        )


# ---------------------------------------------------------------- ARTs (caixa na aba de preço)
with t2:
    with st.container(border=True):
        st.subheader("ARTs previstas")
        st.caption("Sugestão automática pelas fases e serviços. Regras provisórias — confirmar com o CREA-RJ.")

        def taxa(v):
            return 108.39 if v <= 15000 else 285.59

        arts = pd.DataFrame([
            {"No preço": True, "Profissional": "RT mecânico", "Atividade": "Projeto", "Valor base (R$)": 36657.0},
            {"No preço": True, "Profissional": "RT mecânico", "Atividade": "Execução", "Valor base (R$)": 182400.0},
            {"No preço": True, "Profissional": "Eng. eletricista", "Atividade": "Execução elétrica", "Valor base (R$)": 14200.0},
            {"No preço": False, "Profissional": "Subcontratado", "Atividade": "Isolamento (ART própria)", "Valor base (R$)": 21000.0},
        ])
        arts["Taxa (R$)"] = arts["Valor base (R$)"].map(taxa)
        st.data_editor(arts, use_container_width=True, hide_index=True, key="arts_ed")
        inc = arts[arts["No preço"]]
        st.markdown(f"**{len(inc)} ARTs no preço — {brl(inc['Taxa (R$)'].sum())}**")
