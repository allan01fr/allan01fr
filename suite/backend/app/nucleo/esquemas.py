"""Esquemas comuns: entrada estrita, página de resultados e parâmetros de lista."""

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class EsquemaEntrada(BaseModel):
    """Base de toda entrada: recusa campos extras e apara espaços."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Pagina[T](BaseModel):
    itens: list[T]
    total: int


class ParametrosLista:
    """Dependência com os parâmetros comuns de listagem."""

    def __init__(
        self,
        limite: int = Query(50, ge=1, le=200),
        deslocamento: int = Query(0, ge=0),
        busca: str | None = None,
        incluir_arquivados: bool = False,
    ):
        self.limite = limite
        self.deslocamento = deslocamento
        self.busca = busca
        self.incluir_arquivados = incluir_arquivados
