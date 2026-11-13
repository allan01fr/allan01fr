"""Dimensões da malha 2D (módulo neutro, sem JAX): fórmula única usada pela validação e pela montagem."""

import math


def dimensoes_da_malha(largura, altura, malha_cm):
    """(nx, ny) da malha: round(L/h) por eixo, com mínimo de 8. Lança ValueError se não finito."""
    h = float(malha_cm) / 100.0
    if not (math.isfinite(h) and h > 0):
        raise ValueError("Tamanho de malha inválido.")
    dims = []
    for comprimento in (largura, altura):
        razao = float(comprimento) / h
        if not math.isfinite(razao):
            raise ValueError("Dimensões da malha não finitas.")
        dims.append(max(8, int(round(razao))))
    return dims[0], dims[1]
