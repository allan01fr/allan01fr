"""
Exemplo 01 - Usar o AeroJAX original sem a interface gráfica.

Simula o escoamento em torno de um cilindro (esteira de von Kármán), mede a
frequência de desprendimento de vórtices e calcula o número de Strouhal.
Referência para Re = 100: St ≈ 0,16-0,17 (Williamson, 1996). O canal confinado
deste exemplo (bloqueio de 20 %) tende a aumentar um pouco o St.

Como rodar:
    git clone https://github.com/arriemeijer-creator/AeroJAX
    set AEROJAX_DIR=C:\\caminho\\para\\AeroJAX        (Windows)
    export AEROJAX_DIR=/caminho/para/AeroJAX          (Linux/macOS)
    python exemplos/01_aerojax_cilindro.py
"""

import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AEROJAX_DIR = os.environ.get("AEROJAX_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "AeroJAX"))
sys.path.insert(0, os.path.abspath(AEROJAX_DIR))

import jax.numpy as jnp
from solver import (BaselineSolver, GridParams, FlowParams, FlowConstraints,
                    GeometryParams, SimulationParams)
from solver.operators import vorticity_nonperiodic

# 1) Malha: 8 m x 2 m com 256 x 64 células (dx = 3,1 cm)
grid = GridParams(nx=256, ny=64, lx=8.0, ly=2.0)

# 2) Escoamento: trava U e Re; o AeroJAX calcula nu = U*D/Re (D = diâmetro)
flow = FlowParams(Re=100.0, U_inf=1.0,
                  constraints=FlowConstraints(lock_U=True, lock_nu=False, lock_Re=True, lock_L=True))

# 3) Geometria: cilindro de raio 0,2 m em (2, 1)
geom = GeometryParams(center_x=jnp.array(2.0), center_y=jnp.array(1.0), radius=jnp.array(0.2))

# 4) Opções numéricas (as mesmas do painel da interface)
sim = SimulationParams(obstacle_type="cylinder", flow_type="von_karman", fixed_dt=2e-3,
                       pressure_solver="multigrid")

solver = BaselineSolver(grid, flow, geom, sim)

# Sonda de velocidade vertical 2 diâmetros atrás do cilindro, na linha central
i_sonda = int(2.8 / grid.dx)
j_sonda = grid.ny // 2
n_passos = 40000          # 80 s: o desprendimento leva ~40 s para saturar
sinal = np.empty(n_passos)

t0 = time.time()
for n in range(n_passos):
    solver.step_for_visualization(compute_vorticity=False)
    sinal[n] = float(solver.v[i_sonda, j_sonda])
print(f"{n_passos} passos em {time.time() - t0:.1f} s")

# Strouhal: FFT do sinal após o transiente inicial
s = sinal[n_passos // 2:]      # descarta o transiente (crescimento da instabilidade)
s = s - s.mean()
freqs = np.fft.rfftfreq(len(s), d=solver.dt)
espectro = np.abs(np.fft.rfft(s * np.hanning(len(s))))
f_pico = freqs[np.argmax(espectro[1:]) + 1]
D, U = 0.4, flow.U_inf
print(f"Frequência de desprendimento: {f_pico:.3f} Hz  ->  St = f*D/U = {f_pico * D / U:.3f}")

# Figura: vorticidade e sinal da sonda
w = np.asarray(vorticity_nonperiodic(solver.u, solver.v, grid.dx, grid.dy))
fig, ax = plt.subplots(2, 1, figsize=(10, 6))
ax[0].imshow(w.T, origin="lower", cmap="RdBu_r", vmin=-5, vmax=5,
             extent=[0, grid.lx, 0, grid.ly])
ax[0].set_title(f"Vorticidade, Re = {flow.Re:.0f}")
ax[1].plot(np.arange(n_passos) * solver.dt, sinal)
ax[1].set_xlabel("tempo [s]")
ax[1].set_ylabel("v na sonda [m/s]")
fig.tight_layout()
os.makedirs("resultados", exist_ok=True)
fig.savefig("resultados/01_cilindro.png", dpi=120)
print("Figura salva em resultados/01_cilindro.png")
