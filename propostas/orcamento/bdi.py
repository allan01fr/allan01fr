"""
BDI (Benefícios e Despesas Indiretas) conforme a fórmula do TCU.

Todas as taxas são frações (0.04 = 4%).

BDI = (1 + AC + S + R + G) × (1 + DF) × (1 + L) / (1 − I) − 1

- AC: administração central
- S: seguro
- G: garantia (opcional)
- R: risco
- DF: despesas financeiras
- L: lucro
- I: impostos (PIS, COFINS, ISS etc.)
"""


def _validar_nao_negativo(**entradas):
    for nome, valor in entradas.items():
        if valor < 0:
            raise ValueError(f"O valor de '{nome}' não pode ser negativo (recebido: {valor}).")


def bdi(ac, seguro_garantia, risco, despesas_financeiras, lucro, impostos, garantia=0.0):
    """
    Calcula o BDI pela fórmula do TCU.

    Parâmetros em frações (0.04 = 4%). `seguro_garantia` é o componente S;
    `garantia` é o componente G, opcional.

    Levanta ValueError se `impostos` for maior ou igual a 1 (100%) ou se
    qualquer entrada for negativa.
    """
    _validar_nao_negativo(
        ac=ac,
        seguro_garantia=seguro_garantia,
        risco=risco,
        despesas_financeiras=despesas_financeiras,
        lucro=lucro,
        impostos=impostos,
        garantia=garantia,
    )
    if impostos >= 1:
        raise ValueError(
            f"A alíquota de impostos deve ser menor que 1 (100%) (recebido: {impostos})."
        )

    numerador = (1 + ac + seguro_garantia + risco + garantia) * (1 + despesas_financeiras) * (1 + lucro)
    return numerador / (1 - impostos) - 1


def bdi_implicito(valor_com_bdi, custo):
    """
    Retorna o BDI implícito em um preço já formado: valor_com_bdi / custo − 1.

    Levanta ValueError se `custo` for menor ou igual a zero.
    """
    if custo <= 0:
        raise ValueError(f"O custo deve ser maior que zero (recebido: {custo}).")
    return valor_com_bdi / custo - 1


def fora_da_faixa(valor, faixa):
    """
    Verifica se `valor` está dentro da faixa de referência.

    `faixa` é um dicionário com as chaves "min", "max" e "fonte".
    Retorna um texto de alerta em português quando o valor está fora da faixa,
    ou None quando está dentro (limites inclusive).
    """
    minimo = faixa["min"]
    maximo = faixa["max"]
    fonte = faixa["fonte"]

    if valor < minimo:
        return (
            f"BDI de {valor:.2%} abaixo do mínimo de {minimo:.2%} "
            f"previsto em {fonte}."
        )
    if valor > maximo:
        return (
            f"BDI de {valor:.2%} acima do máximo de {maximo:.2%} "
            f"previsto em {fonte}."
        )
    return None
