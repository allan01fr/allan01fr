"""Comandos de linha: criar empresa, criar usuário e semear os dados de demonstração."""

import argparse
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from getpass import getpass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.nucleo.banco import obter_fabrica_sessao
from app.nucleo.empresa import criar_empresa, criar_usuario
from app.nucleo.erros import ErroDominio
from app.nucleo.modelos import Empresa, Usuario
from app.nucleo.perfis import Perfil


@contextmanager
def abrir_sessao() -> Iterator[Session]:
    """Sessão com commit no sucesso e rollback na exceção."""
    with obter_fabrica_sessao()() as sessao:
        try:
            yield sessao
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise


def _empresa_por_nome(sessao: Session, nome: str) -> Empresa:
    empresa = sessao.scalar(select(Empresa).where(Empresa.nome == nome).order_by(Empresa.criado_em))
    return empresa or criar_empresa(sessao, nome)


def _garantir_usuario(
    sessao: Session, empresa: Empresa, nome: str, email: str, senha: str, perfil: Perfil
) -> None:
    if sessao.scalar(select(Usuario.id).where(Usuario.email == email)) is None:
        criar_usuario(sessao, empresa.id, nome, email, senha, {perfil})


def semear_demo(sessao: Session, senha: str) -> None:
    """Cria as empresas e usuários de demonstração; pode rodar várias vezes."""
    empresa_a = _empresa_por_nome(sessao, "Empresa Demo A")
    for perfil in Perfil:
        _garantir_usuario(
            sessao, empresa_a, f"Demo {perfil.value}", f"{perfil.value}@demo-a.local", senha, perfil
        )
    empresa_b = _empresa_por_nome(sessao, "Empresa Demo B")
    _garantir_usuario(sessao, empresa_b, "Demo admin B", "admin@demo-b.local", senha, Perfil.ADMIN)


def _criar_empresa(sessao: Session, args: argparse.Namespace) -> int:
    empresa = criar_empresa(sessao, args.nome)
    print(empresa.id)
    return 0


def _criar_usuario(sessao: Session, args: argparse.Namespace) -> int:
    if sessao.get(Empresa, args.empresa_id) is None:
        print("Empresa não encontrada.", file=sys.stderr)
        return 1
    usuario = criar_usuario(
        sessao,
        args.empresa_id,
        args.nome,
        args.email,
        getpass("Senha: "),
        {Perfil(p) for p in args.perfil},
    )
    print(usuario.id)
    return 0


def _semear_demo(sessao: Session, _: argparse.Namespace) -> int:
    senha = os.environ.get("SUITE_SEMENTE_SENHA")
    if not senha:
        print("Defina SUITE_SEMENTE_SENHA.", file=sys.stderr)
        return 2
    semear_demo(sessao, senha)
    return 0


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comandos", description="Comandos da suíte KAPTEK.")
    sub = parser.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("criar-empresa", help="Cria uma empresa.")
    p.add_argument("--nome", required=True)
    p.set_defaults(executar=_criar_empresa)
    p = sub.add_parser("criar-usuario", help="Cria um usuário (a senha é pedida no terminal).")
    p.add_argument("--empresa-id", required=True, type=UUID)
    p.add_argument("--nome", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--perfil", required=True, action="append", choices=[x.value for x in Perfil])
    p.set_defaults(executar=_criar_usuario)
    p = sub.add_parser("semear-demo", help="Cria os dados de demonstração.")
    p.set_defaults(executar=_semear_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _montar_parser().parse_args(argv)
    try:
        with abrir_sessao() as sessao:
            return args.executar(sessao, args)
    except ErroDominio as erro:
        print(erro.mensagem, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
