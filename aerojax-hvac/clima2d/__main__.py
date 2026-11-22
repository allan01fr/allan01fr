"""Uso: python -m clima2d projeto.json relatorio.html"""

import argparse
import sys

from .documento import ErroProjeto
from .estudo import rodar_estudo


def main(argv=None):
    ap = argparse.ArgumentParser(prog="clima2d", description="Roda um estudo Clima2D e grava o relatório.")
    ap.add_argument("projeto", help="arquivo JSON do projeto")
    ap.add_argument("relatorio", help="arquivo HTML do relatório a gravar")
    args = ap.parse_args(argv)
    try:
        with open(args.projeto, "rb") as f:
            conteudo = f.read()
    except OSError:
        print(f"Não foi possível ler o arquivo {args.projeto}.", file=sys.stderr)
        return 2
    try:
        res = rodar_estudo(conteudo, args.relatorio)
    except ErroProjeto as e:
        print(f"Projeto inválido: {e}", file=sys.stderr)
        return 2
    except OSError:
        print(f"Não foi possível gravar o relatório em {args.relatorio}.", file=sys.stderr)
        return 2
    atendidos = sum(1 for c in res["conformidade"] if c["atende"])
    print(f"Relatório gravado em {res['relatorio']}")
    print(f"{atendidos} de {len(res['conformidade'])} critérios atendidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
