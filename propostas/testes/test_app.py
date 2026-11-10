import os

import pytest

from conftest import EXEMPLOS, RAIZ

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = os.path.join(RAIZ, "app", "app.py")


def _rodar():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_abre_vazio():
    at = _rodar()
    assert len(at.tabs) >= 8


@pytest.mark.parametrize("caminho", EXEMPLOS)
def test_app_carrega_exemplo_e_gera_arquivos(caminho):
    at = _rodar()
    at.sidebar.selectbox(key="exemplo_sel").select(os.path.basename(caminho)).run()
    next(b for b in at.sidebar.button if b.label == "Carregar exemplo").click().run()
    assert not at.exception, at.exception
    assert at.session_state.proposta["opcoes"][0]["itens"]
    next(b for b in at.button if b.label == "Gerar planilha e propostas").click().run()
    assert not at.exception, at.exception
    arquivos = at.session_state.arquivos
    assert arquivos["xlsx"][0][:2] == b"PK"
    ofertadas = [o for o in at.session_state.proposta["opcoes"] if o["modalidade"] != "estimativa"]
    assert len(arquivos["docx"]) == len(ofertadas)        # a estimativa interna não vira proposta


def test_app_adiciona_servico_e_duplica_opcao():
    at = _rodar()
    at.selectbox(key="0|f_disc").select("Segurança do trabalho").run()
    next(b for b in at.button if b.label == "Adicionar à opção").click().run()
    assert not at.exception, at.exception
    p = at.session_state.proposta
    assert len(p["opcoes"][0]["itens"]) == 1
    next(b for b in at.button if b.label == "⧉ Duplicar").click().run()
    assert not at.exception, at.exception
    assert len(at.session_state.proposta["opcoes"]) == 2


def _carregar(nome, tmp_path, monkeypatch):
    monkeypatch.setenv("KAPTEK_REFERENCIAS", str(tmp_path / "ref.sqlite"))   # nunca toca a base real
    at = _rodar()
    at.sidebar.selectbox(key="exemplo_sel").select(nome).run()
    next(b for b in at.sidebar.button if b.label == "Carregar exemplo").click().run()
    assert not at.exception, at.exception
    return at


def test_app_fases_e_viabilidade(tmp_path, monkeypatch):
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    textos = [m.value for m in at.markdown]
    assert "**Fases da proposta**" in textos and "**Cobrança de cada fase**" in textos
    assert any("Fase 4 — Assessoria de obra" in t for t in textos)
    next(b for b in at.button if b.label == "Gerar planilha do estudo (.xlsx)").click().run()
    assert not at.exception, at.exception
    assert at.session_state.arquivo_viab[0][:2] == b"PK"


def test_app_piso_de_engenheiro_vira_custo_do_perfil(tmp_path, monkeypatch):
    from orcamento import referencias as rf
    at = _carregar("hvac_consultoria_2d_3d_bim.json", tmp_path, monkeypatch)
    at.radio(key="piso_modo").set_value("Engenheiro — Lei 4.950-A").run()
    perfil = at.selectbox(key="piso_perfil").value
    at.button(key="piso_apl_prop").click().run()
    assert not at.exception, at.exception
    esperado = rf.custo_hora_piso(rf.piso_lei_4950a(rf.SALARIO_MINIMO_2026, 8), 0.0, 0.70, 1200.0, 140.0)
    perfis = at.session_state.proposta["parametros"]["perfis"]
    assert perfis[perfil]["custo_h"] == pytest.approx(round(esperado, 2))
    assert perfis[perfil]["origem"]["fonte"] == "Lei 4.950-A/1966"


def test_app_busca_na_base_importada(tmp_path, monkeypatch):
    from orcamento import referencias as rf
    con = rf.conectar(str(tmp_path / "ref.sqlite"))
    rf.importar_itens(con, [{"codigo": "15.020.0010-A", "descricao": "Instalação de split hi-wall 12.000 BTU/h", "unidade": "un",
                             "valor": 742.40}], "EMOP-RJ", "2026-03", "RJ")
    con.close()
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    at.text_input(key="busca_termo").input("split").run()
    assert not at.exception, at.exception
    tabela = next(d for d in at.dataframe if {"descricao", "uf"} <= set(d.value.columns))
    assert list(tabela.value["fonte"]) == ["EMOP-RJ"]


