#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Animação de CFD da fumaça da ilha de fogões sendo capturada pela coifa A, em um comando:
caso (Boussinesq) -> malha -> escoamento estacionário -> transporte de fumaça (escalar passivo) -> quadros -> MP4.
Cada etapa é pulada se o resultado já existe: pode ser interrompido e retomado com o mesmo comando.
O escoamento é estacionário; só a fumaça evolui no tempo (não é uma simulação transiente do ar).
Uso: python3 animacao.py <pasta> [--nivel media] [--np 4] [--iter 2000] [--t-fim 90] [--dt 0.05] [--DT 0.01] [--escreve 0.25] [--t-lento 30] [--passo-rapido 3] [--fps 15]
Saída em <pasta>/video: coifa_A_fumaca.mp4, coifa_A_fumaca_720p.mp4, coifa_A_fumaca_capa.jpg, animacao.json, quadro_*.png"""
import argparse, os, re, shutil, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import rodar_teste as RT, gerar_caso as G

def etapa(txt): print(f"\n== {txt}", flush=True); return time.time()

def tempos(caso): return sorted(float(d) for d in os.listdir(caso) if re.fullmatch(r"\d+(\.\d+)?", d) and float(d) > 0)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--nivel", default="media", choices=list(G.NIVEIS)); ap.add_argument("--np", type=int, default=4)
    ap.add_argument("--iter", type=int, default=0, help="iterações do estacionário (padrão: o do nível)"); ap.add_argument("--t-fim", type=float, default=90.0)
    ap.add_argument("--dt", type=float, default=0.05); ap.add_argument("--DT", type=float, default=0.01); ap.add_argument("--fps", type=int, default=15); ap.add_argument("--sub", type=int, default=1)
    ap.add_argument("--escreve", type=float, default=0.25, help="intervalo (s) entre os instantes gravados da fumaça"); ap.add_argument("--t-lento", type=float, default=30.0, help="até aqui, todos os instantes; depois, avanço rápido")
    ap.add_argument("--passo-rapido", type=float, default=3.0)
    ap.add_argument("--max-quadros", type=int, default=0); a = ap.parse_args()
    caso, fum, vid = (os.path.join(a.pasta, x) for x in ("caso", "fumaca", "video")); os.makedirs(a.pasta, exist_ok=True); n_it = a.iter or G.NIVEIS[a.nivel]["iter"]
    resumo = {}
    # 1) caso e malha
    if not os.path.exists(os.path.join(caso, "constant/polyMesh/boundary")):
        t0 = etapa(f"1/4 caso Boussinesq e malha ({a.nivel})"); shutil.rmtree(caso, ignore_errors=True)
        subprocess.run(["bash", "-c", f"SOLVER_CFD=boussinesq python3 {AQUI}/gerar_caso.py {caso} {a.nivel} {a.np} > /dev/null"], check=True)
        subprocess.run([os.path.join(AQUI, "malha.sh"), caso], check=True); resumo["malha_s"] = time.time() - t0
    # 2) escoamento estacionário (k-ε, flutuação por Boussinesq)
    if not tempos(caso):
        t0 = etapa(f"2/4 escoamento estacionário: {n_it} iterações em {a.np} processos")
        cd = open(os.path.join(caso, "system/controlDict")).read()
        cd = re.sub(r"endTime\s+[\d.]+;", f"endTime {n_it};", cd); cd = re.sub(r"writeInterval\s+[\d.]+;", f"writeInterval {n_it};", cd); open(os.path.join(caso, "system/controlDict"), "w").write(cd)
        if a.np > 1:
            open(os.path.join(caso, "system/decomposeParDict"), "w").write(G.decompor(a.np)); RT.sh("decomposePar -force", caso, "log.decompose")
            seg, mem, rc = RT.sh(f"mpirun -np {a.np} {RT.SOLVER['boussinesq']} -parallel", caso, "log.solver", mpi=True)
            if rc == 0: RT.sh("reconstructPar -latestTime", caso, "log.reconstruct")
        else: seg, mem, rc = RT.sh(RT.SOLVER["boussinesq"], caso, "log.solver")
        if rc or not tempos(caso): sys.exit(f"o solver falhou (rc={rc}); veja {caso}/log.solver")
        resumo["estacionario_s"] = time.time() - t0
        for x in os.listdir(caso):
            if x.startswith("processor"): shutil.rmtree(os.path.join(caso, x), ignore_errors=True)
    # 3) fumaça sobre o campo congelado
    if not (os.path.exists(fum) and len(tempos(fum)) == round(a.t_fim / a.escreve) and abs(tempos(fum)[-1] - a.t_fim) < 1e-6):
        t0 = etapa(f"3/4 transporte de fumaça até t = {a.t_fim:g} s (dt = {a.dt:g} s, DT = {a.DT:g} m²/s)")
        subprocess.run([sys.executable, os.path.join(AQUI, "fumaca.py"), caso, fum, "--t-fim", str(a.t_fim), "--dt", str(a.dt), "--DT", str(a.DT), "--escreve", str(a.escreve), "--np", str(a.np)], check=True)
        resumo["fumaca_s"] = time.time() - t0
    # 4) quadros e vídeo
    t0 = etapa("4/4 quadros e vídeo")
    cmd = [sys.executable, os.path.join(AQUI, "quadros.py"), fum, vid, "--caso-json", os.path.join(caso, "caso.json"), "--fps", str(a.fps), "--sub", str(a.sub), "--t-lento", str(a.t_lento), "--passo-rapido", str(a.passo_rapido)]
    if a.max_quadros: cmd += ["--max-quadros", str(a.max_quadros)]
    subprocess.run(cmd, check=True); resumo["quadros_s"] = time.time() - t0
    print("\nconcluído:", {k: f"{v:.0f} s" for k, v in resumo.items()}, "\nvídeo em", vid)

if __name__ == "__main__": main()
