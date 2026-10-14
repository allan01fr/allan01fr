"""
Exemplo 02 - Psicrometria, ar externo e seleção da serpentina (controle de umidade).

Caso: escritório 5 m x 4 m x 2,8 m com 2 pessoas, mantido a 24 °C e 50 % UR.
Os dados climáticos e as cargas são ILUSTRATIVOS: para projeto, use a
ABNT NBR 16401-1 (dados climáticos e cargas) e a NBR 16401-3 (ar externo).

O que o exemplo mostra:
1. estados psicrométricos (interno, externo, mistura);
2. estado de insuflamento que retira as cargas sensível e latente;
3. ponto de orvalho do aparelho (ADP) e fator de bypass (BF) da serpentina;
4. capacidade da serpentina (W, TR, BTU/h) e água condensada;
5. sensibilidades com jax.grad (quanto custa cada m³/h de ar externo, cada % de UR);
6. comparação de setpoints de umidade e necessidade de reaquecimento.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

from hvac import psicrometria as psi

W_PARA_TR = 1.0 / 3516.85
W_PARA_BTUH = 3.41214

# ---------------------------------------------------------------- dados do caso
T_INT, UR_INT = 24.0, 0.50                 # condição interna de projeto
T_EXT, TBU_EXT = 35.0, 26.0                # condição externa de verão (ILUSTRATIVA)
VAZAO_INS = 600.0                          # vazão de insuflamento [m³/h]
N_PESSOAS, AREA = 2, 20.0
# Ar externo (NBR 16401-3, nível 1, escritório): 2,5 L/s/pessoa + 0,3 L/s/m²
VAZAO_AE = (2.5 * N_PESSOAS + 0.3 * AREA) * 3.6      # m³/h
# Cargas internas do ambiente [W]
CARGA_SENS = 898.0     # pessoas, equipamento, fachada, cobertura (ver exemplo 03)
CARGA_LAT = 110.0      # pessoas


def estados(vazao_ae, ur_int, vazao_ins=VAZAO_INS):
    w_int = psi.umidade_absoluta(T_INT, ur_int)
    w_ext = psi.umidade_absoluta_tbu(T_EXT, TBU_EXT)
    m_ae = vazao_ae / psi.volume_especifico(T_EXT, w_ext)
    m_ret = (vazao_ins - vazao_ae) / psi.volume_especifico(T_INT, w_int)
    t_mis, w_mis = psi.mistura(T_INT, w_int, m_ret, T_EXT, w_ext, m_ae)
    t_ins, w_ins = psi.estado_insuflamento(T_INT, w_int, CARGA_SENS, CARGA_LAT, vazao_ins)
    return w_int, w_ext, t_mis, w_mis, t_ins, w_ins


def capacidade(vazao_ae, ur_int):
    """Capacidade total da serpentina [W] - função diferenciável dos dados de projeto."""
    _, _, t_mis, w_mis, t_ins, w_ins = estados(vazao_ae, ur_int)
    total, _, _, _ = psi.cargas_serpentina(VAZAO_INS, t_mis, w_mis, t_ins, w_ins)
    return total


def relatorio(ur_int):
    w_int, w_ext, t_mis, w_mis, t_ins, w_ins = estados(VAZAO_AE, ur_int)
    print(f"\n=== Setpoint interno: {T_INT:.1f} °C / {ur_int * 100:.0f} % UR ===")
    linha = "  {:<12} t = {:5.1f} °C   W = {:6.2f} g/kg   UR = {:5.1f} %   h = {:5.1f} kJ/kg   orvalho = {:5.1f} °C"
    for nome, t, w in (("interno", T_INT, w_int), ("externo", T_EXT, w_ext),
                       ("mistura", t_mis, w_mis), ("insuflamento", t_ins, w_ins)):
        print(linha.format(nome, float(t), float(w) * 1000, float(psi.umidade_relativa(t, w)) * 100,
                           float(psi.entalpia(t, w)), float(psi.ponto_orvalho(w))))

    t_adp, bf = psi.adp_serpentina(t_mis, w_mis, t_ins, w_ins)
    total, sens, lat, cond = psi.cargas_serpentina(VAZAO_INS, t_mis, w_mis, t_ins, w_ins)
    print(f"  Serpentina: ADP = {float(t_adp):.1f} °C, BF = {float(bf):.2f}"
          "   (referência: expansão direta trabalha com ADP de ~8 a 15 °C; BF de 0,03 a ~0,5)")
    print(f"  Capacidade: total {float(total):.0f} W = {float(total) * W_PARA_TR:.2f} TR = "
          f"{float(total) * W_PARA_BTUH:.0f} BTU/h | sensível {float(sens):.0f} W | latente {float(lat):.0f} W"
          f" | FCS = {float(sens / total):.2f}")
    print(f"  Água condensada: {float(cond):.2f} kg/h")

    # Alternativa clássica para controle fino de umidade: resfriar até o orvalho
    # necessário (+1 K) e reaquecer até a temperatura de insuflamento.
    t_orv = float(psi.ponto_orvalho(w_ins))
    m_ar = VAZAO_INS / 3600.0 / psi.volume_especifico(t_ins, w_ins)
    reaquec = m_ar * psi.CP_AR * (float(t_ins) - (t_orv + 1.0))
    print(f"  Alternativa resfriar+reaquecer: ar saindo da serpentina a ~{t_orv + 1:.1f} °C"
          f" e reaquecimento de {reaquec:.0f} W (energia extra, mas controle independente de T e UR).")
    return total


def relatorio(ur_int):
    w_int, w_ext, t_mis, w_mis, t_ins, w_ins = estados(VAZAO_AE, ur_int)
    print(f"\n=== Setpoint interno: {T_INT:.1f} °C / {ur_int * 100:.0f} % UR ===")
    linha = "  {:<12} t = {:5.1f} °C   W = {:6.2f} g/kg   UR = {:5.1f} %   h = {:5.1f} kJ/kg   orvalho = {:5.1f} °C"
    for nome, t, w in (("interno", T_INT, w_int), ("externo", T_EXT, w_ext),
                       ("mistura", t_mis, w_mis), ("insuflamento", t_ins, w_ins)):
        print(linha.format(nome, float(t), float(w) * 1000, float(psi.umidade_relativa(t, w)) * 100,
                           float(psi.entalpia(t, w)), float(psi.ponto_orvalho(w))))

    t_adp, bf = psi.adp_serpentina(t_mis, w_mis, t_ins, w_ins)
    total, sens, lat, cond = psi.cargas_serpentina(VAZAO_INS, t_mis, w_mis, t_ins, w_ins)
    print(f"  Serpentina: ADP = {float(t_adp):.1f} °C, BF = {float(bf):.2f}"
          "   (referência: expansão direta trabalha com ADP de ~8 a 15 °C; BF de 0,03 a ~0,5)")
    print(f"  Capacidade: total {float(total):.0f} W = {float(total) * W_PARA_TR:.2f} TR = "
          f"{float(total) * W_PARA_BTUH:.0f} BTU/h | sensível {float(sens):.0f} W | latente {float(lat):.0f} W"
          f" | FCS = {float(sens / total):.2f}")
    print(f"  Água condensada: {float(cond):.2f} kg/h")

    # Alternativa clássica para controle fino de umidade: resfriar até o orvalho
    # necessário (+1 K) e reaquecer até a temperatura de insuflamento.
    t_orv = float(psi.ponto_orvalho(w_ins))
    m_ar = VAZAO_INS / 3600.0 / psi.volume_especifico(t_ins, w_ins)
    reaquec = float(m_ar * psi.CP_AR * (t_ins - (t_orv + 1.0)))
    print(f"  Alternativa resfriar+reaquecer: ar saindo da serpentina a ~{t_orv + 1:.1f} °C"
          f" e reaquecimento de {reaquec:.0f} W (gasta mais energia, mas controla T e UR de forma independente)")
    return total


print(f"Vazão de insuflamento: {VAZAO_INS:.0f} m³/h | ar externo: {VAZAO_AE:.0f} m³/h"
      f" ({VAZAO_AE / VAZAO_INS * 100:.0f} %)")
print(f"Cargas do ambiente: sensível {CARGA_SENS:.0f} W, latente {CARGA_LAT:.0f} W, "
      f"FCS do ambiente = {float(psi.fator_calor_sensivel(CARGA_SENS, CARGA_LAT)):.2f}")

for ur in (0.50, 0.60):
    relatorio(ur)

# Sensibilidades (derivadas exatas pelo JAX, sem diferenças finitas)
d_ae, d_ur = jax.grad(capacidade, argnums=(0, 1))(VAZAO_AE, UR_INT)
print("\n=== Sensibilidades da capacidade da serpentina ===")
print(f"  +1 m³/h de ar externo   -> {float(d_ae):+.1f} W")
print(f"  +1 % de UR no setpoint -> {float(d_ur) / 100:+.1f} W")
