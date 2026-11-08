"""Esquemas comuns: entrada estrita, página de resultados e parâmetros de lista."""

from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

LIMITE_MAXIMO_LISTA = 200


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
        limite: int = Query(50, ge=1, le=LIMITE_MAXIMO_LISTA),
        deslocamento: int = Query(0, ge=0),
        busca: str | None = None,
        incluir_arquivados: bool = False,
    ):
        self.limite = limite
        self.deslocamento = deslocamento
        self.busca = busca
        self.incluir_arquivados = incluir_arquivados


class LoginEntrada(EsquemaEntrada):
    email: str = Field(max_length=254)
    senha: str = Field(max_length=200)


class EmpresaResumo(BaseModel):
    id: UUID
    nome: str


class EuSaida(BaseModel):
    id: UUID
    nome: str
    email: str
    empresa: EmpresaResumo
    perfis: list[str]
    permissoes: list[str]
