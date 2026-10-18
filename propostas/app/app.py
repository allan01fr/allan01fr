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
from orcamento import exportar_docx, exportar_viabilidade, exportar_xlsx, motor
from orcamento import parametros as pm
from orcamento import viabilidade as vb
from orcamento import proposta as pp
from orcamento import referencias as rf

st.set_page_config(page_title="Propostas KAPTEK", page_icon="📐", layout="wide")

AZUL, COBRE, GRAFITE = "#1B3A5C", "#C18E6D", "#3E4448"
LOGO = os.path.join(RAIZ, "modelos", "logo-horizontal.png")
PASTA_EXEMPLOS = os.path.join(RAIZ, "exemplos")
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI",
       "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
RISCOS = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto"}
MODELOS = {"fechado": "Escopo fechado", "hora": "Hora técnica", "fee": "% sobre o valor da obra"}
MODALIDADES = {"servicos": "Serviços de engenharia (etapas avulsas)",
               "turnkey": "Turnkey — preço global, entrega do produto final em operação"}
ICONES_ETAPA = {"atendida": "✅", "faltando": "⚠️", "dispensada": "➖", "opcional": "○"}
CATEGORIAS = {"material": "Material", "equipamento": "Equipamento", "mo_execucao": "Mão de obra de execução",
              "subcontrato": "Subcontrato"}
moeda = exportar_docx.moeda


def md(texto):
    """Escapa o $ para o markdown do Streamlit não ler 'R$ ... R$' como fórmula LaTeX."""
    return str(texto).replace("$", "\\$")

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
abas = st.tabs(["1 · Dados gerais", "2 · Escopo", "3 · Fornecimentos e subcontratações", "4 · Preço",
                "5 · Prazo e pagamento", "6 · Exportar", "7 · Catálogo e parâmetros", "8 · Calibração",
                "9 · Viabilidade", "10 · Bases de referência"])

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
    O["modalidade"] = st.radio("Modalidade da proposta", list(MODALIDADES), horizontal=True,
                               index=list(MODALIDADES).index(O.get("modalidade", "servicos")),
                               format_func=MODALIDADES.get, key=k("modalidade", O["id"]),
                               help="Turnkey: assumimos todas as etapas e subcontratações e entregamos o sistema em "
                                    "operação, por preço global. O tipo de sistema (VRF, água gelada, VAV...) é "
                                    "definido no formulário de cada serviço.")
    if O["modalidade"] == "turnkey":
        with st.container(border=True):
            st.markdown("**Turnkey — etapas do produto final**")
            st.caption(CAT["turnkey"]["descricao"] + " Inclua cada etapa no escopo (serviços ou fornecimentos) "
                       "ou marque como fornecida pelo contratante.")
            dispensas = set(O.get("turnkey_dispensas", []))
            novas = []
            for e in motor.checklist_turnkey(CAT, O):
                c1, c2 = st.columns([3, 2])
                c1.markdown(f"{ICONES_ETAPA[e['status']]} {e['rotulo']}")
                if e["status"] == "atendida":
                    c2.caption("Incluída no escopo")
                elif c2.checkbox("A cargo do contratante", value=e["id"] in dispensas, key=k("disp", O["id"], e["id"])):
                    novas.append(e["id"])
            O["turnkey_dispensas"] = novas

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
                st.markdown(md(txt))
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
def base_referencias():
    """Conexão com o banco de referências (criado na primeira importação)."""
    if "con_ref" not in ss:
        ss.con_ref = rf.conectar()
    return ss.con_ref


