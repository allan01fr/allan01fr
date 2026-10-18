"""
Propostas KAPTEK — escopo e preço a partir de formulários por tipo de serviço.

Rodar:  streamlit run app/app.py      (ou dê dois cliques em iniciar.bat no Windows)
"""

import copy
import datetime as dt
import hashlib
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

import altair as alt
import pandas as pd
import streamlit as st

from orcamento import calibracao as cb
from orcamento import catalogo as ct
from orcamento import exportar_docx, exportar_xlsx, motor
from orcamento import parametros as pm
from orcamento import proposta as pp

st.set_page_config(page_title="Propostas KAPTEK", page_icon="📐", layout="wide")

AZUL, COBRE, GRAFITE = "#1B3A5C", "#C18E6D", "#3E4448"
LOGO = os.path.join(RAIZ, "modelos", "logo-horizontal.png")
PASTA_EXEMPLOS = os.path.join(RAIZ, "exemplos")
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI",
       "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
RISCOS = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto"}
MODELOS = {"fechado": "Escopo fechado", "hora": "Hora técnica", "fee": "% sobre o valor da obra"}
CATEGORIAS = {"material": "Material", "equipamento": "Equipamento", "mo_execucao": "Mão de obra de execução",
              "subcontrato": "Subcontrato"}
moeda = exportar_docx.moeda

# ----------------------------------------------------------------------------- estado
ss = st.session_state
if "cat" not in ss:
    ss.cat = ct.carregar()
    ss.params = pm.carregar()
if "proposta" not in ss:
    ss.proposta = pp.padrao(ss.params)
    ss.versao = 0
    ss.op_idx = 0
CAT = ss.cat
P = ss.proposta
V = ss.versao


def k(*partes):
    """Chave de widget; muda quando a estrutura da proposta muda (versao)."""
    return f"{V}|" + "|".join(str(p) for p in partes)


def substituir_proposta(nova):
    ss.proposta = pp.completar(nova, CAT, ss.params)
    ss.versao += 1
    ss.op_idx = 0
    ss.pop("arquivos", None)


def estrutura_mudou():
    ss.versao += 1
    st.rerun()


def assinatura(p):
    return hashlib.md5(json.dumps(p, sort_keys=True, default=str).encode()).hexdigest()


def exemplos():
    return sorted(f for f in os.listdir(PASTA_EXEMPLOS) if f.endswith(".json"))


def pct(v):
    return "—" if v is None else f"{v:.1%}".replace(".", ",")


def num_br(v, casas=1):
    return f"{v:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


# ----------------------------------------------------------------------------- barra lateral
with st.sidebar:
    if os.path.exists(LOGO):
        st.image(LOGO, width=190)
    st.caption("Escopo e preço de propostas a partir de formulários por tipo de serviço")
    c1, c2 = st.columns([3, 1])
    P["numero"] = c1.text_input("Proposta nº", P["numero"], key=k("numero"))
    P["revisao"] = c2.text_input("Rev.", P.get("revisao", "00"), key=k("rev"))
    st.divider()
    nomes_op = [o["nome"] for o in P["opcoes"]]
    ss.op_idx = min(ss.op_idx, len(nomes_op) - 1)
    ss.op_idx = st.radio("Opção em edição", range(len(nomes_op)), index=ss.op_idx,
                         format_func=lambda i: nomes_op[i], key=k("op_sel"))
    st.divider()
    st.subheader("Arquivo da proposta")
    st.download_button("💾 Salvar proposta (.json)", pp.salvar_json(P),
                       file_name=f"{exportar_docx.slug(P['numero'])}.json", mime="application/json", width="stretch")
    arq = st.file_uploader("📂 Abrir proposta (.json)", type=["json"], key=k("abrir"))
    if arq is not None:
        try:
            substituir_proposta(pp.carregar_json(arq.getvalue().decode("utf-8")))
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Arquivo inválido: {e}")
    ex = st.selectbox("Exemplos", exemplos(), key="exemplo_sel")
    if st.button("Carregar exemplo", width="stretch"):
        with open(os.path.join(PASTA_EXEMPLOS, ex), encoding="utf-8") as f:
            substituir_proposta(pp.carregar_json(f.read()))
        st.rerun()
    if st.button("Nova proposta em branco", width="stretch"):
        substituir_proposta(pp.padrao(ss.params))
        st.rerun()
    st.divider()
    st.caption("Fluxo: 1 Dados gerais → 2 Escopo → 3 Fornecimento → 4 Preço → 5 Prazo e pagamento → 6 Exportar")

O = P["opcoes"][ss.op_idx]
abas = st.tabs(["1 · Dados gerais", "2 · Escopo", "3 · Fornecimento e execução", "4 · Preço",
                "5 · Prazo e pagamento", "6 · Exportar", "7 · Catálogo e parâmetros", "8 · Calibração"])

