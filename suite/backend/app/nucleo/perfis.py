"""Perfis de acesso e a matriz de permissões (quem pode o quê)."""

from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated

from app.nucleo.erros import Proibido

if TYPE_CHECKING:
    from app.nucleo.contexto import Contexto


class Perfil(StrEnum):
    ADMIN = "admin"
    ENGENHARIA = "engenharia"
    COMERCIAL = "comercial"
    FINANCEIRO = "financeiro"
    CAMPO = "campo"


TODOS = frozenset(Perfil)

# Uma permissão por tipo de ação. Rota nova declara a sua com `exigir("...")`.
PERMISSOES: dict[str, frozenset[Perfil]] = {
    "cadastro.ler": TODOS,
    # Cobre cliente, contato e obra.
    "cadastro.editar_cliente": frozenset({Perfil.ADMIN, Perfil.COMERCIAL, Perfil.ENGENHARIA}),
    # Cobre ambiente, ativo e importação.
    "cadastro.editar_tecnico": frozenset({Perfil.ADMIN, Perfil.ENGENHARIA, Perfil.CAMPO}),
    "nucleo.usuarios": frozenset({Perfil.ADMIN}),
    "nucleo.empresa_ler": TODOS,
    "nucleo.empresa_editar": frozenset({Perfil.ADMIN}),
    "nucleo.arquivos": TODOS,
    "nucleo.tarefas": TODOS,
    "nucleo.tarefa_exemplo": frozenset({Perfil.ADMIN}),
}


def exigir(permissao: str) -> Callable[..., "Contexto"]:
    """Dependência do FastAPI: exige login e que algum perfil do usuário tenha a permissão."""
    # Importação tardia: contexto.py e sessao.py importam este módulo (Perfil).
    from fastapi import Depends

    from app.nucleo.contexto import Contexto
    from app.nucleo.sessao import contexto_atual

    permitidos = PERMISSOES[permissao]  # permissão desconhecida: KeyError na importação da rota

    def dependencia(contexto: Annotated[Contexto, Depends(contexto_atual)]) -> Contexto:
        if not contexto.perfis & permitidos:
            raise Proibido()
        return contexto

    dependencia.permissao = permissao  # type: ignore[attr-defined]
    return dependencia


def permissoes_de(perfis: Iterable[Perfil]) -> list[str]:
    """Permissões somadas dos perfis, em ordem alfabética."""
    perfis = set(perfis)
    return sorted(nome for nome, permitidos in PERMISSOES.items() if perfis & permitidos)
