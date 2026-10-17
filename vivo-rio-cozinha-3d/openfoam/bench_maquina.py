#!/usr/bin/env python3
"""Calibração na SUA máquina (~10 min): largura de banda de memória + tempo por iteração do solver na malha 'media' (≈ 720 mil células)
com 1..N processos. Com esses números a estimativa do caso completo deixa de ser extrapolação e passa a ser medida.
Pré-requisitos: OpenFOAM ESI no PATH (ajuste env.sh), Python 3 com numpy.
Uso: python3 bench_maquina.py [--np 1,2,4,6] [--iter 30]    -> grava bench_maquina.json (cole o resumo impresso na conversa)"""
import argparse, json, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--np", default="1,2,4,6"); ap.add_argument("--iter", type=int, default=30); a = ap.parse_args()
print("== 1/2 largura de banda de memória ==", flush=True)
banda = subprocess.run([sys.executable, os.path.join(AQUI, "bench_banda.py"), "12"], capture_output=True, text=True).stdout; print(banda)
print("== 2/2 solver na malha media (gera a malha, ~1-2 min, e roda", a.iter, "iterações por contagem de processos) ==", flush=True)
pasta = os.path.join(AQUI, "bench_tmp"); os.makedirs(pasta, exist_ok=True)
subprocess.run([sys.executable, os.path.join(AQUI, "rodar_teste.py"), pasta, "--nivel", "media", "--np", a.np, "--iter", str(a.iter)], check=True)
res = json.load(open(os.path.join(pasta, "custo_media_compressivel.json"))); res["banda_GBs"] = banda
json.dump(res, open(os.path.join(AQUI, "bench_maquina.json"), "w"), indent=1, ensure_ascii=False)
print("\n===== RESUMO (cole na conversa) =====")
print(f"células: {res['celulas']}  malha: {res['malha_s']}")
for r in res["execucoes"]: print(f"np={r['np']}: {r.get('s_por_iter_mediana')} s/iter (mediana)  pico {r['pico_memoria_MB']:.0f} MB")
print(banda)
