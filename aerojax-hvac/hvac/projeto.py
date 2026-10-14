"""
Projeto de climatização: dados de entrada, simulação, verificações e relatório.

É a camada usada pela interface gráfica (app/app.py). Um projeto é um dicionário
simples (salvo em JSON), para ser fácil de editar, versionar e trocar entre pessoas.
"""

import base64
import copy
import datetime as _dt
import io
import json
import math
import time

import numpy as np
import jax
import jax.numpy as jnp

from . import psicrometria as psi
from .sala2d import (Sala, Abertura, FonteCalor, Obstaculo, Insuflamento, montar_geometria,
                     estado_inicial, simular, indicadores, dt_estavel,
                     velocidade_face_insuflamento, Medias, RHO, CP)

# Ganho de calor por pessoa [W] - valores típicos (ASHRAE Fundamentals, cap. 18, tab. 1;
# mesma base da ABNT NBR 16401-1). Confira a tabela da norma para o seu caso.
ATIVIDADES = {
    "Sentado, trabalho leve (escritório)": (70.0, 45.0, 1.1),
    "Escritório, atividade moderada": (75.0, 55.0, 1.2),
    "Em pé, trabalho leve / caminhando devagar": (75.0, 70.0, 1.6),
    "Trabalho leve em bancada": (80.0, 140.0, 2.0),
}

CRITERIOS_PADRAO = {
    "pmv_max": 0.5,           # ISO 7730 categoria B: -0,5 < PMV < +0,5
    "ppd_max": 10.0,          # ISO 7730 categoria B
    "dr_max": 20.0,           # ISO 7730 categoria B: DR < 20 %
    "dT_vertical_max": 3.0,   # ISO 7730 categoria B: < 3 K entre 0,1 e 1,1 m
    "ur_min": 0.35,           # faixa usual de conforto (ver NBR 16401-2)
    "ur_max": 0.65,
    "vel_max": 0.25,          # m/s - referência usual de projeto; ajuste à norma aplicável
}


def projeto_padrao():
    """Escritório de exemplo (mesmo caso dos exemplos 02-04)."""
    return {
        "nome": "Escritório - exemplo",
        "responsavel": "",
        "sala": {"largura": 5.0, "altura": 2.8, "profundidade": 4.0},
        "aberturas": [
            {"parede": "esquerda", "inicio": 2.35, "fim": 2.45, "tipo": "insuflamento"},
            {"parede": "esquerda", "inicio": 2.55, "fim": 2.75, "tipo": "retorno"},
        ],
        "fontes": [
            {"nome": "2 pessoas", "x0": 2.8, "x1": 3.2, "y0": 0.0, "y1": 1.2,
             "sensivel_w": 150.0, "latente_w": 110.0},
            {"nome": "Computador", "x0": 3.6, "x1": 3.9, "y0": 0.75, "y1": 0.85,
             "sensivel_w": 100.0, "latente_w": 0.0},
        ],
        "obstaculos": [
            {"nome": "Mesa", "x0": 3.3, "x1": 4.3, "y0": 0.70, "y1": 0.75},
        ],
        "superficies": {"fluxo_esquerda": 0.0, "fluxo_direita": 40.0,
                        "fluxo_piso": 0.0, "fluxo_teto": 10.0},
        "iluminacao_w_m2": 0.0,
        "condicao": {"T_alvo": 24.0, "UR_alvo": 0.50, "met": 1.1, "clo": 0.5},
        "insuflamento": {"vazao_m3h": 600.0, "angulo_graus": 30.0, "temperatura": 19.6,
                         "ur_saida": 0.64},
        "simulacao": {"malha_cm": 10.0, "tempo_s": 1800.0, "tempo_media_s": 600.0,
                      "nu_efetiva": 1.5e-3},
        "criterios": dict(CRITERIOS_PADRAO),
    }


def completar(projeto):
    """Preenche chaves ausentes com o padrão (projetos antigos/importados)."""
    p = copy.deepcopy(projeto)
    base = projeto_padrao()
    for k, v in base.items():
        if k not in p:
            p[k] = copy.deepcopy(v)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                p[k].setdefault(kk, vv)
    return p


def salvar_json(projeto):
    return json.dumps(projeto, ensure_ascii=False, indent=2)


def carregar_json(texto):
    return completar(json.loads(texto))


# ---------------------------------------------------------------------------
# Cargas e montagem do modelo
# ---------------------------------------------------------------------------