def test_app_cria_fase_muda_cobranca_e_move_servico(tmp_path, monkeypatch):
    from orcamento import catalogo as ct
    from orcamento import motor
    at = _rodar()
    at.selectbox(key="0|f_disc").select("Geral").run()
    next(b for b in at.button if b.label == "Adicionar à opção").click().run()
    next(b for b in at.button if b.label == "➕ Nova fase").click().run()
    assert not at.exception, at.exception
    v = at.session_state.versao
    assert [f["id"] for f in at.session_state.proposta["opcoes"][0]["fases"]] == ["F1", "F2"]
    at.selectbox(key=f"{v}|fz_cob|A|F2").select("percentual").run()
    at.selectbox(key=f"{v}|fz|A|F2|bmodo").select("informado").run()
    at.number_input(key=f"{v}|fz|A|F2|bval").set_value(500000.0).run()
    next(s for s in at.selectbox if (s.key or "").startswith(f"{v}|it_fase|A|0|")).select("F2").run()
    assert not at.exception, at.exception
    p = at.session_state.proposta
    assert p["opcoes"][0]["itens"][0]["fase"] == "F2"
    r = motor.precificar(ct.carregar(), p)["opcoes"][0]
    f2 = next(f for f in r["fases"] if f["id"] == "F2")
    assert f2["cobranca"] == "percentual" and f2["base"] == 500000.0
    assert f2["preco"] > 0 and r["preco"] == f2["preco"] + next(f for f in r["fases"] if f["id"] == "F1")["preco"]


def test_app_recusa_json_de_servico_incompleto():
    """Aplicado sem 'descricao', o serviço derrubaria o app desta sessão antes de qualquer aviso."""
    import json
    at = _rodar()
    sid = at.selectbox(key="cat_sel").value
    servico = json.loads(at.text_area(key=f"cat_json_{sid}").value)
    del servico["descricao"]
    at.text_area(key=f"cat_json_{sid}").input(json.dumps(servico)).run()
    next(b for b in at.button if b.label == "Aplicar JSON").click().run()
    assert not at.exception, at.exception
    assert any("JSON incompleto" in e.value for e in at.error)
    assert "descricao" in next(s for s in at.session_state.cat["servicos"] if s["id"] == sid)


def test_requisitos_da_nuvem_acompanham_os_locais():
    """O Community Cloud lê o requirements.txt ao lado do app; ele é o local sem o pytest."""
    def ler(*partes):
        with open(os.path.join(*partes), encoding="utf-8") as f:
            return {l.strip() for l in f if l.strip() and not l.startswith("#")}
    locais = {r for r in ler(RAIZ, "requirements.txt") if not r.startswith("pytest")}
    assert ler(RAIZ, "app", "requirements.txt") == locais


def test_tema_da_raiz_do_repositorio_igual_ao_local():
    """Na nuvem o app roda a partir da raiz do repositório, que tem a sua cópia do config.toml."""
    raiz_repo = os.path.join(RAIZ, "..", ".streamlit", "config.toml")
    if not os.path.exists(raiz_repo):
        pytest.skip("pasta propostas fora do repositório original")
    with open(raiz_repo, encoding="utf-8") as a, open(os.path.join(RAIZ, ".streamlit", "config.toml"), encoding="utf-8") as b:
        assert a.read() == b.read()


# ----------------------------------------------------------------------------- módulos de escopo e fases ligadas
MODULOS_ROTULOS = ["Projeto", "Acompanhamento de obra", "Execução", "Inspeção com laudo",
                   "Avaliação de desempenho"]      # o nome completo do módulo fica no help do botão


def _botao_modulo(at, rotulo):
    return next(b for b in at.button if b.label == rotulo)


def _tabela_precos(at):
    return next(d.value for d in at.dataframe if {"Cobrança", "Preço"} <= set(d.value.columns))


