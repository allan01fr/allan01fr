"""
Clima2D - interface gráfica para estudo de distribuição de ar, conforto e umidade.

Rodar:  streamlit run app/app.py      (ou dê dois cliques em iniciar.bat no Windows)
"""

import hashlib
import io
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from hvac import projeto as pj
from hvac import importar_dxf as idxf

st.set_page_config(page_title="Clima2D", page_icon="❄️", layout="wide")

# ----------------------------------------------------------------------------- estado
if "projeto" not in st.session_state:
    st.session_state.projeto = pj.projeto_padrao()
    st.session_state.versao = 0
    st.session_state.resultado = None
    st.session_state.malha = None
P = st.session_state.projeto
V = st.session_state.versao   # entra na chave dos widgets: muda quando o projeto é substituído


def substituir_projeto(novo):
    st.session_state.projeto = pj.completar(novo)
    st.session_state.versao += 1
    st.session_state.resultado = None
    st.session_state.malha = None


def hash_projeto(p):
    return hashlib.md5(pj.salvar_json(p).encode()).hexdigest()


def tabela(lista, colunas):
    return pd.DataFrame(lista, columns=colunas) if lista else pd.DataFrame(columns=colunas)


def de_tabela(df, numericas):
    df = df.dropna(how="all")
    linhas = []
    for _, r in df.iterrows():
        d = r.to_dict()
        if any(pd.isna(d.get(c)) for c in numericas):
            continue
        for c in numericas:
            d[c] = float(d[c])
        linhas.append(d)
    return linhas


def mostrar(fig):
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)


# ----------------------------------------------------------------------------- barra lateral
with st.sidebar:
    st.title("❄️ Clima2D")
    st.caption("Distribuição de ar, conforto térmico e umidade em ambientes climatizados")
    P["nome"] = st.text_input("Nome do projeto", P["nome"], key=f"nome{V}")
    P["responsavel"] = st.text_input("Responsável técnico", P.get("responsavel", ""), key=f"resp{V}")
    st.divider()
    st.subheader("Arquivo do projeto")
    st.download_button("💾 Salvar projeto (.json)", pj.salvar_json(P),
                       file_name=f"{P['nome'] or 'projeto'}.json", mime="application/json",
                       width="stretch")
    arq = st.file_uploader("📂 Abrir projeto (.json)", type=["json"], key=f"abrir{V}")
    if arq is not None:
        try:
            substituir_projeto(pj.carregar_json(arq.getvalue().decode("utf-8")))
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Arquivo inválido: {e}")
    if st.button("Carregar exemplo (escritório)", width="stretch"):
        substituir_projeto(pj.projeto_padrao())
        st.rerun()
    st.divider()
    st.caption("Fluxo de trabalho: 1 Geometria → 2 Cargas → 3 Ar-condicionado → 4 Simular → 5 Resultados")

abas = st.tabs(["1 · Geometria", "2 · Cargas", "3 · Ar-condicionado", "4 · Simular", "5 · Resultados e relatório"])

