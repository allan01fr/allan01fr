"""
Exemplo 03 - Distribuição de ar, temperatura e umidade numa sala climatizada (CFD 2D).

Mesmo escritório do exemplo 02 (5 m x 2,8 m de corte, 4 m de profundidade), com:
- unidade de parede à esquerda: insuflamento em 2,35-2,45 m e retorno em 2,55-2,75 m;
- 2 pessoas sentadas (150 W sensível + 110 W latente) e 1 computador (100 W);
- fachada ensolarada à direita (40 W/m²) e cobertura (10 W/m²).

O ar é insuflado no estado calculado no exemplo 02 para 24 °C / 50 % UR.
Se o modelo estiver coerente, o ar de retorno deve sair perto de 24 °C e 9,3 g/kg.

Uso:
    python exemplos/03_sala_ar_condicionado.py            # malha 10 cm (~1-2 min)
    python exemplos/03_sala_ar_condicionado.py --fino     # malha 5 cm (~5-10 min)
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import jax
import jax.numpy as jnp

from hvac import psicrometria as psi
from hvac.sala2d import (Sala, Abertura, FonteCalor, Obstaculo, Insuflamento, montar_geometria,
                         estado_inicial, simular, indicadores, dt_estavel,
                         velocidade_face_insuflamento, velocidade_centro)

fino = "--fino" in sys.argv
nx, ny = (100, 56) if fino else (50, 28)

sala = Sala(
    largura=5.0, altura=2.8, profundidade=4.0, nx=nx, ny=ny,
    aberturas=(Abertura("esquerda", 2.35, 2.45, "insuflamento"),
               Abertura("esquerda", 2.55, 2.75, "retorno")),
    fontes=(FonteCalor(2.8, 3.2, 0.0, 1.2, sensivel_w=150.0, latente_w=110.0),   # pessoas
            FonteCalor(3.6, 3.9, 0.75, 0.85, sensivel_w=100.0)),                   # computador
    obstaculos=(Obstaculo(3.3, 4.3, 0.70, 0.75),),                                 # mesa
    fluxo_direita=40.0,     # fachada
    fluxo_teto=10.0,        # cobertura
    nu_efetiva=1.5e-3,
)
geo = montar_geometria(sala)

# Estado de insuflamento (do exemplo 02, setpoint 24 °C / 50 %)
w_amb = psi.umidade_absoluta(24.0, 0.50)
t_ins, w_ins = psi.estado_insuflamento(24.0, w_amb, 898.0, 110.0, 600.0)
ins = Insuflamento(vazao_m3h=jnp.asarray(600.0), angulo_graus=jnp.asarray(30.0),
                   temperatura=t_ins, umidade_abs=w_ins)

v_face = velocidade_face_insuflamento(sala, geo, 600.0)
dt = dt_estavel(sala, velocidade_max=2.0 * v_face + 0.5)
print(f"Malha {nx}x{ny} (dx = {sala.dx * 100:.0f} cm), dt = {dt:.3f} s, "
      f"velocidade na face do difusor = {v_face:.2f} m/s")
print(f"Insuflamento: {float(t_ins):.1f} °C, {float(w_ins) * 1000:.2f} g/kg, 600 m³/h, 30° para baixo")

estado0 = estado_inicial(sala, T0=24.0, W0=float(w_amb))
rodar = jax.jit(lambda e: simular(sala, geo, ins, e, tempo_total=1800.0, dt=dt, tempo_media=600.0))
t0 = time.time()
estado, medias = rodar(estado0)
estado.T.block_until_ready()
print(f"30 min simulados em {time.time() - t0:.0f} s de CPU")

ind = indicadores(sala, geo, ins, medias, met=1.1, clo=0.5)
print("\n=== Zona ocupada (média dos últimos 10 min) ===")
print(f"  Temperatura          {float(ind['T_ocupada']):6.2f} °C")
print(f"  Umidade relativa     {float(ind['UR_ocupada']) * 100:6.1f} %")
print(f"  Velocidade média     {float(ind['vel_media_ocupada']):6.2f} m/s (máx {float(ind['vel_max_ocupada']):.2f})")
print(f"  PMV médio            {float(ind['PMV_medio']):+6.2f}  (desvio {float(ind['PMV_desvio']):.2f}; -0,5 a +0,5 = categoria B)")
print(f"  PPD médio            {float(ind['PPD_medio']):6.1f} %")
print(f"  Corrente de ar DR    {float(ind['DR_medio']):6.1f} % médio, {float(ind['DR_max']):.1f} % máximo (B: < 20 %)")
print(f"  Estratificação       {float(ind['dT_vertical']):6.2f} K entre 0,1 e 1,1 m (B: < 3 K)")
print("=== Balanço do equipamento ===")
print(f"  Retorno              {float(ind['T_retorno']):6.2f} °C, {float(ind['W_retorno']) * 1000:.2f} g/kg"
      f" ({float(ind['UR_retorno']) * 100:.0f} % UR)")
print(f"  Calor sensível retirado {float(ind['capacidade_sensivel_W']):6.0f} W (cargas: 898 W)")
print(f"  Calor latente retirado  {float(ind['capacidade_latente_W']):6.0f} W (cargas: 110 W)")
print(f"  Eficácia de remoção de calor {float(ind['eficacia_remocao_calor']):.2f} (1 = mistura perfeita)")

# ------------------------------------------------------------------ figura
ext = [0, sala.largura, 0, sala.altura]
uc, vc = (np.asarray(a) for a in velocidade_centro(estado.u, estado.v))
xc = (np.arange(nx) + 0.5) * sala.dx
yc = (np.arange(ny) + 0.5) * sala.dy
campos = [
    ("Temperatura [°C]", np.asarray(medias.T), "coolwarm"),
    ("Umidade relativa [%]", np.asarray(ind["campos"]["UR"]) * 100, "viridis"),
    ("PMV [-]", np.asarray(ind["campos"]["PMV"]), "RdBu_r"),
    ("Risco de corrente de ar DR [%]", np.asarray(ind["campos"]["DR"]), "magma_r"),
]
fig, axs = plt.subplots(2, 2, figsize=(13, 7.5))
for ax, (titulo, campo, cmap) in zip(axs.flat, campos):
    kw = dict(vmin=-1.5, vmax=1.5) if "PMV" in titulo else {}
    im = ax.imshow(campo.T, origin="lower", extent=ext, cmap=cmap, aspect="equal", **kw)
    fig.colorbar(im, ax=ax, shrink=0.85)
    ax.streamplot(xc, yc, uc.T, vc.T, color="k", density=1.0, linewidth=0.5, arrowsize=0.6)
    ax.contour(xc, yc, np.asarray(geo.ocupada).T, levels=[0.5], colors="w", linestyles="--", linewidths=1)
    ax.set_title(titulo)
    ax.set_xlim(0, sala.largura)
    ax.set_ylim(0, sala.altura)
fig.suptitle("Sala climatizada - corte 2D (linhas: escoamento instantâneo; tracejado: zona ocupada)")
fig.tight_layout()
os.makedirs("resultados", exist_ok=True)
fig.savefig("resultados/03_sala.png", dpi=110)
print("\nFigura salva em resultados/03_sala.png")