def _preco_motor(at, oid="A"):
    from orcamento import catalogo as ct
    from orcamento import motor
    r = next(r for r in motor.precificar(ct.carregar(), at.session_state.proposta)["opcoes"] if r["id"] == oid)
    return r


def test_app_tem_cinco_botoes_de_modulo():
    at = _rodar()
    rotulos = [b.label for b in at.button]
    for r in MODULOS_ROTULOS:
        assert r in rotulos
    assert "➕ Nova fase" in rotulos


def test_app_modulos_projeto_e_inspecao_viram_duas_fases():
    from orcamento import exportar_docx
    at = _rodar()
    _botao_modulo(at, "Projeto").click().run()
    assert not at.exception, at.exception
    O = at.session_state.proposta["opcoes"][0]
    assert [f["id"] for f in O["fases"]] == ["F1"] and O["fases"][0]["modulo"] == "projeto"
    assert [i["servico"] for i in O["itens"]] == ["hvac.carga_termica", "hvac.projeto"]
    _botao_modulo(at, "Inspeção com laudo").click().run()
    assert not at.exception, at.exception
    O = at.session_state.proposta["opcoes"][0]
    assert [f["id"] for f in O["fases"]] == ["F1", "F2"] and O["fases"][1]["modulo"] == "inspecao_laudo"
    tab = _tabela_precos(at)
    assert len(tab) == 3                                    # duas fases + total
    assert list(tab["Fase"][:2]) == ["Projeto", "Inspeção com laudo de conformidade"]
    assert "Módulo" not in tab.columns                      # o módulo repetiria o nome de todas as fases
    assert tab["Preço"].iloc[-1] == exportar_docx.moeda(_preco_motor(at)["preco"])


def test_app_desliga_e_religa_fase():
    from orcamento import exportar_docx
    at = _rodar()
    _botao_modulo(at, "Projeto").click().run()
    _botao_modulo(at, "Inspeção com laudo").click().run()
    v = at.session_state.versao
    total2 = _preco_motor(at)["preco"]
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(False).run()
    assert not at.exception, at.exception
    r = _preco_motor(at)
    assert [f["id"] for f in r["fases"]] == ["F1"] and r["preco"] < total2
    tab = _tabela_precos(at)
    assert len(tab) == 2 and tab["Preço"].iloc[-1] == exportar_docx.moeda(r["preco"])
    textos = [m.value for m in at.markdown] + [c.value for c in at.caption]
    assert any("Fora desta proposta" in t and "Inspeção com laudo de conformidade" in t for t in textos)
    assert any("Fases desligadas (fora desta proposta)" in t for t in textos)
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(True).run()
    assert not at.exception, at.exception
    assert _tabela_precos(at)["Preço"].iloc[-1] == exportar_docx.moeda(total2)


def test_app_ultima_fase_ativa_nao_desliga():
    at = _rodar()
    v = at.session_state.versao
    assert at.toggle(key=f"{v}|fz_ativa|A|F1").disabled is True
    _botao_modulo(at, "Projeto").click().run()
    _botao_modulo(at, "Acompanhamento de obra").click().run()
    v = at.session_state.versao
    assert at.toggle(key=f"{v}|fz_ativa|A|F1").disabled is False
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(False).run()
    assert at.toggle(key=f"{v}|fz_ativa|A|F1").disabled is True


def test_app_excluir_unica_fase_ativa_liga_a_primeira_restante():
    at = _rodar()
    _botao_modulo(at, "Projeto").click().run()
    _botao_modulo(at, "Inspeção com laudo").click().run()
    v = at.session_state.versao
    at.toggle(key=f"{v}|fz_ativa|A|F1").set_value(False).run()          # só a F2 fica ativa
    at.button(key=f"{v}|fz_rm|A|F2").click().run()
    assert not at.exception, at.exception
    fases = at.session_state.proposta["opcoes"][0]["fases"]
    assert [f["id"] for f in fases] == ["F1"] and fases[0]["ativa"] is True


