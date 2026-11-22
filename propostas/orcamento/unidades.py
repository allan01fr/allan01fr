"""Conversoes de capacidade de climatizacao.

HP nao e convertido aqui: em VRF e split, "HP" e rotulo comercial sem fator fixo.
Quem informa HP deve informar tambem o kW nominal do fabricante.
"""

BTU_H_POR_TR = 12000
KW_POR_TR = 3.517


def tr_para_kw(tr):
    return tr * KW_POR_TR


def kw_para_tr(kw):
    return kw / KW_POR_TR


def btu_para_tr(btu_h):
    return btu_h / BTU_H_POR_TR


def _estimado(valor, m2_por_tr, texto):
    return {"valor": valor, "estimado": True,
            "premissa": f"{texto} (densidade informada: {m2_por_tr:g} m²/TR)"}


def area_de_capacidade(tr, m2_por_tr):
    """Area estimada (m²) a partir da capacidade em TR e da densidade m²/TR."""
    return _estimado(tr * m2_por_tr, m2_por_tr, "área estimada pela densidade")


def capacidade_de_area(m2, m2_por_tr):
    """Capacidade estimada (TR) a partir da area em m² e da densidade m²/TR."""
    return _estimado(m2 / m2_por_tr, m2_por_tr, "capacidade estimada pela densidade")
