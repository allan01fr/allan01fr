#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estimativa de duração do caso 3D completo (coifa A, estacionário) na máquina do usuário, a partir do que foi medido aqui.

  T = T_malha + N_iter(células) * s_por_iter(células) + T_pos
  s_por_iter aqui: medido em 1..4 processos nas malhas grossa / média / produção (lei de potência no nº de células).
  Passagem para o notebook: o solver em malha grande é limitado pela banda de memória (bytes por iteração ≈ s_por_iter * banda), logo
      s_usuário = s_aqui(4 proc.) * banda_aqui(4) / banda_usuário(6) * k,   k ∈ [0,8; 1,25] (cache, compute, WSL2, aquecimento).
  N_iter: medido nas malhas grossa e média (critério usual: p_rgh 1e-3, U/h/k/ε 1e-4; rigoroso: 10x menor), lei de potência nas células.
Uso: python3 estimar_duracao.py <pasta_medicoes> [--md saida.md] [--usuario bench_maquina.json]"""
import argparse, json, math, os
import numpy as np

def carregar(p, nome):
    f = os.path.join(p, nome); return json.load(open(f)) if os.path.exists(f) else None
def hms(s):
    if s < 5400: return f"{s/60:.0f} min"
    return f"{s/3600:.1f} h"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--md", default=None); ap.add_argument("--json", default=None)
    ap.add_argument("--bw-usuario", default="26,32,36", help="banda de memória do notebook (GB/s) pior,típico,melhor com 6 processos: DDR4-2666 em dois canais")
    ap.add_argument("--np-usuario", type=int, default=6); ap.add_argument("--usuario", default=None); a = ap.parse_args()
    custo = {n: carregar(a.pasta, f"custo_{n}_compressivel.json") for n in ("grossa", "media", "producao")}
    banda = carregar(a.pasta, "banda_aqui.json")["GBs"]; conv = {n: carregar(a.pasta, f"convergencia_{n}_compressivel.json") for n in ("grossa", "media")}
    bw_lo, bw_mid, bw_hi = [float(x) for x in a.bw_usuario.split(",")]
    cel = {n: c["celulas"] for n, c in custo.items()}
    s4 = {n: next(e for e in c["execucoes"] if e["np"] == 4)["s_por_iter_mediana"] for n, c in custo.items()}
    nn = sorted(cel, key=cel.get); X = np.log([cel[n] for n in nn]); Y = np.log([s4[n] for n in nn]); b_s, a_s = np.polyfit(X, Y, 1)
    s_aqui = lambda N: float(np.exp(a_s) * N ** b_s)
    # iterações
    it = {}
    for crit in ("folgado", "rigoroso"):
        pts = [(cel[n], conv[n].get(f"iter_convergencia_{crit}")) for n in ("grossa", "media") if conv[n]]
        it[crit] = pts
    def iters(N, crit):
        pts = [(c, v) for c, v in it[crit] if v]
        if len(pts) >= 2:
            b = math.log(pts[-1][1] / pts[0][1]) / math.log(pts[-1][0] / pts[0][0]); return pts[-1][1] * (N / pts[-1][0]) ** max(b, 0.0), b
        return (pts[0][1] * 1.5 if pts else 3000.0), None
    mesh = custo["producao"]["malha_s"]; t_mesh_prod = mesh["blockMesh"] + mesh["snappyHexMesh"] + mesh["topoSet_createPatch"]
    bwa = banda["4"]
    if a.usuario and os.path.exists(a.usuario):
        u = json.load(open(a.usuario)); su = {e["np"]: e["s_por_iter_mediana"] for e in u["execucoes"] if e.get("s_por_iter_mediana")}
        k_ref = min(su, key=lambda x: abs(x - a.np_usuario)); fator = su[k_ref] / next(e for e in custo["media"]["execucoes"] if e["np"] == 4)["s_por_iter_mediana"]
        usr = lambda N: (0.9 * s_aqui(N) * fator, s_aqui(N) * fator, 1.15 * s_aqui(N) * fator); base_txt = f"calibrado com bench_maquina.py (fator {fator:.2f}x sobre esta nuvem, np={k_ref})"
    else:
        usr = lambda N: (0.8 * s_aqui(N) * bwa / bw_hi, s_aqui(N) * bwa / bw_mid, 1.25 * s_aqui(N) * bwa / bw_lo)
        base_txt = f"extrapolado pela banda de memória ({bwa:.0f} GB/s aqui com 4 processos; {bw_lo:.0f}–{bw_hi:.0f} GB/s no notebook com {a.np_usuario})"
    linhas = []
    for N, nome in ((cel["media"], "média"), (1_500_000, "intermediária"), (cel["producao"], "produção")):
        lo, mid, hi = usr(N); r = dict(malha=nome, celulas=N, s_iter=(lo, mid, hi), mem_GB=custo["producao"]["execucoes"][-1]["pico_memoria_MB"] / 1024 * N / cel["producao"], malha_min=t_mesh_prod * N / cel["producao"] / 60 * 1.0)
        for crit in ("folgado", "rigoroso"):
            n_it, _ = iters(N, crit); r[crit] = dict(iter=n_it, h=(lo * n_it / 3600 + (r["malha_min"] + 10) / 60, mid * n_it / 3600 + (r["malha_min"] + 5) / 60, hi * n_it / 3600 + (r["malha_min"] * 1.4 + 5) / 60))
        linhas.append(r)
    out = dict(modelo=dict(expoente_s_iter=float(b_s), base=base_txt), medidas={n: dict(celulas=cel[n], s4=s4[n], por_np={e["np"]: e["s_por_iter_mediana"] for e in custo[n]["execucoes"]}, mem_MB={e["np"]: e["pico_memoria_MB"] for e in custo[n]["execucoes"]}) for n in custo},
               iteracoes_medidas=it, expoente_iter={c: iters(1e6, c)[1] for c in ("folgado", "rigoroso")}, estimativas=linhas, banda_aqui=banda, malha_prod_s=t_mesh_prod)
    json.dump(out, open(a.json or os.path.join(a.pasta, "estimativa.json"), "w"), indent=1, default=float)
    # relatório
    m = []; P = m.append
    P("# Quanto custa o caso 3D completo (coifa A, estacionário, compressível)\n")
    P("Medido na nuvem (Xeon 2,1 GHz, 4 núcleos, 15 GB; OpenFOAM ESI v1912). **Não foi rodado até o fim**: o teste mede a malha, o tempo por iteração e o número de iterações até convergir em malhas menores, e extrapola.\n")
    P("## O que foi medido aqui\n")
    P("| Malha | Células | 1 proc. | 2 proc. | 3 proc. | 4 proc. | Memória (4 proc.) |\n|---|---:|---:|---:|---:|---:|---:|")
    for n in nn:
        c = custo[n]; e = {x["np"]: x for x in c["execucoes"]}
        P(f"| {n} | {c['celulas']:,} | " + " | ".join(f"{e[k]['s_por_iter_mediana']:.2f} s" for k in (1, 2, 3, 4)) + f" | {e[4]['pico_memoria_MB']/1024:.1f} GB |".replace(",", "."))
    P(f"\nSegundos por iteração (mediana). Malha de produção: blockMesh + snappyHexMesh + patches = **{t_mesh_prod:.0f} s** (um processo, {mesh['snappy_pico_MB']/1024:.1f} GB). O tempo por iteração cresce com as células^{b_s:.2f}.\n")
    P("## Quantas iterações até convergir\n")
    for crit, desc in (("folgado", "critério usual (p_rgh 1e-3; U, h, k, ε 1e-4)"), ("rigoroso", "critério rigoroso (p_rgh 1e-4; U, h, k, ε 1e-5)")):
        P(f"- {desc}: " + "; ".join(f"{n}: {v if v else 'não convergiu'}" for n, v in ((n, (conv[n] or {}).get(f'iter_convergencia_{crit}')) for n in ('grossa', 'media')) ))
    P("\n## Estimativa para o seu notebook (Xeon E-2176M, 6 processos, 64 GB)\n")
    P(f"Base: {base_txt}. Faixa = pior … melhor; entre parênteses o valor central.\n")
    P("| Malha | Células | Memória | s/iteração | Iterações (usual / rigoroso) | Duração total, critério usual | Duração total, rigoroso |\n|---|---:|---:|---|---|---|---|")
    for r in linhas:
        lo, mid, hi = r["s_iter"]; f, g = r["folgado"], r["rigoroso"]
        P(f"| {r['malha']} | {r['celulas']:,} | {r['mem_GB']:.1f} GB | {lo:.1f} – {hi:.1f} ({mid:.1f}) | {f['iter']:.0f} / {g['iter']:.0f} | **{f['h'][1]:.1f} h** ({f['h'][0]:.1f} – {f['h'][2]:.1f} h) | {g['h'][1]:.1f} h ({g['h'][0]:.1f} – {g['h'][2]:.1f} h) |".replace(",", "."))
    P("\nA duração inclui geração da malha e ~5 min de pós-processamento. O notebook tem menos banda de memória que esta nuvem, e é ela que limita o solver: por isso o tempo sobe mais do que a diferença de clock sugere.\n")
    P("## Como trocar a extrapolação por medida\n")
    P("Rode `python3 openfoam/bench_maquina.py --np 1,2,4,6` no notebook (≈ 10 min, gera a malha média e mede 30 iterações) e mande o resumo impresso: `estimar_duracao.py --usuario bench_maquina.json` recalcula a tabela com o seu tempo por iteração.\n")
    if a.md: open(a.md, "w", encoding="utf-8").write("\n".join(m))
    print("\n".join(m))

if __name__ == "__main__": main()