with abas[2]:
    st.subheader(f"Fornecimentos e subcontratações — {O['nome']}")
    st.caption("Para turnkey e obra: equipamentos, materiais, mão de obra própria de execução e subcontratos "
               "(instalação mecânica, elétrica, isolamento, automação...). Cada categoria recebe o seu BDI "
               "(aba Preço → parâmetros). Busque preços nas bases (EMOP, SCO-Rio, SINAPI, cotações...) na aba 10.")
    colunas_f = ["uid", "descricao", "categoria", "unid", "qtd", "custo_unit", "fonte", "codigo", "data_base"]
    base = pd.DataFrame([{c: f.get(c, "") for c in colunas_f} for f in O["fornecimentos"]], columns=colunas_f)
    base = base.astype({"uid": str, "descricao": str, "categoria": str, "unid": str, "qtd": float, "custo_unit": float,
                        "fonte": str, "codigo": str, "data_base": str})
    ed = st.data_editor(
        base, num_rows="dynamic", width="stretch", key=k("forn", O["id"]),
        column_order=[c for c in colunas_f if c != "uid"],
        column_config={
            "descricao": st.column_config.TextColumn("Descrição", width="large"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=list(CATEGORIAS), required=True,
                                                          default="material"),
            "unid": st.column_config.TextColumn("Unid", default="un"),
            "qtd": st.column_config.NumberColumn("Qtd", min_value=0.0, default=1.0),
            "custo_unit": st.column_config.NumberColumn("Custo unitário (R$)", min_value=0.0, default=0.0, format="%.2f"),
            "fonte": st.column_config.TextColumn("Fonte"),
            "codigo": st.column_config.TextColumn("Código"),
            "data_base": st.column_config.TextColumn("Data-base (AAAA-MM)"),
        })
    antigos = {f["uid"]: f for f in O["fornecimentos"]}
    novos = []
    for _, row in ed.iterrows():
        if not str(row.get("descricao") or "").strip() or str(row.get("descricao")) == "nan":
            continue
        uid = row.get("uid") if isinstance(row.get("uid"), str) and row.get("uid") in antigos else None
        item = antigos.get(uid) or pp.novo_fornecimento()
        texto = lambda c: "" if pd.isna(row.get(c)) or str(row.get(c)) == "nan" else str(row.get(c))  # noqa: E731
        novos.append({**item, "descricao": str(row["descricao"]).strip(), "categoria": row.get("categoria") or "material",
                      "unid": texto("unid") or "un", "qtd": float(row.get("qtd") or 0),
                      "custo_unit": float(row.get("custo_unit") or 0), "fonte": texto("fonte"),
                      "codigo": texto("codigo"), "data_base": texto("data_base")})
    O["fornecimentos"] = novos
    c1, c2 = st.columns(2)
    O["prazo_fornecimento_dias"] = int(c1.number_input("Prazo de fornecimento dos equipamentos — lead time (dias úteis)",
                                                       0, 2000, int(O.get("prazo_fornecimento_dias") or 0),
                                                       key=k("prazo_forn", O["id"]),
                                                       help="Etapa 'Suprimentos' do cronograma, quando há equipamentos ou materiais."))
    O["prazo_execucao_dias"] = int(c2.number_input("Prazo de execução da obra/instalação (dias úteis)", 0, 2000,
                                                   int(O.get("prazo_execucao_dias") or 0), key=k("prazo_exec", O["id"]),
                                                   help="Usado no cronograma quando há fornecimentos."))

    if O["fornecimentos"]:
        with st.expander("Pesquisa de preços (cesta) por item"):
            cfg = P["parametros"]["cesta"]
            st.caption(f"Junte referências de várias fontes e cotações para o mesmo item. O valor adotado é a "
                       f"{cfg['criterio']} dos valores dentro de ±{cfg['faixa_alerta']:.0%} da mediana; recomenda-se no "
                       f"mínimo {cfg['minimo_fontes']} referências. Adicione itens das bases pela aba 10 → Buscar.")
            rot_f = {f["uid"]: f"{f['descricao']}  ({len(f.get('referencias', []))} ref.)" for f in O["fornecimentos"]}
            uid_sel = st.selectbox("Item", list(rot_f), format_func=rot_f.get, key=k("cesta_item", O["id"]))
            item = next(f for f in O["fornecimentos"] if f["uid"] == uid_sel)
            dref = pd.DataFrame(item.get("referencias", []), columns=["fonte", "codigo", "data_base", "valor"])
            dref = dref.astype({"fonte": str, "codigo": str, "data_base": str, "valor": float})
            edr = st.data_editor(dref, num_rows="dynamic", width="stretch", key=k("cesta_ref", O["id"], uid_sel),
                                 column_config={"fonte": st.column_config.TextColumn("Fonte / fornecedor"),
                                                "codigo": st.column_config.TextColumn("Código"),
                                                "data_base": st.column_config.TextColumn("Data-base (AAAA-MM)"),
                                                "valor": st.column_config.NumberColumn("Valor unitário (R$)", min_value=0.0, format="%.2f")})
            # o editor não mostra o fator de atualização gravado ao aplicar a cesta: preserva-o nas linhas inalteradas
            fatores = {(r["fonte"], r.get("codigo", ""), r.get("data_base", ""), float(r["valor"])): r["fator"]
                       for r in item.get("referencias", []) if r.get("fator")}
            item["referencias"] = []
            for _, r in edr.iterrows():
                if str(r.get("fonte") or "").strip() in ("", "nan") or not pd.notna(r["valor"]):
                    continue
                ref = {"fonte": str(r["fonte"]), "codigo": "" if str(r["codigo"]) == "nan" else str(r["codigo"]),
                       "data_base": "" if str(r["data_base"]) == "nan" else str(r["data_base"]), "valor": float(r["valor"])}
                fator = fatores.get((ref["fonte"], ref["codigo"], ref["data_base"], ref["valor"]))
                if fator:
                    ref["fator"] = fator
                item["referencias"].append(ref)
            c1, c2, c3 = st.columns(3)
            criterios = {"mediana": "Mediana", "media": "Média", "menor": "Menor valor"}
            crit = c1.selectbox("Critério", list(criterios), index=list(criterios).index(cfg["criterio"]),
                                format_func=criterios.get, key=k("cesta_crit", O["id"]))
            con = base_referencias()
            nomes_idx = [""] + [i["nome"] for i in rf.indices_disponiveis(con)]
            indice = c2.selectbox("Atualizar pelo índice", nomes_idx, key=k("cesta_idx", O["id"]),
                                  format_func=lambda n: n or "Não atualizar")
            alvo = c3.text_input("Data-alvo (AAAA-MM)", P["data"][:7], key=k("cesta_alvo", O["id"]))
            if item["referencias"]:
                res_c = rf.cesta(item["referencias"], crit, cfg["faixa_alerta"], cfg["minimo_fontes"], con, alvo, indice)
                st.dataframe(pd.DataFrame([{
                    "Fonte": l["fonte"], "Código": l.get("codigo", ""), "Data-base": l.get("data_base", ""),
                    "Valor": moeda(l["valor"]), "Atualizado": moeda(l["valor_atualizado"]),
                    "Desvio da mediana": pct(l["desvio"]), "Situação": "fora da faixa" if l["fora_da_faixa"] else "ok"}
                    for l in res_c["linhas"]]), hide_index=True, width="stretch")
                for a in res_c["avisos"]:
                    st.warning(a)
                st.markdown(md(f"**Valor adotado ({criterios[crit].lower()}): {moeda(res_c['valor'])}** · mediana "
                               f"{moeda(res_c['mediana'])} · média {moeda(res_c['media'])} · menor {moeda(res_c['menor'])}"))
                if st.button("Aplicar o valor adotado ao item", key=k("cesta_aplicar", O["id"])):
                    item["custo_unit"] = round(res_c["valor"], 2)
                    item["fonte"] = f"Cesta de preços ({criterios[crit].lower()} de {res_c['n_validos']} referências)"
                    item["codigo"] = ""
                    item["data_base"] = alvo if indice else max((l.get("data_base") or "" for l in res_c["linhas"]), default="")
                    for ref, l in zip(item["referencias"], res_c["linhas"]):
                        ref["fator"] = l["fator"] or 1.0
                    estrutura_mudou()

