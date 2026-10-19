"""
Avaliador seguro das expressões de driver do catálogo.

Um driver liga o formulário de um serviço à quantidade que multiplica as horas,
por exemplo  terminais*amostragem  ou  area*(0.0055*nivel__2d + 0.037*nivel__bim).
O catálogo é editado pelo usuário, então nada de eval(): só aritmética, comparações,
"a if cond else b" e as funções da lista abaixo.
"""

import ast
import math
import operator as op

CASAS_MAX = 15
TEXTO_MAX = 500


def _round(x, casas=None):
    """round() de inteiro com casas = -10**7 seguraria o servidor inteiro; em float é instantâneo."""
    if casas is None:
        return round(x)
    casas = int(casas)
    if abs(casas) > CASAS_MAX:
        raise ErroExpressao(f"round com {casas} casas: o limite é {CASAS_MAX}")
    return round(float(x), casas)


FUNCOES = {
    "ceil": math.ceil,
    "floor": math.floor,
    "round": _round,
    "sqrt": math.sqrt,
    "min": min,
    "max": max,
    "abs": abs,
}

# potência sempre em float: 9**9**9 com inteiros travaria o servidor inteiro; em float estoura na hora
_BIN = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: lambda a, b: float(a) ** float(b), ast.Mod: op.mod, ast.FloorDiv: op.floordiv,
}
_UN = {ast.UAdd: op.pos, ast.USub: op.neg, ast.Not: op.not_}
_CMP = {
    ast.Eq: op.eq, ast.NotEq: op.ne, ast.Lt: op.lt, ast.LtE: op.le,
    ast.Gt: op.gt, ast.GtE: op.ge,
}


_INT_MAX = 10 ** 15


class ErroExpressao(ValueError):
    pass


class DivisaoPorZero(ErroExpressao):
    pass


def _arvore(texto):
    texto = str(texto)
    if len(texto) > TEXTO_MAX:
        raise ErroExpressao(f"expressão com mais de {TEXTO_MAX} caracteres")
    try:
        return ast.parse(texto, mode="eval")
    except SyntaxError as e:
        raise ErroExpressao(f"expressão inválida '{texto}': {e.msg}") from None
    except (RecursionError, MemoryError, ValueError):     # aninhamento demais para o analisador
        raise ErroExpressao(f"expressão complexa demais: '{texto[:60]}...'") from None


def _checar(no):
    """Recusa qualquer nó fora da aritmética permitida (atributos, índices, lambdas...)."""
    for n in ast.walk(no):
        if isinstance(n, (ast.Expression, ast.Load, ast.Name, ast.BoolOp, ast.And, ast.Or,
                          ast.IfExp, ast.Compare)):
            continue
        if isinstance(n, ast.Constant):
            if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
                raise ErroExpressao(f"só números são aceitos como constante, não {n.value!r}")
            continue
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            continue
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UN:
            continue
        if type(n) in _BIN or type(n) in _UN or type(n) in _CMP:
            continue
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.func.id not in FUNCOES or n.keywords:
                raise ErroExpressao("só as funções " + ", ".join(sorted(FUNCOES)) + " são permitidas")
            continue
        raise ErroExpressao(f"elemento não permitido: {type(n).__name__}")


def nomes(texto):
    """Nomes de variáveis usados na expressão (sem as funções)."""
    arv = _arvore(texto)
    _checar(arv)
    chamadas = {n.func.id for n in ast.walk(arv) if isinstance(n, ast.Call)}
    return {n.id for n in ast.walk(arv) if isinstance(n, ast.Name)} - chamadas


def avaliar(texto, contexto):
    """Avalia a expressão com as variáveis de `contexto` e devolve float."""
    if texto is None or str(texto).strip() == "":
        return 0.0
    arv = _arvore(texto)
    _checar(arv)

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in contexto:
                raise ErroExpressao(f"variável desconhecida '{n.id}' em '{texto}'")
            return contexto[n.id]
        if isinstance(n, ast.BinOp):
            try:
                v = _BIN[type(n.op)](ev(n.left), ev(n.right))
            except ZeroDivisionError:
                raise DivisaoPorZero(f"divisão por zero em '{texto}'") from None
            # inteiro gigante passa a float, que estoura na hora em vez de multiplicar sem fim
            return float(v) if isinstance(v, int) and abs(v) > _INT_MAX else v
        if isinstance(n, ast.UnaryOp):
            return _UN[type(n.op)](ev(n.operand))
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]
            return all(vals) if isinstance(n.op, ast.And) else any(vals)
        if isinstance(n, ast.Compare):
            esq = ev(n.left)
            for o, d in zip(n.ops, n.comparators):
                dir_ = ev(d)
                if not _CMP[type(o)](esq, dir_):
                    return False
                esq = dir_
            return True
        if isinstance(n, ast.IfExp):
            return ev(n.body) if ev(n.test) else ev(n.orelse)
        if isinstance(n, ast.Call):
            return FUNCOES[n.func.id](*[ev(a) for a in n.args])
        raise ErroExpressao(f"elemento não permitido: {type(n).__name__}")

    try:
        v = float(ev(arv))
    except ErroExpressao:
        raise
    except (ArithmeticError, ValueError, TypeError) as e:     # estouro, sqrt de negativo, potência complexa
        raise ErroExpressao(f"conta impossível em '{texto}': {e}") from None
    if not math.isfinite(v):
        raise ErroExpressao(f"resultado infinito em '{texto}'")
    return v
