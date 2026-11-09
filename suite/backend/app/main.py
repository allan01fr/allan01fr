"""Ponto de entrada da API."""

from fastapi import FastAPI

from app.nucleo.config import obter_configuracao
from app.nucleo.erros import instalar_tratadores
from app.nucleo.rotas import roteador as roteador_nucleo


def criar_app() -> FastAPI:
    em_desenvolvimento = obter_configuracao().ambiente == "dev"
    app = FastAPI(
        title="KAPTEK Suíte",
        docs_url="/docs" if em_desenvolvimento else None,
        redoc_url="/redoc" if em_desenvolvimento else None,
        openapi_url="/openapi.json" if em_desenvolvimento else None,
    )
    instalar_tratadores(app)
    app.include_router(roteador_nucleo)

    @app.get("/api/saude")
    def saude():
        return {"situacao": "ok"}

    return app