# ----------------------------------------------------------------------------- 4 preço (entradas antes do cálculo)
with abas[3]:
    topo_preco = st.container()
    with st.expander("Modelo de preço desta opção e parâmetros comerciais da proposta", expanded=False):
        c1, c2, c3 = st.columns(3)
        mods = list(MODELOS)
        if O.get("modalidade") == "turnkey":
            O["modelo_preco"] = "fechado"
            c1.info("Turnkey: a proposta usa sempre o preço global (escopo fechado). Hora técnica e % sobre obra "
                    "aparecem só como referência.")
        else:
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
            PR["perfis"][row["perfil"]] = {**PR["perfis"][row["perfil"]], "custo_h": float(row["custo_h"]),
                                           "taxa_venda_h": float(row["taxa_venda_h"])}
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
        modos_art = {"faixas": "Por faixa do valor do contrato (Tabela A do Confea)", "fixo": "Valor fixo"}
        PR["art"]["modo"] = c1.selectbox("Taxa de ART", list(modos_art), format_func=modos_art.get,
                                         index=list(modos_art).index(PR["art"].get("modo", "fixo")), key=k("p_art_modo"))
        if PR["art"]["modo"] == "fixo":
            PR["art"]["valor"] = c1.number_input("Valor da ART (R$)", 0.0, 10000.0, float(PR["art"]["valor"]), step=10.0, key=k("p_art"))
        else:
            c1.caption(md("Faixas: " + " · ".join(
                (f"até {moeda(f['ate'])}" if f.get("ate") else "acima") + f" = {moeda(f['valor'])}" for f in PR["art"]["faixas"])
                + f". {PR['art'].get('fonte', '')} Edite na aba 10."))
        PR["cronograma"]["equipe"] = int(c2.number_input("Equipe por etapa (pessoas)", 1, 20, int(PR["cronograma"]["equipe"]), key=k("p_eq")))
        PR["pagamento"]["sinal"] = c3.number_input("Sinal na assinatura (%)", 0.0, 100.0, PR["pagamento"]["sinal"] * 100,
                                                   step=5.0, key=k("p_sinal")) / 100
        c1, c2, c3, c4 = st.columns(4)
        PR["turnkey"]["garantia_pct"] = c1.number_input("Turnkey: provisão de garantia (% do custo de fornecimento)", 0.0, 20.0,
                                                        PR["turnkey"]["garantia_pct"] * 100, step=0.5, key=k("p_gar")) / 100
        PR["turnkey"]["garantia_meses"] = int(c2.number_input("Turnkey: garantia (meses)", 0, 120,
                                                              int(PR["turnkey"]["garantia_meses"]), key=k("p_gar_m")))
        PR["turnkey"]["retencao_aceite"] = c2.number_input(
            "Turnkey: parcela mínima no aceite (%)", 0.0, 50.0, PR["turnkey"].get("retencao_aceite", 0.10) * 100, step=5.0,
            key=k("p_ret"), help="Retida até o comissionamento e o termo de aceite.") / 100
        PR["cub"]["valor"] = c3.number_input(f"CUB/m² {PR['cub'].get('padrao', '')} (R$) — 0 = sem referência", 0.0, 1e5,
                                             float(PR["cub"].get("valor") or 0), step=10.0, key=k("p_cub"),
                                             help="Importe ou consulte na aba 10 (SINDUSCON / CBIC).")
        PR["cub"]["pct_honorarios"] = c4.number_input("% do CUB × área (referência de honorários)", 0.0, 30.0,
                                                      float(PR["cub"].get("pct_honorarios") or 0) * 100, step=0.5,
                                                      key=k("p_cub_pct")) / 100
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
        ("Referência: % do CUB × área", lambda r: moeda(r["ref_cub"]) if r.get("ref_cub") else "—"),
        ("Modalidade", lambda r: "Turnkey" if r["modalidade"] == "turnkey" else "Serviços"),
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
            c1.metric("Preço global (turnkey)" if R["modalidade"] == "turnkey" else "Escopo fechado",
                      moeda(R["preco_fechado"]))
            c2.metric("Hora técnica (estimado)", moeda(R["preco_hora"]), help=f"Teto: {moeda(R['preco_hora_teto'])}")
            c3.metric("% sobre obra", moeda(R["preco_fee"]) if R["preco_fee"] is not None else "sem base")
            c4.metric("Preço mínimo (margem zero)", moeda(R["preco_minimo_servicos"]))
            c5.metric("Margem efetiva (fechado)", pct(R["margem_efetiva"]["fechado"]))
            st.caption(md(f"Modelo usado na proposta: **{MODELOS[R['modelo_preco']]}** → {moeda(R['preco'])}. "
                       f"{num_br(R['total_h'])} h · {R['prazo_dias_corridos']} dias corridos · "
                       f"{R['dias_campo']} dia(s) de campo · ART {moeda(R['art'])}."
                       + (f" Referência pelo CUB: {moeda(R['ref_cub'])}." if R.get("ref_cub") else "")))
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
            c1.success(md("Parcelas somam 100%. " + " · ".join(f"{pct(m['pct'])}: {moeda(m['pct'] * R['preco'])}" for m in novos)))
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
            PE["perfis"][row["perfil"]] = {**PE["perfis"][row["perfil"]], "custo_h": float(row["custo_h"]),
                                           "taxa_venda_h": float(row["taxa_venda_h"])}
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

# ----------------------------------------------------------------------------- 9 viabilidade
def anos_txt(v):
    return "> horizonte" if v is None else f"{num_br(v, 1)} anos"


