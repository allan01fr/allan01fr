"""Autenticação por e-mail e senha."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.nucleo.erros import ErroDominio
from app.nucleo.modelos import Usuario
from app.nucleo.senhas import HASH_FICTICIO, conferir_senha, normalizar_email


def _credenciais_invalidas() -> ErroDominio:
    return ErroDominio("credenciais_invalidas", "E-mail ou senha incorretos.", 401)


def autenticar(sessao: Session, email: str, senha: str) -> Usuario:
    """Devolve o usuário ativo cuja senha confere; qualquer falha dá o mesmo erro.

    Este é o único ponto do código que busca usuário SEM filtro de empresa: no login ainda não
    se sabe a empresa, e o e-mail é único em todo o sistema. Todo o resto parte do Contexto.
    """
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == normalizar_email(email)))
    if usuario is None:
        # Confere um hash fictício para o tempo de resposta não revelar se o e-mail existe.
        conferir_senha(senha, HASH_FICTICIO)
        raise _credenciais_invalidas()
    if not conferir_senha(senha, usuario.senha_hash) or not usuario.ativo:
        raise _credenciais_invalidas()
    return usuario
