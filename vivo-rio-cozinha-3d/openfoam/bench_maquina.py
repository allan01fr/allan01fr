#!/usr/bin/env python3
"""Calibração na SUA máquina (~10 min): largura de banda de memória + tempo por iteração do solver na malha 'media' (≈ 720 mil células)
com 1..N processos. Com esses números a estimativa do caso completo deixa de ser extrapolação e passa a ser medida.
Pré-requisitos: OpenFOAM ESI no PATH (ajuste env.sh), Python 3 com numpy.
Uso: python3 bench_maquina.py [--np 1,2,4,6] [--iter 30]    -> grava bench_maquina.json (cole o resumo impresso na conversa)"""
import argparse, json, multiprocessing as mp, os, platform, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import bench_banda

def cpu():
    try: return next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception: return platform.processor() or platform.machine()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--np", default="1,2,4,6"); ap.add_argument("--iter", type=int, default=30); a = ap.parse_args()
    ok = subprocess.run(["bash", "-c", f"source {AQUI}/env.sh; command -v blockMesh snappyHexMesh buoyantSimpleFoam decomposePar >/dev/null"]).returncode == 0
    if not ok:
        print("O OpenFOAM não está no PATH deste terminal, ou falta o solver buoyantSimpleFoam (versões novas do OpenFOAM ESI o trocaram por buoyantFoam).\n"
              "Os scripts foram validados no OpenFOAM ESI v1912. Ajuste openfoam/env.sh para carregar o seu OpenFOAM ou use só a banda de memória:\n"
              "  python3 openfoam/bench_banda.py 12     # ~20 s; peça a linha dos 6 processos\n"
              "  python3 openfoam/estimar_duracao.py openfoam/medicoes --bw-medido <GB/s dos 6 processos> --md estimativa_cfd.md", file=sys.stderr); sys.exit(2)
    print("== 1/2 largura de banda de memória ==", flush=True)
    banda = {}
    for p in sorted({1, 2, 4, 6, 8, 12} & set(range(1, mp.cpu_count() + 1))): banda[str(p)] = round(bench_banda.medir(p), 1); print(f"  {p:2d} processo(s): {banda[str(p)]:6.1f} GB/s", flush=True)
    print("== 2/2 solver na malha media (gera a malha, ~1-2 min, e roda", a.iter, "iterações por contagem de processos) ==", flush=True)
    pasta = os.path.join(AQUI, "bench_tmp"); os.makedirs(pasta, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(AQUI, "rodar_teste.py"), pasta, "--nivel", "media", "--np", a.np, "--iter", str(a.iter)], check=True)
    res = json.load(open(os.path.join(pasta, "custo_media_compressivel.json"))); res["banda_GBs"] = banda; res["cpu"] = cpu(); res["nucleos_logicos"] = mp.cpu_count(); res["so"] = platform.platform()
    json.dump(res, open(os.path.join(AQUI, "bench_maquina.json"), "w"), indent=1, ensure_ascii=False)
    print("\n===== RESUMO (cole na conversa) =====")
    print(f"{res['cpu']} · {res['nucleos_logicos']} núcleos lógicos · {res['so']}")
    print(f"células: {res['celulas']}  malha: {res['malha_s']}")
    for r in res["execucoes"]: print(f"np={r['np']}: {r.get('s_por_iter_mediana')} s/iter (mediana)  pico {r['pico_memoria_MB']:.0f} MB")
    print("banda de memória (GB/s por nº de processos):", banda)
