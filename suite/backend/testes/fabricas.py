"""Fábricas de dados para os testes."""

import uuid

from sqlalchemy.orm import Session

from app.nucleo.empresa import criar_empresa, criar_usuario
from app.nucleo.modelos import Empresa, Usuario
from app.nucleo.perfis import Perfil

SENHA_TESTE = "senha-de-teste-123"


def nova_empresa(sessao: Session, nome: str = "Empresa A") -> Empresa:
    return criar_empresa(sessao, nome)


def novo_usuario(
    sessao: Session, empresa: Empresa, perfis: set[Perfil], email: str | None = None
) -> Usuario:
    email = email or f"usuario-{uuid.uuid4().hex[:12]}@teste.com"
    return criar_usuario(sessao, empresa.id, "Usuário de Teste", email, SENHA_TESTE, perfis)
