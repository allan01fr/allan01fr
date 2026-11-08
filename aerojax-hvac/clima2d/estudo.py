"""Estudo de ponta a ponta: projeto -> simulação -> relatório em arquivo, com rastreabilidade."""

import datetime

from . import __version__
from .criterios import conformidade
from .documento import ErroProjeto, carregar_json, validar_documento
from .montagem import validar
from .relatorio import gravar_relatorio
from .simulacao import simular_projeto

NORMAS = ("ISO 7730:2005", "ABNT NBR 16401-2:2008")
AVISOS_NORMA = (
    "ABNT NBR 16401-2:2008 foi substituída pela edição de 2024; "
    "a faixa de umidade deste estudo segue a edição de 2008.",
)


def rodar_estudo(documento, destino_relatorio, progresso=None):
    """Roda o estudo e grava o relatório. Recusa projetos inválidos antes de simular."""
    if isinstance(documento, dict):
        projeto = validar_documento(documento)
    else:
        projeto = carregar_json(documento)
    erros = validar(projeto)
    if erros:
        raise ErroProjeto("O projeto não pode ser simulado: " + " ".join(erros))

    resultado = simular_projeto(projeto, progresso)
    caminho = gravar_relatorio(projeto, resultado, destino_relatorio)
    return {
        "relatorio": caminho,
        "indicadores": resultado["indicadores"],
        "conformidade": conformidade(resultado, projeto["criterios"]),
        "avisos": list(AVISOS_NORMA),
        "rastreabilidade": {
            "motor": "clima2d",
            "versao_motor": __version__,
            "normas": list(NORMAS),
            "data": datetime.date.today().isoformat(),
            "entradas": projeto,
        },
    }
