#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figura do histórico de resíduos (malhas grossa e média, solver compressível) com o patamar detectado e, ao lado, os monitores físicos da malha média.
Uso: python3 figura_convergencia.py <pasta_medicoes> <saida.png>"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import estimar_duracao as E

def main():
    pasta, saida = sys.argv[1], sys.argv[2]
    hist = {n: dict(np.load(os.path.join(pasta, f"residuos_{n}_compressivel.npz"))) for n in ("grossa", "media")}
    cel = {n: json.load(open(os.path.join(pasta, f"custo_{n}_compressivel.json")))["celulas"] for n in hist}
    mon = json.load(open(os.path.join(pasta, "monitores_media_compressivel.json")))
    br = lambda v, _: f"{v:,.0f}".replace(",", ".")
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6), dpi=120, gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.9], wspace=0.28, left=0.055, right=0.985, top=0.84, bottom=0.14))
    cor = {"Ux": "#2563eb", "h": "#dc2626", "p_rgh": "#059669"}; rot = {"Ux": "U (componente x)", "h": "entalpia h", "p_rgh": "p_rgh"}
    for ax, n in zip(axs[:2], ("grossa", "media")):
        h = hist[n]; por, nivel, atingido = E.patamar(h); N = len(h["Ux"]); bloco = 25
        for c in ("Ux", "h", "p_rgh"):
            r = h[c]; med = np.array([np.nanmedian(r[i:i + bloco]) for i in range(0, N - bloco + 1, bloco)]); x = np.arange(len(med)) * bloco + bloco / 2
            ax.semilogy(np.arange(1, N + 1), r, color=cor[c], alpha=0.16, lw=0.6); ax.semilogy(x, med, color=cor[c], lw=1.8, label=rot[c])
        ax.axhline(1e-4, color="#6b7280", ls="--", lw=1); ax.text(N * 0.985, 1.15e-4, "critério usual: 1e-4", ha="right", va="bottom", fontsize=8, color="#374151")
        if atingido:
            p = max(por.values()); ax.axvline(p, color="#111827", ls=":", lw=1.2); ax.text(p + N * 0.01, 0.6, f"patamar ≈ {p:,}".replace(",", "."), fontsize=8.5, color="#111827", va="top")
        else: ax.text(N * 0.5, 0.6, "sem patamar visível:\nainda cai devagar", fontsize=8.5, color="#111827", ha="center", va="top")
        ax.set_title(f"Malha {E.NOME[n]}: {cel[n] / 1e6:.2f} M células".replace(".", ","), fontsize=10.5, loc="left"); ax.set_xlim(0, N); ax.set_ylim(1e-6, 1)
        ax.set_xlabel("iteração", fontsize=9); ax.set_ylabel("resíduo inicial", fontsize=9); ax.grid(alpha=0.25, which="both", lw=0.4); ax.tick_params(labelsize=8); ax.xaxis.set_major_formatter(FuncFormatter(br))
    axs[0].legend(fontsize=8, loc="lower left", frameon=False)
    ax = axs[2]; ins = mon["instantes"]; ts = sorted(int(t) for t in ins); T0 = 293.15
    ser = {"T sob a coifa (excesso)": [ins[str(t)]["T_sob_coifa"] - T0 for t in ts], "|U| sob a coifa": [ins[str(t)]["U_sob_coifa"] for t in ts],
           "T na sonda (excesso)": [ins[str(t)]["T_sonda"] - T0 for t in ts], "|U| na sonda": [ins[str(t)]["U_sonda"] for t in ts]}
    est = {"T sob a coifa (excesso)": ("#dc2626", "-"), "|U| sob a coifa": ("#2563eb", "-"), "T na sonda (excesso)": ("#dc2626", ":"), "|U| na sonda": ("#2563eb", ":")}
    for k, v in ser.items():
        v = np.array(v); ax.plot(ts, v / v[ts.index(3500)] if 3500 in ts else v / v[-1], marker="o", ms=3.5, lw=1.5, color=est[k][0], ls=est[k][1], label=k)
    ax.axhline(1, color="#6b7280", lw=0.8); ax.axhspan(0.95, 1.05, color="#9ca3af", alpha=0.25, lw=0); ax.text(ts[0], 1.07, "±5 %", fontsize=8, color="#374151")
    ax.set_title("Malha média: grandezas físicas (relativas a 3.500)", fontsize=10.5, loc="left"); ax.set_xlabel("iteração", fontsize=9); ax.set_ylabel("valor / valor em 3.500 iterações", fontsize=9)
    ax.set_ylim(0, 3.6); ax.grid(alpha=0.25, lw=0.4); ax.tick_params(labelsize=8); ax.legend(fontsize=7.5, frameon=False, loc="upper right"); ax.xaxis.set_major_formatter(FuncFormatter(br))
    fig.suptitle("Convergência do estacionário compressível: os resíduos estacionam na malha fina porque a pluma pulsa; integrais ficam em ±5 %, pontos oscilam", x=0.055, ha="left", fontsize=11.5, weight="bold", y=0.98)
    fig.savefig(saida); print("ok", saida)

if __name__ == "__main__": main()