def areas(projeto):
    s = projeto["sala"]
    lat = s["altura"] * s["profundidade"]
    hor = s["largura"] * s["profundidade"]
    return {"esquerda": lat, "direita": lat, "piso": hor, "teto": hor}


def cargas_totais(projeto):
    """Cargas do ambiente [W]: dicionário com parcelas, sensível e latente totais."""
    a = areas(projeto)
    sup = projeto["superficies"]
    parcelas = {}
    for f in projeto["fontes"]:
        parcelas[f.get("nome") or "fonte"] = (float(f["sensivel_w"]), float(f["latente_w"]))
    for parede in ("esquerda", "direita", "piso", "teto"):
        q = float(sup.get("fluxo_" + parede, 0.0)) * a[parede]
        if q:
            parcelas[f"Superfície {parede}"] = (q, 0.0)
    ilum = float(projeto.get("iluminacao_w_m2", 0.0)) * a["piso"]
    if ilum:
        parcelas["Iluminação"] = (ilum, 0.0)
    sens = sum(v[0] for v in parcelas.values())
    lat = sum(v[1] for v in parcelas.values())
    return {"parcelas": parcelas, "sensivel": sens, "latente": lat, "total": sens + lat}


def dimensionar_insuflamento(projeto):
    """Estado de insuflamento que mantém T_alvo/UR_alvo com a vazão informada."""
    c = projeto["condicao"]
    cg = cargas_totais(projeto)
    vazao = float(projeto["insuflamento"]["vazao_m3h"])
    w_amb = psi.umidade_absoluta(c["T_alvo"], c["UR_alvo"])
    t_ins, w_ins = psi.estado_insuflamento(c["T_alvo"], w_amb, cg["sensivel"], cg["latente"], vazao)
    ur_ins = psi.umidade_relativa(t_ins, w_ins)
    return {
        "temperatura": float(t_ins),
        "umidade_abs": float(w_ins),
        "ur_saida": float(ur_ins),
        "ponto_orvalho": float(psi.ponto_orvalho(w_ins)),
        "delta_T": float(c["T_alvo"] - t_ins),
        "capacidade_W": cg["total"],
        "capacidade_btuh": cg["total"] * 3.41214,
        "capacidade_TR": cg["total"] / 3516.85,
        "trocas_hora": vazao / (projeto["sala"]["largura"] * projeto["sala"]["altura"]
                                * projeto["sala"]["profundidade"]),
    }


def montar_modelo(projeto, malha_cm=None):
    """Converte o projeto em (Sala, Geometria, Insuflamento). Lança ValueError se inválido."""
    p = projeto
    s = p["sala"]
    h = (malha_cm or p["simulacao"]["malha_cm"]) / 100.0
    nx = max(8, int(round(s["largura"] / h)))
    ny = max(8, int(round(s["altura"] / h)))
    sup = dict(p["superficies"])
    sup["fluxo_teto"] = float(sup.get("fluxo_teto", 0.0)) + float(p.get("iluminacao_w_m2", 0.0))
    sala = Sala(
        largura=float(s["largura"]), altura=float(s["altura"]), profundidade=float(s["profundidade"]),
        nx=nx, ny=ny,
        aberturas=tuple(Abertura(a["parede"], float(a["inicio"]), float(a["fim"]), a["tipo"])
                        for a in p["aberturas"]),
        fontes=tuple(FonteCalor(float(f["x0"]), float(f["x1"]), float(f["y0"]), float(f["y1"]),
                                float(f["sensivel_w"]), float(f["latente_w"])) for f in p["fontes"]),
        obstaculos=tuple(Obstaculo(float(o["x0"]), float(o["x1"]), float(o["y0"]), float(o["y1"]))
                         for o in p["obstaculos"]),
        fluxo_esquerda=float(sup["fluxo_esquerda"]), fluxo_direita=float(sup["fluxo_direita"]),
        fluxo_piso=float(sup["fluxo_piso"]), fluxo_teto=float(sup["fluxo_teto"]),
        nu_efetiva=float(p["simulacao"]["nu_efetiva"]),
    )
    geo = montar_geometria(sala)
    i = p["insuflamento"]
    t_ins = float(i["temperatura"])
    ins = Insuflamento(vazao_m3h=jnp.asarray(float(i["vazao_m3h"])),
                       angulo_graus=jnp.asarray(float(i["angulo_graus"])),
                       temperatura=jnp.asarray(t_ins),
                       umidade_abs=psi.umidade_absoluta(t_ins, float(i["ur_saida"])))
    return sala, geo, ins