with abas[8]:
    VB = P["viabilidade"]
    st.subheader("Estudo de viabilidade — payback, breakeven, VPL e TIR")
    st.caption("Compara alternativas de intervenção com o sistema atual e com o projeto original. O CAPEX de uma "
               "alternativa pode vir do preço de uma opção desta proposta (por exemplo, o turnkey) mais um extra.")
    VB["titulo"] = st.text_input("Título do estudo", VB["titulo"], key=k("v_tit"))
    b, fin = VB["base"], VB["financeiro"]
    with st.container(border=True):
        st.markdown("**Sistema atual (linha de base)**")
        modos_b = {"tr": "Pela capacidade: TR × kW/TR × horas × fator de carga", "kwh": "Pelo consumo anual medido (kWh)"}
        b["modo"] = st.radio("Linha de base", list(modos_b), horizontal=True, index=list(modos_b).index(b["modo"]),
                             format_func=modos_b.get, key=k("v_modo"))
        c = st.columns(5)
        if b["modo"] == "tr":
            b["tr"] = c[0].number_input("Capacidade (TR)", 0.0, 1e5, float(b["tr"]), step=5.0, key=k("v_tr"))
            b["kw_tr_real"] = c[1].number_input("kW/TR medido", 0.0, 10.0, float(b["kw_tr_real"]), step=0.05, key=k("v_kwr"))
            b["kw_tr_projeto"] = c[2].number_input("kW/TR de projeto", 0.0, 10.0, float(b["kw_tr_projeto"]), step=0.05,
                                                   key=k("v_kwp"), help="Estimativa do projeto original; 0 = não comparar.")
            b["horas_ano"] = c[3].number_input("Horas de operação/ano", 0.0, 8760.0, float(b["horas_ano"]), step=100.0, key=k("v_h"))
            b["fator_carga"] = c[4].number_input("Fator de carga médio", 0.0, 1.0, float(b["fator_carga"]), step=0.05, key=k("v_fc"))
        else:
            b["kwh_ano"] = c[0].number_input("Consumo anual (kWh)", 0.0, 1e9, float(b["kwh_ano"]), step=1000.0, key=k("v_kwh"))
        c = st.columns(3)
        b["tarifa"] = c[0].number_input("Tarifa média (R$/kWh)", 0.0, 10.0, float(b["tarifa"]), step=0.01, key=k("v_tar"),
                                        help="Faturas do cliente ou tarifa homologada pela ANEEL com tributos.")
        b["manutencao_ano"] = c[1].number_input("Manutenção atual (R$/ano)", 0.0, 1e9, float(b["manutencao_ano"]),
                                                step=1000.0, key=k("v_man"))
        b["paliativos"] = c[2].number_input("Paliativos / manutenção de emergência (R$)", 0.0, 1e9,
                                            float(b.get("paliativos") or 0), step=1000.0, key=k("v_pal"),
                                            help="Comuns a todas as alternativas: entram no LCC, não no fluxo incremental.")
    c = st.columns(4)
    fin["tma"] = c[0].number_input("TMA (% a.a.)", 0.0, 100.0, fin["tma"] * 100, step=0.5, key=k("v_tma")) / 100
    fin["horizonte"] = int(c[1].number_input("Horizonte (anos)", 1, vb.HORIZONTE_MAX, int(fin["horizonte"]), key=k("v_hz")))
    fin["reajuste_energia"] = c[2].number_input("Reajuste da energia (% a.a.)", -20.0, 50.0, fin["reajuste_energia"] * 100,
                                                step=0.5, key=k("v_ge")) / 100
    fin["reajuste_manutencao"] = c[3].number_input("Reajuste da manutenção (% a.a.)", -20.0, 50.0,
                                                   fin["reajuste_manutencao"] * 100, step=0.5, key=k("v_gm")) / 100
    st.markdown("**Alternativas**")
    ids_op = ["—"] + [o["id"] for o in P["opcoes"]]     # "—" = usar o CAPEX informado
    dfa = pd.DataFrame([{"nome": a["nome"], "descricao": a.get("descricao", ""), "capex": float(a.get("capex") or 0),
                         "capex_opcao": a.get("capex_opcao") or "—", "capex_extra": float(a.get("capex_extra") or 0),
                         "reducao_pct": float(a.get("reducao_pct") or 0) * 100, "geracao_kwh": float(a.get("geracao_kwh") or 0),
                         "manutencao_ano": a.get("manutencao_ano")} for a in VB["alternativas"]],
                       columns=["nome", "descricao", "capex", "capex_opcao", "capex_extra", "reducao_pct", "geracao_kwh",
                                "manutencao_ano"])
    dfa = dfa.astype({"nome": str, "descricao": str, "capex": float, "capex_opcao": str, "capex_extra": float,
                      "reducao_pct": float, "geracao_kwh": float, "manutencao_ano": float})
    eda = st.data_editor(dfa, num_rows="dynamic", width="stretch", key=k("v_alts"), column_config={
        "nome": st.column_config.TextColumn("Alternativa", width="medium"),
        "descricao": st.column_config.TextColumn("Descrição", width="large"),
        "capex": st.column_config.NumberColumn("CAPEX (R$)", min_value=0.0, format="%.2f",
                                               help="Ignorado quando a alternativa está vinculada a uma opção da proposta"),
        "capex_opcao": st.column_config.SelectboxColumn("CAPEX = preço da opção", options=ids_op,
                                                         help="— = usar o CAPEX informado"),
        "capex_extra": st.column_config.NumberColumn("Extra sobre a opção (R$)", min_value=0.0, format="%.2f"),
        "reducao_pct": st.column_config.NumberColumn("Redução de consumo (%)", min_value=0.0, max_value=100.0, format="%.1f"),
        "geracao_kwh": st.column_config.NumberColumn("Geração FV (kWh/ano)", min_value=0.0, format="%.0f"),
        "manutencao_ano": st.column_config.NumberColumn("Manutenção (R$/ano) — vazio = igual à atual", min_value=0.0,
                                                        format="%.2f"),
    })
    VB["alternativas"] = [{
        "nome": str(r["nome"]).strip(), "descricao": str(r.get("descricao") or "") if pd.notna(r.get("descricao")) else "",
        "capex": float(r["capex"]) if pd.notna(r["capex"]) else 0.0,
        "capex_opcao": r["capex_opcao"] if isinstance(r["capex_opcao"], str) and r["capex_opcao"] in ids_op[1:] else "",
        "capex_extra": float(r["capex_extra"]) if pd.notna(r["capex_extra"]) else 0.0,
        "reducao_pct": float(r["reducao_pct"]) / 100 if pd.notna(r["reducao_pct"]) else 0.0,
        "geracao_kwh": float(r["geracao_kwh"]) if pd.notna(r["geracao_kwh"]) else 0.0,
        "manutencao_ano": float(r["manutencao_ano"]) if pd.notna(r["manutencao_ano"]) else None,
    } for _, r in eda.iterrows() if str(r.get("nome") or "").strip() and str(r.get("nome")) != "nan"]
    VB["ativo"] = bool(VB["alternativas"])
    if VB["alternativas"]:
        EST = vb.calcular(VB, {r["id"]: r["preco"] for r in RES["opcoes"]} if RES else None)
        c = st.columns(4)
        c[0].metric("Consumo atual (kWh/ano)", num_br(EST["consumo_base"], 0))
        if EST["consumo_projeto"]:
            c[1].metric("Previsto no projeto original (kWh/ano)", num_br(EST["consumo_projeto"], 0),
                        delta=f"{pct(EST['excesso_vs_projeto'])} acima", delta_color="inverse")
            c[2].metric("Custo anual da perda de desempenho", moeda(EST["perda_desempenho"]))
        c[3].metric("Custo anual de energia atual", moeda(EST["custo_energia_base"]))
        st.dataframe(pd.DataFrame([{
            "Alternativa": a["nome"], "CAPEX": moeda(a["capex"]), "Origem do CAPEX": a["capex_origem"],
            "Economia ano 1": moeda(a["economia_ano1"]), "VPL": moeda(a["vpl"]),
            "TIR": pct(a["tir"]), "Payback": anos_txt(a["payback"]),
            "Breakeven econômico": anos_txt(a["payback_descontado"]) + (f" ({a['breakeven_meses']} meses)" if a["breakeven_meses"] else ""),
            "Economia mínima (VPL = 0)": moeda(a["economia_minima"]) if a["economia_minima"] else "—",
            "LCC": moeda(a["lcc"]), "Consumo × projeto": pct(a["vs_projeto"]), "Classificação": a["classificacao"],
        } for a in EST["alternativas"]]), hide_index=True, width="stretch")
        dfl = pd.DataFrame([{"Ano": t, "Alternativa": a["nome"], "Acumulado": sum(a["fluxo"][:t + 1])}
                            for a in EST["alternativas"] for t in range(len(a["fluxo"]))])
        linhas = alt.Chart(dfl).mark_line(point=True).encode(
            x=alt.X("Ano:Q", axis=alt.Axis(format="d", tickMinStep=1)),
            y=alt.Y("Acumulado:Q", title="Fluxo acumulado (R$)", axis=alt.Axis(format="~s")),
            color=alt.Color("Alternativa:N", legend=alt.Legend(orient="bottom")),
            tooltip=["Alternativa", "Ano", alt.Tooltip("Acumulado:Q", format=",.0f")])
        zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=COBRE).encode(y="y:Q")
        st.altair_chart((linhas + zero).properties(height=320), width="stretch")
        st.markdown("**Sensibilidade do VPL**")
        for titulo, chave in (("Variação da economia anual", "economia"), ("Variação do CAPEX", "capex"),
                              ("Variação da tarifa de energia", "tarifa")):
            st.caption(titulo)
            st.dataframe(pd.DataFrame([{"Alternativa": a["nome"], **{f"{d:+.0%}": moeda(v) for d, v in a["sensibilidade"][chave].items()}}
                                        for a in EST["alternativas"]]), hide_index=True, width="stretch")
        if st.button("Gerar planilha do estudo (.xlsx)"):
            ss.arquivo_viab = (exportar_viabilidade.gerar(P, EST), assinatura([P, CAT]))
        if ss.get("arquivo_viab") and ss.arquivo_viab[1] == assinatura([P, CAT]):
            st.download_button("📈 Baixar estudo de viabilidade", ss.arquivo_viab[0],
                               file_name=f"KAPTEK-viabilidade-{exportar_docx.slug(P['cliente'].get('razao'))}-{exportar_docx.slug(P['numero'])}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Adicione alternativas na tabela acima (nome, CAPEX ou opção vinculada, redução de consumo, manutenção).")

