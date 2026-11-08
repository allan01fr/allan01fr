"""Registro central: importa os modelos para o Alembic enxergar todas as tabelas."""

from importlib import import_module

MODULOS_DE_MODELOS = [
    "app.nucleo.modelos",
]


def importar_modelos() -> None:
    for caminho in MODULOS_DE_MODELOS:
        import_module(caminho)