def validar(projeto):
    """Lista de problemas que impedem ou comprometem a simulação."""
    erros = []
    s = projeto["sala"]
    if min(s["largura"], s["altura"], s["profundidade"]) <= 0:
        erros.append("Dimensões da sala devem ser positivas.")
    tipos = [a["tipo"] for a in projeto["aberturas"]]
    if "insuflamento" not in tipos:
        erros.append("Inclua ao menos uma abertura de insuflamento.")
    if "retorno" not in tipos:
        erros.append("Inclua ao menos uma abertura de retorno.")
    for a in projeto["aberturas"]:
        comp = s["altura"] if a["parede"] in ("esquerda", "direita") else s["largura"]
        if not (0 <= a["inicio"] < a["fim"] <= comp + 1e-9):
            erros.append(f"Abertura {a['tipo']} na parede {a['parede']}: início/fim fora da parede (0 a {comp} m).")
    if abs(float(projeto["insuflamento"]["angulo_graus"])) > 75:
        erros.append("Ângulo do jato deve estar entre -75° e 75°.")
    if not erros:
        try:
            montar_modelo(projeto)
        except ValueError as e:
            erros.append(str(e))
    return erros


# ---------------------------------------------------------------------------
# Simulação
# ---------------------------------------------------------------------------

def simular_projeto(projeto, progresso=None, malha_cm=None):
    """Roda a simulação em blocos de ~60 s (para mostrar progresso).

    progresso(fração, mensagem) é chamado a cada bloco.
    Retorna dicionário com campos médios (numpy), indicadores (float) e verificações.
    """
    p = projeto
    sala, geo, ins = montar_modelo(p, malha_cm)
    c = p["condicao"]
    v_face = velocidade_face_insuflamento(sala, geo, float(p["insuflamento"]["vazao_m3h"]))
    ang = math.radians(abs(float(p["insuflamento"]["angulo_graus"])))
    dt = dt_estavel(sala, velocidade_max=1.5 * v_face / max(math.cos(ang), 0.2) + 0.5)

    passos_bloco = 50
    n_bloco = max(passos_bloco, int(round(60.0 / dt / passos_bloco)) * passos_bloco)
    t_bloco = n_bloco * dt
    n_blocos = max(1, int(math.ceil(p["simulacao"]["tempo_s"] / t_bloco)))
    n_media = min(n_blocos, max(1, int(round(p["simulacao"]["tempo_media_s"] / t_bloco))))

    rodar = jax.jit(lambda e: simular(sala, geo, ins, e, t_bloco, dt, t_bloco, passos_por_bloco=passos_bloco))
    estado = estado_inicial(sala, c["T_alvo"], float(psi.umidade_absoluta(c["T_alvo"], c["UR_alvo"])))
    soma = None
    t0 = time.time()
    for k in range(n_blocos):
        estado, med = rodar(estado)
        if k >= n_blocos - n_media:
            soma = med if soma is None else Medias(*(a + b for a, b in zip(soma, med)))
        if progresso is not None:
            progresso((k + 1) / n_blocos, f"{(k + 1) * t_bloco / 60:.0f} de {n_blocos * t_bloco / 60:.0f} min simulados")
    medias = Medias(*(a / n_media for a in soma))
    ind = indicadores(sala, geo, ins, medias, met=c["met"], clo=c["clo"])
    cg = cargas_totais(p)

    campos = {k: np.asarray(v) for k, v in ind.pop("campos").items()}
    indf = {k: float(v) for k, v in ind.items()}
    erro_sens = (indf["capacidade_sensivel_W"] - cg["sensivel"]) / max(cg["sensivel"], 1.0)
    erro_lat = (indf["capacidade_latente_W"] - cg["latente"]) / max(cg["latente"], 1.0) if cg["latente"] > 0 else 0.0
    return {
        "indicadores": indf,
        "T": np.asarray(medias.T), "W": np.asarray(medias.W), "vel": np.asarray(medias.vel),
        "PMV": campos["PMV"], "DR": campos["DR"], "UR": campos["UR"],
        "u": np.asarray(estado.u), "v": np.asarray(estado.v),
        "ocupada": np.asarray(geo.ocupada), "solido": np.asarray(geo.solido_c),
        "malha": (sala.nx, sala.ny, sala.dx, sala.dy),
        "dt": dt, "tempo_simulado": n_blocos * t_bloco, "tempo_cpu": time.time() - t0,
        "erro_balanco_sensivel": erro_sens, "erro_balanco_latente": erro_lat,
        "v_face": v_face,
    }


