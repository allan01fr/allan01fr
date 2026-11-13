"""Rotas do núcleo: sessão (login e logout) e dados do usuário logado."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, UploadFile
from sqlalchemy import select

from app.nucleo.arquivos import (
    Armazenamento,
    guardar_arquivo,
    obter_armazenamento,
    url_de_download,
)
from app.nucleo.auditoria import registrar_auditoria
from app.nucleo.banco import SessaoDoBanco
from app.nucleo.config import obter_configuracao
from app.nucleo.contexto import Contexto
from app.nucleo.erros import NaoAutenticado
from app.nucleo.esquemas import (
    ArquivoSaida,
    EmpresaResumo,
    EuSaida,
    LoginEntrada,
    Pagina,
    ParametrosLista,
    UrlAssinadaSaida,
    UsuarioAlteracao,
    UsuarioEntrada,
    UsuarioSaida,
)
from app.nucleo.login import autenticar
from app.nucleo.modelos import Empresa, Usuario
from app.nucleo.perfis import Perfil, exigir, permissoes_de
from app.nucleo.sessao import ContextoAtual, apagar_cookie, emitir_cookie
from app.nucleo.usuarios import (
    alterar_usuario,
    criar_usuario_na_empresa,
    listar_usuarios,
)

roteador = APIRouter(prefix="/api/nucleo", tags=["nucleo"])


def _eu(sessao: SessaoDoBanco, usuario: Usuario) -> EuSaida:
    empresa = sessao.scalar(select(Empresa).where(Empresa.id == usuario.empresa_id))
    return EuSaida(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        empresa=EmpresaResumo(id=empresa.id, nome=empresa.nome),
        perfis=sorted(p.perfil for p in usuario.perfis),
        permissoes=permissoes_de(Perfil(p.perfil) for p in usuario.perfis),
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


AdminDeUsuarios = Annotated[Contexto, Depends(exigir("nucleo.usuarios"))]


@roteador.get("/usuarios", response_model=Pagina[UsuarioSaida])
def listar(
    sessao: SessaoDoBanco,
    contexto: AdminDeUsuarios,
    parametros: Annotated[ParametrosLista, Depends()],
):
    return listar_usuarios(sessao, contexto, parametros.limite, parametros.deslocamento)


@roteador.post("/usuarios", response_model=UsuarioSaida, status_code=201)
def criar(entrada: UsuarioEntrada, sessao: SessaoDoBanco, contexto: AdminDeUsuarios):
    return criar_usuario_na_empresa(sessao, contexto, entrada)


@roteador.patch("/usuarios/{usuario_id}", response_model=UsuarioSaida)
def alterar(
    usuario_id: UUID, alteracao: UsuarioAlteracao, sessao: SessaoDoBanco, contexto: AdminDeUsuarios
):
    return alterar_usuario(sessao, contexto, usuario_id, alteracao)


ComArquivos = Annotated[Contexto, Depends(exigir("nucleo.arquivos"))]
ArmazenamentoAtual = Annotated[Armazenamento, Depends(obter_armazenamento)]


@roteador.post("/arquivos", response_model=ArquivoSaida, status_code=201)
def enviar_arquivo(
    arquivo: UploadFile,
    sessao: SessaoDoBanco,
    contexto: ComArquivos,
    armazenamento: ArmazenamentoAtual,
):
    # Lê no máximo o limite + 1 byte: assim um arquivo enorme não vai inteiro para a memória.
    limite = obter_configuracao().arquivo_max_bytes
    conteudo = arquivo.file.read(limite + 1)
    return guardar_arquivo(
        sessao,
        armazenamento,
        contexto.empresa_id,
        contexto.usuario_id,
        arquivo.filename or "",
        arquivo.content_type or "",
        conteudo,
    )


@roteador.get("/arquivos/{arquivo_id}/url", response_model=UrlAssinadaSaida)
def url_do_arquivo(
    arquivo_id: UUID,
    sessao: SessaoDoBanco,
    contexto: ComArquivos,
    armazenamento: ArmazenamentoAtual,
):
    return url_de_download(sessao, armazenamento, contexto.empresa_id, arquivo_id)
