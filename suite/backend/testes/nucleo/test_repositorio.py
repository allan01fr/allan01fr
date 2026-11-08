from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.nucleo.contexto import Contexto
from app.nucleo.erros import NaoEncontrado
from app.nucleo.esquemas import EsquemaEntrada, Pagina
from app.nucleo.modelos import Usuario
from app.nucleo.perfis import Perfil
from app.nucleo.repositorio import RepositorioBase
from testes.fabricas import nova_empresa, novo_usuario


class _RepoUsuario(RepositorioBase[Usuario]):
    modelo = Usuario


def test_obter_nao_enxerga_outra_empresa(sessao):
    a, b = nova_empresa(sessao, "A"), nova_empresa(sessao, "B")
    u = novo_usuario(sessao, a, {Perfil.ADMIN})
    assert _RepoUsuario(sessao, b.id).obter(u.id) is None
    assert _RepoUsuario(sessao, a.id).obter(u.id) is u


def test_obter_ou_erro(sessao):
    repo = _RepoUsuario(sessao, nova_empresa(sessao).id)
    with pytest.raises(NaoEncontrado, match="Usuário não encontrado."):
        repo.obter_ou_erro(uuid4(), "Usuário não encontrado.")


def test_obter_ou_erro_devolve_o_objeto(sessao):
    a = nova_empresa(sessao, "A")
    u = novo_usuario(sessao, a, {Perfil.ADMIN})
    assert _RepoUsuario(sessao, a.id).obter_ou_erro(u.id, "x") is u


def test_listar_filtra_pagina_e_conta(sessao):
    a, b = nova_empresa(sessao, "A"), nova_empresa(sessao, "B")
    novo_usuario(sessao, a, {Perfil.ADMIN})
    novo_usuario(sessao, a, {Perfil.CAMPO})
    novo_usuario(sessao, b, {Perfil.ADMIN})
    repo_a = _RepoUsuario(sessao, a.id)
    itens, total = repo_a.listar(repo_a.consulta(), limite=1, deslocamento=0)
    assert len(itens) == 1 and total == 2
    assert all(i.empresa_id == a.id for i in itens)


def test_adicionar_forca_empresa_do_repositorio(sessao):
    a, b = nova_empresa(sessao, "A"), nova_empresa(sessao, "B")
    obj = Usuario(empresa_id=b.id, nome="X", email=f"{uuid4().hex[:10]}@teste.com", senha_hash="h")
    repo_a = _RepoUsuario(sessao, a.id)
    assert repo_a.adicionar(obj).empresa_id == a.id
    assert obj.id is not None


def test_empresa_obrigatoria(sessao):
    with pytest.raises(ValueError):
        _RepoUsuario(sessao, None)


def test_contexto_e_imutavel():
    ctx = Contexto(usuario_id=uuid4(), empresa_id=uuid4(), perfis=frozenset({Perfil.ADMIN}))
    with pytest.raises(AttributeError):
        ctx.empresa_id = uuid4()


def test_esquema_entrada_proibe_extras_e_apara_espacos():
    class Entrada(EsquemaEntrada):
        nome: str

    assert Entrada(nome="  Ana ").nome == "Ana"
    with pytest.raises(ValidationError):
        Entrada(nome="Ana", extra=1)


def test_pagina_generica():
    pagina = Pagina[int](itens=[1, 2], total=5)
    assert pagina.itens == [1, 2] and pagina.total == 5
