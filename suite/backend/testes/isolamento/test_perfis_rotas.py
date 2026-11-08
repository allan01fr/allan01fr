from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.nucleo.perfis import PERMISSOES, Perfil
from testes.fabricas import entrar, nova_empresa, novo_usuario
from testes.rotas_da_api import ROTAS_PUBLICAS, rotas_da_api

# Cada tarefa que cria rota acrescenta aqui (método, caminho, permissão). Rota nova sem
# entrada aqui, ou rota que sumiu, quebra o teste de propósito.
ROTAS_ESPERADAS = {
    ("GET", "/api/saude", "publica"),
    ("POST", "/api/nucleo/sessao", "publica"),
    ("DELETE", "/api/nucleo/sessao", "publica"),
    ("GET", "/api/nucleo/eu", "login"),
    ("GET", "/api/nucleo/usuarios", "nucleo.usuarios"),
    ("POST", "/api/nucleo/usuarios", "nucleo.usuarios"),
    ("PATCH", "/api/nucleo/usuarios/{usuario_id}", "nucleo.usuarios"),
}


def test_conjunto_de_rotas_e_permissoes_e_o_esperado():
    encontradas = {(r.metodo, r.caminho, r.acesso) for r in rotas_da_api(criar_app())}
    assert encontradas == ROTAS_ESPERADAS


def test_descoberta_recusa_tipo_de_rota_desconhecido():
    from fastapi import FastAPI
    from starlette.routing import Mount

    app = FastAPI()
    app.router.routes.append(Mount("/estatico", app=FastAPI()))
    with pytest.raises(TypeError, match="não reconhecido"):
        rotas_da_api(app)


def test_descoberta_confere_com_o_openapi():
    from fastapi import FastAPI

    app = FastAPI()
    app.get("/a")(lambda: None)
    rotas_da_api(app)  # passa
    app.get("/escondida", include_in_schema=False)(lambda: None)
    rotas_da_api(app)  # fora do esquema não conta na comparação


def test_documentacao_so_existe_em_desenvolvimento(monkeypatch):
    from app.nucleo.config import obter_configuracao

    cfg = obter_configuracao()
    monkeypatch.setattr(cfg, "ambiente", "producao")
    prod = TestClient(criar_app(), raise_server_exceptions=False)
    for caminho in ("/docs", "/redoc", "/openapi.json"):
        assert prod.get(caminho).status_code == 404, caminho
    monkeypatch.setattr(cfg, "ambiente", "dev")
    assert TestClient(criar_app()).get("/openapi.json").status_code == 200
    # a descoberta continua funcionando com a documentação desligada
    monkeypatch.setattr(cfg, "ambiente", "producao")
    assert rotas_da_api(criar_app())


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
    com_permissao = {(r.metodo, r.caminho, r.acesso) for r in rotas_da_api(cliente_http.app)}
    assert verificadas == len([e for e in ROTAS_ESPERADAS if e[2] in PERMISSOES])
    assert com_permissao == ROTAS_ESPERADAS


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
