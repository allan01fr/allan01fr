#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de custo do caso 3D: tempo de malha, tempo por iteração em 1..N processos, pico de memória e escala.
Não vai até a convergência: mede poucas iterações e extrapola em estimar_duracao.py.
Uso: python3 rodar_teste.py <pasta_de_trabalho> [--nivel producao] [--np 1,2,3,4] [--iter 30] [--solver compressivel|boussinesq]"""
import argparse, json, os, re, shutil, statistics, subprocess, sys, threading, time

AQUI = os.path.dirname(os.path.abspath(__file__))
ENV = f"source {AQUI}/env.sh"
SOLVER = {"compressivel": "buoyantSimpleFoam", "boussinesq": "buoyantBoussinesqSimpleFoam"}

def sh(cmd, cwd, log=None, mpi=False):
    """Roda `cmd` com o ambiente do OpenFOAM; devolve (segundos, pico de memória RSS somada em MB)."""
    full = f"{ENV}; cd {cwd}; {cmd}" + (f" > {log} 2>&1" if log else "")
    t0 = time.time(); pico = [0.0]; parar = threading.Event()
    nome = cmd.split()[0] if not mpi else cmd.split("-parallel")[0].split()[-1]
    def vigia():
        while not parar.is_set():
            tot = 0
            for pid in filter(str.isdigit, os.listdir("/proc")):
                try:
                    if os.path.basename(open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")[0].decode()) == nome:
                        for l in open(f"/proc/{pid}/status"):
                            if l.startswith("VmRSS"): tot += int(l.split()[1]) / 1024
                except Exception: pass
            pico[0] = max(pico[0], tot); time.sleep(0.4)
    th = threading.Thread(target=vigia, daemon=True); th.start()
    p = subprocess.run(["bash", "-c", full]); parar.set(); th.join()
    return time.time() - t0, pico[0], p.returncode

def tempos_por_iteracao(log):
    t = [float(m) for m in re.findall(r"ExecutionTime = ([\d.]+) s", open(log).read())]
    return [b - a for a, b in zip(t, t[1:])], t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--nivel", default="producao"); ap.add_argument("--np", default="1,2,3,4")
    ap.add_argument("--iter", type=int, default=30); ap.add_argument("--solver", default="compressivel"); ap.add_argument("--manter", action="store_true")
    a = ap.parse_args(); caso = os.path.join(a.pasta, f"{a.nivel}_{a.solver}"); os.makedirs(a.pasta, exist_ok=True)
    out = dict(nivel=a.nivel, solver=a.solver, iter=a.iter, nprocs=os.cpu_count())
    if not (a.manter and os.path.exists(os.path.join(caso, "constant/polyMesh"))):
        shutil.rmtree(caso, ignore_errors=True)
        subprocess.run(["bash", "-c", f"SOLVER_CFD={a.solver} python3 {AQUI}/gerar_caso.py {caso} {a.nivel} 4 > /dev/null"], check=True)
        T = {}
        T["blockMesh"], _, _ = sh("blockMesh", caso, "log.blockMesh")
        T["snappyHexMesh"], mem, rc = sh("snappyHexMesh -overwrite", caso, "log.snappy"); T["snappy_pico_MB"] = mem
        T["topoSet_createPatch"] = sh("topoSet; createPatch -overwrite", caso, "log.patch")[0]
        sh("checkMesh", caso, "log.checkMesh")
        out["malha_s"] = T
    ck = open(os.path.join(caso, "log.checkMesh")).read()
    out["celulas"] = int(re.search(r"cells:\s+(\d+)", ck).group(1)); out["faces"] = int(re.search(r"faces:\s+(\d+)", ck).group(1))
    out["nao_ortogonalidade_max"] = float(re.search(r"non-orthogonality Max: ([\d.]+)", ck).group(1)); out["checkMesh_ok"] = "Mesh OK" in ck
    sol = SOLVER[a.solver]; out["execucoes"] = []
    for n in [int(x) for x in a.np.split(",")]:
        d = os.path.join(a.pasta, f"run_{a.nivel}_{a.solver}_np{n}"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        for sub in ("constant", "system", "0"): shutil.copytree(os.path.join(caso, sub), os.path.join(d, sub), symlinks=True)
        cd = open(os.path.join(d, "system/controlDict")).read()
        cd = re.sub(r"endTime\s+\d+;", f"endTime {a.iter};", cd); cd = re.sub(r"writeInterval\s+\d+;", f"writeInterval {a.iter};", cd); open(os.path.join(d, "system/controlDict"), "w").write(cd)
        r = dict(np=n)
        if n == 1: seg, mem, rc = sh(f"{sol}", d, "log.solver")
        else:
            sys.path.insert(0, AQUI); import gerar_caso as G
            open(os.path.join(d, "system/decomposeParDict"), "w").write(G.decompor(n))
            r["decomposePar_s"], _, _ = sh("decomposePar -force", d, "log.decompose")
            seg, mem, rc = sh(f"mpirun -np {n} {sol} -parallel", d, "log.solver", mpi=True)
        dts, ts = tempos_por_iteracao(os.path.join(d, "log.solver"))
        r.update(rc=rc, parede_total_s=seg, pico_memoria_MB=mem, iteracoes_medidas=len(dts), tempo_primeira_iter_s=ts[0] if ts else None)
        util = dts[5:] if len(dts) > 8 else dts
        if util: r.update(s_por_iter_mediana=statistics.median(util), s_por_iter_media=statistics.mean(util), s_por_iter_min=min(util), s_por_iter_max=max(util))
        out["execucoes"].append(r); print(json.dumps(r, ensure_ascii=False)); sys.stdout.flush()
    json.dump(out, open(os.path.join(a.pasta, f"custo_{a.nivel}_{a.solver}.json"), "w"), indent=1, ensure_ascii=False)
    print("OK", os.path.join(a.pasta, f"custo_{a.nivel}_{a.solver}.json"))

if __name__ == "__main__": main()
