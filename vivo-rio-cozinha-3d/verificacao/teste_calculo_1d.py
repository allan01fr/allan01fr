# Verifica calculo_1d.py: hidráulica contra solução independente, conservação de vazão, topologia, números do relatório e saídas.
import csv, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import calculo_1d as C
res = []
def ok(nome, cond, info=""):
    res.append((nome, bool(cond), info)); print(("OK  " if cond else "FALHA ") + nome, info)

# 1. hidráulica: Colebrook resolvido por bisseção (independente da iteração de ponto fixo usada no código)
def colebrook_bisseccao(Re, rr):
    g = lambda f: 1 / math.sqrt(f) + 2 * math.log10(rr / 3.7 + 2.51 / (Re * math.sqrt(f)))
    lo, hi = 0.005, 0.2
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(lo) * g(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2
pior = max(abs(C.atrito(Re, rr) / colebrook_bisseccao(Re, rr) - 1) for Re in (5e3, 2e4, 1e5, 3e5, 1e6) for rr in (1e-5, 1e-4, 5e-4, 2e-3))
ok("fator de atrito = Colebrook por bisseção (< 0,1 %)", pior < 1e-3, f"pior desvio {pior:.2e}")
ok("laminar: f = 64/Re", abs(C.atrito(1000, 1e-4) - 0.064) < 1e-12)
# duto quadrado 0,30 x 0,30, 10 m/s, 10 m: Dh = 0,30; Δp = f L/D ρv²/2
Q = 10 * 0.09; dp = C.dp_atrito(10.0, 0.30, 0.30, Q, 0.15e-3)
Re = C.AR["rho"] * 10 * 0.30 / C.AR["mu"]; ref = colebrook_bisseccao(Re, 0.15e-3 / 0.30) * (10 / 0.30) * 0.5 * C.AR["rho"] * 100
ok("Δp de atrito num duto de referência", abs(dp / ref - 1) < 1e-3, f"{dp:.2f} Pa (ref. {ref:.2f})")
ok("diâmetro hidráulico 0,5 x 0,3", abs(C.dh(0.5, 0.3) - 0.375) < 1e-12)

# 2. números do relatório PA-COZINHA-003 (DIV-013) e prumada E-70x50 na vazão de placa
A = 0.6 * 0.5
ok("13,28 m/s e 17,15 m/s reproduzidos pelas vazões implícitas", abs(C.Q_REL["Método I"] / 3600 / A - 13.28) < 1e-9 and abs(C.Q_REL["Método II"] / 3600 / A - 17.15) < 1e-9)
ok("prumada E-70x50 na placa de 15.200 m³/h = 12,06 m/s", abs(15200 / 3600 / (0.7 * 0.5) - 12.06) < 0.01)

# 3. topologia e conservação
o = C.calcular(); R = o["redes"]
for s in ("EXA", "EXG", "INS", "AEX"):
    ok(f"{s}: sem ciclos e todos os dutos alcançados a partir do shaft", not R[s].ciclos and not R[s].nao_alcancadas, f"{R[s].n} nós, {len(R[s].E)} arestas, {len(R[s].raizes)} raiz(es)")
    ok(f"{s}: floresta (nós − arestas = nº de árvores)", R[s].n - len(R[s].E) == len(R[s].raizes))
def balanco_nos(Rd, q, qa, supply):
    ruins = []
    for n in range(Rd.n):
        if n in Rd.raizes: continue
        pe = Rd.pai_ar.get(n)
        if pe is None: continue
        filhos = sum(qa.get(i, 0.0) for i in Rd.filhos[n]) + q.get(n, 0.0)
        if abs(qa.get(pe, 0.0) - filhos) > 1e-6: ruins.append(n)
    return ruins
for cod, c in o["cen"].items():
    sis = "EXA" if cod[0] == "S" else ("INS" if cod == "INS" else "AEX")
    ok(f"conservação de vazão em todos os nós ({cod})", not balanco_nos(R[sis], c["q"], c["qa"], sis != "EXA"))
    for f, d in c["fans"].items():
        tot = sum(v for n, v in c["q"].items() if R[sis].arv.get(n) == [r for r, fs in o["raiz_fan"][sis].items() if f.split(" + ")[0] in fs][0])
        ok(f"{cod} {f}: soma das folhas = vazão da árvore", abs(tot - d["Q"]) < 1e-6, f"{tot:.0f} m³/h")
# exaustor declarado no duto = ventilador da árvore
erros = []
for d in C.M["dutos"]:
    if d["sistema"] == "EXA" and d["exaustor"] in ("VM-COZ01", "VM-COZ02", "VM-COZ03") and d["tipo"] != "descarga":
        for i, e in enumerate(R["EXA"].E):
            if e["duto"] == d["id"]:
                raiz = R["EXA"].arv[e["n1"]]
                if o["raiz_fan"]["EXA"][raiz][0] != d["exaustor"]: erros.append(d["id"])
ok("cada duto de exaustão cai na árvore do ventilador que o desenho declara", not erros, str(erros[:3]))

# 4. perdas: monotonia entre casos, cenários e soma dos componentes
for cod in ("S1", "S2", "INS", "AEX"):
    for f, d in o["cen"][cod]["fans"].items():
        t = d["casos"]; ok(f"{cod} {f}: baixo ≤ base ≤ alto", t["baixo"]["total"] <= t["base"]["total"] <= t["alto"]["total"])
        b = t["base"]; ok(f"{cod} {f}: total = atrito + singularidades + coifa + descarga", abs(b["total"] - (b["atrito"] + b["singul"] + b["coifa"] + b["descarga"])) < 1e-6)
ok("pressão sobe com a vazão (S2 ≥ S1 nos ventiladores 1 e 2)", all(o["cen"]["S2"]["fans"][f]["casos"]["base"]["total"] > o["cen"]["S1"]["fans"][f]["casos"]["base"]["total"] for f in ("VM-COZ01", "VM-COZ02")))
sens = o["sens"]["coletor_A"]; ok("coletor A maior reduz a pressão da Exaustão 1", sens[("S1", "base")]["total"] < o["cen"]["S1"]["fans"]["VM-COZ01"]["casos"]["base"]["total"])
ok("troca temporária de seção foi revertida", [e["W"] for e in R["EXA"].E if e["duto"] == "D-EXA-SS-011"] == [0.50, 0.50, 0.50])

# 5. saídas
linhas = list(csv.DictReader(open(os.path.join(ROOT, "saida", "calculo_dutos.csv"), encoding="utf-8-sig"), delimiter=";"))
ok("CSV tem os 61 dutos do modelo", len(linhas) == len(C.M["dutos"]) == 61, str(len(linhas)))
j = json.load(open(os.path.join(ROOT, "saida", "calculo_dutos.json"), encoding="utf-8"))
ok("JSON: peças cobrem todos os dutos", {p["duto"] for p in j["pecas"]} == {d["id"] for d in C.M["dutos"]}, f"{len(j['pecas'])} peças")
comp = sum(p["a"] != p["b"] for p in j["pecas"]); ok("JSON: nenhuma peça de comprimento nulo", comp == len(j["pecas"]))
Lsoma = {}
for p in j["pecas"]: Lsoma[p["duto"]] = Lsoma.get(p["duto"], 0) + math.dist(p["a"], p["b"])
d_err = [d["id"] for d in C.M["dutos"] if abs(Lsoma[d["id"]] - d["comprimento"]) > 0.01]
ok("JSON: peças somam o comprimento de cada duto", not d_err, str(d_err[:3]))
json.dump([{"teste": a, "ok": b, "info": c} for a, b, c in res], open(os.path.join(HERE, "resultado_calculo_1d.json"), "w"), ensure_ascii=False, indent=1)
print(f"{sum(r[1] for r in res)} / {len(res)} ok")
sys.exit(0 if all(r[1] for r in res) else 1)
