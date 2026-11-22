"""Repositório base: toda consulta de módulo parte de `consulta()`, sempre filtrada por empresa."""

from uuid import UUID

from sqlalchemy import Select, func, inspect, select
from sqlalchemy.orm import Session

from app.nucleo.banco import ComEmpresa
from app.nucleo.erros import NaoEncontrado
from app.nucleo.esquemas import LIMITE_MAXIMO_LISTA
from app.nucleo.modelos import Usuario


class RepositorioBase[M: ComEmpresa]:
    modelo: type[M]

    def __init__(self, sessao: Session, empresa_id: UUID):
        if empresa_id is None:
            raise ValueError("empresa_id é obrigatório.")
        self.sessao = sessao
        self.empresa_id = empresa_id

    def consulta(self) -> Select[tuple[M]]:
        return (
            select(self.modelo)
            .where(self.modelo.empresa_id == self.empresa_id)
            .execution_options(suite_empresa_id=self.empresa_id)
        )

    def obter(self, id_: UUID) -> M | None:
        return self.sessao.scalar(self.consulta().where(self.modelo.id == id_))

    def obter_ou_erro(self, id_: UUID, mensagem: str) -> M:
        obj = self.obter(id_)
        if obj is None:
            raise NaoEncontrado(mensagem)
        return obj

    def listar(self, consulta: Select, limite: int, deslocamento: int) -> tuple[list[M], int]:
        if consulta.get_execution_options().get("suite_empresa_id") != self.empresa_id:
            raise ValueError("A consulta deve partir de consulta() deste repositório.")
        if not 1 <= limite <= LIMITE_MAXIMO_LISTA:
            raise ValueError(f"O limite deve estar entre 1 e {LIMITE_MAXIMO_LISTA}.")
        if deslocamento < 0:
            raise ValueError("O deslocamento não pode ser negativo.")
        total = self.sessao.scalar(select(func.count()).select_from(consulta.subquery())) or 0
        itens = self.sessao.scalars(consulta.limit(limite).offset(deslocamento)).all()
        return list(itens), total

    def adicionar(self, obj: M) -> M:
        estado = inspect(obj)
        if (estado.persistent or estado.detached) and obj.empresa_id != self.empresa_id:
            raise ValueError("Objeto de outra empresa não pode ser adicionado a este repositório.")
        obj.empresa_id = self.empresa_id
        self.sessao.add(obj)
        self.sessao.flush()
        return obj


class UsuarioRepositorio(RepositorioBase[Usuario]):
    modelo = Usuario