def test_app_exemplo_de_fases_nao_muda_de_preco(tmp_path, monkeypatch):
    from orcamento import catalogo as ct
    from orcamento import motor
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    assert not at.exception
    r = motor.precificar(ct.carregar(), at.session_state.proposta)
    assert not [a for a in r["avisos"] if "fases desligadas" in a]
    A = r["opcoes"][0]
    tab = _tabela_precos(at)
    assert len(tab) == len(A["fases"]) + 1
    assert list(tab["Nº"][:-1]) == [str(n) for n in range(1, len(A["fases"]) + 1)]
    assert tab["Preço"].iloc[-1] == __import__("orcamento.exportar_docx", fromlist=["moeda"]).moeda(A["preco"])


def test_app_estimativa_sem_botoes_de_modulo():
    at = _rodar()
    v = at.session_state.versao
    at.radio(key=f"{v}|modalidade|A").set_value("estimativa").run()
    assert not at.exception, at.exception
    assert not [b for b in at.button if b.label in MODULOS_ROTULOS]


def test_app_sem_fase_incluida_mostra_erro_sem_quebrar():
    at = _rodar()
    _botao_modulo(at, "Projeto").click().run()
    at.session_state.proposta["opcoes"][0]["fases"][0]["ativa"] = False      # arquivo editado à mão
    at.session_state.versao += 1
    at.run()
    assert not at.exception, at.exception
    assert any("nenhuma fase incluída" in e.value for e in at.error)


# ----------------------------------------------------------------------------- só execução (fornecimentos sem serviços)
def _so_execucao_no_app():
    from orcamento import proposta as pp
    at = _rodar()
    _botao_modulo(at, "Execução").click().run()
    O = at.session_state.proposta["opcoes"][0]
    O["fornecimentos"] += [pp.novo_fornecimento("Tubulação de cobre", "material", "m", 120, 85.0, fase="F1"),
                           pp.novo_fornecimento("Instalação do sistema", "mo_execucao", "dia", 20, 650.0, fase="F1")]
    at.session_state.versao += 1
    at.run()
    assert not at.exception, at.exception
    return at


def test_app_so_execucao_mostra_preco_prazo_e_libera_exportacao():
    from orcamento import exportar_docx
    at = _so_execucao_no_app()
    r = _preco_motor(at)
    assert r["linhas"] == [] and r["preco"] > 0
    textos = [i.value for i in at.info] + [w.value for w in at.warning]
    assert not any("Adicione serviços" in t for t in textos)
    assert not any("nenhum serviço com horas" in t or "sem serviços" in t for t in textos)
    assert _tabela_precos(at)["Preço"].iloc[-1] == exportar_docx.moeda(r["preco"])
    assert any("prazo de execução" in t for t in textos)             # no lugar do cronograma vazio
    next(b for b in at.button if b.label == "Gerar planilha e propostas").click().run()
    assert not at.exception, at.exception
    arq = at.session_state.arquivos
    assert arq["xlsx"][0][:2] == b"PK" and len(arq["docx"]) == 1


def test_app_execucao_sem_nada_nao_libera_exportacao():
    at = _rodar()
    _botao_modulo(at, "Execução").click().run()
    assert any("Adicione serviços" in i.value for i in at.info)
    assert not [b for b in at.button if b.label == "Gerar planilha e propostas"]


# ----------------------------------------------------------------------------- fases desligadas na tela (revisão)
def _retrofit_com_f1_f2_off(tmp_path, monkeypatch):
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    v = at.session_state.versao
    for fid in ("F1", "F2"):
        at.toggle(key=f"{v}|fz_ativa|A|{fid}").set_value(False).run()
    return at


def test_app_excluir_fase_leva_servicos_para_a_primeira_fase_ativa(tmp_path, monkeypatch):
    at = _retrofit_com_f1_f2_off(tmp_path, monkeypatch)
    O = at.session_state.proposta["opcoes"][0]
    assert [f["ativa"] for f in O["fases"][:3]] == [False, False, True]
    movidos = [x for x in O["itens"] + O["fornecimentos"] if x["fase"] == "F3"]
    assert movidos
    v = at.session_state.versao
    at.button(key=f"{v}|fz_rm|A|F3").click().run()
    assert not at.exception, at.exception
    O = at.session_state.proposta["opcoes"][0]
    primeira_ativa = next(f["id"] for f in O["fases"] if f.get("ativa", True))
    assert primeira_ativa != "F1" and all(x["fase"] == primeira_ativa for x in movidos)
    assert not any(x["fase"] in ("F1", "F2") and x in movidos for x in O["itens"] + O["fornecimentos"])
    ids_precificados = {f["id"] for f in _preco_motor(at)["fases"]}
    assert primeira_ativa in ids_precificados               # os serviços de F3 continuam no preço


