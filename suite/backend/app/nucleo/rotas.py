"""Rotas do núcleo: sessão (login e logout) e dados do usuário logado."""

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.nucleo.auditoria import registrar_auditoria
from app.nucleo.banco import SessaoDoBanco
from app.nucleo.erros import NaoAutenticado
from app.nucleo.esquemas import EmpresaResumo, EuSaida, LoginEntrada
from app.nucleo.login import autenticar
from app.nucleo.modelos import Empresa, Usuario
from app.nucleo.sessao import ContextoAtual, apagar_cookie, emitir_cookie

roteador = APIRouter(prefix="/api/nucleo", tags=["nucleo"])


def _eu(sessao: SessaoDoBanco, usuario: Usuario) -> EuSaida:
    empresa = sessao.scalar(select(Empresa).where(Empresa.id == usuario.empresa_id))
    return EuSaida(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        empresa=EmpresaResumo(id=empresa.id, nome=empresa.nome),
        perfis=sorted(p.perfil for p in usuario.perfis),
        permissoes=[],  # preenchido quando a matriz de permissões entrar
    )


@roteador.post("/sessao", response_model=EuSaida)
def entrar(entrada: LoginEntrada, resposta: Response, sessao: SessaoDoBanco):
    usuario = autenticar(sessao, entrada.email, entrada.senha)
    registrar_auditoria(sessao, usuario.empresa_id, usuario.id, "login", "usuario", usuario.id)
    emitir_cookie(resposta, usuario.id)
    return _eu(sessao, usuario)


@roteador.delete("/sessao", status_code=204)
def sair(resposta: Response):
    apagar_cookie(resposta)
    resposta.status_code = 204
    return resposta


@roteador.get("/eu", response_model=EuSaida)
def eu(sessao: SessaoDoBanco, contexto: ContextoAtual):
    usuario = sessao.scalar(select(Usuario).where(Usuario.id == contexto.usuario_id))
    if usuario is None:
        raise NaoAutenticado()
    return _eu(sessao, usuario)
