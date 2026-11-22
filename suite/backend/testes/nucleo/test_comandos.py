import pytest
from sqlalchemy import func, select

from app.nucleo import comandos
from app.nucleo.modelos import Empresa, PerfilUsuario, Usuario
from app.nucleo.perfis import Perfil


@pytest.fixture
def banco_dos_comandos(sessao, monkeypatch):
    """Faz main() usar a sessão de teste (transação desfeita no fim)."""
    from contextlib import contextmanager

    @contextmanager
    def abrir():
        yield sessao
        sessao.flush()

    monkeypatch.setattr(comandos, "abrir_sessao", abrir)
    return sessao


def test_semear_demo_e_idempotente(sessao):
    comandos.semear_demo(sessao, "senha-demo-12345")
    comandos.semear_demo(sessao, "senha-demo-12345")
    nomes = set(sessao.scalars(select(Empresa.nome)))
    assert {"Empresa Demo A", "Empresa Demo B"} <= nomes
    emails = set(sessao.scalars(select(Usuario.email).where(Usuario.email.like("%@demo-%.local"))))
    assert emails == {f"{p.value}@demo-a.local" for p in Perfil} | {"admin@demo-b.local"}
    assert (
        sessao.scalar(
            select(func.count()).select_from(Empresa).where(Empresa.nome.like("Empresa Demo%"))
        )
        == 2
    )


def test_semear_demo_um_perfil_por_usuario_na_empresa_certa(sessao):
    comandos.semear_demo(sessao, "senha-demo-12345")
    for perfil in Perfil:
        u = sessao.scalar(select(Usuario).where(Usuario.email == f"{perfil.value}@demo-a.local"))
        assert [p.perfil for p in u.perfis] == [perfil.value]
    a = sessao.scalar(select(Usuario).where(Usuario.email == "admin@demo-a.local"))
    b = sessao.scalar(select(Usuario).where(Usuario.email == "admin@demo-b.local"))
    assert a.empresa_id != b.empresa_id
    assert (
        sessao.scalar(
            select(func.count())
            .select_from(PerfilUsuario)
            .where(PerfilUsuario.empresa_id == b.empresa_id)
        )
        == 1
    )


def test_main_semear_demo_sem_variavel_sai_com_2(banco_dos_comandos, monkeypatch, capsys):
    monkeypatch.delenv("SUITE_SEMENTE_SENHA", raising=False)
    assert comandos.main(["semear-demo"]) == 2
    assert "Defina SUITE_SEMENTE_SENHA." in capsys.readouterr().err


def test_main_semear_demo_com_variavel(banco_dos_comandos, monkeypatch):
    monkeypatch.setenv("SUITE_SEMENTE_SENHA", "senha-demo-12345")
    assert comandos.main(["semear-demo"]) == 0
    assert banco_dos_comandos.scalar(
        select(Usuario).where(Usuario.email == "financeiro@demo-a.local")
    )


def test_main_criar_empresa_e_usuario(banco_dos_comandos, monkeypatch, capsys):
    monkeypatch.setattr(comandos, "getpass", lambda *_: "senha-longa-123")
    assert comandos.main(["criar-empresa", "--nome", "Nova Ltda"]) == 0
    empresa = banco_dos_comandos.scalar(select(Empresa).where(Empresa.nome == "Nova Ltda"))
    assert str(empresa.id) in capsys.readouterr().out
    codigo = comandos.main(
        ["criar-usuario", "--empresa-id", str(empresa.id), "--nome", "Ana",
         "--email", "ana@nova.com", "--perfil", "admin", "--perfil", "campo"]
    )  # fmt: skip
    assert codigo == 0
    u = banco_dos_comandos.scalar(select(Usuario).where(Usuario.email == "ana@nova.com"))
    assert u.empresa_id == empresa.id and {p.perfil for p in u.perfis} == {"admin", "campo"}


def test_main_criar_usuario_erros(banco_dos_comandos, monkeypatch, capsys):
    monkeypatch.setattr(comandos, "getpass", lambda *_: "curta")
    empresa = comandos.criar_empresa(banco_dos_comandos, "X")
    base = ["criar-usuario", "--empresa-id", str(empresa.id), "--nome", "A", "--email", "a@x.com"]
    assert comandos.main([*base, "--perfil", "admin"]) == 1  # senha curta
    assert "pelo menos 10 caracteres" in capsys.readouterr().err
    monkeypatch.setattr(comandos, "getpass", lambda *_: "senha-longa-123")
    inexistente = ["criar-usuario", "--empresa-id", "00000000-0000-4000-8000-000000000000"]
    assert (
        comandos.main([*inexistente, "--nome", "A", "--email", "a@x.com", "--perfil", "admin"]) == 1
    )
    assert "Empresa não encontrada." in capsys.readouterr().err
    with pytest.raises(SystemExit) as saida:
        comandos.main([*base, "--perfil", "chefe"])
    assert saida.value.code == 2