def test_app_excluir_unica_fase_ativa_leva_servicos_para_a_fase_religada(tmp_path, monkeypatch):
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    O = at.session_state.proposta["opcoes"][0]
    v = at.session_state.versao
    ids = [f["id"] for f in O["fases"]]
    movidos = [x for x in O["itens"] + O["fornecimentos"] if x["fase"] == ids[-1]]
    assert movidos
    for fid in ids[:-1]:
        at.toggle(key=f"{v}|fz_ativa|A|{fid}").set_value(False).run()
    at.button(key=f"{v}|fz_rm|A|{ids[-1]}").click().run()
    assert not at.exception, at.exception
    O = at.session_state.proposta["opcoes"][0]
    assert O["fases"][0]["ativa"] is True
    assert all(x["fase"] == O["fases"][0]["id"] for x in movidos)
    assert _preco_motor(at)["preco"] > 0


def test_app_reordenar_com_fase_desligada_mantem_numeracao_do_preco(tmp_path, monkeypatch):
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    v = at.session_state.versao
    at.toggle(key=f"{v}|fz_ativa|A|F1").set_value(False).run()
    at.button(key=f"{v}|fz_sobe|A|F3").click().run()
    assert not at.exception, at.exception
    r = _preco_motor(at)
    tab = _tabela_precos(at)
    assert list(tab["Fase"][:-1]) == [f["nome"] for f in r["fases"]]
    assert list(tab["Nº"][:-1]) == [str(n) for n in range(1, len(r["fases"]) + 1)]


def test_app_religa_fase_pela_aba_de_preco(tmp_path, monkeypatch):
    at = _retrofit_com_f1_f2_off(tmp_path, monkeypatch)
    v = at.session_state.versao
    at.toggle(key=f"{v}|fz_religa|A|F2").set_value(True).run()
    assert not at.exception, at.exception
    fases = {f["id"]: f for f in at.session_state.proposta["opcoes"][0]["fases"]}
    assert fases["F2"]["ativa"] is True and fases["F1"]["ativa"] is False


def test_app_json_com_fase_desligada_mostra_o_botao_desligado(tmp_path, monkeypatch):
    import json
    from conftest import RAIZ as raiz
    d = json.load(open(os.path.join(raiz, "exemplos", "hvac_retrofit_fases.json"), encoding="utf-8"))
    d["opcoes"][0]["fases"][1]["ativa"] = False
    (tmp_path / "ex").mkdir()
    (tmp_path / "ex" / "off.json").write_text(json.dumps(d), encoding="utf-8")
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    from orcamento import proposta as pp
    from orcamento import parametros as pm
    at.session_state.proposta = pp.completar(pp.carregar_json(json.dumps(d)), at.session_state.cat, pm.carregar())
    at.session_state.versao += 1
    at.run()
    assert not at.exception, at.exception
    v = at.session_state.versao
    fid = d["opcoes"][0]["fases"][1]["id"]
    assert at.toggle(key=f"{v}|fz_ativa|A|{fid}").value is False


def test_app_duas_fases_desligadas_na_mesma_execucao_mantem_a_primeira(tmp_path, monkeypatch):
    at = _carregar("hvac_retrofit_fases.json", tmp_path, monkeypatch)
    O = at.session_state.proposta["opcoes"][0]
    v = at.session_state.versao
    ids = [f["id"] for f in O["fases"]]
    for fid in ids:      # troca todos os botões de uma vez, sem rodar entre eles
        at.session_state[f"{v}|fz_ativa|A|{fid}"] = False
    at.run()
    assert not at.exception, at.exception
    assert not any("nenhuma fase incluída" in e.value for e in at.error)
    O = at.session_state.proposta["opcoes"][0]
    assert [f["ativa"] for f in O["fases"]] == [True] + [False] * (len(ids) - 1)


