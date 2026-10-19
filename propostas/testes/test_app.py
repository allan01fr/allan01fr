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
    at.selectbox(key=f"{v}|it_fase|A|0").select("F2").run()
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