def estudo_malha(projeto, malhas_cm=(10.0, 5.0), progresso=None):
    """Roda o mesmo caso em duas malhas e compara os principais indicadores."""
    res = []
    for i, m in enumerate(malhas_cm):
        cb = None if progresso is None else (lambda f, msg, i=i, m=m: progresso((i + f) / len(malhas_cm), f"malha {m:g} cm: {msg}"))
        res.append(simular_projeto(projeto, cb, malha_cm=m))
    chaves = ["T_ocupada", "UR_ocupada", "vel_media_ocupada", "PMV_medio", "DR_max", "dT_vertical"]
    tabela = []
    for k in chaves:
        a, b = res[0]["indicadores"][k], res[-1]["indicadores"][k]
        tabela.append({"indicador": k, f"malha {malhas_cm[0]:g} cm": a, f"malha {malhas_cm[-1]:g} cm": b,
                       "diferença": b - a})
    return res, tabela


def conformidade(resultado, criterios):
    ind = resultado["indicadores"]
    c = criterios
    linhas = [
        ("PMV médio na zona ocupada", ind["PMV_medio"], f"entre -{c['pmv_max']} e +{c['pmv_max']}",
         abs(ind["PMV_medio"]) <= c["pmv_max"], "ISO 7730 / NBR 16401-2"),
        ("PPD médio [%]", ind["PPD_medio"], f"≤ {c['ppd_max']}", ind["PPD_medio"] <= c["ppd_max"], "ISO 7730"),
        ("Risco de corrente de ar DR máximo [%]", ind["DR_max"], f"≤ {c['dr_max']}",
         ind["DR_max"] <= c["dr_max"], "ISO 7730"),
        ("Estratificação 0,1-1,1 m [K]", ind["dT_vertical"], f"≤ {c['dT_vertical_max']}",
         abs(ind["dT_vertical"]) <= c["dT_vertical_max"], "ISO 7730"),
        ("Umidade relativa média [%]", ind["UR_ocupada"] * 100, f"{c['ur_min'] * 100:.0f} a {c['ur_max'] * 100:.0f}",
         c["ur_min"] <= ind["UR_ocupada"] <= c["ur_max"], "NBR 16401-2"),
        ("Velocidade máxima do ar [m/s]", ind["vel_max_ocupada"], f"≤ {c['vel_max']}",
         ind["vel_max_ocupada"] <= c["vel_max"], "critério de projeto"),
    ]
    return [{"critério": a, "resultado": round(b, 2), "limite": l, "atende": ok, "referência": r}
            for a, b, l, ok, r in linhas]


# ---------------------------------------------------------------------------
# Figuras e relatório
# ---------------------------------------------------------------------------

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


def _png_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode()


