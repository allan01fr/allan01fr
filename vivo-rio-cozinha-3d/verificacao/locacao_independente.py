# Conferência independente das cotas de locação: distância do ponto à LINHA DE FACE de parede mais
# próxima, medida direto nas linhas do vetor da prancha (sem usar os eixos/espessuras do modelo).
import sys, json, os, math, random, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
M = json.load(open(os.path.join(ROOT, "saida", "modelo.json"), encoding="utf-8"))
mpp = M["origem"]["mpp"]
p = pymupdf.open(sys.argv[1])[0]
L = []
for d in p.get_drawings():
    c = tuple(round(x, 2) for x in (d.get("color") or ()))
    if c not in [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 1.0)] or d.get("fill"): continue
    for it in d["items"]:
        if it[0] == "l" and math.dist(it[1], it[2]) > (45 if c == (0.0, 1.0, 1.0) else 6): L.append((it[1].x, it[1].y, it[2].x, it[2].y))  # ciano: só painéis longos de câmara
random.seed(7)
amostra = [q for q in M["pontos"] if q["status"] != "PENDENTE"]
res = []
for q in amostra:
    P = q["pt"]; best = None
    for x1, y1, x2, y2 in L:
        dx, dy = x2 - x1, y2 - y1; LL = math.hypot(dx, dy); ux, uy = dx / LL, dy / LL
        s = (P[0] - x1) * ux + (P[1] - y1) * uy
        if s < 0 or s > LL: continue
        dd = abs((P[0] - x1) * uy - (P[1] - y1) * ux)
        if best is None or dd < best: best = dd
    A = M["locacao"][q["id"]]["A"]
    res.append(dict(id=q["id"], indep_m=round(best * mpp, 3), modelo_m=A["dist"] if A else None,
                    dif_cm=round((best * mpp - A["dist"]) * 100, 1) if A else None))
dif = [abs(r["dif_cm"]) for r in res if r["dif_cm"] is not None]
grandes = [r for r in res if r["dif_cm"] is not None and abs(r["dif_cm"]) > 1.0]
print(f"{len(res)} pontos; |dif| <= 1 cm em {sum(1 for d in dif if d <= 1.0)}; mediana {sorted(dif)[len(dif)//2]:.1f} cm")
for r in grandes: print("  >1 cm:", r)
json.dump(res, open(os.path.join(HERE, "locacao_independente.json"), "w"), indent=1)
