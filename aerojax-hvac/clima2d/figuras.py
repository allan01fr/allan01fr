"""Figuras do projeto: corte da geometria e mapas de resultados."""

import base64
import io

import numpy as np

def figura_geometria(projeto, ax=None):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    s = projeto["sala"]
    W, H = s["largura"], s["altura"]
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8 * H / W * 0.9 + 0.6))
    else:
        fig = ax.figure
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, lw=2, color="k"))
    for o in projeto["obstaculos"]:
        ax.add_patch(Rectangle((o["x0"], o["y0"]), o["x1"] - o["x0"], o["y1"] - o["y0"], color="0.5"))
        ax.text((o["x0"] + o["x1"]) / 2, o["y1"] + 0.03, o.get("nome", ""), ha="center", fontsize=8)
    for f in projeto["fontes"]:
        ax.add_patch(Rectangle((f["x0"], f["y0"]), f["x1"] - f["x0"], f["y1"] - f["y0"],
                               color="tab:orange", alpha=0.5))
        ax.text((f["x0"] + f["x1"]) / 2, f["y1"] + 0.03, f"{f.get('nome', '')}\n{f['sensivel_w']:.0f} W",
                ha="center", fontsize=8)
    cores = {"insuflamento": "tab:blue", "retorno": "tab:red"}
    for a in projeto["aberturas"]:
        cor = cores[a["tipo"]]
        if a["parede"] == "esquerda":
            ax.plot([0, 0], [a["inicio"], a["fim"]], color=cor, lw=7, solid_capstyle="butt")
        elif a["parede"] == "direita":
            ax.plot([W, W], [a["inicio"], a["fim"]], color=cor, lw=7, solid_capstyle="butt")
        elif a["parede"] == "piso":
            ax.plot([a["inicio"], a["fim"]], [0, 0], color=cor, lw=7, solid_capstyle="butt")
        else:
            ax.plot([a["inicio"], a["fim"]], [H, H], color=cor, lw=7, solid_capstyle="butt")
    ax.plot([], [], color="tab:blue", lw=7, label="insuflamento")
    ax.plot([], [], color="tab:red", lw=7, label="retorno")
    ax.add_patch(Rectangle((0, 0), 0, 0, color="tab:orange", alpha=0.5, label="fonte de calor"))
    ax.add_patch(Rectangle((0, 0), 0, 0, color="0.5", label="obstáculo"))
    ax.set_xlim(-0.2, W + 0.2)
    ax.set_ylim(-0.2, H + 0.25)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("altura [m]")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=8, frameon=False)
    ax.set_title("Corte do ambiente (modelo 2D)")
    fig.tight_layout()
    return fig


def figura_resultados(projeto, r):
    import matplotlib.pyplot as plt
    nx, ny, dx, dy = r["malha"]
    W, H = projeto["sala"]["largura"], projeto["sala"]["altura"]
    ext = [0, W, 0, H]
    xc = (np.arange(nx) + 0.5) * dx
    yc = (np.arange(ny) + 0.5) * dy
    uc = 0.5 * (r["u"][1:] + r["u"][:-1])
    vc = 0.5 * (r["v"][:, 1:] + r["v"][:, :-1])
    solido = r["solido"] > 0.5
    campos = [
        ("Temperatura [°C]", r["T"], "coolwarm", {}),
        ("Velocidade média [m/s]", r["vel"], "viridis", {"vmin": 0, "vmax": max(0.3, float(np.percentile(r["vel"], 99)))}),
        ("Umidade relativa [%]", r["UR"] * 100, "YlGnBu", {}),
        ("PMV (conforto térmico)", r["PMV"], "RdBu_r", {"vmin": -1.5, "vmax": 1.5}),
        ("Risco de corrente de ar DR [%]", r["DR"], "magma_r", {"vmin": 0, "vmax": 40}),
    ]
    fig, axs = plt.subplots(3, 2, figsize=(13, 11))
    for ax, (tit, campo, cmap, kw) in zip(axs.flat, campos):
        c = np.ma.masked_where(solido, campo)
        im = ax.imshow(c.T, origin="lower", extent=ext, cmap=cmap, aspect="equal", **kw)
        fig.colorbar(im, ax=ax, shrink=0.85)
        ax.streamplot(xc, yc, uc.T, vc.T, color="k", density=0.9, linewidth=0.4, arrowsize=0.5)
        ax.contour(xc, yc, r["ocupada"].T, levels=[0.5], colors="w", linestyles="--", linewidths=1)
        ax.set_title(tit)
        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
    figura_geometria(projeto, axs.flat[5])
    fig.suptitle("Resultados (média no tempo) - tracejado branco: zona ocupada; linhas: escoamento")
    fig.tight_layout()
    return fig


def png_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode()
