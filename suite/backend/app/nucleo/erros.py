"""Erros de domínio e tratadores que produzem o formato único de erro."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

registro = logging.getLogger(__name__)


class ErroDominio(Exception):
    def __init__(self, codigo: str, mensagem: str, status: int, detalhes: dict | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status
        self.detalhes = detalhes or {}


class NaoAutenticado(ErroDominio):
    def __init__(self, mensagem: str = "Sessão expirada ou inválida. Entre novamente."):
        super().__init__("nao_autenticado", mensagem, 401)


class Proibido(ErroDominio):
    def __init__(self, mensagem: str = "Seu perfil não permite esta ação."):
        super().__init__("proibido", mensagem, 403)


class NaoEncontrado(ErroDominio):
    def __init__(self, mensagem: str = "Recurso não encontrado."):
        super().__init__("nao_encontrado", mensagem, 404)


class Conflito(ErroDominio):
    def __init__(self, mensagem: str, detalhes: dict | None = None):
        super().__init__("conflito", mensagem, 409, detalhes)


class EntradaInvalida(ErroDominio):
    def __init__(self, mensagem: str, detalhes: dict | None = None):
        super().__init__("entrada_invalida", mensagem, 422, detalhes)


class RegraNegocio(ErroDominio):
    def __init__(self, mensagem: str):
        super().__init__("regra_negocio", mensagem, 422)


def _resposta(status: int, codigo: str, mensagem: str, detalhes: dict | None = None):
    corpo = {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes or {}}
    return JSONResponse(status_code=status, content=corpo)


def _mensagem_de_validacao(erro: dict) -> str:
    tipo = erro.get("type")
    ctx = erro.get("ctx") or {}
    if tipo == "missing":
        return "Campo obrigatório."
    if tipo == "extra_forbidden":
        return "Campo não permitido."
    if tipo == "greater_than":
        return f"Deve ser maior que {ctx['gt']}."
    if tipo == "less_than_equal":
        return f"Deve ser no máximo {ctx['le']}."
    if tipo == "string_too_long":
        return "Texto longo demais."
    if tipo == "value_error":
        return str(erro.get("msg", "")).removeprefix("Value error, ")
    return "Valor inválido."


def instalar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroDominio)
    def _dominio(_: Request, erro: ErroDominio):
        return _resposta(erro.status, erro.codigo, erro.mensagem, erro.detalhes)

    @app.exception_handler(StarletteHTTPException)
    def _http(_: Request, erro: StarletteHTTPException):
        if erro.status_code == 404:
            return _resposta(404, "nao_encontrado", "Recurso não encontrado.")
        if erro.status_code == 405:
            return _resposta(405, "metodo_nao_permitido", "Método não permitido.")
        return _resposta(erro.status_code, "erro_http", str(erro.detail))

    @app.exception_handler(RequestValidationError)
    def _validacao(_: Request, erro: RequestValidationError):
        campos = [
            {
                "campo": ".".join(str(p) for p in e["loc"][1:]),
                "mensagem": _mensagem_de_validacao(e),
            }
            for e in erro.errors()
        ]
        return _resposta(422, "entrada_invalida", "Dados inválidos.", {"campos": campos})

    @app.exception_handler(Exception)
    def _inesperado(_: Request, erro: Exception):
        registro.error("Erro inesperado", exc_info=erro)
        return _resposta(500, "erro_interno", "Erro interno. Tente novamente.")