# ----------------------------------------------------------------------------- 1 dados gerais
with abas[0]:
    cl = P["cliente"]
    st.subheader("Cliente e objeto")
    c1, c2 = st.columns(2)
    cl["razao"] = c1.text_input("Razão social do contratante", cl.get("razao", ""), key=k("razao"))
    cl["contato"] = c2.text_input("Contato (nome / cargo / e-mail / telefone)", cl.get("contato", ""), key=k("contato"))
    c1, c2, c3 = st.columns([3, 2, 1])
    cl["endereco"] = c1.text_input("Endereço do objeto", cl.get("endereco", ""), key=k("endereco"))
    cl["cidade"] = c2.text_input("Cidade", cl.get("cidade", ""), key=k("cidade"))
    uf_atual = cl.get("uf", "RJ") if cl.get("uf", "RJ") in UFS else "RJ"
    cl["uf"] = c3.selectbox("UF", UFS, index=UFS.index(uf_atual), key=k("uf"))
    if cl["uf"] not in motor.UFS_SEM_VISTO:
        st.warning(f"Atuação em {cl['uf']}: fora de RJ e SP é preciso visto no CREA-{cl['uf']} (Lei 5.194/1966, art. 58).")
    cl["signatario"] = st.text_input("Signatário do contratante (nome e cargo)", cl.get("signatario", ""), key=k("signatario"))
    P["objeto"] = st.text_area("Objeto da proposta (uma frase precisa)", P.get("objeto", ""), key=k("objeto"), height=80)
    c1, c2, c3 = st.columns(3)
    try:
        data_ini = dt.date.fromisoformat(P["data"])
    except (TypeError, ValueError):
        data_ini = dt.date.today()
    P["data"] = c1.date_input("Data de emissão", data_ini, format="DD/MM/YYYY", key=k("data")).isoformat()
    P["validade_dias"] = int(c2.number_input("Validade (dias corridos)", 1, 180, int(P["validade_dias"]), key=k("validade")))
    P["prazo_pagamento_dias"] = int(c3.number_input("Vencimento das faturas (dias)", 0, 120,
                                                    int(P.get("prazo_pagamento_dias", 15)), key=k("venc")))

    st.subheader("Contexto que ajusta as horas")
    st.caption("Estes fatores multiplicam as horas das atividades que dependem deles. Cada serviço pode "
               "sobrescrever a complexidade na aba Escopo.")
    cx = P["contexto"]
    c1, c2, c3, c4 = st.columns(4)
    for col, nome in zip((c1, c2, c3, c4), ("complexidade", "documentacao", "acesso", "urgencia")):
        fat = CAT["fatores"][nome]
        vals = [o["valor"] for o in fat["opcoes"]]
        rot = {o["valor"]: f"{o['rotulo']} (×{num_br(o['num'], 2)})" for o in fat["opcoes"]}
        cx[nome] = col.selectbox(fat["rotulo"], vals, index=vals.index(cx[nome]) if cx[nome] in vals else 0,
                                 format_func=rot.get, key=k("cx", nome))
    c1, c2, c3 = st.columns(3)
    riscos = list(RISCOS)
    cont = P["parametros"]["contingencia"]
    cx["risco"] = c1.selectbox("Risco do escopo (contingência)", riscos, index=riscos.index(cx["risco"]),
                               format_func=lambda r: f"{RISCOS[r]} ({pct(cont[r])})", key=k("risco"))
    cx["dist_km"] = float(c2.number_input("Distância da base até o local (km)", 0.0, 5000.0, float(cx["dist_km"]),
                                          step=5.0, key=k("dist"),
                                          help="Acima do raio isento, o deslocamento entra como custo direto."))
    cx["area_ref"] = float(c3.number_input("Área de referência (m²)", 0.0, 1e7, float(cx.get("area_ref") or 0),
                                           step=50.0, key=k("area_ref"), help="Só para o indicador R$/m². 0 = não calcular."))

# ----------------------------------------------------------------------------- 2 escopo
def widget_campo(c, valor, chave):
    rot = c["rotulo"] + (f" ({c['unidade']})" if c.get("unidade") else "")
    ajuda = c.get("ajuda") or None
    if c["tipo"] == "int":
        return int(st.number_input(rot, min_value=int(c.get("min", 0)), value=int(valor or 0), step=1, key=chave, help=ajuda))
    if c["tipo"] == "float":
        passo = 0.05 if float(c["padrao"]) <= 1 else 1.0
        return float(st.number_input(rot, min_value=float(c.get("min", 0)), value=float(valor or 0), step=passo,
                                     key=chave, help=ajuda))
    if c["tipo"] == "bool":
        return bool(st.checkbox(rot, value=bool(valor), key=chave, help=ajuda))
    vals = [o["valor"] for o in c["opcoes"]]
    rots = {o["valor"]: o["rotulo"] for o in c["opcoes"]}
    return st.selectbox(rot, vals, index=vals.index(valor) if valor in vals else 0, format_func=rots.get,
                        key=chave, help=ajuda)


