"""Descobre as rotas da API e a permissão que cada uma exige (usado nos testes de acesso)."""

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from starlette.routing import Route

from app.nucleo.sessao import contexto_atual

ROTAS_PUBLICAS = {
    ("GET", "/api/saude"),
    ("POST", "/api/nucleo/sessao"),
    ("DELETE", "/api/nucleo/sessao"),
}


# Rotas de documentação que o FastAPI cria sozinho (só existem em desenvolvimento).
ROTAS_DE_DOCUMENTACAO = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


@dataclass
class Rota:
    metodo: str
    caminho: str
    acesso: str  # "publica", "login" ou o nome da permissão
    parametros: list[str]
    no_esquema: bool = True  # include_in_schema


def _acesso(dependente: Dependant) -> str:
    """Permissão exigida (a mais específica), "login" ou "publica", olhando as dependências."""
    resultado = "publica"
    for sub in dependente.dependencies:
        permissao = getattr(sub.call, "permissao", None)
        if permissao is not None:
            return permissao
        if sub.call is contexto_atual:
            resultado = "login"
        interna = _acesso(sub)
        if interna != "publica":
            resultado = interna
    return resultado


def _acesso_da_rota(rota: APIRoute, extras: list) -> str:
    """Permissão da rota, contando as dependências declaradas ao incluir o roteador."""
    for dependencia in extras:
        permissao = getattr(dependencia.dependency, "permissao", None)
        if permissao is not None:
            return permissao
    acesso = _acesso(rota.dependant)
    if acesso == "publica" and any(d.dependency is contexto_atual for d in extras):
        return "login"
    return acesso


def _percorrer(rotas, inclusao=None):
    """Percorre as rotas, entrando nos roteadores incluídos (o FastAPI recente os embrulha).

    `inclusao` é o contexto de inclusão (prefixo e dependências do include_router).
    """
    for rota in rotas:
        if isinstance(rota, APIRoute):
            caminho = inclusao.path_for(rota) if inclusao else rota.path
            yield rota, caminho, list(inclusao.dependencies) if inclusao else []
        elif hasattr(rota, "original_router"):  # roteador incluído
            yield from _percorrer(rota.original_router.routes, rota.include_context)
        elif isinstance(rota, Route) and rota.path in ROTAS_DE_DOCUMENTACAO:
            continue
        else:
            # Mount, WebSocketRoute, Route comum...: não sabemos que permissão exigem.
            raise TypeError(f"Tipo de rota não reconhecido na descoberta: {rota!r}")


def rotas_da_api(app: FastAPI) -> list[Rota]:
    """Todas as rotas da API com a permissão de cada uma.

    Confere que o conjunto (método, caminho) bate com o OpenAPI público: se a descoberta
    perder uma rota (ou inventar uma), o teste quebra aqui.
    """
    rotas = []
    for rota, caminho, extras in _percorrer(app.routes):
        for metodo in sorted(rota.methods):
            parametros = [p.name for p in rota.dependant.path_params]
            acesso = _acesso_da_rota(rota, extras)
            rotas.append(Rota(metodo, caminho, acesso, parametros, rota.include_in_schema))
    # app.openapi() funciona mesmo com a documentação desligada (openapi_url=None).
    publicas = {(r.metodo, r.caminho) for r in rotas if r.no_esquema}
    no_openapi = {
        (metodo.upper(), caminho)
        for caminho, operacoes in app.openapi()["paths"].items()
        for metodo in operacoes
    }
    assert publicas == no_openapi, publicas ^ no_openapi
    return rotas
