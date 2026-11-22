"""Ambiente do Alembic: URL vinda de Configuracao e modelos de importar_modelos()."""

from alembic import context
from sqlalchemy import create_engine

from app.nucleo.banco import Base
from app.nucleo.config import obter_configuracao
from app.registro import importar_modelos

importar_modelos()

if context.is_offline_mode():
    context.configure(
        url=obter_configuracao().banco_url,
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    motor = create_engine(obter_configuracao().banco_url)
    with motor.connect() as conexao:
        context.configure(connection=conexao, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()