with abas[1]:
    st.subheader(f"Escopo — {O['nome']}")
    c1, c2, c3, c4 = st.columns([3, 1.2, 1.6, 1.2])
    O["nome"] = c1.text_input("Nome da opção", O["nome"], key=k("op_nome", O["id"]))
    if c2.button("➕ Nova opção", width="stretch"):
        P["opcoes"].append(pp.nova_opcao(pp.proxima_letra(P), P["parametros"]))
        ss.op_idx = len(P["opcoes"]) - 1
        estrutura_mudou()
    nivel = c3.selectbox("Duplicar com nível", ["(igual)", "2d", "3d", "bim"], key=k("dup_nivel"),
                         format_func=lambda v: {"(igual)": "Duplicar igual", "2d": "Duplicar em 2D",
                                                "3d": "Duplicar em 3D", "bim": "Duplicar em BIM"}[v])
    if c4.button("⧉ Duplicar", width="stretch"):
        pp.duplicar_opcao(P, ss.op_idx, None if nivel == "(igual)" else nivel)
        ss.op_idx = len(P["opcoes"]) - 1
        estrutura_mudou()

    with st.container(border=True):
        st.markdown("**Adicionar serviço do catálogo**")
        c1, c2, c3 = st.columns([1.2, 1.2, 3])
        disc = c1.selectbox("Disciplina", ["Todas"] + ct.disciplinas(CAT), key=k("f_disc"))
        tipos = {"": "Todos", **CAT["tipos"]}
        tipo = c2.selectbox("Tipo", list(tipos), format_func=tipos.get, key=k("f_tipo"))
        lista = ct.filtrar(CAT, None if disc == "Todas" else disc, tipo or None)
        if lista:
            sid = c3.selectbox("Serviço", [s["id"] for s in lista], key=k("f_serv"),
                               format_func=lambda i: f"{ct.servico(CAT, i)['nome']}  ·  {CAT['tipos'][ct.servico(CAT, i)['tipo']]}")
            st.caption(ct.servico(CAT, sid)["descricao"])
            if st.button("Adicionar à opção", type="primary"):
                O["itens"].append(pp.novo_item(ct.servico(CAT, sid)))
                ss.aberto = len(O["itens"]) - 1
                estrutura_mudou()
        else:
            c3.info("Nenhum serviço com esse filtro.")

    if not O["itens"]:
        st.info("Esta opção ainda não tem serviços. Escolha um serviço acima e preencha o formulário dele.")
    perfis = list(CAT["perfis"])
    for i, it in enumerate(O["itens"]):
        serv = ct.servico(CAT, it["servico"])
        titulo = f"{i + 1}. {it.get('descricao') or serv['nome']}  ·  {serv['disciplina']}"
        with st.expander(titulo, expanded=(ss.get("aberto") == i)):
            st.caption(serv["descricao"])
            cols = st.columns(3)
            for j, c in enumerate(serv["dados"]):
                with cols[j % 3]:
                    it["dados"][c["id"]] = widget_campo(c, it["dados"].get(c["id"], c["padrao"]),
                                                        k("campo", O["id"], i, c["id"]))
            with st.popover("Ajustes deste serviço"):
                it["descricao"] = st.text_input("Nome na proposta (vazio = nome do catálogo)", it.get("descricao", ""),
                                                key=k("desc", O["id"], i))
                fat = CAT["fatores"]["complexidade"]
                vals = [""] + [o["valor"] for o in fat["opcoes"]]
                rot = {"": "Igual à proposta", **{o["valor"]: f"{o['rotulo']} (×{num_br(o['num'], 2)})" for o in fat["opcoes"]}}
                atual = it.get("ajustes", {}).get("complexidade", "")
                esc = st.selectbox("Complexidade neste serviço", vals, index=vals.index(atual) if atual in vals else 0,
                                   format_func=rot.get, key=k("cplx", O["id"], i))
                it["ajustes"] = {"complexidade": esc} if esc else {}
                it["fator_manual"] = float(st.number_input("Fator manual sobre as horas", 0.1, 5.0,
                                                           float(it.get("fator_manual", 1.0)), step=0.05,
                                                           key=k("fman", O["id"], i)))
            try:
                linhas, diretos = motor.linhas_item(CAT, P, it, i)
                df = pd.DataFrame([{"Atividade": l["nome"], "Etapa": ct.etapa(CAT, l["etapa"])["rotulo"],
                                    "Qtd": round(l["q"], 2), "Fator": round(l["fator"], 3),
                                    **{p: round(l["horas"][p], 1) for p in perfis},
                                    "Total (h)": round(l["total_h"], 1)} for l in linhas])
                st.dataframe(df, hide_index=True, width="stretch")
                tot = sum(l["total_h"] for l in linhas)
                txt = f"**{num_br(tot)} h** neste serviço"
                if diretos:
                    txt += " · custos diretos: " + "; ".join(f"{d['descricao']} {moeda(d['valor'])}" for d in diretos)
                st.markdown(txt)
            except Exception as e:  # noqa: BLE001
                st.error(f"Erro ao calcular este serviço: {e}")
            c1, c2, c3, _ = st.columns([1, 1, 1, 4])
            if c1.button("⬆", key=k("sobe", O["id"], i), disabled=i == 0, help="Subir"):
                O["itens"][i - 1], O["itens"][i] = O["itens"][i], O["itens"][i - 1]
                estrutura_mudou()
            if c2.button("⬇", key=k("desce", O["id"], i), disabled=i == len(O["itens"]) - 1, help="Descer"):
                O["itens"][i + 1], O["itens"][i] = O["itens"][i], O["itens"][i + 1]
                estrutura_mudou()
            if c3.button("🗑 Remover", key=k("rm", O["id"], i)):
                O["itens"].pop(i)
                ss.aberto = None
                estrutura_mudou()
    if len(P["opcoes"]) > 1:
        st.divider()
        if st.button(f"🗑 Excluir a opção '{O['nome']}'"):
            P["opcoes"].pop(ss.op_idx)
            ss.op_idx = 0
            estrutura_mudou()

# ----------------------------------------------------------------------------- 3 fornecimento
with abas[2]:
    st.subheader(f"Fornecimento e execução — {O['nome']}")
    st.caption("Para turnkey e obra: materiais, equipamentos, mão de obra de execução e subcontratos. "
               "Cada categoria recebe o seu BDI (aba Preço → parâmetros). Deixe vazio quando a proposta for só de engenharia.")
    base = pd.DataFrame(O["fornecimentos"] or [], columns=["descricao", "categoria", "unid", "qtd", "custo_unit"])
    base = base.astype({"descricao": str, "categoria": str, "unid": str, "qtd": float, "custo_unit": float})
    ed = st.data_editor(
        base, num_rows="dynamic", width="stretch", key=k("forn", O["id"]),
        column_config={
            "descricao": st.column_config.TextColumn("Descrição", width="large"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=list(CATEGORIAS), required=True,
                                                          default="material"),
            "unid": st.column_config.TextColumn("Unid", default="un"),
            "qtd": st.column_config.NumberColumn("Qtd", min_value=0.0, default=1.0),
            "custo_unit": st.column_config.NumberColumn("Custo unitário (R$)", min_value=0.0, default=0.0, format="%.2f"),
        })
    novos = []
    for _, row in ed.iterrows():
        if not str(row.get("descricao") or "").strip():
            continue
        novos.append({"descricao": str(row["descricao"]).strip(), "categoria": row.get("categoria") or "material",
                      "unid": str(row.get("unid") or "un"), "qtd": float(row.get("qtd") or 0),
                      "custo_unit": float(row.get("custo_unit") or 0)})
    O["fornecimentos"] = novos
    O["prazo_execucao_dias"] = int(st.number_input("Prazo de execução da obra/instalação (dias úteis)", 0, 2000,
                                                   int(O.get("prazo_execucao_dias") or 0), key=k("prazo_exec", O["id"]),
                                                   help="Usado no cronograma quando há fornecimentos."))

