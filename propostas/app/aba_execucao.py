"""Aba Execução: itens de execução (HH), equipe, prazo, curva ABC e envio ao preço."""

import pandas as pd
import streamlit as st

from orcamento import modelos
from orcamento.execucao import FATORES_PADRAO

try:
    from orcamento import execucao_itens as ei
    from orcamento.curva_abc import curva_abc
    import graficos_execucao as gx
except ImportError:                       # módulos ainda em construção
    ei = gx = None

COLUNAS = ["descricao", "unid", "qtd", "hh_unid", "funcao", "material", "base", "fase", "kit"]
ROTULOS = {"descricao": "Descrição", "unid": "Unid", "qtd": "Qtd", "hh_unid": "HH/unid", "funcao": "Função",
           "material": "Material (R$/unid)", "base": "Base", "fase": "Fase", "kit": "Frente/kit"}


def _brl(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render(O, params, k, estrutura_mudou):
    if ei is None or gx is None:
        st.info("Aba Execução em construção.")
        return

    with st.container(border=True):
        st.markdown("**Kits de execução**")
        try:
            kits = modelos.carregar_kits()
        except (OSError, ValueError, KeyError):
            kits = []
        if kits:
            c1, c2 = st.columns([3, 1])
            sel = c1.selectbox("Aplicar kit", range(len(kits)), format_func=lambda i: kits[i]["nome"],
                               key=k("kit_sel", O["id"]))
            if c2.button("Aplicar kit", key=k("kit_ap", O["id"])):
                modelos.aplicar_kit(O, kits[sel])
                estrutura_mudou()

    st.markdown("**Itens de execução**")
    itens = O.get("itens_execucao") or []
    df = pd.DataFrame(itens, columns=COLUNAS) if itens else pd.DataFrame(columns=COLUNAS)
    ed = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key=k("exec_itens", O["id"]),
                        column_config={c: st.column_config.Column(r) for c, r in ROTULOS.items()})
    novos = [{c: (None if pd.isna(v) else v) for c, v in r.items()} for r in ed.to_dict("records")]
    O["itens_execucao"] = [r for r in novos if r.get("descricao")]

    cfg = ei.config_da_opcao(O)
    st.markdown("**Configuração**")
    pad = cfg.setdefault("fator_padrao", {})
    cols = st.columns(4)
    for col, nome in zip(cols, FATORES_PADRAO):
        opcoes = list(FATORES_PADRAO[nome])
        atual = pad.get(nome, opcoes[0])
        pad[nome] = col.selectbox(nome.capitalize(), opcoes, index=opcoes.index(atual) if atual in opcoes else 0,
                                  key=k("exec_f", nome, O["id"]))
    c1, c2, c3 = st.columns(3)
    cfg["prazo_alvo_dias"] = c1.number_input("Prazo-alvo (dias úteis)", 1, 1000, int(cfg.get("prazo_alvo_dias", 20)),
                                             key=k("exec_prazo", O["id"]))
    cfg["horas_dia"] = c2.number_input("Horas/dia", 1.0, 24.0, float(cfg.get("horas_dia", 8.0)), 0.5,
                                       key=k("exec_hd", O["id"]))
    cfg["eficiencia"] = c3.number_input("Eficiência", 0.1, 1.0, float(cfg.get("eficiencia", 0.8)), 0.05,
                                        key=k("exec_ef", O["id"]))

    res = ei.calcular_execucao(O, params)
    if res.get("erro"):
        st.warning(res["erro"])
    plano = res.get("plano")
    if plano:
        hh = sum((plano.get("hh_funcao") or {}).values())
        m = st.columns(4)
        m[0].metric("HH total", f"{hh:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m[1].metric("Mão de obra", _brl(res.get('mao_obra', 0)))
        m[2].metric("Material", _brl(res.get('material', 0)))
        m[3].metric("Prazo (dias úteis)", plano.get("prazo_dias_uteis", "-"))
        st.dataframe(gx.tabela_equipe(plano), hide_index=True, width="stretch")
        g = gx.grafico_frentes(plano)
        if g is not None:
            st.altair_chart(g, width="stretch")
        if res.get("custo_itens"):
            curva = curva_abc(res["custo_itens"])
            st.altair_chart(gx.grafico_abc(curva), width="stretch")
            st.dataframe(gx.tabela_abc(curva), hide_index=True, width="stretch")

    if st.button("Levar execução para o preço", key=k("exec_levar", O["id"])):
        n = ei.sincronizar_fornecimentos(O, params)
        st.success(f"{n} itens levados")
        st.rerun()
    st.caption("O preço aparece na aba Preço (fornecimentos de mão de obra/material da execução).")
