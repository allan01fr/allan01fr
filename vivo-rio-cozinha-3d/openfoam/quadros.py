#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quadros de CFD da fumaça sobre o campo estacionário (saída de fumaca.py).
Cada quadro tem 4 cortes (duas elevações e duas plantas, com as linhas de corrente do escoamento ao fundo) e uma coluna lateral com o relógio,
os dados do caso e a fumaça acumulada no ambiente. Saída: vídeo MP4 e quadros-chave em PNG.
A geometria sólida vem das próprias células da malha (caixa envolvente de cada célula), não de uma distância ao centro mais próximo.
Uso: python3 quadros.py <caso_fumaca> <saida> --caso-json <caso.json do caso base> [--fps 15] [--sub 2]"""
import argparse, json, os, re, shutil, subprocess, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from scipy.spatial import cKDTree
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ler_vtu

def br(v, n=2): return f"{v:.{n}f}".replace(".", ",")
def eixo_br(v, _): return f"{v:g}".replace(".", ",")

def exportar_u(caso):
    """Geometria das células (centros, caixas) e o campo U estacionário, de um único .vtu do tempo 0."""
    sh = f"source {AQUI}/env.sh; cd {caso}; rm -rf VTK_U; foamToVTK -ascii -fields '(U)' -time '0' -no-boundary -name VTK_U > log.VTK_U 2>&1"
    subprocess.run(["bash", "-c", sh], check=True)
    base = os.path.join(caso, "VTK_U")
    pasta = next(d for d in sorted(os.listdir(base)) if os.path.isdir(os.path.join(base, d)))
    return ler_vtu.ler_completo(os.path.join(base, pasta, "internal.vtu"))

def campo_escalar(path, n):
    """internalField de um volScalarField do OpenFOAM, ascii ou binário (uniform ou nonuniform)."""
    b = open(path, "rb").read(); cab = b[:b.find(b"internalField")]
    m = re.search(rb"internalField\s+uniform\s+([^;\s]+)\s*;", b)
    if m: return np.full(n, float(m.group(1)))
    m = re.search(rb"internalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(", b)
    N = int(m.group(1)); i = m.end()
    if re.search(rb"format\s+binary", cab):
        a = np.frombuffer(b, dtype="<f8" if b"scalar=64" in cab else "<f4", count=N, offset=i).astype(float)
    else:
        a = np.array(b[i:b.index(b"\n)", i)].split(), dtype=float)
    if N != n: raise SystemExit(f"{path}: {N} valores para {n} células")
    return a

def celula_que_contem(P, arvore, C, meia, ks=(12, 48, 192)):
    """Índice da célula (caixa) que contém cada ponto, ou -1 se nenhuma contém (sólido). A busca cresce com k porque, na interface entre níveis de refino,
    a célula grossa que contém o ponto pode ter o centro mais longe que dezenas de células finas."""
    achado = np.full(len(P), -1); pend = np.arange(len(P))
    for k in ks:
        if not len(pend): break
        _, idx = arvore.query(P[pend], k=min(k, len(C)))
        ok = (np.abs(P[pend][:, None, :] - C[idx]) <= meia[idx] + 1e-6).all(axis=2); tem = ok.any(axis=1)
        achado[pend[tem]] = idx[tem, ok[tem].argmax(axis=1)]; pend = pend[~tem]
    return achado

def tempos_gravados(caso):
    return sorted((float(d), d) for d in os.listdir(caso) if re.fullmatch(r"\d+(\.\d+)?", d) and float(d) > 0 and os.path.exists(os.path.join(caso, d, "T")))

def difusividade(caso):
    try: return float(re.search(r"DT\s+DT\s*\[[^\]]*\]\s*([\d.eE+-]+)", open(os.path.join(caso, "constant/transportProperties")).read()).group(1))
    except Exception: return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("caso"); ap.add_argument("saida"); ap.add_argument("--caso-json", required=True)
    ap.add_argument("--fps", type=int, default=15); ap.add_argument("--passo", type=float, default=0.03, help="passo da grade dos cortes (m)")
    ap.add_argument("--sub", type=int, default=1, help="quadros por instante gravado (interpolação linear do campo entre instantes)")
    ap.add_argument("--max-quadros", type=int, default=0, help="só os primeiros N instantes (teste de layout)"); ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--crf", type=int, default=24)
    ap.add_argument("--titulo", default="Coifa A (ilha dos fogões): transporte de fumaça sobre o escoamento estacionário"); a = ap.parse_args()
    cj = json.load(open(a.caso_json)); dom = cj["dominio"]; hood = cj["coifa"]; z_piso, z_forro = dom["z0"], dom["z1"]; cap = cj["captores"]
    shutil.rmtree(a.saida, ignore_errors=True); os.makedirs(os.path.join(a.saida, "quadros"))
    geo = exportar_u(a.caso); LO, HI = geo["lo"], geo["hi"]; U = geo["campos"]["U"]; n = len(LO)
    # centro da caixa, não a média dos vértices: nas células com nós pendurados (interface entre níveis de refino) a média dos vértices é deslocada
    C = (LO + HI) / 2; meia = (HI - LO) / 2; vol = np.prod(HI - LO, axis=1); arvore = cKDTree(C)
    tempos = tempos_gravados(a.caso)
    if a.max_quadros: tempos = tempos[:a.max_quadros]
    xc, yc = cap[0]["x"], (hood["y0"] + hood["y1"]) / 2; h = a.passo
    def grade(eixos, fixo):
        (e1, r1), (e2, r2) = eixos; g1 = np.arange(r1[0] + h / 2, r1[1], h); g2 = np.arange(r2[0] + h / 2, r2[1], h); G1, G2 = np.meshgrid(g1, g2)
        P = np.zeros(G1.shape + (3,)); P[..., "xyz".index(e1)] = G1; P[..., "xyz".index(e2)] = G2; P[..., "xyz".index(fixo[0])] = fixo[1]
        return G1, G2, P.reshape(-1, 3)
    cortes = [
        dict(nome=f"Corte vertical y = {br(yc)} m (centro da coifa)", ex=("x", "z"), fixo=("y", yc), r1=(dom["x0"], dom["x1"]), r2=(z_piso, z_forro)),
        dict(nome=f"Corte vertical x = {br(xc)} m (captor 1)", ex=("y", "z"), fixo=("x", xc), r1=(dom["y0"], dom["y1"]), r2=(z_piso, z_forro)),
        dict(nome=f"Planta 0,3 m abaixo da borda da coifa (z = {br(hood['z0'] - 0.3)} m)", ex=("x", "y"), fixo=("z", hood["z0"] - 0.3), r1=(dom["x0"], dom["x1"]), r2=(dom["y0"], dom["y1"])),
        dict(nome=f"Planta a 1,60 m do piso (z = {br(z_piso + 1.6)} m)", ex=("x", "y"), fixo=("z", z_piso + 1.6), r1=(dom["x0"], dom["x1"]), r2=(dom["y0"], dom["y1"]))]
    for c in cortes:
        G1, G2, P = grade(((c["ex"][0], c["r1"]), (c["ex"][1], c["r2"])), c["fixo"])
        fluido = celula_que_contem(P, arvore, C, meia) >= 0      # ponto fora de toda célula = sólido (célula ausente da malha)
        d, idx = arvore.query(P, k=6); w = 1.0 / (d + 1e-3) ** 2
        c.update(G1=G1, G2=G2, idx=idx, w=w, fluido=fluido.reshape(G1.shape), sol=~fluido.reshape(G1.shape))
        i1, i2 = ["xyz".index(e) for e in c["ex"]]
        u = (U[idx][:, :, i1] * w).sum(1) / w.sum(1); v = (U[idx][:, :, i2] * w).sum(1) / w.sum(1)
        c["u"] = np.where(fluido, u, 0).reshape(G1.shape); c["v"] = np.where(fluido, v, 0).reshape(G1.shape)
    # 1ª passada: campos dos cortes e fumaça acumulada (∫T dV) em cada instante gravado
    paineis, inv = [], []
    for t, nome in tempos:
        T = campo_escalar(os.path.join(a.caso, nome, "T"), n)
        paineis.append([np.clip((T[c["idx"]] * c["w"]).sum(1) / c["w"].sum(1), 1e-6, 1.0).reshape(c["G1"].shape).astype(np.float32) for c in cortes])
        inv.append(float((T * vol).sum()))
    ts = np.array([t for t, _ in tempos]); inv = np.array(inv)
    # quadros a desenhar: sub-quadros por interpolação linear entre instantes gravados
    quadros = []
    for k in range(len(ts)):
        for s in range(a.sub if k < len(ts) - 1 else 1):
            f = s / a.sub; k2 = min(k + 1, len(ts) - 1)
            quadros.append((ts[k] + f * (ts[k2] - ts[k]), [(1 - f) * p + f * q for p, q in zip(paineis[k], paineis[k2])], inv[k] + f * (inv[k2] - inv[k])))
    # figura (polegadas): linha de cima e de baixo com a largura de cada painel igual à razão de aspecto dos dados, coluna lateral à direita
    W, H = 12.8, 7.2; fig = plt.figure(figsize=(W, H), dpi=a.dpi)
    def novo(x, y, w, hh): return fig.add_axes([x / W, y / H, w / W, hh / H])
    altura, xe, folga = 2.25, 0.70, 0.78; y_baixo = 1.05; y_cima = y_baixo + altura + 0.90; pos = []; x = xe
    for c in cortes[:2]: w = altura * (c["r1"][1] - c["r1"][0]) / (c["r2"][1] - c["r2"][0]); pos.append((x, y_cima, w, altura)); x += w + folga
    x = xe
    for c in cortes[2:]: w = altura * (c["r1"][1] - c["r1"][0]) / (c["r2"][1] - c["r2"][0]); pos.append((x, y_baixo, w, altura)); x += w + folga
    norma = LogNorm(vmin=1e-3, vmax=1.0); cmap = plt.get_cmap("viridis").copy(); cmap.set_bad("#d9dde3"); ims = []
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    for (px, py, pw, ph), c in zip(pos, cortes):
        ax = novo(px, py, pw, ph); e1, e2 = c["ex"]; ext = (c["r1"][0], c["r1"][1], c["r2"][0], c["r2"][1])
        im = ax.imshow(np.ma.masked_array(np.full(c["G1"].shape, 1e-6), mask=c["sol"]), origin="lower", extent=ext, norm=norma, cmap=cmap, interpolation="nearest", zorder=1, aspect="equal")
        ax.streamplot(c["G1"][0], c["G2"][:, 0], c["u"], c["v"], color=(1, 1, 1, 0.5), linewidth=0.5, density=1.1, arrowsize=0.55, zorder=2)
        if c["sol"].any() and c["fluido"].any(): ax.contour(c["G1"], c["G2"], c["sol"].astype(float), levels=[0.5], colors="#1f2937", linewidths=0.9, zorder=4)
        if c["fixo"][0] == "z":     # plantas: projeção da coifa, captores e pegada dos equipamentos que ficam abaixo do plano
            ax.add_patch(Rectangle((hood["x0"], hood["y0"]), hood["x1"] - hood["x0"], hood["y1"] - hood["y0"], fill=False, ec="#f8fafc", lw=1.1, ls="--", zorder=5))
            for k in cap: ax.add_patch(Rectangle((k["x"] - k["W"] / 2, k["y"] - k["H"] / 2), k["W"], k["H"], fill=False, ec="#ef4444", lw=1.5, zorder=5))
            for b in cj["ilha"]:
                if b["z1"] < c["fixo"][1]:
                    ax.add_patch(Rectangle((b["x0"], b["y0"]), b["x1"] - b["x0"], b["y1"] - b["y0"], fill=False, ec="#e5e7eb", lw=0.9, ls=":", zorder=5))
                    ax.text((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2, "ilha dos fogões", fontsize=6.5, ha="center", va="center", color="#111827", path_effects=halo, zorder=6)
            for b in cj["bancadas"]:
                if b["z1"] < c["fixo"][1]: ax.add_patch(Rectangle((b["x0"], b["y0"]), b["x1"] - b["x0"], b["y1"] - b["y0"], fill=False, ec="#e5e7eb", lw=0.9, ls=":", zorder=5))
        ax.set_xlim(*c["r1"]); ax.set_ylim(*c["r2"]); ax.set_title(c["nome"], fontsize=8.8, loc="left", pad=4)
        ax.set_xlabel(f"{e1} (m)", fontsize=8, labelpad=2); ax.set_ylabel(f"{e2} (m)", fontsize=8, labelpad=2); ax.tick_params(labelsize=7.2, length=2.5, pad=2)
        ax.xaxis.set_major_formatter(FuncFormatter(eixo_br)); ax.yaxis.set_major_formatter(FuncFormatter(eixo_br)); ims.append(im)
    # coluna lateral
    xr, wr = 9.60, 2.95
    fig.text(0.30 / W, 1 - 0.08 / H, a.titulo, fontsize=12.2, weight="bold", color="#111827", ha="left", va="top")
    fig.text(0.30 / W, 1 - 0.33 / H, f"Cozinha de banquetes do subsolo (Vivo Rio) · OpenFOAM v1912 · recorte de {br(dom['x1'] - dom['x0'], 1)} × {br(dom['y1'] - dom['y0'], 1)} m em planta, pé-direito de {br(dom['z1'] - dom['z0'], 2)} m",
             fontsize=8.2, color="#4b5563", ha="left", va="top")
    solver = {"boussinesq": "Boussinesq (flutuação) + k-ε", "compressivel": "compressível + k-ε"}.get(cj.get("solver"), cj.get("solver", ""))
    DT = difusividade(a.caso); par = cj.get("params", {})
    relogio = fig.text(xr / W, 1 - 0.78 / H, "", fontsize=27, weight="bold", color="#111827", ha="left", va="top")
    fig.text(xr / W, 1 - 1.34 / H, "após o início da liberação de fumaça", fontsize=8, color="#4b5563", ha="left", va="top")
    linhas = [f"Malha: {n / 1e6:.2f} M células (nível {cj.get('nivel')})".replace(".", ","),
              f"Escoamento estacionário: {solver}",
              f"Exaustão: {br(cj['Qexaustao_m3s'] * 60, 1)} m³/min em 2 captores",
              f"Reposição: {br(100 * cj['Qreposicao_m3s'] / cj['Qexaustao_m3s'], 0)} % da exaustão, 3 difusores de forro",
              f"Topo dos fogões: +{br(par.get('dT_quente', 0), 0)} K sobre o ambiente"]
    if DT: linhas.append(f"Fumaça: escalar passivo, difusividade {br(DT, 3)} m²/s")
    fig.text(xr / W, 1 - 1.68 / H, "\n".join(linhas), fontsize=7.6, color="#111827", ha="left", va="top", linespacing=1.55)
    axi = novo(xr + 0.52, 2.60, wr - 0.62, 1.50); axi.set_title("Fumaça no ambiente (∫ c dV)", fontsize=8.8, loc="left", pad=4)
    axi.plot(ts, inv, color="#cbd5e1", lw=1.2); linha, = axi.plot([], [], color="#2563eb", lw=1.8); ponto, = axi.plot([], [], "o", color="#2563eb", ms=4.5)
    axi.set_xlim(0, ts[-1]); axi.set_ylim(0, inv.max() * 1.12); axi.set_xlabel("t (s)", fontsize=8, labelpad=2); axi.set_ylabel("m³ equivalentes", fontsize=8, labelpad=2)
    axi.tick_params(labelsize=7.2, length=2.5, pad=2); axi.grid(alpha=0.25, lw=0.5)
    for lado in ("top", "right"): axi.spines[lado].set_visible(False)
    axi.xaxis.set_major_formatter(FuncFormatter(eixo_br)); axi.yaxis.set_major_formatter(FuncFormatter(eixo_br))
    cax = novo(xr, 1.38, wr, 0.16); cb = fig.colorbar(ims[0], cax=cax, orientation="horizontal"); cb.ax.tick_params(labelsize=7, length=2.5, pad=2)
    cb.set_label("concentração relativa de fumaça\n(1 = superfície de cocção; escala logarítmica)", fontsize=7.4, labelpad=3)
    fig.text(0.30 / W, 0.52 / H, "Ilustrativo: carga térmica dos fogões, ar de reposição e difusividade são hipóteses do caso (ver openfoam/README.md); o escoamento é estacionário e só a fumaça evolui.\n"
             "Linhas brancas = linhas de corrente · tracejado = projeção da coifa · retângulos vermelhos = captores · cinza = sólidos (equipamentos, chapas da coifa, chaminés).",
             fontsize=6.6, color="#4b5563", ha="left", va="top", linespacing=1.5)
    for q, (t, pn, iv) in enumerate(quadros):
        for im, c, val in zip(ims, cortes, pn): im.set_data(np.ma.masked_array(val, mask=c["sol"]))
        relogio.set_text(f"t = {t:.0f} s"); sel = ts <= t + 1e-9; linha.set_data(list(ts[sel]) + [t], list(inv[sel]) + [iv]); ponto.set_data([t], [iv])
        fig.savefig(os.path.join(a.saida, "quadros", f"q_{q:03d}.png"), dpi=a.dpi)
    nq = len(quadros); print(nq, "quadros,", len(tempos), "instantes gravados, t =", ts[0], "…", ts[-1], "s")
    mp4 = os.path.join(a.saida, "coifa_A_fumaca.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", os.path.join(a.saida, "quadros", "q_%03d.png"), "-c:v", "libx264", "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-crf", str(a.crf), "-movflags", "+faststart", mp4], check=True)
    print("mp4:", os.path.getsize(mp4) // 1024, "KB,", f"{nq / a.fps:.1f} s de vídeo")
    for nome, k in (("inicio", max(1, nq // 8)), ("meio", nq // 3), ("fim", nq - 1)): shutil.copy(os.path.join(a.saida, "quadros", f"q_{min(k, nq - 1):03d}.png"), os.path.join(a.saida, f"quadro_{nome}.png"))

if __name__ == "__main__": main()
