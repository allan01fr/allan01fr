import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from app.nucleo.banco import Base
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
