from uuid import uuid4

import pytest

from app.main import criar_app
from app.nucleo.perfis import PERMISSOES, Perfil
from testes.fabricas import entrar, nova_empresa, novo_usuario
from testes.rotas_da_api import ROTAS_PUBLICAS, rotas_da_api


def test_toda_rota_declara_acesso():
    rotas = rotas_da_api(criar_app())
    assert rotas  # a descoberta não pode ficar vazia sem ninguém notar
    for r in rotas:
        assert (
            r.acesso in PERMISSOES or r.acesso == "login" or (r.metodo, r.caminho) in ROTAS_PUBLICAS
        ), r


def test_rotas_publicas_existem_e_sao_publicas():
    por_chave = {(r.metodo, r.caminho): r for r in rotas_da_api(criar_app())}
    for chave in ROTAS_PUBLICAS:
        assert por_chave[chave].acesso == "publica", chave


def test_rotas_de_usuarios_exigem_a_permissao():
    por_chave = {(r.metodo, r.caminho): r.acesso for r in rotas_da_api(criar_app())}
    assert por_chave[("GET", "/api/nucleo/usuarios")] == "nucleo.usuarios"
    assert por_chave[("POST", "/api/nucleo/usuarios")] == "nucleo.usuarios"
    assert por_chave[("PATCH", "/api/nucleo/usuarios/{usuario_id}")] == "nucleo.usuarios"


@pytest.mark.parametrize("perfil", list(Perfil))
def test_cada_perfil_ve_so_o_que_pode(cliente_http, sessao, perfil):
    emp = nova_empresa(sessao)
    u = novo_usuario(sessao, emp, {perfil})
    sessao.commit()
    entrar(cliente_http, u.email)
    verificadas = 0
    for r in rotas_da_api(cliente_http.app):
        if r.acesso not in PERMISSOES:
            continue
        caminho = r.caminho.format(**{p: uuid4() for p in r.parametros})
        resp = cliente_http.request(r.metodo, caminho, json={})
        if perfil in PERMISSOES[r.acesso]:
            assert resp.status_code != 403, r
        else:
            assert resp.status_code == 403 and resp.json()["codigo"] == "proibido", r
        verificadas += 1
    assert verificadas >= 3


def test_descoberta_enxerga_permissao_declarada_no_include_e_em_roteador_aninhado():
    from fastapi import APIRouter, Depends, FastAPI

    from app.nucleo.perfis import exigir
    from app.nucleo.sessao import contexto_atual

    interno = APIRouter(prefix="/interno")
    interno.get("/a")(lambda: None)
    interno.get("/b/{item_id}", dependencies=[Depends(exigir("cadastro.ler"))])(
        lambda item_id: None
    )
    externo = APIRouter(prefix="/externo")
    externo.include_router(interno, dependencies=[Depends(contexto_atual)])
    app = FastAPI()
    app.include_router(externo)
    por_chave = {(r.metodo, r.caminho): r for r in rotas_da_api(app)}
    assert por_chave[("GET", "/externo/interno/a")].acesso == "login"
    b = por_chave[("GET", "/externo/interno/b/{item_id}")]
    assert b.acesso == "cadastro.ler" and b.parametros == ["item_id"]
