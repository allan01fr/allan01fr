#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roda um caso estacionário por N iterações e mede quantas iterações levam a convergir (resíduos), para estimar a duração do caso completo.
Uso: python3 convergencia.py <pasta_de_trabalho> --nivel grossa|media --solver boussinesq|compressivel --np 4 --iter 3000"""
import argparse, json, os, re, shutil, subprocess, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import rodar_teste as RT, gerar_caso as G

CAMPOS = {"compressivel": ["Ux", "Uy", "Uz", "h", "p_rgh", "k", "epsilon"], "boussinesq": ["Ux", "Uy", "Uz", "T", "p_rgh", "k", "epsilon"]}
CRIT = {"folgado": dict(p_rgh=1e-3, U=1e-4, h=1e-4, T=1e-4, k=1e-4, epsilon=1e-4), "rigoroso": dict(p_rgh=1e-4, U=1e-5, h=1e-5, T=1e-5, k=1e-5, epsilon=1e-5)}

def historico(log, solver):
    txt = open(log).read(); res = {c: [] for c in CAMPOS[solver]}
    for bloco in txt.split("\nTime = ")[1:]:
        for c in res:
            m = re.search(rf"Solving for {c}, Initial residual = ([\d.e+-]+)", bloco)
            res[c].append(float(m.group(1)) if m else np.nan)
    return {c: np.array(v) for c, v in res.items()}

def primeira_iteracao(h, crit, solver, janela=20):
    n = len(next(iter(h.values()))); campos = {"U": ["Ux", "Uy", "Uz"], "h": ["h"], "T": ["T"], "p_rgh": ["p_rgh"], "k": ["k"], "epsilon": ["epsilon"]}
    ok = np.ones(n, bool)
    for chave, lim in crit.items():
        for c in campos[chave]:
            if c in h: ok &= (h[c] < lim)
    for i in range(n - janela):
        if ok[i:i + janela].all(): return i + 1
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--nivel", default="grossa"); ap.add_argument("--solver", default="boussinesq")
    ap.add_argument("--np", type=int, default=4); ap.add_argument("--iter", type=int, default=3000); ap.add_argument("--escreve", type=int, default=500)
    ap.add_argument("--rapido", action="store_true", help="reutiliza a malha existente"); a = ap.parse_args()
    caso = os.path.join(a.pasta, f"{a.nivel}_{a.solver}"); run = os.path.join(a.pasta, f"conv_{a.nivel}_{a.solver}")
    if not os.path.exists(os.path.join(caso, "constant/polyMesh")):
        subprocess.run(["bash", "-c", f"SOLVER_CFD={a.solver} python3 {AQUI}/gerar_caso.py {caso} {a.nivel} {a.np} > /dev/null"], check=True)
        for cmd, lg in (("blockMesh", "log.blockMesh"), ("snappyHexMesh -overwrite", "log.snappy"), ("topoSet; createPatch -overwrite", "log.patch"), ("checkMesh", "log.checkMesh")): RT.sh(cmd, caso, lg)
    shutil.rmtree(run, ignore_errors=True); os.makedirs(run)
    for sub in ("constant", "system", "0"): shutil.copytree(os.path.join(caso, sub), os.path.join(run, sub), symlinks=True)
    cd = open(os.path.join(run, "system/controlDict")).read()
    cd = re.sub(r"endTime\s+\d+;", f"endTime {a.iter};", cd); cd = re.sub(r"writeInterval\s+\d+;", f"writeInterval {a.escreve};", cd); cd = cd.replace("purgeWrite      1;", "purgeWrite      0;")
    open(os.path.join(run, "system/controlDict"), "w").write(cd)
    # residualControl desligado para medir o histórico inteiro
    fs = open(os.path.join(run, "system/fvSolution")).read(); fs = re.sub(r"residualControl\s*\{[^}]*\}", "residualControl { }", fs); open(os.path.join(run, "system/fvSolution"), "w").write(fs)
    sol = RT.SOLVER[a.solver]
    if a.np > 1:
        open(os.path.join(run, "system/decomposeParDict"), "w").write(G.decompor(a.np)); RT.sh("decomposePar -force", run, "log.decompose")
        seg, mem, rc = RT.sh(f"mpirun -np {a.np} {sol} -parallel", run, "log.solver", mpi=True)
        RT.sh("reconstructPar -latestTime", run, "log.reconstruct")
    else: seg, mem, rc = RT.sh(sol, run, "log.solver")
    h = historico(os.path.join(run, "log.solver"), a.solver); dts, ts = RT.tempos_por_iteracao(os.path.join(run, "log.solver"))
    out = dict(nivel=a.nivel, solver=a.solver, np=a.np, rc=rc, iteracoes=len(next(iter(h.values()))), parede_s=seg, pico_MB=mem,
               s_por_iter=float(np.median(dts[5:])) if len(dts) > 8 else None,
               s_por_iter_inicio=float(np.median(dts[15:45])) if len(dts) > 50 else None,                 # iterações 15–45 (o que o teste de custo mede)
               s_por_iter_fim=float(np.median(dts[len(dts) // 2:])) if len(dts) > 100 else None)         # segunda metade da execução
    for nome, crit in CRIT.items(): out[f"iter_convergencia_{nome}"] = primeira_iteracao(h, crit, a.solver)
    fin = {c: float(v[-1]) for c, v in h.items()}; out["residuo_final"] = fin
    # inclinação (décadas por 1000 iterações) nas últimas 1000
    out["inclinacao_decadas_por_1000"] = {c: float((np.log10(v[-1]) - np.log10(v[-1001])) if len(v) > 1001 and v[-1] > 0 and v[-1001] > 0 else np.nan) for c, v in h.items()}
    np.savez(os.path.join(a.pasta, f"residuos_{a.nivel}_{a.solver}.npz"), **h)
    json.dump(out, open(os.path.join(a.pasta, f"convergencia_{a.nivel}_{a.solver}.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))

if __name__ == "__main__": main()
