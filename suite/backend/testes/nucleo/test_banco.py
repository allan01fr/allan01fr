import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.nucleo.banco import Base, SessaoDoBanco
from app.nucleo.modelos import Empresa, Usuario
from app.registro import importar_modelos


def test_toda_tabela_tem_empresa_id_obrigatorio():
    importar_modelos()
    for tabela in Base.metadata.sorted_tables:
        if tabela.name == "empresa":
            continue
        assert "empresa_id" in tabela.c, tabela.name
        assert tabela.c.empresa_id.nullable is False, tabela.name


def test_migracoes_descem_sobem_e_batem_com_os_modelos(motor):
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    command.check(cfg)  # falha se modelos e migrações divergirem


def test_email_unico_global(sessao):
    a, b = Empresa(nome="A"), Empresa(nome="B")
    sessao.add_all([a, b])
    sessao.flush()
    sessao.add(Usuario(empresa_id=a.id, nome="X", email="x@x.com", senha_hash="h"))
    sessao.flush()
    sessao.add(Usuario(empresa_id=b.id, nome="Y", email="x@x.com", senha_hash="h"))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_email_com_maiuscula_e_recusado_pelo_banco(sessao):
    empresa = Empresa(nome="A")
    sessao.add(empresa)
    sessao.flush()
    sessao.add(Usuario(empresa_id=empresa.id, nome="X", email="X@x.com", senha_hash="h"))
    with pytest.raises(IntegrityError):
        sessao.flush()


def _rota_de_teste(cliente_http, caminho, funcao):
    cliente_http.app.add_api_route(caminho, funcao, methods=["GET"])


def test_falha_no_flush_nao_quebra_a_requisicao_seguinte(cliente_http):
    def duplicado(sessao: SessaoDoBanco):
        empresa = Empresa(nome="A")
        sessao.add(empresa)
        sessao.flush()
        for _ in range(2):
            sessao.add(Usuario(empresa_id=empresa.id, nome="X", email="d@d.com", senha_hash="h"))
            sessao.flush()

    def contar(sessao: SessaoDoBanco):
        return {"total": sessao.scalar(select(func.count()).select_from(Empresa))}

    _rota_de_teste(cliente_http, "/teste/duplicado", duplicado)
    _rota_de_teste(cliente_http, "/teste/contar", contar)
    assert cliente_http.get("/teste/duplicado").status_code == 500
    resposta = cliente_http.get("/teste/contar")
    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0}


def test_falha_no_commit_vira_erro_unico_e_nao_200(cliente_http, sessao, monkeypatch):
    def gravar(sessao: SessaoDoBanco):
        sessao.add(Empresa(nome="A"))
        return {"ok": True}

    def commit_quebrado():
        raise RuntimeError("commit falhou")

    monkeypatch.setattr(sessao, "commit", commit_quebrado)
    _rota_de_teste(cliente_http, "/teste/gravar", gravar)
    resposta = cliente_http.get("/teste/gravar")
    assert resposta.status_code == 500
    assert resposta.json()["codigo"] == "erro_interno"
