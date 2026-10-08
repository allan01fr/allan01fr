# Sobreposição dos dutos do modelo final (modelo.json, coordenadas do modelo) sobre a prancha do as-built de exaustão
# (Anexo D), pela transformação inversa do registro. Uso: python3 verificacao/sobreposicao_dutos.py <PDF do Anexo D>
import sys, json, os, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
M = json.load(open(os.path.join(ROOT, "saida", "modelo.json"), encoding="utf-8"))
MPP = M["origem"]["mpp"]; OX, OY = M["origem"]["pt"]
mppD, xr, yr = 0.012357, (111.3, 316.6), (392.5, 921.4)
def inv(X, Y):
    xp, yp = OX + X / MPP, OY - Y / MPP
    return (xr[0] + (xp - xr[1]) * MPP / mppD, yr[0] + (yp - yr[1]) * MPP / mppD)
doc = pymupdf.open(sys.argv[1]); p = doc[0]
C = {"EXA": (0, 0.6, 0), "EXG": (0, 0.35, 0.2), "INS": (0, 0.3, 1), "AEX": (0.55, 0, 0.75)}
for d in M["dutos"]:
    a, b = inv(*d["a"][:2]), inv(*d["b"][:2])
    if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1:
        w, h = d["W"] / mppD / 2, d["H"] / mppD / 2
        p.draw_rect(pymupdf.Rect(a[0] - w, a[1] - h, a[0] + w, a[1] + h), color=C[d["sistema"]], width=1.2)
    else:
        p.draw_line(a, b, color=C[d["sistema"]], width=d["W"] / mppD, stroke_opacity=0.3)
        p.draw_line(a, b, color=C[d["sistema"]], width=0.8)
for w in M["paredes"]:
    p.draw_line(inv(*w["a"]), inv(*w["b"]), color=(1, 0.45, 0), width=1.2, stroke_opacity=0.5)
for c in M["mec"]["coifas"]:
    x, y = inv(c["x"], c["y"]); hw, hh = c["L"] / mppD / 2, c["P"] / mppD / 2
    p.draw_rect(pymupdf.Rect(x - hw, y - hh, x + hw, y + hh), color=(0.9, 0, 0.5), width=1.2, dashes="[4 3] 0")
out = os.path.join(HERE, "sobreposicao"); os.makedirs(out, exist_ok=True)
p.get_pixmap(dpi=60, clip=pymupdf.Rect(300, 250, 2300, 1060)).save(os.path.join(out, "sobreposicao_dutos_anexoD.png"))
print("ok")
