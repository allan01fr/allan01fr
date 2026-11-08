"""Modelos do núcleo: empresa, usuário, perfis e auditoria."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.nucleo.banco import Base, ComEmpresa
from app.nucleo.perfis import Perfil


class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Usuario(ComEmpresa, Base):
    __tablename__ = "usuario"
    __table_args__ = (CheckConstraint("email = lower(email)", name="email_minusculo"),)

    nome: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254), unique=True)  # sempre minúsculo
    senha_hash: Mapped[str] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(default=True)
    perfis: Mapped[list["PerfilUsuario"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class PerfilUsuario(ComEmpresa, Base):
    __tablename__ = "perfil_usuario"
    __table_args__ = (
        UniqueConstraint("usuario_id", "perfil"),
        CheckConstraint(
            "perfil IN (" + ", ".join(f"'{p.value}'" for p in Perfil) + ")", name="perfil_valido"
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"))
    perfil: Mapped[str] = mapped_column(String(20))


class Auditoria(ComEmpresa, Base):
    __tablename__ = "auditoria"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
    acao: Mapped[str] = mapped_column(String(100))
    entidade: Mapped[str] = mapped_column(String(100))
    entidade_id: Mapped[uuid.UUID | None] = mapped_column()
    dados: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
