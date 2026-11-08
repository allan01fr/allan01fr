"""Registro de auditoria: quem fez o quê, em qual entidade."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.nucleo.modelos import Auditoria


def registrar_auditoria(
    sessao: Session,
    empresa_id: UUID,
    usuario_id: UUID | None,
    acao: str,
    entidade: str,
    entidade_id: UUID | None,
    dados: dict | None = None,
) -> None:
    sessao.add(
        Auditoria(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            dados=dados,
        )
    )
    sessao.flush()