# ============================================================================= 1. GEOMETRIA
with abas[0]:
    st.header("Geometria do ambiente")
    modo = st.radio("Como definir a geometria?", ["Digitar medidas", "Importar CORTE (DXF)", "Importar PLANTA (DXF)"],
                    horizontal=True, key="modo_geo")

    if modo != "Digitar medidas":
        with st.expander("Convenção de layers do DXF", expanded=False):
            st.markdown("""
| Layer (o nome precisa **conter** a palavra) | O que desenhar |
|---|---|
| `AMBIENTE` | contorno do ambiente (polilinha fechada) |
| `INSUFLAMENTO` | difusor/grelha de insuflamento (linha ou retângulo) |
| `RETORNO` | grelha de retorno |
| `PESSOA` | um retângulo, círculo ou bloco por pessoa |
| `EQUIPAMENTO` | equipamento que dissipa calor |
| `OBSTACULO` | móveis e sólidos |

Unidades lidas do DXF (mm, cm ou m). Arquivos de exemplo: `exemplos/dxf/`.
""")
        up = st.file_uploader("Arquivo DXF", type=["dxf"], key=f"dxf_{modo}")
        if modo == "Importar CORTE (DXF)":
            prof = st.number_input("Profundidade do ambiente (perpendicular ao corte) [m]", 0.5, 100.0,
                                   float(P["sala"]["profundidade"]), 0.1)
            if up is not None and st.button("Importar corte", type="primary"):
                try:
                    dados, avisos = idxf.importar_corte(up.getvalue(), profundidade=prof)
                    novo = dict(P, **dados)
                    substituir_projeto(novo)
                    st.session_state.avisos_import = avisos
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Não foi possível importar: {e}")
        else:
            c1, c2, c3 = st.columns(3)
            eixo = c1.selectbox("Direção do corte", ["x", "y"], help="O modelo 2D é um corte da planta nessa direção. "
                                "Escolha a direção do jato do equipamento.")
            pe = c2.number_input("Pé-direito [m]", 2.0, 15.0, 2.8, 0.05)
            hp = c3.number_input("Altura das pessoas [m]", 0.8, 2.0, 1.2, 0.05, help="1,2 sentado; 1,7 em pé")
            c1, c2, c3, c4 = st.columns(4)
            i0 = c1.number_input("Insuflamento de parede: base [m]", 0.0, 15.0, 2.35, 0.05)
            i1 = c2.number_input("Insuflamento de parede: topo [m]", 0.0, 15.0, 2.45, 0.05)
            r0 = c3.number_input("Retorno de parede: base [m]", 0.0, 15.0, 2.55, 0.05)
            r1 = c4.number_input("Retorno de parede: topo [m]", 0.0, 15.0, 2.75, 0.05)
            if up is not None:
                try:
                    dados, avisos, previa = idxf.importar_planta(
                        up.getvalue(), eixo=eixo, pe_direito=pe, faixa_parede_insuflamento=(i0, i1),
                        faixa_parede_retorno=(r0, r1), altura_pessoa=hp)
                    cp1, cp2 = st.columns([1, 1])
                    with cp1:
                        mostrar(idxf.figura_planta(previa, eixo))
                    with cp2:
                        st.markdown(f"**Corte resultante:** largura {dados['sala']['largura']:.2f} m, "
                                    f"profundidade {dados['sala']['profundidade']:.2f} m, pé-direito {pe:.2f} m")
                        st.markdown(f"- {len(dados['aberturas'])} abertura(s)\n- {len(dados['fontes'])} fonte(s) de calor\n"
                                    f"- {len(dados['obstaculos'])} obstáculo(s)")
                        for a in avisos:
                            st.caption("⚠️ " + a)
                    if st.button("Gerar corte a partir da planta", type="primary"):
                        substituir_projeto(dict(P, **dados))
                        st.session_state.avisos_import = avisos
                        st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Não foi possível importar: {e}")
        for a in st.session_state.get("avisos_import", []):
            st.warning(a)

    st.subheader("Dimensões do corte")
    c1, c2, c3 = st.columns(3)
    P["sala"]["largura"] = c1.number_input("Largura do corte [m]", 1.0, 50.0, float(P["sala"]["largura"]), 0.1, key=f"L{V}")
    P["sala"]["altura"] = c2.number_input("Pé-direito [m]", 2.0, 15.0, float(P["sala"]["altura"]), 0.05, key=f"H{V}")
    P["sala"]["profundidade"] = c3.number_input("Profundidade [m]", 0.5, 100.0, float(P["sala"]["profundidade"]),
                                                0.1, key=f"D{V}",
                                                help="Dimensão perpendicular ao corte. As cargas são divididas por ela.")

    col_esq, col_dir = st.columns([1, 1])
    with col_esq:
        st.subheader("Aberturas (insuflamento e retorno)")
        st.caption("Paredes laterais: início/fim = altura [m]. Piso/teto: início/fim = posição x [m].")
        df = st.data_editor(
            tabela(P["aberturas"], ["tipo", "parede", "inicio", "fim"]), num_rows="dynamic", key=f"ab{V}",
            width="stretch",
            column_config={
                "tipo": st.column_config.SelectboxColumn("Tipo", options=["insuflamento", "retorno"], required=True),
                "parede": st.column_config.SelectboxColumn("Parede", options=["esquerda", "direita", "teto", "piso"],
                                                           required=True),
                "inicio": st.column_config.NumberColumn("Início [m]", format="%.2f"),
                "fim": st.column_config.NumberColumn("Fim [m]", format="%.2f"),
            })
        P["aberturas"] = de_tabela(df, ["inicio", "fim"])
        st.subheader("Obstáculos (móveis)")
        df = st.data_editor(
            tabela(P["obstaculos"], ["nome", "x0", "x1", "y0", "y1"]), num_rows="dynamic", key=f"ob{V}",
            width="stretch",
            column_config={c: st.column_config.NumberColumn(c, format="%.2f") for c in ["x0", "x1", "y0", "y1"]})
        P["obstaculos"] = de_tabela(df, ["x0", "x1", "y0", "y1"])
    with col_dir:
        try:
            mostrar(pj.figura_geometria(P))
        except Exception as e:  # noqa: BLE001
            st.error(f"Erro ao desenhar: {e}")

