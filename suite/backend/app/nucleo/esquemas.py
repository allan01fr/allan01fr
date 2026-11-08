"""Esquemas comuns: entrada estrita, página de resultados e parâmetros de lista."""

from datetime import datetime
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.nucleo.perfis import Perfil

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


class UsuarioEntrada(EsquemaEntrada):
    nome: str = Field(min_length=1, max_length=200)
    email: EmailStr = Field(max_length=254)
    senha: str = Field(max_length=200)
    perfis: set[Perfil]


class UsuarioAlteracao(EsquemaEntrada):
    """Só os campos enviados mudam; `null` não é aceito em nenhum deles."""

    nome: str | None = Field(default=None, min_length=1, max_length=200)
    ativo: bool | None = None
    perfis: set[Perfil] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _sem_nulo_explicito(self):
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError("Valor não pode ser nulo.")
        return self


class UsuarioSaida(BaseModel):
    id: UUID
    nome: str
    email: str
    ativo: bool
    perfis: list[str]


class ArquivoSaida(BaseModel):
    id: UUID
    nome: str
    tipo_conteudo: str
    tamanho_bytes: int
    criado_em: datetime


class UrlAssinadaSaida(BaseModel):
    url: str
    expira_em: datetime
