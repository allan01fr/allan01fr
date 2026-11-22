"""Criação de empresa e de usuário."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.nucleo.erros import Conflito, EntradaInvalida
from app.nucleo.modelos import Empresa, PerfilUsuario, Usuario
from app.nucleo.perfis import Perfil
from app.nucleo.senhas import gerar_hash, normalizar_email

TAMANHO_MINIMO_SENHA = 10


def criar_empresa(sessao: Session, nome: str) -> Empresa:
    empresa = Empresa(nome=nome)
    sessao.add(empresa)
    sessao.flush()
    return empresa


def criar_usuario(
    sessao: Session,
    empresa_id: uuid.UUID,
    nome: str,
    email: str,
    senha: str,
    perfis: set[Perfil],
) -> Usuario:
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise EntradaInvalida(f"A senha precisa de pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    if not perfis:
        raise EntradaInvalida("Escolha ao menos um perfil.")
    usuario = Usuario(
        empresa_id=empresa_id,
        nome=nome,
        email=normalizar_email(email),
        senha_hash=gerar_hash(senha),
        perfis=[PerfilUsuario(empresa_id=empresa_id, perfil=Perfil(p).value) for p in perfis],
    )
    try:
        with sessao.begin_nested():
            sessao.add(usuario)
    except IntegrityError as erro:
        raise Conflito("Já existe usuário com este e-mail.") from erro
    return usuario