# ============================================================================= 2. CARGAS
with abas[1]:
    st.header("Cargas térmicas do ambiente")
    st.caption("Valores TOTAIS do ambiente (toda a profundidade). Para projeto, levante as cargas conforme ABNT NBR 16401-1.")

    with st.expander("➕ Adicionar pessoas rapidamente"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.number_input("Quantidade", 1, 500, 2)
        atv = c2.selectbox("Atividade", list(pj.ATIVIDADES))
        xp = c3.number_input("Posição x do centro [m]", 0.0, 50.0, 3.0, 0.1)
        alt = c4.number_input("Altura [m]", 0.8, 2.0, 1.2, 0.05)
        s_, l_, met = pj.ATIVIDADES[atv]
        st.caption(f"{atv}: {s_:.0f} W sensível + {l_:.0f} W latente por pessoa, {met} met")
        if st.button("Adicionar"):
            P["fontes"].append({"nome": f"{n} pessoa(s)", "x0": round(xp - 0.2, 2), "x1": round(xp + 0.2, 2),
                                "y0": 0.0, "y1": alt, "sensivel_w": n * s_, "latente_w": n * l_})
            P["condicao"]["met"] = met
            st.session_state.versao += 1
            st.rerun()

    st.subheader("Fontes internas (pessoas, equipamentos)")
    st.caption("x0-x1: posição horizontal; y0-y1: altura da região que libera calor [m].")
    df = st.data_editor(
        tabela(P["fontes"], ["nome", "x0", "x1", "y0", "y1", "sensivel_w", "latente_w"]), num_rows="dynamic",
        key=f"fo{V}", width="stretch",
        column_config={
            **{c: st.column_config.NumberColumn(c, format="%.2f") for c in ["x0", "x1", "y0", "y1"]},
            "sensivel_w": st.column_config.NumberColumn("Sensível [W]", format="%.0f"),
            "latente_w": st.column_config.NumberColumn("Latente [W]", format="%.0f"),
        })
    P["fontes"] = de_tabela(df, ["x0", "x1", "y0", "y1", "sensivel_w", "latente_w"])

    st.subheader("Superfícies e iluminação")
    st.caption("Calor que entra pelas superfícies [W/m²]: insolação + condução em fachadas, cobertura, piso sobre área quente.")
    c = st.columns(5)
    sup = P["superficies"]
    sup["fluxo_esquerda"] = c[0].number_input("Parede esquerda [W/m²]", -200.0, 500.0, float(sup["fluxo_esquerda"]), 1.0, key=f"fe{V}")
    sup["fluxo_direita"] = c[1].number_input("Parede direita [W/m²]", -200.0, 500.0, float(sup["fluxo_direita"]), 1.0, key=f"fd{V}")
    sup["fluxo_teto"] = c[2].number_input("Teto/cobertura [W/m²]", -200.0, 500.0, float(sup["fluxo_teto"]), 1.0, key=f"ft{V}")
    sup["fluxo_piso"] = c[3].number_input("Piso [W/m²]", -200.0, 500.0, float(sup["fluxo_piso"]), 1.0, key=f"fp{V}")
    P["iluminacao_w_m2"] = c[4].number_input("Iluminação [W/m² de piso]", 0.0, 100.0, float(P["iluminacao_w_m2"]), 0.5, key=f"il{V}")

    cg = pj.cargas_totais(P)
    st.subheader("Resumo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sensível", f"{cg['sensivel']:.0f} W")
    c2.metric("Latente", f"{cg['latente']:.0f} W")
    c3.metric("Total", f"{cg['total']:.0f} W", f"{cg['total'] * 3.41214:,.0f} BTU/h".replace(",", "."), delta_color="off")
    fcs = cg["sensivel"] / cg["total"] if cg["total"] else 1.0
    c4.metric("Fator de calor sensível", f"{fcs:.2f}")
    st.dataframe(pd.DataFrame([(k, v[0], v[1]) for k, v in cg["parcelas"].items()],
                              columns=["Parcela", "Sensível [W]", "Latente [W]"]), hide_index=True)

# ============================================================================= 3. AR-CONDICIONADO
with abas[2]:
    st.header("Condição de projeto e insuflamento")
    c = P["condicao"]
    c1, c2, c3, c4 = st.columns(4)
    c["T_alvo"] = c1.number_input("Temperatura desejada [°C]", 16.0, 30.0, float(c["T_alvo"]), 0.5, key=f"ta{V}")
    c["UR_alvo"] = c2.number_input("Umidade relativa desejada [%]", 20.0, 80.0, float(c["UR_alvo"]) * 100, 1.0, key=f"ua{V}") / 100
    c["met"] = c3.number_input("Atividade [met]", 0.8, 4.0, float(c["met"]), 0.1, key=f"me{V}",
                               help="1,0 sentado em repouso; 1,1-1,2 escritório; 1,6 em pé leve")
    c["clo"] = c4.number_input("Vestimenta [clo]", 0.0, 2.0, float(c["clo"]), 0.05, key=f"cl{V}",
                               help="0,5 roupa leve de verão; 1,0 terno")

    i = P["insuflamento"]
    st.subheader("Equipamento / difusor")
    c1, c2, c3, c4 = st.columns(4)
    i["vazao_m3h"] = c1.number_input("Vazão de insuflamento [m³/h]", 50.0, 50000.0, float(i["vazao_m3h"]), 10.0, key=f"vz{V}",
                                     help="Catálogo do equipamento. Split de 12.000 BTU/h: ~500-650 m³/h")
    i["angulo_graus"] = c2.number_input("Ângulo do jato [°]", -75.0, 75.0, float(i["angulo_graus"]), 1.0, key=f"an{V}",
                                        help="Em relação à normal da parede. Positivo = para baixo (paredes) ou para +x (teto)")
    i["temperatura"] = c3.number_input("Temperatura de insuflamento [°C]", 5.0, 35.0, float(i["temperatura"]), 0.1, key=f"ti{V}")
    i["ur_saida"] = c4.number_input("UR do ar insuflado [%]", 30.0, 100.0, float(i["ur_saida"]) * 100, 1.0, key=f"ui{V}",
                                    help="Ar saindo de serpentina úmida: tipicamente 85-95 %") / 100

    d = pj.dimensionar_insuflamento(P)
    st.subheader("Dimensionamento pelo balanço de energia e umidade")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura de insuflamento necessária", f"{d['temperatura']:.1f} °C")
    c2.metric("UR de insuflamento necessária", f"{d['ur_saida'] * 100:.0f} %")
    c3.metric("Capacidade (só cargas do ambiente)", f"{d['capacidade_btuh']:,.0f} BTU/h".replace(",", "."),
              f"{d['capacidade_TR']:.2f} TR", delta_color="off")
    c4.metric("Renovações por hora", f"{d['trocas_hora']:.1f} /h")
    if d["ur_saida"] < 0.80:
        st.warning(f"Para manter {c['UR_alvo'] * 100:.0f} % UR, o ar precisa sair com {d['ur_saida'] * 100:.0f} % UR "
                   f"(orvalho {d['ponto_orvalho']:.1f} °C). Uma serpentina comum entrega 85-95 %: será preciso "
                   "resfriar mais e reaquecer, reduzir a vazão ou usar desumidificação dedicada.")
    if st.button("Usar estes valores no insuflamento", type="primary"):
        i["temperatura"] = round(d["temperatura"], 2)
        i["ur_saida"] = round(d["ur_saida"], 3)
        st.session_state.versao += 1
        st.rerun()
    st.caption("A capacidade acima não inclui o ar externo de renovação (NBR 16401-3), que soma carga na serpentina.")

# ============================================================================= 4. SIMULAR
with abas[3]:
    st.header("Simulação")
    s = P["simulacao"]
    c1, c2, c3 = st.columns(3)
    opcoes = {"Rápida (10 cm)": 10.0, "Precisa (5 cm)": 5.0, "Muito precisa (2,5 cm)": 2.5}
    atual = next((k for k, v in opcoes.items() if v == s["malha_cm"]), "Rápida (10 cm)")
    s["malha_cm"] = opcoes[c1.selectbox("Malha", list(opcoes), index=list(opcoes).index(atual), key=f"ma{V}")]
    s["tempo_s"] = 60.0 * c2.number_input("Tempo simulado [min]", 5.0, 240.0, s["tempo_s"] / 60, 5.0, key=f"ts{V}",
                                         help="Precisa ser suficiente para a sala entrar em regime (veja o balanço).")
    s["tempo_media_s"] = 60.0 * c3.number_input("Média dos últimos [min]", 1.0, 120.0, s["tempo_media_s"] / 60, 1.0, key=f"tm{V}")
    with st.expander("Parâmetros avançados"):
        s["nu_efetiva"] = st.number_input("Viscosidade turbulenta efetiva [m²/s]", 1e-4, 2e-2, float(s["nu_efetiva"]),
                                          1e-4, format="%.4f", key=f"nu{V}",
                                          help="Calibre com medição. Faixa típica 5e-4 a 5e-3.")
        cr = P["criterios"]
        c1, c2, c3, c4 = st.columns(4)
        cr["pmv_max"] = c1.number_input("|PMV| máximo", 0.1, 1.0, float(cr["pmv_max"]), 0.1, key=f"c1{V}")
        cr["dr_max"] = c2.number_input("DR máximo [%]", 5.0, 40.0, float(cr["dr_max"]), 1.0, key=f"c2{V}")
        cr["vel_max"] = c3.number_input("Velocidade máxima [m/s]", 0.05, 1.0, float(cr["vel_max"]), 0.01, key=f"c3{V}")
        cr["dT_vertical_max"] = c4.number_input("Estratificação máx. [K]", 1.0, 6.0, float(cr["dT_vertical_max"]), 0.5, key=f"c4{V}")
    malha_extra = st.checkbox("Fazer também o estudo de malha (roda 10 cm e 5 cm e compara; ~3x mais tempo)",
                              help="Recomendado para relatórios: mostra se o resultado depende da malha.")

    erros = pj.validar(P)
    for e in erros:
        st.error(e)
    nx = int(round(P["sala"]["largura"] / s["malha_cm"] * 100))
    ny = int(round(P["sala"]["altura"] / s["malha_cm"] * 100))
    st.caption(f"Malha: {nx} x {ny} = {nx * ny:,} células. Estimativa grosseira: "
               f"{max(1, nx * ny * s['tempo_s'] / 4.2e6 * (10 / s['malha_cm'])):.0f} min em CPU de notebook."
               .replace(",", "."))
    if st.button("▶ Simular", type="primary", disabled=bool(erros)):
        barra = st.progress(0.0, "Compilando o modelo...")
        try:
            cb = lambda f, msg: barra.progress(min(f, 1.0), msg)
            if malha_extra:
                res, tab = pj.estudo_malha(P, (10.0, 5.0), cb)
                st.session_state.resultado = res[-1]
                st.session_state.malha = tab
            else:
                st.session_state.resultado = pj.simular_projeto(P, cb)
                st.session_state.malha = None
            st.session_state.hash_sim = hash_projeto(P)
            barra.progress(1.0, "Concluído. Veja a aba 5.")
            st.success("Simulação concluída. Abra a aba **5 · Resultados e relatório**.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Falha na simulação: {e}")

# ============================================================================= 5. RESULTADOS
with abas[4]:
    st.header("Resultados")
    r = st.session_state.resultado
    if r is None:
        st.info("Rode a simulação na aba 4.")
    else:
        if st.session_state.get("hash_sim") != hash_projeto(P):
            st.warning("O projeto foi alterado depois da simulação. Rode novamente para atualizar os resultados.")
        ind = r["indicadores"]
        c = st.columns(6)
        c[0].metric("Temperatura zona ocupada", f"{ind['T_ocupada']:.1f} °C")
        c[1].metric("Umidade relativa", f"{ind['UR_ocupada'] * 100:.0f} %")
        c[2].metric("PMV médio", f"{ind['PMV_medio']:+.2f}")
        c[3].metric("PPD", f"{ind['PPD_medio']:.0f} %")
        c[4].metric("Corrente de ar (DR máx.)", f"{ind['DR_max']:.0f} %")
        c[5].metric("Ar de retorno", f"{ind['T_retorno']:.1f} °C")

        st.subheader("Conformidade")
        conf = pj.conformidade(r, P["criterios"])
        st.dataframe(pd.DataFrame([{**x, "atende": "✅" if x["atende"] else "❌"} for x in conf]),
                     hide_index=True, width="stretch")

        st.subheader("Controle de qualidade")
        c1, c2, c3 = st.columns(3)
        es, el = r["erro_balanco_sensivel"], r["erro_balanco_latente"]
        c1.metric("Balanço de calor sensível", f"{es * 100:+.1f} %")
        c2.metric("Balanço de calor latente", f"{el * 100:+.1f} %")
        c3.metric("Tempo de cálculo", f"{r['tempo_cpu'] / 60:.1f} min")
        if max(abs(es), abs(el)) > 0.05:
            st.warning("Balanço acima de ±5 %: a sala ainda não está em regime. Aumente o tempo simulado.")
        else:
            st.success("Balanços de energia e umidade fecham: a simulação está em regime permanente.")
        if st.session_state.malha:
            st.write("**Estudo de malha**")
            st.dataframe(pd.DataFrame(st.session_state.malha), hide_index=True)

        fig = pj.figura_resultados(P, r)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        mostrar(fig)

        st.subheader("Exportar")
        c1, c2, c3 = st.columns(3)
        c1.download_button("📄 Relatório técnico (HTML)", pj.relatorio_html(P, r, st.session_state.malha),
                           file_name=f"relatorio_{P['nome']}.html", mime="text/html", width="stretch")
        c2.download_button("🖼️ Figura (PNG)", buf.getvalue(), file_name=f"resultados_{P['nome']}.png",
                           mime="image/png", width="stretch")
        nx, ny, dx, dy = r["malha"]
        X, Y = np.meshgrid((np.arange(nx) + 0.5) * dx, (np.arange(ny) + 0.5) * dy, indexing="ij")
        campos = pd.DataFrame({"x_m": X.ravel(), "y_m": Y.ravel(), "T_C": r["T"].ravel(),
                               "UR": r["UR"].ravel(), "vel_m_s": r["vel"].ravel(),
                               "PMV": r["PMV"].ravel(), "DR_pct": r["DR"].ravel()})
        c3.download_button("📊 Campos (CSV)", campos.to_csv(index=False, sep=";", decimal=","),
                           file_name=f"campos_{P['nome']}.csv", mime="text/csv", width="stretch")
        st.caption("O relatório HTML pode ser aberto no navegador e impresso em PDF (Ctrl+P).")