# ----------------------------------------------------------------------------- 4 preço (entradas antes do cálculo)
with abas[3]:
    topo_preco = st.container()
    with st.expander("Modelo de preço desta opção e parâmetros comerciais da proposta", expanded=False):
        c1, c2, c3 = st.columns(3)
        mods = list(MODELOS)
        O["modelo_preco"] = c1.radio("Modelo usado na proposta (DOCX)", mods, index=mods.index(O.get("modelo_preco", "fechado")),
                                     format_func=MODELOS.get, key=k("modelo", O["id"]))
        O["fee_pct"] = c2.number_input("% sobre o valor da obra", 0.0, 100.0, float(O.get("fee_pct") or 0) * 100,
                                       step=0.5, key=k("fee_pct", O["id"])) / 100
        O["fee_base"] = float(c3.number_input("Valor da obra / CAPEX (R$) — 0 usa o custo dos fornecimentos", 0.0, 1e10,
                                              float(O.get("fee_base") or 0), step=1000.0, key=k("fee_base", O["id"])))
        st.divider()
        PR = P["parametros"]
        st.markdown("**Parâmetros desta proposta** (cópia dos parâmetros da empresa; mudar aqui não altera outras propostas)")
        c1, c2, c3, c4 = st.columns(4)
        PR["margem"] = c1.number_input("Margem-alvo (%)", 0.0, 80.0, PR["margem"] * 100, step=1.0, key=k("p_margem")) / 100
        regimes = {"presumido": "Lucro Presumido", "simples": "Simples Nacional"}
        PR["impostos"]["regime"] = c2.selectbox("Regime tributário", list(regimes), format_func=regimes.get,
                                                index=list(regimes).index(PR["impostos"]["regime"]), key=k("p_regime"))
        if PR["impostos"]["regime"] == "simples":
            PR["impostos"]["simples_aliquota"] = c3.number_input("Alíquota efetiva do Simples (%)", 0.0, 40.0,
                                                                 PR["impostos"]["simples_aliquota"] * 100, step=0.1,
                                                                 key=k("p_simples")) / 100
        else:
            PR["impostos"]["iss"] = c3.number_input("ISS do município (%)", 0.0, 5.0, PR["impostos"]["iss"] * 100,
                                                    step=0.5, key=k("p_iss")) / 100
        c4.metric("Impostos sobre o faturamento", pct(pm.aliquota_impostos(PR)))
        c1, c2, c3, c4 = st.columns(4)
        metodos = {"percentual": "% sobre a mão de obra", "hora": "Custo fixo ÷ horas faturáveis"}
        PR["overhead"]["metodo"] = c1.selectbox("Overhead", list(metodos), format_func=metodos.get,
                                                index=list(metodos).index(PR["overhead"]["metodo"]), key=k("p_ovm"))
        if PR["overhead"]["metodo"] == "percentual":
            PR["overhead"]["pct"] = c2.number_input("Overhead (%)", 0.0, 200.0, PR["overhead"]["pct"] * 100, step=1.0,
                                                    key=k("p_ovp")) / 100
        else:
            PR["overhead"]["custo_fixo_mensal"] = c2.number_input("Custo fixo mensal (R$)", 0.0, 1e7,
                                                                  float(PR["overhead"]["custo_fixo_mensal"]), step=500.0,
                                                                  key=k("p_ovf"))
            PR["overhead"]["horas_faturaveis_mes"] = c3.number_input("Horas faturáveis por mês", 1.0, 10000.0,
                                                                     float(PR["overhead"]["horas_faturaveis_mes"]),
                                                                     step=10.0, key=k("p_ovh"))
        PR["reembolsaveis_adm"] = c4.number_input("Administração sobre reembolsáveis (%)", 0.0, 100.0,
                                                  PR["reembolsaveis_adm"] * 100, step=1.0, key=k("p_adm")) / 100
        st.markdown("Custo e taxa de venda por perfil")
        dfp = pd.DataFrame([{"perfil": c, "nome": CAT["perfis"][c], "custo_h": PR["perfis"][c]["custo_h"],
                             "taxa_venda_h": PR["perfis"][c]["taxa_venda_h"]} for c in CAT["perfis"]])
        edp = st.data_editor(dfp, hide_index=True, disabled=["perfil", "nome"], key=k("p_perfis"),
                             column_config={"custo_h": st.column_config.NumberColumn("Custo/h (R$)", min_value=0.0, format="%.2f"),
                                            "taxa_venda_h": st.column_config.NumberColumn("Taxa de venda/h (R$)", min_value=0.0, format="%.2f")})
        for _, row in edp.iterrows():
            PR["perfis"][row["perfil"]] = {"custo_h": float(row["custo_h"]), "taxa_venda_h": float(row["taxa_venda_h"])}
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("Contingência por risco (%)")
            cc = st.columns(3)
            for col, r in zip(cc, RISCOS):
                PR["contingencia"][r] = col.number_input(RISCOS[r], 0.0, 100.0, PR["contingencia"][r] * 100, step=1.0,
                                                         key=k("p_cont", r)) / 100
        with c2:
            st.markdown("BDI de fornecimento (%)")
            cc = st.columns(4)
            for col, cat_ in zip(cc, CATEGORIAS):
                PR["bdi_fornecimento"][cat_] = col.number_input(CATEGORIAS[cat_], 0.0, 200.0,
                                                                PR["bdi_fornecimento"][cat_] * 100, step=1.0,
                                                                key=k("p_bdi", cat_)) / 100
        c1, c2, c3, c4, c5 = st.columns(5)
        d = PR["deslocamento"]
        d["raio_isento_km"] = c1.number_input("Raio isento (km)", 0.0, 1000.0, float(d["raio_isento_km"]), key=k("p_ri"))
        d["raio_pernoite_km"] = c2.number_input("Raio com retorno diário (km)", 0.0, 2000.0, float(d["raio_pernoite_km"]), key=k("p_rp"))
        d["rs_km"] = c3.number_input("R$/km", 0.0, 50.0, float(d["rs_km"]), step=0.1, key=k("p_km"))
        d["diaria"] = c4.number_input("Diária por pessoa (R$)", 0.0, 5000.0, float(d["diaria"]), step=10.0, key=k("p_diaria"))
        d["pessoas_campo"] = int(c5.number_input("Pessoas em campo", 1, 20, int(d["pessoas_campo"]), key=k("p_pessoas")))
        c1, c2, c3 = st.columns(3)
        PR["art"]["valor"] = c1.number_input("Taxa de ART (R$)", 0.0, 10000.0, float(PR["art"]["valor"]), step=10.0, key=k("p_art"))
        PR["cronograma"]["equipe"] = int(c2.number_input("Equipe por etapa (pessoas)", 1, 20, int(PR["cronograma"]["equipe"]), key=k("p_eq")))
        PR["pagamento"]["sinal"] = c3.number_input("Sinal na assinatura (%)", 0.0, 100.0, PR["pagamento"]["sinal"] * 100,
                                                   step=5.0, key=k("p_sinal")) / 100
        if st.button("Restaurar os parâmetros da empresa nesta proposta"):
            P["parametros"] = copy.deepcopy(ss.params)
            estrutura_mudou()

