"""Contexto do usuário autenticado, entregue às rotas e serviços."""

from dataclasses import dataclass
from uuid import UUID

from app.nucleo.perfis import Perfil


@dataclass(frozen=True)
class Contexto:
    usuario_id: UUID
    empresa_id: UUID
    perfis: frozenset[Perfil]
