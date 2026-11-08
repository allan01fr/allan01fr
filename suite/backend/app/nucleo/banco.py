"""Base declarativa, mixin de empresa e sessão do banco."""

import uuid
from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, ForeignKey, MetaData, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.nucleo.config import obter_configuracao

# Nomes previsíveis para índices e restrições, para a migração bater com os modelos.
CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


class ComEmpresa:
    """Colunas comuns de toda tabela que pertence a uma empresa."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("empresa.id"), nullable=False, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


@lru_cache
def obter_fabrica_sessao() -> sessionmaker[Session]:
    motor = create_engine(obter_configuracao().banco_url, pool_pre_ping=True)
    return sessionmaker(bind=motor, expire_on_commit=False)


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: commit no sucesso, rollback na exceção."""
    with obter_fabrica_sessao()() as sessao:
        try:
            yield sessao
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise
