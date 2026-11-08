"""Sessão em cookie httpOnly assinado: emitir, apagar e ler o contexto do usuário logado."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select

from app.nucleo.banco import SessaoDoBanco
from app.nucleo.config import obter_configuracao
from app.nucleo.contexto import Contexto
from app.nucleo.erros import NaoAutenticado
from app.nucleo.modelos import Usuario
from app.nucleo.perfis import Perfil

COOKIE_SESSAO = "suite_sessao"


def _serializador() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(obter_configuracao().segredo_sessao, salt="sessao")


def emitir_cookie(resposta: Response, usuario_id: UUID) -> None:
    config = obter_configuracao()
    resposta.set_cookie(
        COOKIE_SESSAO,
        _serializador().dumps({"u": str(usuario_id)}),
        max_age=config.sessao_horas * 3600,
        httponly=True,
        samesite="lax",
        secure=config.cookie_seguro,
        path="/",
    )


def apagar_cookie(resposta: Response) -> None:
    config = obter_configuracao()
    resposta.delete_cookie(
        COOKIE_SESSAO, path="/", httponly=True, samesite="lax", secure=config.cookie_seguro
    )


def _usuario_do_cookie(request: Request) -> UUID:
    """Lê o id do cookie; ausente, adulterado, expirado ou malformado dá NaoAutenticado."""
    valor = request.cookies.get(COOKIE_SESSAO)
    if not valor:
        raise NaoAutenticado()
    max_age = obter_configuracao().sessao_horas * 3600
    try:
        return UUID(_serializador().loads(valor, max_age=max_age)["u"])
    except (BadSignature, KeyError, TypeError, ValueError) as erro:
        raise NaoAutenticado() from erro


def contexto_atual(request: Request, sessao: SessaoDoBanco) -> Contexto:
    """Dependência: o usuário logado. Usuário removido ou desativado perde a sessão na hora."""
    usuario = sessao.scalar(select(Usuario).where(Usuario.id == _usuario_do_cookie(request)))
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado()
    return Contexto(
        usuario_id=usuario.id,
        empresa_id=usuario.empresa_id,
        perfis=frozenset(Perfil(p.perfil) for p in usuario.perfis),
    )


ContextoAtual = Annotated[Contexto, Depends(contexto_atual)]
