"""Ponto de entrada da API."""

from fastapi import FastAPI

from app.nucleo.erros import instalar_tratadores


def criar_app() -> FastAPI:
    app = FastAPI(title="KAPTEK Suíte")
    instalar_tratadores(app)

    @app.get("/api/saude")
    def saude():
        return {"situacao": "ok"}

    return app
