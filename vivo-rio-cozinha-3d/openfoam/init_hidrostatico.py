#!/usr/bin/env python3
"""Escreve 0/p hidrostático (barométrico) célula a célula: p(z) = p0 exp(-g z / (R T)); p_rgh resulta ~uniforme e o solver
estacionário parte do equilíbrio em vez de um estado em que a gravidade não está balanceada.
Uso: init_hidrostatico.py <caso>   (a malha já deve existir; usa foamToVTK para obter os centros de célula)"""
import math, os, re, subprocess, sys, shutil
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ler_vtu
caso = sys.argv[1]; env = f"source {AQUI}/env.sh; cd {caso}"
shutil.rmtree(os.path.join(caso, "VTK_init"), ignore_errors=True)
subprocess.run(["bash", "-c", f"{env}; foamToVTK -ascii -fields '(p)' -time 0 -no-boundary -name VTK_init > /dev/null 2>&1"], check=True)
vtu = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(caso, "VTK_init")) for f in fs if f == "internal.vtu"][0]
C, _, _ = ler_vtu.ler(vtu)
R, T, g, p0 = 287.1, 293.15, 9.81, 1e5
p = p0 * math.e ** (-g * C[:, 2] / (R * T))
txt = open(os.path.join(caso, "0/p")).read()
i = txt.index("internalField"); j = txt.index("boundaryField")
lista = "\n".join(f"{v:.3f}" for v in p)
txt = txt[:i] + f"internalField   nonuniform List<scalar>\n{len(p)}\n(\n{lista}\n)\n;\n\n" + txt[j:]
open(os.path.join(caso, "0/p"), "w").write(txt)
shutil.rmtree(os.path.join(caso, "VTK_init"), ignore_errors=True)
print(f"0/p hidrostático escrito: {len(p)} células, p de {p.min():.1f} a {p.max():.1f} Pa")