# ----------------------------------------------------------------------------- rótulos e textos da tela (fix-2)
def _tres_fases_com_a_do_meio_desligada():
    at = _rodar()
    for r in ("Projeto", "Inspeção com laudo", "Execução"):
        _botao_modulo(at, r).click().run()
    v = at.session_state.versao
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(False).run()
    assert not at.exception, at.exception
    return at, at.session_state.versao


def test_app_botao_de_modulo_tem_nome_completo_no_help():
    at = _rodar()
    b = _botao_modulo(at, "Inspeção com laudo")
    assert b.help.startswith("Inspeção com laudo de conformidade")


def test_app_seletores_de_fase_usam_a_numeracao_das_fases_ativas():
    at, v = _tres_fases_com_a_do_meio_desligada()
    esperado = ["Fase 1 — Projeto", "Inspeção com laudo de conformidade (desligada)", "Fase 2 — Execução"]
    assert next(s for s in at.selectbox if (s.key or "").startswith(f"{v}|f_fase|")).options == esperado
    assert next(s for s in at.selectbox if (s.key or "").startswith(f"{v}|it_fase|A|0|")).options == esperado
    seletores = [s for s in at.selectbox if s.key and "|f_fase|" in s.key or "|it_fase|" in (s.key or "")]
    assert seletores and all(s.options == esperado for s in seletores)
    assert not any("Fase 3" in o for s in seletores for o in s.options)


def test_app_toggle_de_fase_tem_rotulo_curto_com_ajuda():
    at, v = _tres_fases_com_a_do_meio_desligada()
    t = at.toggle(key=f"{v}|fz_ativa|A|F1")
    assert t.label == "Incluir" and t.help
    assert at.toggle(key=f"{v}|fz_religa|A|F2").label == "Incluir"


def test_app_sem_redundancia_entre_fase_e_modulo():
    at, v = _tres_fases_com_a_do_meio_desligada()
    textos = [m.value for m in at.markdown] + [c.value for c in at.caption]
    assert "Fora desta proposta: Inspeção com laudo de conformidade." in textos
    assert not any("Módulo: " in t for t in textos)
    assert not any("· Inspeção com laudo de conformidade ·" in t or "Inspeção com laudo de conformidade · Inspeção" in t
                   for t in textos)
    off = next(t for t in textos if t.startswith("~~"))
    assert off == "~~Inspeção com laudo de conformidade~~ · desligada"


def test_app_modulo_diferente_do_nome_da_fase_aparece_em_parenteses_e_na_tabela():
    at, v = _tres_fases_com_a_do_meio_desligada()
    at.toggle(key=f"{v}|fz_religa|A|F2").set_value(True).run()
    v = at.session_state.versao
    at.text_input(key=f"{v}|fz_nome|A|F2").set_value("Laudo do 3º andar").run()
    assert "Módulo" in _tabela_precos(at).columns
    assert "Módulo: Inspeção com laudo de conformidade" in [c.value for c in at.caption]
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(False).run()
    textos = [m.value for m in at.markdown] + [c.value for c in at.caption]
    assert "Fora desta proposta: Laudo do 3º andar (Inspeção com laudo de conformidade)." in textos
    assert "~~Laudo do 3º andar~~ · Inspeção com laudo de conformidade · desligada" in textos


def test_app_nome_de_fase_desligada_nao_vira_markdown():
    at, v = _tres_fases_com_a_do_meio_desligada()
    at.toggle(key=f"{v}|fz_religa|A|F2").set_value(True).run()
    v = at.session_state.versao
    at.text_input(key=f"{v}|fz_nome|A|F2").set_value("a*b_c~d[e]`f$").run()
    at.toggle(key=f"{v}|fz_ativa|A|F2").set_value(False).run()
    riscado = next(m.value for m in at.markdown if m.value.startswith("~~"))
    assert riscado.startswith("~~a\\*b\\_c\\~d\\[e\\]\\`f\\$~~")
