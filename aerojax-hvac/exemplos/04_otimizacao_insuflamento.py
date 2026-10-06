"""
Exemplo 04 - Otimização do insuflamento com jax.grad (conforto x umidade x energia).

Parte do caso do exemplo 03, onde o jato frio "despenca" na zona ocupada (PMV ≈ -1,2),
e procura vazão, ângulo das aletas e temperatura de insuflamento que:
- levem o PMV médio da zona ocupada a ~0 com pouca variação espacial;
- mantenham a UR da zona ocupada entre 40 % e 60 % (controle de umidade);
- evitem corrente de ar (DR máximo < 20 %, categoria B da ISO 7730);
- não gastem ventilador à toa (potência ~ vazão³).

A umidade de insuflamento depende da temperatura: o ar sai da serpentina com ~90 % UR,
então insuflar mais quente melhora o PMV mas desumidifica menos. É esse compromisso
que o otimizador resolve.

O gradiente da função objetivo em relação aos 3 parâmetros é calculado pelo JAX
através de toda a simulação CFD (milhares de passos), com o custo de ~3 simulações,
independente do número de parâmetros.

Uso:  python exemplos/04_otimizacao_insuflamento.py      (~10-15 min em CPU de notebook)
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
UR_SERPENTINA = 0.90

# Limites físicos dos parâmetros: vazão [m³/h], ângulo [graus], temperatura [°C]
LIM_INF = jnp.array([300.0, -10.0, 14.0])
LIM_SUP = jnp.array([1200.0, 60.0, 23.0])
ESCALA = LIM_SUP - LIM_INF


def para_insuflamento(x):
    return Insuflamento(vazao_m3h=x[0], angulo_graus=x[1], temperatura=x[2],
                        umidade_abs=psi.umidade_absoluta(x[2], UR_SERPENTINA))


def avaliar(x, estado0, tempo_total, tempo_media):
    ins = para_insuflamento(x)
    est, med = simular(sala, geo, ins, estado0, tempo_total, DT, tempo_media)
    return est, indicadores(sala, geo, ins, med, met=1.1, clo=0.5)


def objetivo(x, estado0):
    _, ind = avaliar(x, estado0, tempo_total=900.0, tempo_media=300.0)
    relu = jax.nn.relu
    j_conforto = ind["PMV_medio"] ** 2 + ind["PMV_desvio"] ** 2
    j_umidade = 100.0 * (relu(ind["UR_ocupada"] - 0.60) ** 2 + relu(0.40 - ind["UR_ocupada"]) ** 2)
    j_corrente = (relu(ind["DR_max"] - 20.0) / 10.0) ** 2
    j_ventilador = 0.05 * (x[0] / 600.0) ** 3
    total = j_conforto + j_umidade + j_corrente + j_ventilador
    return total, ind


def mostrar(rotulo, x, ind):
    print(f"{rotulo:>10} | vazão {float(x[0]):6.0f} m³/h | ângulo {float(x[1]):5.1f}° | "
          f"T_ins {float(x[2]):5.2f} °C || PMV {float(ind['PMV_medio']):+5.2f} "
          f"(±{float(ind['PMV_desvio']):.2f}) | UR {float(ind['UR_ocupada']) * 100:4.1f} % | "
          f"DRmax {float(ind['DR_max']):4.1f} % | T_occ {float(ind['T_ocupada']):5.2f} °C")


# Estado de partida: sala já em regime com o projeto original (exemplo 03)
x0 = jnp.array([600.0, 30.0, 19.6])
print("Preparando estado inicial (30 min com o projeto original)...")
estado_base, ind_base = jax.jit(lambda x: avaliar(x, estado_inicial(sala, 24.0, 0.0093), 1800.0, 600.0))(x0)

valor_e_grad = jax.jit(jax.value_and_grad(objetivo, has_aux=True))

# Adam em variáveis normalizadas (0-1) com projeção nos limites
z = (x0 - LIM_INF) / ESCALA
m = jnp.zeros(3)
v = jnp.zeros(3)
lr, b1, b2 = 0.06, 0.8, 0.95
historico = []
print("\nIteração   parâmetros                                        || indicadores na zona ocupada")
for it in range(12):
    t0 = time.time()
    x = LIM_INF + z * ESCALA
    (j, ind), g = valor_e_grad(x, estado_base)
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

# Verificação independente: simulação longa partindo da sala parada
print("\nVerificação com simulação longa (30 min, partindo de 24 °C):")
verif = jax.jit(lambda x: avaliar(x, estado_inicial(sala, 24.0, 0.0093), 1800.0, 600.0))
_, ind_otimo = verif(jnp.asarray(x_otimo))
mostrar("original", x0, ind_base)
mostrar("otimizado", x_otimo, ind_otimo)
for nome, ind in (("original", ind_base), ("otimizado", ind_otimo)):
    print(f"{nome:>10} | retorno {float(ind['T_retorno']):.2f} °C / {float(ind['UR_retorno']) * 100:.0f} % UR | "
          f"capacidade {float(ind['capacidade_total_W']):.0f} W | PPD {float(ind['PPD_medio']):.1f} %")
print("\nObs.: com o insuflamento otimizado o termostato no retorno deve ser ajustado para a"
      " temperatura de retorno acima, e não para a temperatura desejada na zona ocupada.")
