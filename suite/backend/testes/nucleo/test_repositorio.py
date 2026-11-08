from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select

from app.nucleo.contexto import Contexto
from app.nucleo.erros import NaoEncontrado
from app.nucleo.esquemas import LIMITE_MAXIMO_LISTA, EsquemaEntrada, Pagina, ParametrosLista
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


def _duas_empresas(sessao):
    a, b = nova_empresa(sessao, "A"), nova_empresa(sessao, "B")
    return a, b, _RepoUsuario(sessao, a.id), _RepoUsuario(sessao, b.id)


def test_obter_ou_erro_com_id_de_outra_empresa(sessao):
    a, b, repo_a, _ = _duas_empresas(sessao)
    u_b = novo_usuario(sessao, b, {Perfil.ADMIN})
    with pytest.raises(NaoEncontrado):
        repo_a.obter_ou_erro(u_b.id, "Usuário não encontrado.")


def test_paginacao_nunca_devolve_linhas_de_outra_empresa(sessao):
    a, b, repo_a, _ = _duas_empresas(sessao)
    ids_a = {novo_usuario(sessao, a, {Perfil.ADMIN}).id for _ in range(3)}
    for _ in range(2):
        novo_usuario(sessao, b, {Perfil.ADMIN})
    vistos = set()
    for deslocamento in range(5):
        itens, total = repo_a.listar(repo_a.consulta(), limite=1, deslocamento=deslocamento)
        assert total == 3
        assert all(i.empresa_id == a.id for i in itens)
        vistos |= {i.id for i in itens}
    assert vistos == ids_a


def test_objeto_adicionado_por_a_e_invisivel_para_b(sessao):
    a, _, repo_a, repo_b = _duas_empresas(sessao)
    obj = Usuario(empresa_id=a.id, nome="X", email=f"{uuid4().hex[:10]}@teste.com", senha_hash="h")
    repo_a.adicionar(obj)
    assert repo_b.obter(obj.id) is None
    assert repo_b.listar(repo_b.consulta(), limite=10, deslocamento=0) == ([], 0)


def test_listar_recusa_consulta_que_nao_vem_de_consulta(sessao):
    _, _, repo_a, _ = _duas_empresas(sessao)
    with pytest.raises(ValueError, match="consulta"):
        repo_a.listar(select(Usuario), limite=10, deslocamento=0)


def test_listar_recusa_consulta_de_outro_repositorio(sessao):
    _, _, repo_a, repo_b = _duas_empresas(sessao)
    with pytest.raises(ValueError, match="consulta"):
        repo_a.listar(repo_b.consulta(), limite=10, deslocamento=0)


def test_listar_aceita_consulta_refinada(sessao):
    a, _, repo_a, _ = _duas_empresas(sessao)
    novo_usuario(sessao, a, {Perfil.ADMIN})
    refinada = repo_a.consulta().where(Usuario.nome.is_not(None)).order_by(Usuario.nome)
    itens, total = repo_a.listar(refinada, limite=10, deslocamento=0)
    assert total == 1 and len(itens) == 1


@pytest.mark.parametrize("limite", [0, -1, LIMITE_MAXIMO_LISTA + 1])
def test_listar_valida_limite(sessao, limite):
    _, _, repo_a, _ = _duas_empresas(sessao)
    with pytest.raises(ValueError, match="limite"):
        repo_a.listar(repo_a.consulta(), limite=limite, deslocamento=0)


def test_listar_valida_deslocamento(sessao):
    _, _, repo_a, _ = _duas_empresas(sessao)
    with pytest.raises(ValueError, match="deslocamento"):
        repo_a.listar(repo_a.consulta(), limite=10, deslocamento=-1)


def test_listar_aceita_limite_maximo(sessao):
    _, _, repo_a, _ = _duas_empresas(sessao)
    assert repo_a.listar(repo_a.consulta(), LIMITE_MAXIMO_LISTA, 0) == ([], 0)


def test_adicionar_recusa_objeto_persistente_de_outra_empresa(sessao):
    _, b, repo_a, _ = _duas_empresas(sessao)
    u_b = novo_usuario(sessao, b, {Perfil.ADMIN})
    with pytest.raises(ValueError, match="outra empresa"):
        repo_a.adicionar(u_b)
    assert u_b.empresa_id == b.id


def test_adicionar_aceita_objeto_persistente_da_mesma_empresa(sessao):
    a, _, repo_a, _ = _duas_empresas(sessao)
    u = novo_usuario(sessao, a, {Perfil.ADMIN})
    assert repo_a.adicionar(u) is u


def test_parametros_lista_respeita_limites():
    app = FastAPI()

    @app.get("/lista")
    def lista(p: Annotated[ParametrosLista, Depends()]):
        return {"limite": p.limite, "deslocamento": p.deslocamento}

    cliente = TestClient(app)
    assert cliente.get("/lista").json() == {"limite": 50, "deslocamento": 0}
    assert cliente.get(f"/lista?limite={LIMITE_MAXIMO_LISTA}").status_code == 200
    assert cliente.get(f"/lista?limite={LIMITE_MAXIMO_LISTA + 1}").status_code == 422
    assert cliente.get("/lista?limite=0").status_code == 422
    assert cliente.get("/lista?deslocamento=-1").status_code == 422
