#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitores físicos de convergência a partir dos instantes gravados por convergencia.py (500, 1000, ...): quando os resíduos param de cair
(patamar), o que diz que o campo parou de mudar são grandezas de interesse, não o resíduo. Calcula, por instante:
  T e |U| médios (volumétricos) no volume sob a coifa e acima da ilha; T médio do ambiente; T e |U| numa sonda 0,5 m acima do centro da ilha.
Uso: python3 convergencia_monitores.py <pasta_do_caso_rodado> <caso.json> [--tempos 500,1000,...] [--saida monitores.json]"""
import argparse, json, os, re, subprocess, sys
import numpy as np
from scipy.spatial import cKDTree
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import quadros

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("caso_json"); ap.add_argument("--tempos", default=None); ap.add_argument("--saida", default=None); a = ap.parse_args()
    proc = os.path.join(a.run, "processor0"); tem_proc = os.path.isdir(proc)
    base = proc if tem_proc else a.run
    tempos = [int(x) for x in a.tempos.split(",")] if a.tempos else sorted(int(d) for d in os.listdir(base) if re.fullmatch(r"[1-9]\d*", d))
    faltam = [t for t in tempos if not os.path.exists(os.path.join(a.run, str(t), "T"))]
    if faltam and tem_proc:
        subprocess.run(["bash", "-c", f"source {AQUI}/env.sh; cd {a.run}; reconstructPar -time '{','.join(map(str, faltam))}' -fields '(T U)' > log.reconstruct_monitores 2>&1"], check=True)
    geo = quadros.exportar_u(a.run); LO, HI = geo["lo"], geo["hi"]; C = (LO + HI) / 2; vol = np.prod(HI - LO, axis=1); n = len(C)
    cj = json.load(open(a.caso_json)); h = cj["coifa"]; ilha = cj["ilha"][0]
    sob = (C[:, 0] >= h["x0"]) & (C[:, 0] <= h["x1"]) & (C[:, 1] >= h["y0"]) & (C[:, 1] <= h["y1"]) & (C[:, 2] >= ilha["z1"]) & (C[:, 2] <= h["z0"])
    sonda = np.array([(ilha["x0"] + ilha["x1"]) / 2, (ilha["y0"] + ilha["y1"]) / 2, ilha["z1"] + 0.5]); i_s = cKDTree(C).query(sonda)[1]
    out = {}
    for t in tempos:
        T = quadros.campo_foam(os.path.join(a.run, str(t), "T"), n); U = np.linalg.norm(quadros.campo_foam(os.path.join(a.run, str(t), "U"), n, vetor=True), axis=1)
        out[t] = dict(T_sob_coifa=float((T[sob] * vol[sob]).sum() / vol[sob].sum()), U_sob_coifa=float((U[sob] * vol[sob]).sum() / vol[sob].sum()),
                      T_ambiente=float((T * vol).sum() / vol.sum()), T_sonda=float(T[i_s]), U_sonda=float(U[i_s]))
        print(t, {k: round(v, 3) for k, v in out[t].items()}, flush=True)
    json.dump(dict(celulas=n, celulas_sob_coifa=int(sob.sum()), sonda=sonda.tolist(), instantes=out), open(a.saida or os.path.join(a.run, "monitores.json"), "w"), indent=1)

if __name__ == "__main__": main()
