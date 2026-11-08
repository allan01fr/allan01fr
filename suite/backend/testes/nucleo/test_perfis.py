import pytest

from app.nucleo.perfis import PERMISSOES, TODOS, Perfil, exigir, permissoes_de
from testes.fabricas import entrar, nova_empresa, novo_usuario


def test_matriz_exata():
    assert {
        "cadastro.ler": TODOS,
        "cadastro.editar_cliente": {Perfil.ADMIN, Perfil.COMERCIAL, Perfil.ENGENHARIA},
        "cadastro.editar_tecnico": {Perfil.ADMIN, Perfil.ENGENHARIA, Perfil.CAMPO},
        "nucleo.usuarios": {Perfil.ADMIN},
        "nucleo.empresa_ler": TODOS,
        "nucleo.empresa_editar": {Perfil.ADMIN},
        "nucleo.arquivos": TODOS,
        "nucleo.tarefas": TODOS,
        "nucleo.tarefa_exemplo": {Perfil.ADMIN},
    } == PERMISSOES
    assert frozenset(Perfil) == TODOS


def test_permissao_desconhecida():
    with pytest.raises(KeyError):
        exigir("nao.existe")


def test_dependencia_carrega_o_nome_da_permissao():
    assert exigir("nucleo.usuarios").permissao == "nucleo.usuarios"


def test_permissoes_de_une_perfis_em_ordem_alfabetica():
    assert permissoes_de([]) == []
    resultado = permissoes_de([Perfil.FINANCEIRO, Perfil.CAMPO])
    assert resultado == sorted(resultado)
    assert "cadastro.editar_tecnico" in resultado and "cadastro.editar_cliente" not in resultado
    assert len(resultado) == len(set(resultado))


def test_eu_traz_permissoes(cliente_http, sessao):
    emp = nova_empresa(sessao)
    u = novo_usuario(sessao, emp, {Perfil.FINANCEIRO})
    entrar(cliente_http, u.email)
    permissoes = cliente_http.get("/api/nucleo/eu").json()["permissoes"]
    assert "cadastro.ler" in permissoes and "cadastro.editar_cliente" not in permissoes
    assert "nucleo.usuarios" not in permissoes and permissoes == sorted(permissoes)


def test_eu_de_perfil_duplo_soma_permissoes(cliente_http, sessao):
    emp = nova_empresa(sessao)
    u = novo_usuario(sessao, emp, {Perfil.FINANCEIRO, Perfil.COMERCIAL})
    entrar(cliente_http, u.email)
    permissoes = cliente_http.get("/api/nucleo/eu").json()["permissoes"]
    assert "cadastro.editar_cliente" in permissoes and "cadastro.editar_tecnico" not in permissoes
