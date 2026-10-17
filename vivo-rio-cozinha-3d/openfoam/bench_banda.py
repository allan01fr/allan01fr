#!/usr/bin/env python3
"""Largura de banda de memória (tipo STREAM triad, a = b + s*c) com 1..N processos; o CFD em malha grande é limitado por isso.
Uso: python3 bench_banda.py [max_processos]   (precisa de numpy; ~20 s)"""
import multiprocessing as mp, sys, time
import numpy as np

def trabalho(args):
    n, rep = args
    a = np.zeros(n); b = np.ones(n); c = np.ones(n)
    np.multiply(c, 3.0, out=a); np.add(a, b, out=a)            # aquece
    t0 = time.perf_counter()
    for _ in range(rep):
        np.multiply(c, 3.0, out=a); np.add(a, b, out=a)         # 2 passagens: lê c, escreve a; lê a,b, escreve a
    dt = time.perf_counter() - t0
    return rep * (2 + 3) * 8 * n / dt / 1e9                      # GB/s (5 vetores movidos por iteração, 8 bytes)

def medir(p, n=25_000_000, rep=8):
    with mp.Pool(p) as pool: r = pool.map(trabalho, [(n, rep)] * p)
    return sum(r)

if __name__ == "__main__":
    mx = int(sys.argv[1]) if len(sys.argv) > 1 else mp.cpu_count()
    print(f"CPUs lógicas: {mp.cpu_count()}")
    for p in sorted({1, 2, 3, 4, 6, 8, 12, mx} & set(range(1, mx + 1))):
        print(f"  {p:2d} processo(s): {medir(p):6.1f} GB/s", flush=True)
