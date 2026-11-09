"""Administração de usuários da própria empresa."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.nucleo.auditoria import registrar_auditoria
from app.nucleo.contexto import Contexto
from app.nucleo.empresa import criar_usuario
from app.nucleo.erros import RegraNegocio
from app.nucleo.esquemas import Pagina, UsuarioAlteracao, UsuarioEntrada, UsuarioSaida
from app.nucleo.modelos import Empresa, PerfilUsuario, Usuario
from app.nucleo.perfis import Perfil
from app.nucleo.repositorio import UsuarioRepositorio

MENSAGEM_AUTO_ADMIN = "Você não pode remover o próprio acesso de administrador."
MENSAGEM_SEM_ADMIN = "A empresa precisa ter pelo menos um administrador ativo."


def _saida(usuario: Usuario) -> UsuarioSaida:
    return UsuarioSaida(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        ativo=usuario.ativo,
        perfis=sorted(p.perfil for p in usuario.perfis),
    )


def listar_usuarios(
    sessao: Session, ctx: Contexto, limite: int, deslocamento: int
) -> Pagina[UsuarioSaida]:
    repo = UsuarioRepositorio(sessao, ctx.empresa_id)
    consulta = repo.consulta().order_by(Usuario.nome, Usuario.email)
    usuarios, total = repo.listar(consulta, limite, deslocamento)
    return Pagina(itens=[_saida(u) for u in usuarios], total=total)


def criar_usuario_na_empresa(
    sessao: Session, ctx: Contexto, entrada: UsuarioEntrada
) -> UsuarioSaida:
    """A empresa vem sempre do contexto do admin, nunca do corpo da requisição."""
    usuario = criar_usuario(
        sessao, ctx.empresa_id, entrada.nome, entrada.email, entrada.senha, entrada.perfis
    )
    registrar_auditoria(
        sessao,
        ctx.empresa_id,
        ctx.usuario_id,
        "usuario.criar",
        "usuario",
        usuario.id,
        {"email": usuario.email, "perfis": sorted(p.perfil for p in usuario.perfis)},
    )
    return _saida(usuario)


def _trocar_perfis(usuario: Usuario, novos: set[Perfil]) -> None:
    """Remove só os perfis que saíram e acrescenta os novos (evita violar a unicidade)."""
    desejados = {p.value for p in novos}
    usuario.perfis = [p for p in usuario.perfis if p.perfil in desejados]
    existentes = {p.perfil for p in usuario.perfis}
    for perfil in sorted(desejados - existentes):
        usuario.perfis.append(PerfilUsuario(empresa_id=usuario.empresa_id, perfil=perfil))


def garantir_admin_ativo(sessao: Session, empresa_id: UUID) -> None:
    """Falha se a empresa ficou sem nenhum usuário ativo com o perfil admin."""
    admins = sessao.scalar(
        select(func.count())
        .select_from(PerfilUsuario)
        .join(Usuario, Usuario.id == PerfilUsuario.usuario_id)
        .where(
            PerfilUsuario.empresa_id == empresa_id,
            PerfilUsuario.perfil == Perfil.ADMIN.value,
            Usuario.empresa_id == empresa_id,
            Usuario.ativo.is_(True),
        )
    )
    if not admins:
        raise RegraNegocio(MENSAGEM_SEM_ADMIN)


def alterar_usuario(
    sessao: Session, ctx: Contexto, usuario_id: UUID, alteracao: UsuarioAlteracao
) -> UsuarioSaida:
    # Trava a linha da empresa: alterações de usuário da mesma empresa rodam em série, e a
    # conferência do último admin abaixo não corre contra outra alteração simultânea.
    sessao.execute(select(Empresa.id).where(Empresa.id == ctx.empresa_id).with_for_update())
    # Usuário de outra empresa não é achado pelo repositório: 404, nunca 403.
    usuario = UsuarioRepositorio(sessao, ctx.empresa_id).obter_ou_erro(
        usuario_id, "Usuário não encontrado."
    )
    if usuario.id == ctx.usuario_id:
        # O ator é sempre um admin ativo; por isso a empresa nunca perde o último admin ativo
        # por esta rota: só o próprio ator poderia ser o último, e ele não pode se remover.
        if alteracao.ativo is False:
            raise RegraNegocio(MENSAGEM_AUTO_ADMIN)
        if alteracao.perfis is not None and Perfil.ADMIN not in alteracao.perfis:
            raise RegraNegocio(MENSAGEM_AUTO_ADMIN)
    antes = {
        "nome": usuario.nome,
        "ativo": usuario.ativo,
        "perfis": sorted(p.perfil for p in usuario.perfis),
    }
    if alteracao.nome is not None:
        usuario.nome = alteracao.nome
    if alteracao.ativo is not None:
        usuario.ativo = alteracao.ativo
    if alteracao.perfis is not None:
        _trocar_perfis(usuario, alteracao.perfis)
    sessao.flush()
    sessao.refresh(usuario)
    garantir_admin_ativo(sessao, ctx.empresa_id)
    registrar_auditoria(
        sessao,
        ctx.empresa_id,
        ctx.usuario_id,
        "usuario.alterar",
        "usuario",
        usuario.id,
        {
            "antes": antes,
            "depois": {
                "nome": usuario.nome,
                "ativo": usuario.ativo,
                "perfis": _saida(usuario).perfis,
            },
        },
    )
    return _saida(usuario)
