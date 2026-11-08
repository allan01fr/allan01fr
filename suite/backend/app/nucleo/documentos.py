"""Validação de CPF e CNPJ pelo dígito verificador (módulo 11).

A entrada pode vir com máscara (pontos, traço, barra e espaços). Ela é
normalizada para dígitos antes da conferência. Letras são recusadas.
"""

import re

DIGITOS = "0123456789"
CARACTERES_PERMITIDOS = re.compile(r"[0-9\s.\-/]*")

PESOS_CPF_1 = list(range(10, 1, -1))  # 10..2
PESOS_CPF_2 = list(range(11, 1, -1))  # 11..2
PESOS_CNPJ_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_CNPJ_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def somente_digitos(valor: str) -> str:
    return "".join(c for c in valor if c in DIGITOS)


def _tem_so_mascara_e_digitos(valor: str) -> bool:
    return CARACTERES_PERMITIDOS.fullmatch(valor) is not None


def _digito_verificador(base: str, pesos: list[int]) -> str:
    soma = sum(int(d) * p for d, p in zip(base, pesos, strict=True))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def _sequencia_repetida(digitos: str) -> bool:
    return len(set(digitos)) == 1


def validar_cpf(valor: str) -> str:
    if not _tem_so_mascara_e_digitos(valor):
        raise ValueError("CPF inválido.")
    digitos = somente_digitos(valor)
    if len(digitos) != 11 or _sequencia_repetida(digitos):
        raise ValueError("CPF inválido.")
    primeiro = _digito_verificador(digitos[:9], PESOS_CPF_1)
    segundo = _digito_verificador(digitos[:9] + primeiro, PESOS_CPF_2)
    if digitos[9:] != primeiro + segundo:
        raise ValueError("CPF inválido.")
    return digitos


def validar_cnpj(valor: str) -> str:
    if not _tem_so_mascara_e_digitos(valor):
        raise ValueError("CNPJ inválido.")
    digitos = somente_digitos(valor)
    if len(digitos) != 14 or _sequencia_repetida(digitos):
        raise ValueError("CNPJ inválido.")
    primeiro = _digito_verificador(digitos[:12], PESOS_CNPJ_1)
    segundo = _digito_verificador(digitos[:12] + primeiro, PESOS_CNPJ_2)
    if digitos[12:] != primeiro + segundo:
        raise ValueError("CNPJ inválido.")
    return digitos


def validar_cpf_cnpj(valor: str) -> str:
    digitos = somente_digitos(valor)
    if len(digitos) == 11:
        return validar_cpf(valor)
    if len(digitos) == 14:
        return validar_cnpj(valor)
    raise ValueError("Informe um CPF (11 dígitos) ou CNPJ (14 dígitos).")
