"""Ponto de entrada da API."""

from fastapi import FastAPI

from app.nucleo.erros import instalar_tratadores
from app.nucleo.rotas import roteador as roteador_nucleo


def criar_app() -> FastAPI:
    app = FastAPI(title="KAPTEK Suíte")
    instalar_tratadores(app)
    app.include_router(roteador_nucleo)

    @app.get("/api/saude")
    def saude():
        return {"situacao": "ok"}

    return app