# ----------------------------------------------------------------------------- 10 bases de referência
TIPOS_IMPORT = {
    "precos": ("Preços de insumos e serviços (EMOP, SCO-Rio, SINAPI, ABRAVA...)", {"codigo": "Código", "descricao": "Descrição",
                                                                                   "unidade": "Unidade", "valor": "Preço / custo"}),
    "pisos": ("Pisos de convenção coletiva (SENGE, SINDRATAR, SINDISTAL, SINDUSCON...)", {"descricao": "Função / cargo",
                                                                                        "valor": "Piso mensal (R$)"}),
    "cub": ("CUB/m² (SINDUSCON / CBIC)", {"descricao": "Padrão (R8-N, CSL-8N...)", "valor": "CUB (R$/m²)"}),
    "indices": ("Índice de reajuste (INCC, IPCA, IGP-M)", {"codigo": "Mês", "valor": "Número-índice"}),
}

with abas[9]:
    con = base_referencias()
    registro = rf.carregar_fontes()
    st.subheader("Bases de referência e convenções coletivas")
    st.caption(registro["nota"])
    sub = st.tabs(["Entidades", "Importar", "Buscar itens", "Convenções e pisos → custo/h", "CUB", "ART", "Índices"])

    with sub[0]:
        st.info(registro["hierarquia_rj"])
        st.dataframe(pd.DataFrame(registro["entidades"])[["grupo", "id", "nome", "abrangencia", "fornece", "periodicidade",
                                                          "formato", "url", "verificado"]],
                     hide_index=True, width="stretch",
                     column_config={"grupo": "Grupo", "id": "Código", "nome": "Entidade", "abrangencia": "Abrangência",
                                    "fornece": "O que fornece", "periodicidade": "Periodicidade", "formato": "Formato",
                                    "url": st.column_config.LinkColumn("Onde obter"),
                                    "verificado": st.column_config.CheckboxColumn("Endereço verificado")})
        imp = rf.fontes_importadas(con)
        st.markdown("**Bases importadas**")
        if imp:
            st.dataframe(pd.DataFrame(imp), hide_index=True, width="stretch",
                         column_config={"fonte": "Fonte", "uf": "UF", "data_base": "Data-base", "itens": "Itens",
                                        "importado_em": "Importado em"})
        else:
            st.caption("Nenhuma base importada ainda.")

    with sub[1]:
        tipo_imp = st.radio("O que importar", list(TIPOS_IMPORT), format_func=lambda t: TIPOS_IMPORT[t][0], key="imp_tipo")
        arq_imp = st.file_uploader("Arquivo da entidade (XLSX, CSV ou PDF)", type=["xlsx", "xlsm", "csv", "txt", "pdf"], key="imp_arq")
        if arq_imp is not None:
            dados_arq = arq_imp.getvalue()
            info = rf.info_do_nome(arq_imp.name)
            aba_sel = None
            if arq_imp.name.lower().endswith((".xlsx", ".xlsm")):
                abas_arq = rf.abas_xlsx(dados_arq)
                aba_sel = st.selectbox("Aba da planilha", abas_arq, key="imp_aba") if len(abas_arq) > 1 else abas_arq[0]
            preset = "Genérico"
            if tipo_imp == "precos":
                preset = st.selectbox("Preset de importação", list(rf.PRESETS), key="imp_preset",
                                      index=next((i for i, p_ in enumerate(rf.PRESETS) if p_.lower().split("-")[0] in arq_imp.name.lower()), len(rf.PRESETS) - 1))
            try:
                linhas_arq = rf.ler_tabela(dados_arq, arq_imp.name, aba_sel)
            except Exception as e:  # noqa: BLE001
                linhas_arq = []
                st.error(f"Não foi possível ler o arquivo: {e}")
            if linhas_arq:
                largura = max(len(r_) for r_ in linhas_arq)
                grade = pd.DataFrame([list(r_) + [None] * (largura - len(r_)) for r_ in linhas_arq],
                                     columns=[f"C{j + 1}" for j in range(largura)]).astype(str).replace({"None": "", "nan": ""})
                if arq_imp.name.lower().endswith(".pdf"):
                    st.warning("Tabelas extraídas do PDF: confira e corrija a grade antes de importar (layout de PDF varia).")
                    grade = st.data_editor(grade, num_rows="dynamic", width="stretch", key="imp_grade")
                    revisado = st.checkbox("Revisei a extração do PDF", key="imp_revisado")
                else:
                    st.dataframe(grade.head(40), width="stretch")
                    revisado = True
                linhas_arq = grade.values.tolist()
                ini_cab, mapa = rf.detectar_cabecalho(linhas_arq, preset)
                cols_opc = [None] + list(range(largura))
                c = st.columns(5)
                ini_cab = int(c[0].number_input("Linha do cabeçalho (0 = primeira)", 0, max(len(linhas_arq) - 1, 0),
                                                int(ini_cab or 0), key="imp_cab"))
                cab = linhas_arq[ini_cab] if linhas_arq else []
                rot_col = {j: (f"C{j + 1} · {cab[j]}"[:40] if j is not None and j < len(cab) else "—") for j in cols_opc}
                mapa_final = {}
                for col_ui, (campo, rotulo) in zip(c[1:], TIPOS_IMPORT[tipo_imp][1].items()):
                    padrao_j = mapa.get(campo)
                    mapa_final[campo] = col_ui.selectbox(rotulo, cols_opc, index=cols_opc.index(padrao_j) if padrao_j in cols_opc else 0,
                                                         format_func=lambda j: rot_col.get(j, "—"), key=f"imp_map_{campo}")
                c = st.columns(4)
                fontes_ids = [e["id"] for e in registro["entidades"]]
                if tipo_imp == "precos":
                    fonte_imp = c[0].text_input("Fonte", preset if preset != "Genérico" else "", key="imp_fonte")
                elif tipo_imp == "pisos":
                    fonte_imp = c[0].selectbox("Entidade", fontes_ids, key="imp_ent",
                                               index=fontes_ids.index("SENGE-RJ") if "SENGE-RJ" in fontes_ids else 0)
                elif tipo_imp == "cub":
                    fonte_imp = c[0].text_input("Fonte", "SINDUSCON-Rio", key="imp_fonte_cub")
                else:
                    fonte_imp = c[0].text_input("Nome do índice", "INCC-M", key="imp_idx_nome")
                uf_imp = c[1].text_input("UF", info["uf"] or P["cliente"].get("uf", "RJ"), key="imp_uf")
                db_imp = c[2].text_input("Data-base (AAAA-MM)", info["data_base"], key="imp_db")
                extra_imp = c[3].text_input("Convenção (nome / registro no MTE)" if tipo_imp == "pisos" else "Observação", "",
                                            key="imp_extra")
                deson = st.checkbox("Desonerado", value=bool(info["desonerado"]), key="imp_deson") if tipo_imp == "precos" else None
                itens_imp = rf.extrair_itens(linhas_arq, ini_cab, {k_: v_ for k_, v_ in mapa_final.items() if v_ is not None}) \
                    if mapa_final.get("valor") is not None and (mapa_final.get("descricao") is not None or mapa_final.get("codigo") is not None) else []
                if tipo_imp == "indices":
                    itens_imp = [{"mes": rf.converter_mes(r_[mapa_final["codigo"]]), "valor": rf.converter_valor(r_[mapa_final["valor"]])}
                                 for r_ in linhas_arq[ini_cab + 1:] if mapa_final.get("codigo") is not None and mapa_final.get("valor") is not None
                                 and rf.converter_mes(r_[mapa_final["codigo"]]) and rf.converter_valor(r_[mapa_final["valor"]]) is not None]
                st.caption(f"{len(itens_imp)} registro(s) reconhecido(s).")
                if itens_imp:
                    st.dataframe(pd.DataFrame(itens_imp).head(10), hide_index=True, width="stretch")
                pronto_imp = bool(itens_imp) and revisado and bool(fonte_imp)
                if st.button(f"Importar {len(itens_imp)} registro(s)", type="primary", disabled=not pronto_imp, key="imp_ok"):
                    if tipo_imp == "precos":
                        n_imp = rf.importar_itens(con, itens_imp, fonte_imp, db_imp, uf_imp, deson,
                                                  rf.PRESETS[preset]["tipo"], arq_imp.name)
                    elif tipo_imp == "pisos":
                        n_imp = rf.importar_pisos(con, [{"funcao": i["descricao"], "piso": i["valor"]} for i in itens_imp],
                                                  fonte_imp, extra_imp, db_imp, uf_imp)
                    elif tipo_imp == "cub":
                        n_imp = rf.importar_cub(con, [{"fonte": fonte_imp, "uf": uf_imp, "padrao": i["descricao"], "mes": db_imp,
                                                       "valor": i["valor"]} for i in itens_imp])
                    else:
                        n_imp = rf.importar_indices(con, fonte_imp, [(i["mes"], i["valor"]) for i in itens_imp])
                    st.success(f"{n_imp} registro(s) importado(s).")

    with sub[2]:
        imp = rf.fontes_importadas(con)
        if not imp:
            st.info("Importe pelo menos uma base de preços (aba Importar) para buscar.")
        else:
            c = st.columns([3, 1, 2])
            termo = c[0].text_input("Buscar por código ou descrição", key="busca_termo")
            uf_b = c[1].text_input("UF", P["cliente"].get("uf", "RJ"), key="busca_uf")
            fontes_b = c[2].multiselect("Fontes", sorted({i["fonte"] for i in imp}), key="busca_fontes")
            hier = P["parametros"]["hierarquia_fontes"]
            ordem = rf.ordem_hierarquia(hier, uf_b)
            with st.expander(f"Prioridade das fontes para {uf_b}"):
                txt_h = st.text_input("Fontes em ordem de prioridade, separadas por vírgula", ", ".join(ordem),
                                      key=k("hier", uf_b), help="RJ (Decreto 48.929/2024): EMOP-RJ, SCO-RIO, SINAPI, SICRO. "
                                                                "Em obra do município do Rio, ponha o SCO-RIO primeiro.")
                nova_h = [x.strip() for x in txt_h.split(",") if x.strip()]
                if nova_h != ordem:
                    hier[uf_b] = nova_h
                    ordem = rf.ordem_hierarquia(hier, uf_b)
                if st.button("Salvar como padrão da empresa", key="hier_salvar"):
                    ss.params.setdefault("hierarquia_fontes", {})[uf_b] = nova_h
                    pm.salvar(ss.params)
                    st.success(f"Prioridade de {uf_b} salva nos parâmetros da empresa.")
            if ordem:
                st.caption("Prioridade das fontes para " + uf_b + ": " + " → ".join(ordem))
            if termo:
                achados = rf.buscar(con, termo, uf_b, fontes_b or None, P["parametros"]["hierarquia_fontes"])
                dfb = pd.DataFrame([{"fonte": a["fonte"], "codigo": a["codigo"], "descricao": a["descricao"], "unidade": a["unidade"],
                                     "valor": a["valor"], "data_base": a["data_base"], "uf": a["uf"]} for a in achados])
                if dfb.empty:
                    st.info("Nada encontrado.")
                else:
                    sel = st.dataframe(dfb, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row",
                                       key="busca_res", column_config={
                                           "fonte": "Fonte", "codigo": "Código", "descricao": "Descrição", "unidade": "Unid.",
                                           "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
                                           "data_base": "Data-base", "uf": "UF"})
                    linhas_sel = [achados[i] for i in sel.selection.rows] if sel and sel.selection else []
                    c = st.columns([2, 1, 1])
                    alvos = {"__novo__": "Criar novo fornecimento"} | {f["uid"]: f["descricao"] for f in O["fornecimentos"]}
                    alvo_uid = c[0].selectbox(f"Destino em '{O['nome']}'", list(alvos), format_func=alvos.get, key="busca_alvo")
                    cat_novo = c[1].selectbox("Categoria (novo)", list(CATEGORIAS), format_func=CATEGORIAS.get, key="busca_cat")
                    if c[2].button(f"Usar {len(linhas_sel)} selecionado(s)", disabled=not linhas_sel, key="busca_usar"):
                        refs = [{"fonte": a["fonte"], "codigo": a["codigo"], "data_base": a["data_base"], "valor": a["valor"]}
                                for a in linhas_sel]
                        if alvo_uid == "__novo__":
                            a0 = linhas_sel[0]
                            novo_f = pp.novo_fornecimento(a0["descricao"], cat_novo, a0["unidade"] or "un", 1.0, a0["valor"],
                                                          a0["fonte"], a0["codigo"], a0["data_base"])
                            novo_f["referencias"] = refs
                            O["fornecimentos"].append(novo_f)
                        else:
                            destino = next(f for f in O["fornecimentos"] if f["uid"] == alvo_uid)
                            destino.setdefault("referencias", []).extend(refs)
                        estrutura_mudou()

    with sub[3]:
        st.caption("Custo/h = (piso × (1 + adicionais) × (1 + encargos sociais) + benefícios) ÷ horas produtivas. "
                   "Use os encargos sociais do SINAPI para a UF e os benefícios previstos na convenção.")
        pisos = rf.listar_pisos(con)
        piso_base, origem = 0.0, {}
        modo_piso = st.radio("Piso de referência", ["Convenção importada", "Engenheiro — Lei 4.950-A", "Informar"],
                             horizontal=True, key="piso_modo")
        if modo_piso == "Convenção importada":
            if not pisos:
                st.info("Importe os pisos de uma convenção (aba Importar → Pisos).")
            else:
                rot_p = {p_["id"]: f"{p_['entidade']} · {p_['funcao']} · {moeda(p_['piso'])} ({p_['data_base']})" for p_ in pisos}
                pid = st.selectbox("Função", list(rot_p), format_func=rot_p.get, key="piso_sel")
                pz = next(p_ for p_ in pisos if p_["id"] == pid)
                piso_base = pz["piso"]
                origem = {"fonte": pz["entidade"], "convencao": pz["cct"], "funcao": pz["funcao"], "data_base": pz["data_base"]}
        elif modo_piso == "Engenheiro — Lei 4.950-A":
            c = st.columns(3)
            base_sm = c[0].radio("Base de cálculo", ["Salário mínimo vigente", "Base fixada pelo STF (R$ 1.212) + reajuste"],
                                 key="piso_base")
            if base_sm == "Salário mínimo vigente":
                sm = c[1].number_input("Salário mínimo (R$)", 0.0, 1e5, rf.SALARIO_MINIMO_2026, step=1.0, key="piso_sm",
                                       help="R$ 1.621,00 em 2026 (Decreto 12.797/2025).")
            else:
                reaj = c[1].number_input("Reajuste acumulado negociado (%)", 0.0, 500.0, 0.0, step=0.5, key="piso_reaj")
                sm = rf.BASE_CONGELADA_STF * (1 + reaj / 100)
            horas_dia = c[2].selectbox("Jornada diária (h)", [6, 7, 8], index=2, key="piso_jornada")
            piso_base = rf.piso_lei_4950a(sm, horas_dia)
            st.caption(md(f"Piso: {moeda(piso_base)} ({num_br(6 + 1.25 * (horas_dia - 6), 1)} × {moeda(sm)}). O STF (ADPF 53, 149 e 171) "
                       "vedou a indexação ao salário mínimo e fixou a base em R$ 1.212; confira a convenção do SENGE-RJ vigente."))
            origem = {"fonte": "Lei 4.950-A/1966", "funcao": f"Engenheiro — {horas_dia} h/dia", "base": base_sm}
        else:
            piso_base = st.number_input("Piso mensal (R$)", 0.0, 1e6, 5000.0, step=100.0, key="piso_manual")
            origem = {"fonte": "informado"}
        c = st.columns(4)
        adic = c[0].number_input("Adicionais (%)", 0.0, 200.0, 0.0, step=5.0, key="piso_adic",
                                 help="Periculosidade 30%, insalubridade, adicional de função...") / 100
        enc_sinapi = rf.encargos(con, P["cliente"].get("uf", "RJ"))
        enc = c[1].number_input("Encargos sociais (%)", 0.0, 300.0, float(enc_sinapi * 100) if enc_sinapi else 70.0, step=1.0,
                                key="piso_enc", help="Encargos do SINAPI para a UF (mensalista) quando importados.") / 100
        benef = c[2].number_input("Benefícios (R$/mês)", 0.0, 1e5, 1200.0, step=50.0, key="piso_benef",
                                  help="Vale-refeição, transporte, plano de saúde da convenção.")
        horas_prod = c[3].number_input("Horas produtivas/mês", 1.0, 400.0, 140.0, step=5.0, key="piso_horas")
        custo_piso = rf.custo_hora_piso(piso_base, adic, enc, benef, horas_prod)
        st.metric("Custo/h resultante", moeda(custo_piso))
        c = st.columns([2, 1, 1, 2])
        perfil_alvo = c[0].selectbox("Aplicar ao perfil", list(CAT["perfis"]), format_func=CAT["perfis"].get, key="piso_perfil")
        orig_full = {**origem, "piso": piso_base, "adicional": adic, "encargos": enc, "beneficios": benef, "horas": horas_prod}
        if c[1].button("Nesta proposta", disabled=custo_piso <= 0, key="piso_apl_prop"):
            P["parametros"]["perfis"][perfil_alvo].update({"custo_h": round(custo_piso, 2), "origem": orig_full})
            estrutura_mudou()
        if c[2].button("Na empresa (salva)", disabled=custo_piso <= 0, key="piso_apl_emp"):
            ss.params["perfis"][perfil_alvo].update({"custo_h": round(custo_piso, 2), "origem": orig_full})
            pm.salvar(ss.params)
            st.success("Custo/h salvo nos parâmetros da empresa.")
        if c[3].button("Criar item de mão de obra de execução (h)", disabled=custo_piso <= 0, key="piso_mo"):
            O["fornecimentos"].append(pp.novo_fornecimento(f"Mão de obra — {origem.get('funcao', 'equipe própria')}",
                                                           "mo_execucao", "h", 0.0, round(custo_piso, 2),
                                                           origem.get("fonte", ""), "", origem.get("data_base", "")))
            estrutura_mudou()
        with st.expander("Encargos sociais por UF (SINAPI)"):
            c = st.columns(5)
            e_uf = c[0].text_input("UF", P["cliente"].get("uf", "RJ"), key="enc_uf")
            e_reg = c[1].selectbox("Regime", ["mensalista", "horista"], key="enc_reg")
            e_des = c[2].checkbox("Desonerado", key="enc_des")
            e_pct = c[3].number_input("Encargos (%)", 0.0, 300.0, 70.0, step=0.1, key="enc_pct")
            e_db = c[4].text_input("Data-base", P["data"][:7], key="enc_db")
            if st.button("Gravar encargos", key="enc_ok"):
                rf.importar_encargos(con, [{"uf": e_uf, "regime": e_reg, "desonerado": e_des, "pct": e_pct / 100, "data_base": e_db}])
                st.success("Encargos gravados.")

    with sub[4]:
        cubs = rf.listar_cub(con)
        if cubs:
            rot_c = {c_["id"]: f"{c_['fonte']} · {c_['uf']} · {c_['padrao']} · {c_['mes']} · {moeda(c_['valor'])}" for c_ in cubs}
            cid = st.selectbox("CUB importado", list(rot_c), format_func=rot_c.get, key="cub_sel")
            if st.button("Usar este CUB nesta proposta", key="cub_usar"):
                c_ = next(x for x in cubs if x["id"] == cid)
                P["parametros"]["cub"].update({"valor": c_["valor"], "padrao": c_["padrao"], "mes": c_["mes"], "uf": c_["uf"],
                                               "fonte": c_["fonte"]})
                estrutura_mudou()
        with st.form("cub_manual"):
            st.markdown("Informar CUB/m²")
            c = st.columns(5)
            cm_f = c[0].text_input("Fonte", "SINDUSCON-Rio")
            cm_uf = c[1].text_input("UF", P["cliente"].get("uf", "RJ"))
            cm_p = c[2].text_input("Padrão", P["parametros"]["cub"].get("padrao", "CSL-8N"))
            cm_m = c[3].text_input("Mês (AAAA-MM)", P["data"][:7])
            cm_v = c[4].number_input("CUB (R$/m²)", 0.0, 1e5, 0.0, step=10.0)
            if st.form_submit_button("Gravar") and cm_v > 0:
                rf.importar_cub(con, [{"fonte": cm_f, "uf": cm_uf, "padrao": cm_p, "mes": cm_m, "valor": cm_v}])
                st.rerun()

    with sub[5]:
        art = P["parametros"]["art"]
        st.caption("Taxa de ART escolhida pela faixa do valor do contrato. " + art.get("fonte", ""))
        dfr = pd.DataFrame([{"ate": f_.get("ate"), "valor": f_["valor"]} for f_ in art.get("faixas", [])], columns=["ate", "valor"])
        edr = st.data_editor(dfr.astype({"ate": float, "valor": float}), num_rows="dynamic", width="stretch", key=k("art_faixas"),
                             column_config={"ate": st.column_config.NumberColumn("Até o valor do contrato (R$) — vazio = acima", format="%.2f"),
                                            "valor": st.column_config.NumberColumn("Taxa (R$)", format="%.2f")})
        faixas = sorted([{"ate": float(r_["ate"]) if pd.notna(r_["ate"]) else None, "valor": float(r_["valor"])}
                         for _, r_ in edr.iterrows() if pd.notna(r_["valor"])],
                        key=lambda f_: float("inf") if f_["ate"] is None else f_["ate"])
        art["faixas"] = faixas
        art["fonte"] = st.text_input("Fonte da tabela", art.get("fonte", ""), key=k("art_fonte"))
        if st.button("Salvar esta tabela de ART nos parâmetros da empresa", key="art_salvar"):
            ss.params["art"] = copy.deepcopy(art)
            pm.salvar(ss.params)
            st.success("Tabela de ART salva.")

    with sub[6]:
        idx = rf.indices_disponiveis(con)
        if idx:
            st.dataframe(pd.DataFrame(idx), hide_index=True, width="stretch")
        with st.form("idx_manual"):
            st.markdown("Informar número-índice de um mês")
            c = st.columns(3)
            i_n = c[0].text_input("Índice", "INCC-M")
            i_m = c[1].text_input("Mês (AAAA-MM)", P["data"][:7])
            i_v = c[2].number_input("Número-índice", 0.0, 1e7, 0.0, step=0.01)
            if st.form_submit_button("Gravar") and i_v > 0 and rf.converter_mes(i_m):
                rf.importar_indices(con, i_n, [(rf.converter_mes(i_m), i_v)])
                st.rerun()

# ----------------------------------------------------------------------------- consistência
# Entradas desenhadas depois do cálculo (pagamento, catálogo) mudam o resultado: recalcula uma vez.
if assinatura([P, CAT]) != ASSINATURA:
    ss["_reexec"] = ss.get("_reexec", 0) + 1
    if ss["_reexec"] <= 3:
        st.rerun()
else:
    ss["_reexec"] = 0