# ----------------------------------------------------------------------------- cálculo
erro_calc = None
try:
    RES = motor.precificar(CAT, P)
except Exception as e:  # noqa: BLE001
    RES, erro_calc = None, e
ASSINATURA = assinatura([P, CAT])
R = RES["opcoes"][ss.op_idx] if RES else None


def tabela_indicadores(resultados):
    linhas = [
        ("Horas técnicas", lambda r: num_br(r["total_h"])),
        ("Prazo (dias corridos)", lambda r: str(r["prazo_dias_corridos"])),
        ("Custo dos serviços", lambda r: moeda(r["custo_servicos"])),
        ("Preço — escopo fechado", lambda r: moeda(r["preco_fechado"])),
        ("Preço — hora técnica (estimado)", lambda r: moeda(r["preco_hora"])),
        ("Preço — hora técnica (teto)", lambda r: moeda(r["preco_hora_teto"])),
        ("Preço — % sobre obra", lambda r: moeda(r["preco_fee"]) if r["preco_fee"] is not None else "—"),
        ("Preço mínimo dos serviços (margem zero)", lambda r: moeda(r["preco_minimo_servicos"])),
        ("Margem efetiva — escopo fechado", lambda r: pct(r["margem_efetiva"]["fechado"])),
        ("R$/h", lambda r: moeda(r["rs_h"]) if r["rs_h"] else "—"),
        ("R$/m²", lambda r: moeda(r["rs_m2"]) if r["rs_m2"] else "—"),
        ("Modelo escolhido", lambda r: MODELOS[r["modelo_preco"]]),
        ("PREÇO DA PROPOSTA", lambda r: moeda(r["preco"])),
    ]
    return pd.DataFrame({"Indicador": [n for n, _ in linhas],
                         **{r["nome"]: [f(r) for _, f in linhas] for r in resultados}})


with abas[3]:
    with topo_preco:
        if erro_calc:
            st.error(f"Não foi possível calcular: {erro_calc}")
        elif not R["linhas"]:
            st.info("Adicione serviços na aba Escopo para ver o preço.")
        else:
            st.subheader(f"Preço — {O['nome']}")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Escopo fechado", moeda(R["preco_fechado"]))
            c2.metric("Hora técnica (estimado)", moeda(R["preco_hora"]), help=f"Teto: {moeda(R['preco_hora_teto'])}")
            c3.metric("% sobre obra", moeda(R["preco_fee"]) if R["preco_fee"] is not None else "sem base")
            c4.metric("Preço mínimo (margem zero)", moeda(R["preco_minimo_servicos"]))
            c5.metric("Margem efetiva (fechado)", pct(R["margem_efetiva"]["fechado"]))
            st.caption(f"Modelo usado na proposta: **{MODELOS[R['modelo_preco']]}** → {moeda(R['preco'])}. "
                       f"{num_br(R['total_h'])} h · {R['prazo_dias_corridos']} dias corridos · "
                       f"{R['dias_campo']} dia(s) de campo.")
            c1, c2 = st.columns([1.1, 1])
            with c1:
                st.markdown("**Formação do preço — escopo fechado**")
                cadeia = [("Mão de obra", R["custo_mo"]), ("Overhead", R["overhead"]), ("Custos diretos", R["diretos_total"]),
                          ("Custo dos serviços", R["custo_servicos"]),
                          (f"Contingência ({pct(R['cont_pct'])})", R["contingencia"]),
                          (f"Impostos ({pct(R['imp_pct'])})", R["impostos"]), (f"Margem ({pct(R['margem_pct'])})", R["margem"]),
                          ("Preço dos serviços", R["preco_servicos"]), ("Fornecimentos (com BDI)", R["preco_fornec"]),
                          ("PREÇO — ESCOPO FECHADO", R["preco_fechado"])]
                st.dataframe(pd.DataFrame([{"Item": a, "Valor": moeda(b)} for a, b in cadeia]), hide_index=True, width="stretch")
                if R["diretos"]:
                    st.markdown("**Custos diretos**")
                    st.dataframe(pd.DataFrame([{"Descrição": d["descricao"], "Serviço / memória": d["servico_nome"],
                                                "Qtd": f"{num_br(d['qtd'], 2)} {d['unid']}", "Valor": moeda(d["valor"])}
                                               for d in R["diretos"]]), hide_index=True, width="stretch")
            with c2:
                st.markdown("**Horas por perfil**")
                PRf = P["parametros"]["perfis"]
                st.dataframe(pd.DataFrame([{"Perfil": CAT["perfis"][p], "Horas": num_br(h),
                                            "Custo": moeda(h * PRf[p]["custo_h"]),
                                            "Venda (hora técnica)": moeda(h * PRf[p]["taxa_venda_h"])}
                                           for p, h in R["horas_perfil"].items() if h > 0]),
                             hide_index=True, width="stretch")
                if R["fee_pct"] > 0 and R["capex_minimo_fee"]:
                    st.caption(f"Para o modelo % ({pct(R['fee_pct'])}) igualar o escopo fechado, o valor da obra precisaria "
                               f"ser de pelo menos {moeda(R['capex_minimo_fee'])}.")
            if len(RES["opcoes"]) > 1:
                st.markdown("**Comparativo das opções**")
                st.dataframe(tabela_indicadores(RES["opcoes"]), hide_index=True, width="stretch")
                dfc = pd.DataFrame([{"Opção": r["nome"], "Modelo": MODELOS[m], "Preço": v}
                                    for r in RES["opcoes"]
                                    for m, v in (("fechado", r["preco_fechado"]), ("hora", r["preco_hora"]),
                                                 ("fee", r["preco_fee"] or 0))])
                graf = alt.Chart(dfc).mark_bar().encode(
                    x=alt.X("Opção:N", sort=None, title=None), xOffset="Modelo:N",
                    y=alt.Y("Preço:Q", title="R$"),
                    color=alt.Color("Modelo:N", scale=alt.Scale(range=[AZUL, COBRE, GRAFITE]), legend=alt.Legend(orient="bottom")),
                    tooltip=["Opção", "Modelo", alt.Tooltip("Preço:Q", format=",.2f")]).properties(height=280)
                st.altair_chart(graf, width="stretch")

