# Sobreposição do modelo (pontos, trechos em planta, paredes, louças) sobre a prancha original.
# Uso: python3 verificacao/sobreposicao.py <caminho do PDF da prancha de pontos>
import sys, json, os, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
M = json.load(open(os.path.join(ROOT, "saida", "modelo.json"), encoding="utf-8"))
mpp = M["origem"]["mpp"]; OX, OY = M["origem"]["pt"]
inv = lambda x, y: (OX + x / mpp, OY - y / mpp)
doc = pymupdf.open(sys.argv[1]); p = doc[0]
COL = {"HID-AF": (0.1, 0.4, 0.9), "HID-AQ": (0.85, 0.2, 0.15), "SAN-ESG": (0.55, 0.35, 0.15), "DRE": (0.0, 0.65, 0.75), "GAS": (0.9, 0.65, 0.0)}
for w in M["paredes"]:
    p.draw_line(inv(*w["a"]), inv(*w["b"]), color=(1, 0.5, 0), width=max(1.0, w["esp"] / mpp * 0.5), stroke_opacity=0.35)
for l in M["loucas"]:
    xs = [inv(*q) for q in l["poly"]]
    p.draw_polyline(xs + [xs[0]], color=(0.4, 0.2, 0.9), width=0.8)
nodes = {n["id"]: n for n in M["nos"]}
for t in M["trechos"]:
    a, b = nodes[t["a"]], nodes[t["b"]]
    if abs(a["x"] - b["x"]) + abs(a["y"] - b["y"]) > 0.01:
        p.draw_line(inv(a["x"], a["y"]), inv(b["x"], b["y"]), color=COL[t["sistema"]], width=1.0, dashes="[2 1] 0")
for q in M["pontos"]:
    c = COL.get(q["sistema"], (1, 0, 1)) if q["status"] != "PENDENTE" else (0.9, 0.1, 0.5)
    p.draw_circle(inv(q["x"], q["y"]), 2.6, color=c, width=0.7)
out = os.path.join(HERE, "sobreposicao")
os.makedirs(out, exist_ok=True)
tiles = [("geral", (160, 890, 1250, 1365), 90), ("lavagem_loucas", (280, 950, 520, 1130), 260), ("cozinha_lav_panelas", (690, 900, 1130, 1140), 200),
         ("camaras_preparos", (430, 1170, 1060, 1365), 170)]
for nm, r, dpi in tiles:
    p.get_pixmap(dpi=dpi, clip=pymupdf.Rect(*r)).save(os.path.join(out, f"sobreposicao_{nm}.png"))
print("ok")
