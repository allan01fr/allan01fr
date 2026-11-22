import pytest

from app.nucleo.empresa import criar_empresa, criar_usuario
from app.nucleo.erros import Conflito, EntradaInvalida
from app.nucleo.perfis import Perfil
from app.nucleo.senhas import HASH_FICTICIO, conferir_senha, gerar_hash, normalizar_email
from testes.fabricas import SENHA_TESTE, nova_empresa, novo_usuario


def test_hash_argon2_e_conferencia():
    h = gerar_hash("senha-longa-1")
    assert h.startswith("$argon2")
    assert conferir_senha("senha-longa-1", h) and not conferir_senha("outra", h)
    assert conferir_senha("x", "lixo") is False


def test_hash_ficticio_e_valido_e_nao_confere():
    assert HASH_FICTICIO.startswith("$argon2")
    assert conferir_senha("qualquer", HASH_FICTICIO) is False


def test_normalizar_email():
    assert normalizar_email("  Ana@KAPTEK.com ") == "ana@kaptek.com"


def test_criar_usuario_normaliza_email_e_grava_perfis(sessao):
    emp = criar_empresa(sessao, "KAPTEK")
    u = criar_usuario(
        sessao, emp.id, "Ana", "  Ana@KAPTEK.com ", "senha-longa-1", {Perfil.COMERCIAL}
    )
    assert u.email == "ana@kaptek.com" and {p.perfil for p in u.perfis} == {"comercial"}
    assert u.empresa_id == emp.id and u.senha_hash.startswith("$argon2")
    assert all(p.empresa_id == emp.id for p in u.perfis)


def test_email_repetido_da_conflito(sessao):
    emp = criar_empresa(sessao, "KAPTEK")
    criar_usuario(sessao, emp.id, "Ana", "ana@kaptek.com", "senha-longa-1", {Perfil.ADMIN})
    with pytest.raises(Conflito, match="Já existe usuário"):
        criar_usuario(sessao, emp.id, "Ana 2", " ANA@kaptek.com", "senha-longa-1", {Perfil.CAMPO})
    # a sessão continua utilizável depois do conflito
    outro = criar_usuario(sessao, emp.id, "Bia", "bia@kaptek.com", "senha-longa-1", {Perfil.CAMPO})
    assert outro.email == "bia@kaptek.com"


def test_senha_curta_e_sem_perfil_sao_rejeitadas(sessao):
    emp = criar_empresa(sessao, "KAPTEK")
    with pytest.raises(EntradaInvalida, match="pelo menos 10 caracteres"):
        criar_usuario(sessao, emp.id, "Ana", "ana@kaptek.com", "curta", {Perfil.ADMIN})
    with pytest.raises(EntradaInvalida, match="Escolha ao menos um perfil"):
        criar_usuario(sessao, emp.id, "Ana", "ana@kaptek.com", "senha-longa-1", set())


def test_fabricas_geram_empresa_e_usuarios_distintos(sessao):
    emp = nova_empresa(sessao)
    a = novo_usuario(sessao, emp, {Perfil.ADMIN})
    b = novo_usuario(sessao, emp, {Perfil.CAMPO})
    assert emp.nome == "Empresa A" and a.email != b.email
    assert conferir_senha(SENHA_TESTE, a.senha_hash)
