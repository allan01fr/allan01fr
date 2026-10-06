"""
Exemplo 04 - Otimização da distribuição de ar com jax.grad.

Parte do caso do exemplo 03, onde o jato frio "despenca" na zona ocupada (PMV ≈ -1,2),
e procura a VAZÃO e o ÂNGULO DAS ALETAS que:
- levem o PMV médio da zona ocupada a ~0 com pouca variação espacial;
- evitem corrente de ar (DR máximo < 20 %, categoria B da ISO 7730);
- não gastem ventilador à toa (potência ~ vazão³).

Para cada vazão, a temperatura e a umidade de insuflamento saem do balanço de energia e
de umidade (como faz o termostato/controle do equipamento): o ar de retorno fica em
24 °C / 50 % e as cargas são retiradas. A UR que o ar precisa ter na saída da
serpentina é informada no final: se for menor que ~85 %, a umidade não se resolve só
com a distribuição de ar (ver exemplo 02: reaquecimento ou desumidificação dedicada).

O gradiente da função objetivo é calculado pelo JAX através de toda a simulação CFD
(dezenas de milhares de passos), com custo de ~3 simulações, independente do número
de parâmetros. Cada candidato é simulado por 20 min a partir da sala em 24 °C; o
resultado final é conferido com uma simulação independente de 40 min.

Uso:  python exemplos/04_otimizacao_insuflamento.py      (~25 min em CPU de notebook)
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import jax
import jax.numpy as jnp

from hvac import psicrometria as psi
from hvac.sala2d import (Sala, Abertura, FonteCalor, Obstaculo, Insuflamento, montar_geometria,
                         estado_inicial, simular, indicadores)

sala = Sala(
    largura=5.0, altura=2.8, profundidade=4.0, nx=50, ny=28,
    aberturas=(Abertura("esquerda", 2.35, 2.45, "insuflamento"),
               Abertura("esquerda", 2.55, 2.75, "retorno")),
    fontes=(FonteCalor(2.8, 3.2, 0.0, 1.2, sensivel_w=150.0, latente_w=110.0),
            FonteCalor(3.6, 3.9, 0.75, 0.85, sensivel_w=100.0)),
    obstaculos=(Obstaculo(3.3, 4.3, 0.70, 0.75),),
    fluxo_direita=40.0, fluxo_teto=10.0, nu_efetiva=1.5e-3,
)
geo = montar_geometria(sala)
DT = 0.03
T_ALVO, UR_ALVO = 24.0, 0.50
W_ALVO = psi.umidade_absoluta(T_ALVO, UR_ALVO)
CARGA_SENS = 150.0 + 100.0 + 40.0 * 2.8 * 4.0 + 10.0 * 5.0 * 4.0
CARGA_LAT = 110.0

# Limites físicos: vazão [m³/h], ângulo [graus]
LIM_INF = jnp.array([350.0, -10.0])
LIM_SUP = jnp.array([1200.0, 60.0])
ESCALA = LIM_SUP - LIM_INF


def para_insuflamento(x):
    t_ins, w_ins = psi.estado_insuflamento(T_ALVO, W_ALVO, CARGA_SENS, CARGA_LAT, x[0])
    return Insuflamento(vazao_m3h=x[0], angulo_graus=x[1], temperatura=t_ins, umidade_abs=w_ins)


def avaliar(x, tempo_total, tempo_media):
    ins = para_insuflamento(x)
    e0 = estado_inicial(sala, T_ALVO, float(W_ALVO))
    est, med = simular(sala, geo, ins, e0, tempo_total, DT, tempo_media)
    return est, indicadores(sala, geo, ins, med, met=1.1, clo=0.5)


def objetivo(x):
    _, ind = avaliar(x, tempo_total=1200.0, tempo_media=400.0)
    relu = jax.nn.relu
    j_conforto = ind["PMV_medio"] ** 2 + ind["PMV_desvio"] ** 2
    j_corrente = (relu(ind["DR_max"] - 20.0) / 10.0) ** 2
    j_ventilador = 0.02 * (x[0] / 600.0) ** 3
    return j_conforto + j_corrente + j_ventilador, ind


def mostrar(rotulo, x, ind):
    ins = para_insuflamento(jnp.asarray(x))
    print(f"{rotulo:>10} | vazão {float(x[0]):5.0f} m³/h | ângulo {float(x[1]):5.1f}° | "
          f"T_ins {float(ins.temperatura):5.2f} °C || PMV {float(ind['PMV_medio']):+5.2f} "
          f"(±{float(ind['PMV_desvio']):.2f}) | DRmax {float(ind['DR_max']):4.1f} % | "
          f"T_occ {float(ind['T_ocupada']):5.2f} °C | UR {float(ind['UR_ocupada']) * 100:4.1f} %")


x0 = jnp.array([600.0, 30.0])
valor_e_grad = jax.jit(jax.value_and_grad(objetivo, has_aux=True))

# Adam em variáveis normalizadas (0-1) com projeção nos limites
z = (x0 - LIM_INF) / ESCALA
m = jnp.zeros(2)
v = jnp.zeros(2)
lr, b1, b2 = 0.05, 0.8, 0.95
historico = []
print("Iteração   parâmetros                                     || indicadores na zona ocupada (20 min)")
for it in range(10):
    t0 = time.time()
    x = LIM_INF + z * ESCALA
    (j, ind), g = valor_e_grad(x)
    g_z = g * ESCALA
    mostrar(f"it {it:2d}", x, ind)
    print(f"{'':>10}   J = {float(j):.4f}  ({time.time() - t0:.0f} s)")
    historico.append((np.asarray(x), float(j)))
    m = b1 * m + (1 - b1) * g_z
    v = b2 * v + (1 - b2) * g_z**2
    mh = m / (1 - b1 ** (it + 1))
    vh = v / (1 - b2 ** (it + 1))
    z = jnp.clip(z - lr * mh / (jnp.sqrt(vh) + 1e-8), 0.0, 1.0)

x_otimo = min(historico, key=lambda h: h[1])[0]

# Verificação independente: simulação mais longa (40 min, média dos últimos 15 min)
print("\nVerificação independente (40 min simulados):")
verif = jax.jit(lambda x: avaliar(x, 2400.0, 900.0))
resultados = {"original": (np.asarray(x0), verif(x0)[1]), "otimizado": (x_otimo, verif(jnp.asarray(x_otimo))[1])}
for nome, (x, ind) in resultados.items():
    mostrar(nome, x, ind)
for nome, (x, ind) in resultados.items():
    ins = para_insuflamento(jnp.asarray(x))
    ur_serp = float(psi.umidade_relativa(ins.temperatura, ins.umidade_abs))
    print(f"{nome:>10} | retorno {float(ind['T_retorno']):.2f} °C | sensível retirado "
          f"{float(ind['capacidade_sensivel_W']):.0f} W (carga {CARGA_SENS:.0f}) | PPD {float(ind['PPD_medio']):.1f} % | "
          f"UR exigida na saída da serpentina {ur_serp * 100:.0f} %")