# ----------------------------------------------------------------------------- 5 prazo e pagamento
with abas[4]:
    if R and R["linhas"]:
        st.subheader(f"Cronograma — {O['nome']}")
        dfg = pd.DataFrame([{"Etapa": e["rotulo"], "Início": e["inicio"], "Fim": e["fim"] + 1, "Horas": round(e["horas"], 1),
                             "Dias úteis": e["dias_uteis"], "Dias corridos": e["dias_corridos"], "Marco": e["marco"]}
                            for e in R["cronograma"]])
        graf = alt.Chart(dfg).mark_bar(color=AZUL, cornerRadius=2).encode(
            x=alt.X("Início:Q", title="Dia útil"), x2="Fim:Q",
            y=alt.Y("Etapa:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
            tooltip=["Etapa", "Dias úteis", "Horas", "Marco"]).properties(height=36 * len(dfg) + 40)
        st.altair_chart(graf, width="stretch")
        st.dataframe(dfg.drop(columns=["Fim"]), hide_index=True, width="stretch")
        st.caption(f"Prazo total: {R['prazo_dias_uteis']} dias úteis ≈ {R['prazo_dias_corridos']} dias corridos. "
                   "Dias úteis = horas da etapa ÷ (8 h × equipe); etapas em sequência.")
        st.subheader("Forma de pagamento")
        dpg = pd.DataFrame([{"marco": m["marco"], "pct": round(m["pct"] * 100, 2)} for m in R["pagamento"]])
        edg = st.data_editor(dpg, num_rows="dynamic", width="stretch", key=k("pag", O["id"]),
                             column_config={"marco": st.column_config.TextColumn("Marco (texto da proposta)", width="large"),
                                            "pct": st.column_config.NumberColumn("%", min_value=0.0, max_value=100.0, format="%.1f")})
        novos = [{"marco": str(r["marco"]).strip(), "pct": round(float(r["pct"] or 0) / 100, 4)}
                 for _, r in edg.iterrows() if str(r.get("marco") or "").strip()]
        padrao_pg = [{"marco": m["marco"], "pct": round(m["pct"], 4)} for m in R["pagamento"]]
        if novos != padrao_pg:
            O["pagamento"] = novos
        soma = sum(m["pct"] for m in novos)
        c1, c2 = st.columns([3, 1])
        if abs(soma - 1) > 0.001:
            c1.error(f"As parcelas somam {pct(soma)}; precisam somar 100%.")
        else:
            c1.success("Parcelas somam 100%. " + " · ".join(f"{pct(m['pct'])}: {moeda(m['pct'] * R['preco'])}" for m in novos))
        if c2.button("Recalcular parcelas padrão"):
            O["pagamento"] = []
            estrutura_mudou()
    else:
        st.info("Adicione serviços na aba Escopo para ver o cronograma.")

# ----------------------------------------------------------------------------- 6 exportar
with abas[5]:
    st.subheader("Exportar")
    if RES:
        for av in RES["avisos"]:
            st.warning(av)
    pronto = RES and any(r["linhas"] for r in RES["opcoes"])
    if not pronto:
        st.info("Adicione serviços para exportar.")
    else:
        arquivos = ss.get("arquivos")
        if arquivos and arquivos["assinatura"] != ASSINATURA:
            st.caption("A proposta mudou desde a última geração — gere de novo.")
            arquivos = None
        if st.button("Gerar planilha e propostas", type="primary"):
            xlsx = exportar_xlsx.gerar(CAT, P, RES)
            docs = exportar_docx.gerar(CAT, P, RES)
            nome_x = f"KAPTEK-orcamento-{exportar_docx.slug(P['cliente'].get('razao'))}-{exportar_docx.slug(P['numero'])}-rev{P.get('revisao', '00')}.xlsx"
            ss.arquivos = arquivos = {"assinatura": ASSINATURA, "xlsx": (xlsx, nome_x), "docx": docs}
        if arquivos:
            xlsx, nome_x = arquivos["xlsx"]
            st.download_button(f"📊 {nome_x}", xlsx, file_name=nome_x,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.caption("Planilha com fórmulas vivas: todas as opções, parâmetros, fornecimentos, cronograma e pagamento.")
            for conteudo, nome, pend in arquivos["docx"]:
                st.download_button(f"📄 {nome}", conteudo, file_name=nome,
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                v = exportar_docx.verificar(conteudo)
                ok = v["logo"] and v["margem_sup_cm"] == 3.2 and v["margem_esq_cm"] == 3.0
                st.caption(("✅ padrão KAPTEK conferido (margens 3,2/3,0 e logo)" if ok else "⚠️ template alterado — confira")
                           + (f" · pendências no documento: {', '.join(pend)}" if pend else " · sem pendências"))
            st.info("Ao abrir no Word, aceite a atualização de campos. A proposta só produz efeito acompanhada da ART "
                    "registrada e quitada (Lei 6.496/1977).")

# ----------------------------------------------------------------------------- 7 catálogo e parâmetros
with abas[6]:
    sub = st.tabs(["Serviços do catálogo", "Parâmetros da empresa"])
    with sub[0]:
        st.caption(CAT.get("nota", ""))
        ids = [s["id"] for s in CAT["servicos"]]
        sid = st.selectbox("Serviço", ids, key="cat_sel",
                           format_func=lambda i: f"{ct.servico(CAT, i)['disciplina']} · {ct.servico(CAT, i)['nome']}")
        S = ct.servico(CAT, sid)
        c1, c2 = st.columns([2, 1])
        S["nome"] = c1.text_input("Nome", S["nome"], key=f"cat_nome_{sid}")
        S["tipo"] = c2.selectbox("Tipo", list(CAT["tipos"]), index=list(CAT["tipos"]).index(S["tipo"]),
                                 format_func=CAT["tipos"].get, key=f"cat_tipo_{sid}")
        S["descricao"] = st.text_input("Descrição", S["descricao"], key=f"cat_desc_{sid}")
        st.markdown("**Formulário (campos)** — use os ids nas expressões de driver; campo de opções gera `campo__valor` = 1/0")
        st.dataframe(pd.DataFrame([{"id": c["id"], "rótulo": c["rotulo"], "tipo": c["tipo"], "padrão": str(c["padrao"]),
                                    "opções": ", ".join(f"{o['valor']}={o['num']}" for o in c.get("opcoes", []))}
                                   for c in S["dados"]]), hide_index=True, width="stretch")
        st.markdown("**Atividades e produtividade** (h = (fixo + unid × qtd^b) × fatores × calibração)")
        perfis = list(CAT["perfis"])
        etapas_ids = [e["id"] for e in CAT["etapas"]]
        dfa = pd.DataFrame([{"id": a["id"], "nome": a["nome"], "entregavel": a.get("entregavel", ""), "etapa": a["etapa"],
                             "driver": a.get("driver") or "", "b": a.get("b", 1.0), "fatores": ", ".join(a.get("fatores", [])),
                             "calibracao": a.get("calibracao", 1.0),
                             **{f"fixo_{p}": a.get("fixo", {}).get(p, 0.0) for p in perfis},
                             **{f"unid_{p}": a.get("unid", {}).get(p, 0.0) for p in perfis}} for a in S["atividades"]])
        eda = st.data_editor(dfa, num_rows="dynamic", width="stretch", key=f"cat_ativ_{sid}",
                             column_config={"etapa": st.column_config.SelectboxColumn("etapa", options=etapas_ids, required=True),
                                            "b": st.column_config.NumberColumn("b", min_value=0.05, max_value=1.5, format="%.2f")})
        novas = []
        for _, r in eda.iterrows():
            if not str(r.get("id") or "").strip():
                continue
            novas.append({"id": str(r["id"]).strip(), "nome": str(r["nome"] or ""), "entregavel": str(r["entregavel"] or ""),
                          "etapa": r["etapa"] or "calculo", "driver": (str(r["driver"]).strip() or None) if r["driver"] else None,
                          "b": float(r["b"] or 1.0),
                          "fixo": {p: float(r[f"fixo_{p}"]) for p in perfis if float(r[f"fixo_{p}"] or 0) > 0},
                          "unid": {p: float(r[f"unid_{p}"]) for p in perfis if float(r[f"unid_{p}"] or 0) > 0},
                          "fatores": [f.strip() for f in str(r["fatores"] or "").split(",") if f.strip()],
                          "calibracao": float(r["calibracao"] or 1.0)})
        S["atividades"] = novas
        st.markdown("**Custos diretos** (quantidade por expressão sobre o formulário)")
        dfd = pd.DataFrame(S.get("diretos") or [], columns=["id", "nome", "qtd", "valor_unit", "unid"])
        edd = st.data_editor(dfd, num_rows="dynamic", width="stretch", key=f"cat_dir_{sid}")
        S["diretos"] = [{"id": str(r["id"]), "nome": str(r["nome"]), "qtd": str(r["qtd"]), "valor_unit": float(r["valor_unit"] or 0),
                         "unid": str(r["unid"] or "un")} for _, r in edd.iterrows() if str(r.get("id") or "").strip()]
        with st.expander("Edição avançada (JSON do serviço: formulário, exclusões, premissas, normas)"):
            txt = st.text_area("JSON", json.dumps(S, ensure_ascii=False, indent=1), height=320, key=f"cat_json_{sid}")
            if st.button("Aplicar JSON"):
                try:
                    novo = json.loads(txt)
                    CAT["servicos"][ids.index(sid)] = novo
                    st.success("Aplicado (falta salvar).")
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON inválido: {e}")
        erros = ct.validar(CAT)
        if erros:
            st.error("Catálogo com problemas:\n- " + "\n- ".join(erros[:20]))
        c1, c2, c3 = st.columns(3)
        if c1.button("💾 Salvar catálogo", disabled=bool(erros), type="primary"):
            ct.salvar(CAT)
            st.success("Catálogo salvo (versão anterior em dados/catalogo.bak.json).")
        novo_id = c2.text_input("Novo id para duplicar", f"{sid}_copia", key=f"cat_dup_id_{sid}")
        if c2.button("Duplicar serviço"):
            if novo_id in ids:
                st.error("Esse id já existe.")
            else:
                cp = copy.deepcopy(S)
                cp["id"], cp["nome"] = novo_id, S["nome"] + " (cópia)"
                CAT["servicos"].append(cp)
                st.rerun()
        usados = {it["servico"] for o in P["opcoes"] for it in o["itens"]}
        if c3.button("Excluir serviço", disabled=sid in usados, help="Indisponível se o serviço está na proposta aberta"):
            CAT["servicos"].pop(ids.index(sid))
            st.rerun()
        if st.button("Recarregar catálogo do disco (descarta edições não salvas)"):
            ss.cat = ct.carregar()
            st.rerun()

    with sub[1]:
        PE = ss.params
        st.caption("Valores padrão para novas propostas. Cada proposta guarda a sua cópia.")
        dfe = pd.DataFrame([{"perfil": c, "nome": CAT["perfis"][c], "custo_h": PE["perfis"][c]["custo_h"],
                             "taxa_venda_h": PE["perfis"][c]["taxa_venda_h"]} for c in CAT["perfis"]])
        ede = st.data_editor(dfe, hide_index=True, disabled=["perfil", "nome"], key="emp_perfis",
                             column_config={"custo_h": st.column_config.NumberColumn("Custo/h (R$)", format="%.2f"),
                                            "taxa_venda_h": st.column_config.NumberColumn("Taxa de venda/h (R$)", format="%.2f")})
        for _, row in ede.iterrows():
            PE["perfis"][row["perfil"]] = {"custo_h": float(row["custo_h"]), "taxa_venda_h": float(row["taxa_venda_h"])}
        with st.container(border=True):
            st.markdown("**Calculadora de custo-hora**")
            c1, c2, c3, c4, c5 = st.columns(5)
            sal = c1.number_input("Salário / pró-labore (R$)", 0.0, 1e6, 8000.0, step=100.0, key="calc_sal")
            enc = c2.number_input("Encargos (%)", 0.0, 200.0, 70.0, step=1.0, key="calc_enc")
            ben = c3.number_input("Benefícios (R$/mês)", 0.0, 1e5, 1200.0, step=50.0, key="calc_ben")
            hp = c4.number_input("Horas produtivas/mês", 1.0, 400.0, 140.0, step=5.0, key="calc_h")
            custo = pm.custo_hora_calculado({"salario": sal, "encargos": enc / 100, "beneficios": ben, "horas_produtivas_mes": hp})
            c5.metric("Custo/h", moeda(custo))
            alvo = st.selectbox("Aplicar ao perfil", list(CAT["perfis"]), format_func=CAT["perfis"].get, key="calc_alvo")
            if st.button("Aplicar custo/h ao perfil"):
                PE["perfis"][alvo]["custo_h"] = round(custo, 2)
                st.rerun()
        c1, c2, c3 = st.columns(3)
        PE["margem"] = c1.number_input("Margem-alvo padrão (%)", 0.0, 80.0, PE["margem"] * 100, step=1.0, key="emp_margem") / 100
        PE["overhead"]["pct"] = c2.number_input("Overhead padrão (%)", 0.0, 200.0, PE["overhead"]["pct"] * 100, step=1.0,
                                                key="emp_ov") / 100
        PE["fee_pct_padrao"] = c3.number_input("% sobre obra padrão", 0.0, 100.0, PE["fee_pct_padrao"] * 100, step=0.5,
                                               key="emp_fee") / 100
        for nota in PE.get("notas", {}).values():
            st.caption(nota)
        c1, c2 = st.columns(2)
        if c1.button("💾 Salvar parâmetros da empresa", type="primary"):
            pm.salvar(PE)
            st.success("Parâmetros salvos em dados/parametros.json.")
        if c2.button("Aplicar à proposta aberta"):
            P["parametros"] = copy.deepcopy(PE)
            estrutura_mudou()

# ----------------------------------------------------------------------------- 8 calibração
with abas[7]:
    st.subheader("Calibração com horas realizadas")
    st.caption("Ao encerrar um projeto, registre as horas reais de cada atividade. O fator sugerido é a mediana de "
               "realizado ÷ estimado; aplicar grava o fator no catálogo e as próximas propostas já saem calibradas.")
    hist = cb.carregar()
    if R and R["linhas"]:
        dfr = pd.DataFrame([{"servico": l["servico_nome"], "atividade": l["nome"], "estimado_h": round(l["total_h"], 1),
                             "realizado_h": None} for l in R["linhas"]])
        edr = st.data_editor(dfr, hide_index=True, width="stretch", disabled=["servico", "atividade", "estimado_h"],
                             key=k("calib", O["id"]),
                             column_config={"realizado_h": st.column_config.NumberColumn("Realizado (h)", min_value=0.0)})
        if st.button(f"Registrar horas realizadas de '{O['nome']}'"):
            realizados = {i: float(v) for i, v in enumerate(edr["realizado_h"]) if pd.notna(v)}
            try:
                cb.registrar(hist, CAT, P, R, realizados)
                cb.salvar(hist)
                st.success(f"Registro salvo ({len(realizados)} atividades).")
            except ValueError as e:
                st.error(str(e))
    sug = cb.fatores_sugeridos(CAT, hist)
    st.markdown(f"**Histórico:** {len(hist)} registro(s).")
    if sug:
        st.dataframe(pd.DataFrame(sug), hide_index=True, width="stretch")
        minimo = st.number_input("Mínimo de amostras para aplicar", 1, 50, 2)
        if st.button("Aplicar fatores sugeridos ao catálogo e salvar"):
            n = cb.aplicar(CAT, sug, minimo)
            ct.salvar(CAT)
            st.success(f"{n} atividade(s) calibradas e catálogo salvo.")

# ----------------------------------------------------------------------------- consistência
# Entradas desenhadas depois do cálculo (pagamento, catálogo) mudam o resultado: recalcula uma vez.
if assinatura([P, CAT]) != ASSINATURA:
    ss["_reexec"] = ss.get("_reexec", 0) + 1
    if ss["_reexec"] <= 3:
        st.rerun()
else:
    ss["_reexec"] = 0