def relatorio_html(projeto, r, tabela_malha=None):
    """Relatório técnico autocontido (HTML com imagens embutidas)."""
    import matplotlib.pyplot as plt
    ind = r["indicadores"]
    cg = cargas_totais(projeto)
    conf = conformidade(r, projeto["criterios"])
    fig_r = figura_resultados(projeto, r)
    img_r = _png_base64(fig_r)
    plt.close(fig_r)
    i = projeto["insuflamento"]
    c = projeto["condicao"]
    s = projeto["sala"]

    def tab(linhas, cab):
        h = "".join(f"<th>{x}</th>" for x in cab)
        corpo = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in l) + "</tr>" for l in linhas)
        return f"<table><tr>{h}</tr>{corpo}</table>"

    parcelas = [(k, f"{v[0]:.0f}", f"{v[1]:.0f}") for k, v in cg["parcelas"].items()]
    parcelas.append(("<b>Total</b>", f"<b>{cg['sensivel']:.0f}</b>", f"<b>{cg['latente']:.0f}</b>"))
    conf_l = [(x["critério"], x["resultado"], x["limite"], "✔ atende" if x["atende"] else "✘ não atende",
               x["referência"]) for x in conf]
    malha_html = ""
    if tabela_malha:
        cab = list(tabela_malha[0].keys())
        malha_html = "<h2>Estudo de independência de malha</h2>" + tab(
            [[f"{v:.3f}" if isinstance(v, float) else v for v in l.values()] for l in tabela_malha], cab)

    return f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Estudo de climatização - {projeto['nome']}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;margin:8px 0 16px}}td,th{{border:1px solid #bbb;padding:4px 8px;font-size:14px}}
th{{background:#eef}}h1{{font-size:24px}}h2{{font-size:18px;border-bottom:1px solid #ccc;margin-top:28px}}
.aviso{{background:#fff6e0;border-left:4px solid #e0a000;padding:8px 12px}}</style></head><body>
<h1>Estudo de distribuição de ar e conforto térmico</h1>
<p><b>Projeto:</b> {projeto['nome']}<br><b>Responsável:</b> {projeto.get('responsavel') or '-'}<br>
<b>Data:</b> {_dt.date.today().strftime('%d/%m/%Y')}</p>
<h2>1. Dados de entrada</h2>
{tab([("Dimensões do corte (L x H)", f"{s['largura']} x {s['altura']} m"), ("Profundidade", f"{s['profundidade']} m"),
      ("Condição de projeto", f"{c['T_alvo']} °C / {c['UR_alvo'] * 100:.0f} % UR"),
      ("Atividade / vestimenta", f"{c['met']} met / {c['clo']} clo"),
      ("Vazão de insuflamento", f"{i['vazao_m3h']:.0f} m³/h"),
      ("Temperatura de insuflamento", f"{i['temperatura']:.1f} °C ({i['ur_saida'] * 100:.0f} % UR)"),
      ("Ângulo do jato", f"{i['angulo_graus']:.0f}°")], ["Item", "Valor"])}
<h2>2. Cargas térmicas do ambiente [W]</h2>{tab(parcelas, ["Parcela", "Sensível", "Latente"])}
<h2>3. Verificação de conformidade (zona ocupada)</h2>{tab(conf_l, ["Critério", "Resultado", "Limite", "Situação", "Referência"])}
<h2>4. Resultados</h2>
{tab([("Temperatura média na zona ocupada", f"{ind['T_ocupada']:.2f} °C"),
      ("Umidade relativa média", f"{ind['UR_ocupada'] * 100:.1f} %"),
      ("Velocidade média / máxima", f"{ind['vel_media_ocupada']:.2f} / {ind['vel_max_ocupada']:.2f} m/s"),
      ("PMV médio (desvio)", f"{ind['PMV_medio']:+.2f} ({ind['PMV_desvio']:.2f})"),
      ("PPD médio", f"{ind['PPD_medio']:.1f} %"),
      ("Ar de retorno", f"{ind['T_retorno']:.2f} °C / {ind['UR_retorno'] * 100:.0f} % UR"),
      ("Eficácia de remoção de calor", f"{ind['eficacia_remocao_calor']:.2f}")], ["Indicador", "Valor"])}
<img src="data:image/png;base64,{img_r}" style="width:100%">
<h2>5. Controle de qualidade numérica</h2>
{tab([("Balanço de calor sensível (retirado x cargas)", f"{r['erro_balanco_sensivel'] * 100:+.1f} %"),
      ("Balanço de calor latente (retirado x cargas)", f"{r['erro_balanco_latente'] * 100:+.1f} %"),
      ("Malha", f"{r['malha'][0]} x {r['malha'][1]} células ({r['malha'][2] * 100:.1f} cm)"),
      ("Tempo simulado / média", f"{r['tempo_simulado'] / 60:.0f} min / {projeto['simulacao']['tempo_media_s'] / 60:.0f} min"),
      ("Viscosidade turbulenta efetiva", f"{projeto['simulacao']['nu_efetiva']:.1e} m²/s")], ["Verificação", "Valor"])}
<p>Balanços acima de ±5 % indicam que a simulação ainda não atingiu regime permanente
(aumente o tempo simulado) ou que a malha não resolve as aberturas.</p>
{malha_html}
<h2>6. Hipóteses e limitações</h2>
<div class="aviso"><ul>
<li>Modelo bidimensional (corte): o difusor é tratado como linear, ocupando toda a profundidade.
A vazão e os balanços de energia e umidade são preservados; o alcance de jatos de saídas
concentradas (splits) tende a ser subestimado.</li>
<li>Turbulência representada por viscosidade efetiva constante (parâmetro de calibração).</li>
<li>Temperatura radiante média igual à temperatura do ar local; paredes adiabáticas exceto
os fluxos de calor informados.</li>
<li>Estudo de caráter comparativo e de pré-projeto. Não substitui o cálculo de cargas conforme
ABNT NBR 16401-1 nem simulação 3D validada quando exigida.</li></ul></div>
<p style="font-size:12px;color:#777">Gerado por AeroJAX-HVAC (hvac/projeto.py).</p>
</body></html>"""
