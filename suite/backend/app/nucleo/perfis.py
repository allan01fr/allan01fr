"""Perfis de acesso. A matriz de permissões entra numa tarefa posterior."""

from enum import StrEnum


class Perfil(StrEnum):
    ADMIN = "admin"
    ENGENHARIA = "engenharia"
    COMERCIAL = "comercial"
    FINANCEIRO = "financeiro"
    CAMPO = "campo"
