"""Tabela única de conversão de unidades.

O banco e a API usam SI. Só este arquivo conhece as constantes de conversão.
"""

BTU_H_EM_W = 0.29307107  # Btu IT por hora, em watts
TR_EM_BTU_H = 12000.0  # tonelada de refrigeração, em Btu por hora
CFM_EM_M3_H = 1.69901079552  # pé cúbico por minuto, em metros cúbicos por hora
POL_EM_M = 0.0254  # polegada, em metros
PE_EM_M = 0.3048  # pé, em metros
LB_EM_KG = 0.45359237  # libra, em quilogramas
PSI_EM_PA = 6894.757293168  # libra-força por polegada quadrada, em pascal
POL_H2O_EM_PA = 249.0889  # polegada de água convencional, em pascal


def btu_h_para_w(btu_h: float) -> float:
    return btu_h * BTU_H_EM_W


def w_para_btu_h(w: float) -> float:
    return w / BTU_H_EM_W


def tr_para_w(tr: float) -> float:
    return tr * TR_EM_BTU_H * BTU_H_EM_W


def w_para_tr(w: float) -> float:
    return w / (TR_EM_BTU_H * BTU_H_EM_W)


def cfm_para_m3_h(cfm: float) -> float:
    return cfm * CFM_EM_M3_H


def m3_h_para_cfm(m3_h: float) -> float:
    return m3_h / CFM_EM_M3_H


def pol_para_m(pol: float) -> float:
    return pol * POL_EM_M


def m_para_pol(m: float) -> float:
    return m / POL_EM_M


def pe_para_m(pe: float) -> float:
    return pe * PE_EM_M


def m_para_pe(m: float) -> float:
    return m / PE_EM_M


def lb_para_kg(lb: float) -> float:
    return lb * LB_EM_KG


def kg_para_lb(kg: float) -> float:
    return kg / LB_EM_KG


def psi_para_pa(psi: float) -> float:
    return psi * PSI_EM_PA


def pa_para_psi(pa: float) -> float:
    return pa / PSI_EM_PA


def pol_h2o_para_pa(pol_h2o: float) -> float:
    return pol_h2o * POL_H2O_EM_PA


def pa_para_pol_h2o(pa: float) -> float:
    return pa / POL_H2O_EM_PA


def f_para_c(f: float) -> float:
    return (f - 32) * 5 / 9


def c_para_f(c: float) -> float:
    return c * 9 / 5 + 32
