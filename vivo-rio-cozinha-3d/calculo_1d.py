# -*- coding: utf-8 -*-
# Cálculo 1D da rede de dutos (vazão, velocidade, perda de carga) a partir de saida/modelo.json.
# Nada é medido aqui: a geometria e as vazões declaradas do modelo viram uma rede em árvore (ventilador -> coifas/difusores)
# e recebem Darcy-Weisbach + coeficientes K de singularidades. O que não vem do desenho está em PARAMS / INFERENCIAS.
# Saídas: saida/calculo_dutos.csv, calculo_ventiladores.csv, calculo_dutos.json, calculo_dutos.md
import csv, json, math, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__)); SAIDA = os.path.join(ROOT, "saida")
M = json.load(open(os.path.join(SAIDA, "modelo.json"), encoding="utf-8"))

# ---------------------------------------------------------------- parâmetros (tudo que não é do desenho)
AR = dict(rho=1.20, mu=1.81e-5)                    # ar a ~20 °C, nível do mar (kg/m³; Pa·s)
LIM = dict(exa_max=12.5,                           # m/s — critério do relatório PA-COZINHA-003 (DIV-013)
           exa_min=7.5,                            # m/s — ADOTADO, a confirmar na NBR 14518 vigente
           ref_ar=10.0)                            # m/s — referência usual para insuflamento/ar exterior (sem critério do projeto)
K0 = dict(cotovelo90=0.6,                          # cotovelo retangular 90° (liso 0,2 ... mitrado sem aletas 1,2)
          ramal=0.8, passante=0.1,                 # tê/derivação, referidos à pressão dinâmica do trecho comum
          contracao=0.1,                           # redução gradual, referida à seção menor
          saida=1.0)                               # descarga livre na cobertura
CASOS = {"baixo": dict(eps=0.09e-3, k=0.5, dp_coifa=80.0),    # rugosidade (m), multiplicador dos K, perda coifa+filtros (Pa)
         "base":  dict(eps=0.15e-3, k=1.0, dp_coifa=125.0),
         "alto":  dict(eps=0.30e-3, k=2.0, dp_coifa=200.0)}
TOL_JUNCAO = 0.60      # m — pontas de dutos distintos a menos disso formam uma junção
TOL_TAP = 0.30         # m — folga somada à meia-largura do duto para derivação em T
TOL_CAPTOR = 1.00      # m — descida de coifa até o coletor
INFERENCIAS = [
    "Vazão de cada coifa = valor do texto da prancha de 2006 (m³/min), dividida igualmente entre os captores desenhados.",
    "Coifas E1 e E2 (20 m³/min cada) saem pelo mesmo captor CP-E1 (ramal removido, a refazer); só um captor foi desenhado.",
    "Coifa B (forno elétrico) não tem ligação desenhada: derivação adotada no coletor da Exaustão 3 mais próximo da coifa; a perda do ramal próprio não é contada.",
    "Insuflamento: vazão de cada ventilador dividida igualmente entre os difusores ligados à sua rede; cada difusor liga ao duto de insuflamento mais próximo (a ligação não está desenhada). Pontas com 'tampa' ficam sem vazão.",
    "Ar exterior: vazão dividida igualmente entre as duas descidas da coifa A e a ponta que segue fora do recorte (AE-02).",
    "Singularidades (cotovelos, tês, transições) deduzidas da geometria; construção real (raio, aletas) não consta no desenho: K varia de 0,5x a 2x entre os casos baixo/alto.",
    "Perda da coifa com filtros adotada em 125 Pa (80–200 Pa); curva e pressão do ventilador não constam do modelo, então a pressão requerida não é comparada com a de placa.",
    "Insuflamento e ar exterior: perda só nos dutos (sem difusor, filtro, serpentina nem registro).",
]

# ---------------------------------------------------------------- vazões declaradas
def vazao_ventilador(f):
    m = re.search(r"([\d\.]+)\s*m³/h", f["dados"]); return float(m.group(1).replace(".", ""))
def vazao_coifa(c):
    m = re.search(r"(\d+(?:,\d+)?)\s*m³/min", c["texto"]); return float(m.group(1).replace(",", ".")) * 60.0
FAN_Q = {f["id"]: vazao_ventilador(f) for f in M["mec"]["ventiladores"]}
COIFA_Q = {c["id"]: vazao_coifa(c) for c in M["mec"]["coifas"]}
COIFA_AREA = {c["id"]: c["L"] * c["P"] for c in M["mec"]["coifas"]}
# vazões implícitas no relatório (DIV-013): v · A da prumada E-60x50 da Exaustão 2
A_E2 = 0.60 * 0.50
Q_REL = {"Método I": 13.28 * A_E2 * 3600, "Método II": 17.15 * A_E2 * 3600}

def fans_de(ex):
    if "/" in ex:
        a, b = ex.split("/"); return [a, a[:-len(b)] + b]
    return [ex]

# ---------------------------------------------------------------- hidráulica
def dh(W, H): return 2.0 * W * H / (W + H)
def atrito(Re, rr):
    """Fator de atrito de Darcy (Colebrook iterativo; laminar 64/Re; transição interpolada)."""
    if Re <= 0: return 0.0
    if Re < 2300: return 64.0 / Re
    def turb(R):
        f = 0.25 / (math.log10(rr / 3.7 + 5.74 / R ** 0.9)) ** 2
        for _ in range(40): f = (-2.0 * math.log10(rr / 3.7 + 2.51 / (R * math.sqrt(f)))) ** -2
        return f
    if Re < 4000:
        a, b = 64.0 / 2300, turb(4000.0); return a + (b - a) * (Re - 2300) / 1700.0
    return turb(Re)
def pdin(v): return 0.5 * AR["rho"] * v * v
def dp_atrito(L, W, H, Q, eps):
    A = W * H; v = Q / A if A else 0.0
    if v <= 0: return 0.0
    D = dh(W, H); Re = AR["rho"] * v * D / AR["mu"]
    return atrito(Re, eps / D) * (L / D) * pdin(v)

# ---------------------------------------------------------------- rede
class UF:
    def __init__(s): s.p = {}
    def f(s, x):
        s.p.setdefault(x, x)
        while s.p[x] != x: s.p[x] = s.p[s.p[x]]; x = s.p[x]
        return x
    def u(s, a, b): s.p[s.f(a)] = s.f(b)

def seg_proj(p, a, b):
    ax, ay = a[0], a[1]; vx, vy = b[0] - ax, b[1] - ay; L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * vx + (p[1] - ay) * vy) / L2))
    return t, math.hypot(p[0] - (ax + vx * t), p[1] - (ay + vy * t))
def ancoras(d):
    if d["tipo"] == "horizontal": return ["a", "b"]
    if d["tipo"] == "descida": return ["a" if d["a"][2] >= d["b"][2] else "b"]
    if d["tipo"] == "prumada" and "-SS-" in d["id"]: return ["a" if d["a"][2] <= d["b"][2] else "b"]
    return []
def uvec(d):
    v = [d["b"][i] - d["a"][i] for i in range(3)]; L = math.sqrt(sum(c * c for c in v)); return tuple(c / L for c in v)

class Rede:
    def __init__(self, sis, dutos, difusores=(), taps_extra=()):
        self.sis = sis; self.D = {d["id"]: d for d in dutos}; self.uf = UF(); self.cortes = defaultdict(list)
        self.anexos = []; self.sinks = {}; self.taps = []
        self._ligar(); self._derivacoes(difusores, taps_extra); self._arestas()

    def _ligar(self):
        D = self.D; uf = self.uf
        for d in D.values(): uf.f((d["id"], "a")); uf.f((d["id"], "b"))
        ids = list(D)
        for i, p in enumerate(ids):                      # cadeia vertical (prumada -> shaft), coincidência exata em 3D
            for q in ids[i + 1:]:
                for e1 in "ab":
                    for e2 in "ab":
                        if math.dist(D[p][e1], D[q][e2]) < 0.02 and D[p]["tipo"] == D[q]["tipo"] == "prumada": uf.u((p, e1), (q, e2))
        anc = [(d["id"], e, d[e]) for d in D.values() for e in ancoras(d)]
        pares = sorted(((math.hypot(a[2][0] - b[2][0], a[2][1] - b[2][1]), a, b) for i, a in enumerate(anc) for b in anc[i + 1:] if a[0] != b[0]), key=lambda t: t[0])
        def proibido(ra, rb):
            for d in D:
                x, y = uf.f((d, "a")), uf.f((d, "b"))
                if (x == ra and y == rb) or (x == rb and y == ra): return True
            return False
        for dist, a, b in pares:
            if dist > TOL_JUNCAO: break
            ra, rb = uf.f(a[:2]), uf.f(b[:2])
            if ra != rb and not proibido(ra, rb): uf.u(a[:2], b[:2]); self.anexos.append((a[0], a[1], b[0], round(dist, 3), "ponta-ponta"))
        cont = defaultdict(int)
        for a in anc: cont[uf.f(a[:2])] += 1
        for did, e, p in anc:                            # pontas soltas: derivação em T no duto horizontal mais próximo
            if cont[uf.f((did, e))] > 1: continue
            d = D[did]; tol_extra = TOL_CAPTOR if d["tipo"] == "descida" else 0.0
            melhor = None
            for o in D.values():
                if o["id"] == did or o["tipo"] != "horizontal": continue
                t, dist = seg_proj(p, o["a"], o["b"]); tol = (TOL_TAP + o["W"] / 2 if not tol_extra else tol_extra)
                if dist <= tol and (melhor is None or dist < melhor[0]): melhor = (dist, o["id"], t)
            if melhor:
                dist, oid, t = melhor; o = D[oid]
                if 0.02 < t < 0.98:
                    key = ("T", did, e); uf.u((did, e), key); self.cortes[oid].append((t, key)); self.anexos.append((did, e, oid, round(dist, 3), "derivação"))
                else:
                    uf.u((did, e), (oid, "a" if t <= 0.02 else "b")); self.anexos.append((did, e, oid, round(dist, 3), "ponta-ponta"))

    def _derivacoes(self, difusores, taps_extra):
        D = self.D; uf = self.uf
        for tid, xy_, pais, flow in list(difusores) + list(taps_extra):
            melhor = None
            for o in D.values():
                if o["tipo"] != "horizontal" or (pais and o["id"] not in pais): continue
                t, dist = seg_proj(xy_, o["a"], o["b"])
                if melhor is None or dist < melhor[0]: melhor = (dist, o["id"], max(0.03, min(0.97, t)))
            dist, oid, t = melhor; key = ("TAP", tid); uf.f(key); Ld = D[oid]["comprimento"]
            for t0, _ in list(self.cortes[oid]):                 # duas tomadas na mesma estação: afasta a segunda em 15 cm
                if abs(t - t0) * Ld < 0.15: t = t0 - 0.15 / Ld if t0 - 0.15 / Ld > 0.03 else t0 + 0.15 / Ld
            self.cortes[oid].append((t, key))
            self.taps.append(dict(id=tid, duto=oid, t=t, dist=round(dist, 3), key=key, flow=flow))
            self.anexos.append((tid, "-", oid, round(dist, 3), "tomada"))

    def _arestas(self):
        D = self.D; uf = self.uf; idx = {}; self.pos = []
        def no(key):
            r = uf.f(key)
            if r not in idx: idx[r] = len(idx)
            return idx[r]
        self.E = []
        for d in D.values():
            u = uvec(d)
            if d["tipo"] == "horizontal":
                pts = [(0.0, (d["id"], "a"))] + sorted(self.cortes.get(d["id"], [])) + [(1.0, (d["id"], "b"))]
                for k, ((t1, k1), (t2, k2)) in enumerate(zip(pts, pts[1:])):
                    self.E.append(dict(duto=d["id"], peca=k, n1=no(k1), n2=no(k2), t1=t1, t2=t2, L=(t2 - t1) * d["comprimento"], W=d["W"], H=d["H"], tipo=d["tipo"], u=u, sis=self.sis))
            elif d["tipo"] in ("descida", "prumada"):
                self.E.append(dict(duto=d["id"], peca=0, n1=no((d["id"], "a")), n2=no((d["id"], "b")), t1=0.0, t2=1.0, L=d["comprimento"], W=d["W"], H=d["H"], tipo=d["tipo"], u=u, sis=self.sis))
        self.n = len(idx); self.no = no
        for t in self.taps: t["no"] = no(t["key"])
        self.adj = defaultdict(list)
        for i, e in enumerate(self.E): self.adj[e["n1"]].append(i); self.adj[e["n2"]].append(i)

    def orientar(self, raizes):
        """Árvore a partir das raízes (topo do shaft): pai/filho de cada aresta; detecta ciclos e dutos não alcançados."""
        self.raizes = raizes; self.pai_ar = {}; self.pai_no = {}; self.filhos = defaultdict(list); self.arv = {}; self.ciclos = []
        for e in self.E: e["pai"] = e["filho"] = None
        vis = {}
        for r in raizes:
            vis[r] = r; fila = [r]
            while fila:
                n = fila.pop(0)
                for i in self.adj[n]:
                    e = self.E[i]
                    if self.pai_ar.get(n) == i: continue
                    o = e["n2"] if e["n1"] == n else e["n1"]
                    if o in vis:
                        if i not in self.pai_ar.values() and e["pai"] is None: self.ciclos.append(e["duto"])
                        continue
                    vis[o] = r; self.pai_ar[o] = i; self.pai_no[o] = n; self.filhos[n].append(i); e["pai"], e["filho"] = n, o; fila.append(o)
        self.arv = vis
        self.nao_alcancadas = sorted({e["duto"] for e in self.E if e["pai"] is None})
        for e in self.E:
            if e["pai"] is not None: e["upc"] = e["u"] if e["pai"] == e["n1"] else tuple(-c for c in e["u"])
    def subarvore(self, n):
        out = [n]
        for i in self.filhos[n]: out += self.subarvore(self.E[i]["filho"])
        return out

# ---------------------------------------------------------------- montagem do modelo
def montar():
    por_sis = defaultdict(list)
    for d in M["dutos"]: por_sis[d["sistema"]].append(d)
    redes = {}
    # EXA: derivação inferida da coifa B no coletor da Exaustão 3 mais próximo
    cb = next(c for c in M["mec"]["coifas"] if c["id"] == "COIFA-B")
    pais_e3 = {d["id"] for d in por_sis["EXA"] if d["exaustor"] == "VM-COZ03" and d["tipo"] == "horizontal"}
    redes["EXA"] = Rede("EXA", por_sis["EXA"], taps_extra=[("COIFA-B", (cb["x"], cb["y"]), pais_e3, None)])
    redes["EXG"] = Rede("EXG", por_sis["EXG"])
    dif = [(f["id"], (f["x"], f["y"]), None, None) for f in M["mec"]["difusores"]]
    redes["INS"] = Rede("INS", por_sis["INS"], difusores=dif)
    redes["AEX"] = Rede("AEX", por_sis["AEX"])
    for sis, R in redes.items():
        raizes = []
        for d in por_sis[sis]:
            if d["tipo"] == "prumada" and ("-SH-" in d["id"] or (sis == "EXG" and "-SS-" in d["id"])): raizes.append(R.no((d["id"], "b")))
        R.orientar(raizes)
    return redes, por_sis

def ventiladores_da_raiz(sis, por_sis, R):
    out = {}
    for r in R.raizes:
        for d in por_sis[sis]:
            if d["tipo"] == "prumada" and R.no((d["id"], "b")) == r: out[r] = fans_de(d["exaustor"]); break
    return out

def sinks_exa(R, por_sis):
    """Folhas de exaustão: descida de cada captor (e tomada da coifa B) com a vazão base da coifa."""
    capt = {c["id"]: c for c in M["mec"]["captores"] if c["sistema"] == "EXA"}
    desc = {d["id"]: d for d in por_sis["EXA"] if d["tipo"] == "descida"}
    cap_de_desc = {}
    for cid, c in capt.items():
        for did, d in desc.items():
            if math.hypot(d["a"][0] - c["x"], d["a"][1] - c["y"]) < 0.05: cap_de_desc[did] = cid
    por_coifa = defaultdict(list)
    for did, cid in cap_de_desc.items(): por_coifa[capt[cid]["coifa"]].append(did)
    fl = {}
    for cf, lista in por_coifa.items():
        q = COIFA_Q["COIFA-" + cf]
        if cf == "E1": q += COIFA_Q["COIFA-E2"]            # E2 sai pelo mesmo captor
        for did in lista: fl[R.no((did, "b"))] = dict(id=did, coifa=cf, q=q / len(lista), hood=True, tap=False)
    for t in R.taps:
        if t["id"] == "COIFA-B": fl[t["no"]] = dict(id="COIFA-B", coifa="B", q=COIFA_Q["COIFA-B"], hood=True, tap=True)
    return fl

# ---------------------------------------------------------------- cálculo por cenário
def fluxo_exa(R, fl, fan_de_raiz, alvo):
    """Vazão por folha (m³/h) escalonada por árvore para a vazão-alvo do ventilador (alvo None = vazão das coifas)."""
    q = {}
    for r, fans in fan_de_raiz.items():
        nos = [n for n in R.subarvore(r) if n in fl]; soma = sum(fl[n]["q"] for n in nos)
        f = 1.0 if not alvo or alvo.get(fans[0]) is None else alvo[fans[0]] / soma
        for n in nos: q[n] = fl[n]["q"] * f
    return q

def fluxo_ar(R, fan_de_raiz, pesos=None):
    """Insuflamento/ar exterior: vazão de placa dividida entre as folhas da árvore (difusores ou terminais)."""
    q = {}
    for r, fans in fan_de_raiz.items():
        nos = R.subarvore(r); Q = sum(FAN_Q[f] for f in fans)
        folhas = [t["no"] for t in R.taps if t["no"] in nos] or [n for n in nos if not R.filhos[n] and n != r]
        w = {n: (pesos or {}).get(n, 1.0) for n in folhas}; s = sum(w.values())
        for n in folhas: q[n] = Q * w[n] / s
    return q

def vazoes_arestas(R, q):
    """Vazão em cada aresta = soma das folhas na subárvore do filho (m³/h)."""
    qa = {}
    for i, e in enumerate(R.E):
        if e["filho"] is not None: qa[i] = sum(q.get(n, 0.0) for n in R.subarvore(e["filho"]))
    return qa

def fit_no(R, n, ea, eb, supply, tap_final=False):
    """Singularidades do nó n para o percurso que chega por ea e sai por eb (ordem de viagem). Retorna [(tipo, K, aresta_ref)]."""
    E = R.E; out = []
    def viaj(i, chega):
        up = E[i]["upc"]; sinal = 1 if supply else -1
        return tuple(sinal * c for c in up)
    ta, tb = viaj(ea, True), viaj(eb, False)
    ang = math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(ta, tb))))))
    outros = [i for i in R.adj[n] if i not in (ea, eb)] ; tap = any(t["no"] == n for t in R.taps)
    m = 2 + len(outros) + (1 if tap else 0)
    comum = ea if supply else eb
    Aa, Ab = E[ea]["W"] * E[ea]["H"], E[eb]["W"] * E[eb]["H"]
    if m >= 3:
        out.append(("passante" if ang < 25 else "ramal", K0["passante"] if ang < 25 else K0["ramal"], comum))
    elif ang >= 25:
        out.append(("cotovelo", K0["cotovelo90"] * min(ang, 90.0) / 90.0, eb))
    if abs(Aa - Ab) / max(Aa, Ab) > 0.03 and not (m >= 3 and ang >= 25):
        peq = ea if Aa < Ab else eb
        out.append(("transição", 0.5 * (1 - min(Aa, Ab) / max(Aa, Ab)) ** 2 if Ab > Aa else K0["contracao"], peq))
    return out

def avaliar(R, qa, supply, caso, hood_dp=True, fl=None):
    """Perda total (Pa) de cada folha até a raiz (ou da raiz até a folha), com a lista de componentes."""
    E = R.E; c = CASOS[caso]; res = {}
    folhas = set(fl) if fl else set(t["no"] for t in R.taps) | {n for n in range(R.n) if not R.filhos[n] and n in R.pai_ar}
    for s in folhas:
        if s not in R.pai_ar: continue
        cam = []; n = s
        while n in R.pai_ar: cam.append(R.pai_ar[n]); n = R.pai_no[n]      # folha -> raiz
        seq = cam[::-1] if supply else cam
        nos = []                                                           # nós entre arestas consecutivas, em ordem de viagem
        for a, b in zip(seq, seq[1:]):
            comum_no = ({E[a]["n1"], E[a]["n2"]} & {E[b]["n1"], E[b]["n2"]}).pop(); nos.append(comum_no)
        atr = fit = 0.0; det = []
        for i in seq:
            e = E[i]; Q = qa.get(i, 0.0) / 3600.0; pa = dp_atrito(e["L"], e["W"], e["H"], Q, c["eps"]); atr += pa
        for (a, b), n in zip(zip(seq, seq[1:]), nos):
            for tipo, K, ref in fit_no(R, n, a, b, supply):
                v = qa.get(ref, 0.0) / 3600.0 / (E[ref]["W"] * E[ref]["H"]); p = K * c["k"] * pdin(v); fit += p; det.append((tipo, E[ref]["duto"], round(p, 1)))
        tapnode = next((t for t in R.taps if t["no"] == s), None)
        if tapnode:                                                        # derivação da própria tomada
            ref = seq[-1] if supply else seq[0]
            v = qa.get(ref, 0.0) / 3600.0 / (E[ref]["W"] * E[ref]["H"]); p = K0["ramal"] * c["k"] * pdin(v); fit += p; det.append(("derivação", E[ref]["duto"], round(p, 1)))
        hood = c["dp_coifa"] if (hood_dp and fl and s in fl and fl[s]["hood"]) else 0.0
        res[s] = dict(atrito=atr, singul=fit, coifa=hood, total=atr + fit + hood, arestas=[E[i]["duto"] for i in seq], det=det)
    return res


def descarga(por_sis, fan, Q, caso):
    """Perda do duto de descarga (ventilador -> cobertura): atrito + saída livre. Retorna (Pa, id do duto)."""
    c = CASOS[caso]; ds = [d for d in por_sis["EXA"] if d["tipo"] == "descarga" and d["exaustor"] == fan]
    if not ds: return 0.0, None
    d = ds[0]; v = Q / 3600.0 / (d["W"] * d["H"])
    return dp_atrito(d["comprimento"], d["W"], d["H"], Q / 3600.0, c["eps"]) + K0["saida"] * c["k"] * pdin(v), d["id"]

class secao:
    """Troca temporária da seção de um duto (sensibilidade): with secao(R, {'D-EXA-SS-011': (0.70, 0.50)}): ..."""
    def __init__(s, R, ov): s.R, s.ov, s.old = R, ov, []
    def __enter__(s):
        for e in s.R.E:
            if e["duto"] in s.ov: s.old.append((e, e["W"], e["H"])); e["W"], e["H"] = s.ov[e["duto"]]
    def __exit__(s, *a):
        for e, W, H in s.old: e["W"], e["H"] = W, H

def sinks_ar(R, q):
    return {n: dict(id=next((t["id"] for t in R.taps if t["no"] == n), None) or "terminal", hood=False) for n, v in q.items() if v > 0}

def por_arvore(R, res, raiz):
    return {s: r for s, r in res.items() if R.arv.get(s) == raiz}

def resumo_arvore(R, por_sis, res, raiz, fans, sis, Q, caso, rotulo):
    """Pressão requerida pelo caminho crítico de uma árvore (+ descarga na exaustão)."""
    p = por_arvore(R, res, raiz)
    if not p: return None
    s_crit = max(p, key=lambda s: p[s]["total"]); r = p[s_crit]
    desc, dsid = (descarga(por_sis, fans[0], Q, caso) if sis == "EXA" else (0.0, None))
    return dict(total=r["total"] + desc, caminho=r["total"], descarga=desc, atrito=r["atrito"], singul=r["singul"], coifa=r["coifa"],
                critico=rotulo(s_crit), arestas=r["arestas"], det=r["det"])

def calcular():
    redes, por_sis = montar()
    raiz_fan = {s: ventiladores_da_raiz(s, por_sis, redes[s]) for s in ("EXA", "INS", "AEX")}
    fl = sinks_exa(redes["EXA"], por_sis)
    RE, RI, RX = redes["EXA"], redes["INS"], redes["AEX"]
    out = dict(redes=redes, por_sis=por_sis, raiz_fan=raiz_fan, fl_exa=fl, cen={}, sens={})
    alvos = [("S1", "vazão das coifas (prancha 2006)", None),
             ("S2", "vazão de placa dos ventiladores", {f: FAN_Q[f] for f in FAN_Q}),
             ("S3a", "relatório PA-COZINHA-003, Método I (Exaustão 2)", {"VM-COZ02": Q_REL["Método I"]}),
             ("S3b", "relatório PA-COZINHA-003, Método II (Exaustão 2)", {"VM-COZ02": Q_REL["Método II"]})]
    for cod, desc, alvo in alvos:
        q = fluxo_exa(RE, fl, raiz_fan["EXA"], alvo); qa = vazoes_arestas(RE, q)
        c = dict(desc=desc, q=q, qa=qa, fans={})
        for r, fans in raiz_fan["EXA"].items():
            Qf = sum(v for n, v in q.items() if RE.arv.get(n) == r)
            c["fans"][fans[0]] = dict(Q=Qf, casos={})
            for caso in CASOS:
                res = avaliar(RE, qa, False, caso, fl=fl)
                c["fans"][fans[0]]["casos"][caso] = resumo_arvore(RE, por_sis, res, r, fans, "EXA", Qf, caso, lambda s: fl[s]["id"])
        out["cen"][cod] = c
    # insuflamento (vazão de placa dividida entre os difusores) e ar exterior (dividida entre os terminais)
    qi = fluxo_ar(RI, raiz_fan["INS"]); qai = vazoes_arestas(RI, qi); si = sinks_ar(RI, qi)
    qx = fluxo_ar(RX, raiz_fan["AEX"]); qax = vazoes_arestas(RX, qx); sx = sinks_ar(RX, qx)
    desc_aex = [RX.no((d["id"], "b")) for d in por_sis["AEX"] if d["tipo"] == "descida"]
    qx2 = fluxo_ar(RX, raiz_fan["AEX"], {n: (1.0 if n in desc_aex else 0.0) for n in qx}); qax2 = vazoes_arestas(RX, qx2)
    for nome, R, q, qa, sk, sis in (("INS", RI, qi, qai, si, "INS"), ("AEX", RX, qx, qax, sx, "AEX"), ("AEX_alt", RX, qx2, qax2, sinks_ar(RX, qx2), "AEX")):
        d = dict(q=q, qa=qa, fans={})
        for r, fans in raiz_fan[sis].items():
            Qf = sum(FAN_Q[f] for f in fans); d["fans"][" + ".join(fans)] = dict(Q=Qf, casos={})
            for caso in CASOS:
                res = avaliar(R, qa, True, caso, fl=sk)
                d["fans"][" + ".join(fans)]["casos"][caso] = resumo_arvore(R, por_sis, res, r, fans, sis, Qf, caso,
                                                                          lambda s, sk=sk: sk[s]["id"] if sk[s]["id"] != "terminal" else next((e["duto"] for e in R.E if e["filho"] == s), "terminal"))
        out["cen"][nome] = d
    # sensibilidade: coletor da coifa A com a seção da prumada (0,70 x 0,50)
    with secao(RE, {"D-EXA-SS-011": (0.70, 0.50)}):
        s = {}
        for cod in ("S1", "S2"):
            qa = out["cen"][cod]["qa"]
            for caso in CASOS:
                res = avaliar(RE, qa, False, caso, fl=fl)
                s[(cod, caso)] = resumo_arvore(RE, por_sis, res, [r for r, f in raiz_fan["EXA"].items() if f == ["VM-COZ01"]][0], ["VM-COZ01"], "EXA",
                                               out["cen"][cod]["fans"]["VM-COZ01"]["Q"], caso, lambda x: fl[x]["id"])
        out["sens"]["coletor_A"] = s
    return out

# ---------------------------------------------------------------- tabelas e relatório
def br(x, nd=1):
    return "—" if x is None else f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def faixa(sis, v, Q):
    if Q is None: return "sem vazão (exaustor não identificado)"
    if Q <= 0: return "sem vazão atribuída"
    if sis in ("EXA", "EXG"):
        if v > LIM["exa_max"]: return "ACIMA de 12,5 m/s"
        if v < LIM["exa_min"]: return "abaixo de 7,5 m/s (referência adotada, a confirmar)"
        return "dentro da faixa"
    return "acima de 10 m/s (referência usual)" if v > LIM["ref_ar"] else "ok"
def eixo(d, t): return [round(d["a"][i] + (d["b"][i] - d["a"][i]) * t, 3) for i in range(3)]

def tabelas(o):
    redes, por_sis = o["redes"], o["por_sis"]
    esc = {"EXA": ("S1", "S2"), "EXG": (None, None), "INS": ("INS", "INS"), "AEX": ("AEX", "AEX")}
    linhas, pecas = [], []
    for d in M["dutos"]:
        sis = d["sistema"]; R = redes[sis]; A = d["W"] * d["H"]; ed = [(i, e) for i, e in enumerate(R.E) if e["duto"] == d["id"]]
        row = dict(id=d["id"], sistema=sis, rotulo=d["rotulo"], tipo=d["tipo"], status=d["status"], vent=d["exaustor"], W=d["W"], H=d["H"], A=A,
                   L=d["comprimento"], Dh=dh(d["W"], d["H"]), Qmax=(LIM["exa_max"] * A * 3600 if sis in ("EXA", "EXG") else None))
        for k, cod in zip(("base", "placa"), esc[sis]):
            if d["tipo"] == "descarga":
                fan = d["exaustor"]; Q = o["cen"]["S1"]["fans"][fan]["Q"] if k == "base" else FAN_Q[fan]; v = Q / 3600 / A
                row.update({f"Q_{k}": Q, f"v_{k}": v, f"atr_{k}": dp_atrito(d["comprimento"], d["W"], d["H"], Q / 3600, CASOS["base"]["eps"])}); continue
            if cod is None or not ed: row.update({f"Q_{k}": None, f"v_{k}": None, f"atr_{k}": None}); continue
            qa = o["cen"][cod]["qa"]; qs = [qa.get(i, 0.0) for i, _ in ed]
            row.update({f"Q_{k}": max(qs), f"v_{k}": max(qs) / 3600 / A,
                        f"atr_{k}": sum(dp_atrito(e["L"], e["W"], e["H"], qa.get(i, 0.0) / 3600, CASOS["base"]["eps"]) for i, e in ed)})
        row["faixa_base"] = faixa(sis, row["v_base"] or 0, row["Q_base"]); row["faixa_placa"] = faixa(sis, row["v_placa"] or 0, row["Q_placa"])
        linhas.append(row)
        if d["tipo"] == "descarga":
            fan = d["exaustor"]; pecas.append(dict(duto=d["id"], sis=sis, a=d["a"], b=d["b"], sentido=1, Q_base=row["Q_base"], Q_placa=row["Q_placa"], v_base=row["v_base"], v_placa=row["v_placa"], W=d["W"], H=d["H"]))
        for i, e in ed:
            sent = (1 if e["filho"] == e["n1"] else -1) if sis in ("EXA", "EXG") else (1 if e["pai"] == e["n1"] else -1)
            qb = o["cen"][esc[sis][0]]["qa"].get(i) if esc[sis][0] else None; qp = o["cen"][esc[sis][1]]["qa"].get(i) if esc[sis][1] else None
            pecas.append(dict(duto=d["id"], sis=sis, a=eixo(d, e["t1"]), b=eixo(d, e["t2"]), sentido=sent, Q_base=qb, Q_placa=qp, W=d["W"], H=d["H"],
                              v_base=None if qb is None else qb / 3600 / A, v_placa=None if qp is None else qp / 3600 / A))
    return linhas, pecas

def balanco(o):
    ex1 = sum(COIFA_Q.values()); exp_ = sum(FAN_Q[f] for f in ("VM-COZ01", "VM-COZ02", "VM-COZ03"))
    ins = FAN_Q["AC-COZ01"] + FAN_Q["AC-COZ02"]; aex = FAN_Q["VM-COZ05"] + FAN_Q["VM-COZ06"]
    return dict(exaustao_coifas=ex1, exaustao_placa=exp_, insuflamento=ins, ar_exterior=aex, razao_coifas=(ins + aex) / ex1, razao_placa=(ins + aex) / exp_)

def escrever(o):
    linhas, pecas = tabelas(o); B = balanco(o)
    def num(v): return "" if v is None else (str(round(v, 3) if isinstance(v, float) else v).replace(".", ",") if not isinstance(v, bool) else str(v))
    def w(nome, head, rows):
        with open(os.path.join(SAIDA, nome), "w", encoding="utf-8-sig", newline="") as f:
            wr = csv.writer(f, delimiter=";", lineterminator="\r\n"); wr.writerow(head)
            for r in rows: wr.writerow([num(v) for v in r])
    w("calculo_dutos.csv", ["id", "sistema", "rotulo", "tipo", "situacao", "ventilador", "largura_m", "altura_m", "area_m2", "comprimento_m", "diametro_hidraulico_m",
                            "vazao_base_m3h", "vel_base_ms", "faixa_base", "vazao_placa_m3h", "vel_placa_ms", "faixa_placa", "vazao_max_12_5ms_m3h",
                            "perda_atrito_base_Pa", "perda_atrito_Pa_por_m"],
      [[r["id"], r["sistema"], r["rotulo"], r["tipo"], r["status"], r["vent"], r["W"], r["H"], r["A"], r["L"], r["Dh"], r["Q_base"], r["v_base"], r["faixa_base"],
        r["Q_placa"], r["v_placa"], r["faixa_placa"], r["Qmax"], r["atr_base"], (r["atr_base"] / r["L"] if r["atr_base"] is not None and r["L"] else None)] for r in linhas])
    NOME = {"S1": "exaustão: vazão das coifas (2006)", "S2": "exaustão: vazão de placa", "S3a": "exaustão 2: relatório, Método I", "S3b": "exaustão 2: relatório, Método II",
            "INS": "insuflamento: vazão de placa igual por difusor", "AEX": "ar exterior: igual por terminal", "AEX_alt": "ar exterior: tudo nas descidas da coifa A"}
    frows = []
    for cod, c in o["cen"].items():
        for f, d in c["fans"].items():
            b = d["casos"]["base"]
            frows.append([f, NOME[cod], FAN_Q[f] if f in FAN_Q else sum(FAN_Q[x] for x in f.split(" + ")), d["Q"], d["casos"]["baixo"]["total"], b["total"], d["casos"]["alto"]["total"],
                          b["caminho"], b["descarga"], b["critico"]])
    w("calculo_ventiladores.csv", ["ventilador", "cenario", "vazao_placa_m3h", "vazao_calculo_m3h", "pressao_requerida_baixo_Pa", "pressao_requerida_base_Pa",
                                   "pressao_requerida_alto_Pa", "caminho_ate_folha_base_Pa", "descarga_base_Pa", "caminho_critico"], frows)
    json.dump(dict(parametros=dict(ar=AR, limites=LIM, K=K0, casos=CASOS), inferencias=INFERENCIAS, balanco=B, pecas=pecas,
                   ventiladores={f: dict(placa=FAN_Q[f]) for f in FAN_Q}, coifas={k: dict(Q=COIFA_Q[k], area=COIFA_AREA[k]) for k in COIFA_Q},
                   cenarios={cod: {f: dict(Q=d["Q"], P={c: v["total"] for c, v in d["casos"].items()}, critico=d["casos"]["base"]["critico"]) for f, d in c["fans"].items()}
                             for cod, c in o["cen"].items()}),
              open(os.path.join(SAIDA, "calculo_dutos.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return linhas, pecas, B

def relatorio(o, linhas, B):
    L = {r["id"]: r for r in linhas}; cen = o["cen"]; S = lambda cod, f, caso="base": cen[cod]["fans"][f]["casos"][caso]
    out = []
    P = out.append
    P("# Cálculo 1D da rede de dutos — cozinha de banquetes (subsolo)\n")
    P("Vazão, velocidade e perda de carga de cada duto do modelo (`saida/modelo.json`), com Darcy-Weisbach e coeficientes K de singularidades. "
      "É um cálculo de verificação de projeto, não de fabricação: tudo que o desenho não traz está listado em **Premissas** e marcado INFERIDO. "
      "Arquivos: `calculo_dutos.csv` (por duto), `calculo_ventiladores.csv` (por ventilador), `calculo_dutos.json` (para o visualizador).\n")
    P("## Exaustão: pressão que cada ventilador precisa vencer\n")
    P("Cenário 1 = vazão das coifas da prancha de 2006; cenário 2 = vazão de placa do ventilador (coifas proporcionalmente ajustadas). "
      "Pressão total = maior caminho coifa→ventilador (atrito, singularidades e perda de coifa com filtros) + descarga até a cobertura. Faixa = caso baixo – alto.\n")
    P("| Ventilador | Placa (m³/h) | Coifas (m³/h) | Placa/coifas | Veloc. na prumada, cenário 1 / 2 (m/s) | Pressão, cenário 1 (Pa) | Pressão, cenário 2 (Pa) | Caminho crítico |")
    P("|---|---:|---:|---:|---:|---|---|---|")
    pr = {"VM-COZ01": "D-EXA-SS-012", "VM-COZ02": "D-EXA-SS-013", "VM-COZ03": "D-EXA-SS-014"}
    for f in ("VM-COZ01", "VM-COZ02", "VM-COZ03"):
        a, b = S("S1", f), S("S2", f); q1 = cen["S1"]["fans"][f]["Q"]
        P(f"| {f} | {br(FAN_Q[f], 0)} | {br(q1, 0)} | {br(FAN_Q[f] / q1, 2)} | {br(L[pr[f]]['v_base'])} / {br(L[pr[f]]['v_placa'])} | "
          f"**{br(a['total'], 0)}** ({br(S('S1', f, 'baixo')['total'], 0)}–{br(S('S1', f, 'alto')['total'], 0)}) | **{br(b['total'], 0)}** ({br(S('S2', f, 'baixo')['total'], 0)}–{br(S('S2', f, 'alto')['total'], 0)}) | {a['critico']} |")
    P("\nOs ventiladores não têm curva nem pressão de placa no modelo; falta confrontar esses números com o catálogo (GTS 560-9 etc.).\n")
    P("## Achados\n")
    ac = [r for r in linhas if r["sistema"] in ("EXA", "EXG") and (r["v_base"] or 0) > LIM["exa_max"]]
    ac2 = [r for r in linhas if r["sistema"] in ("EXA", "EXG") and (r["v_placa"] or 0) > LIM["exa_max"] and r not in ac]
    c1 = L["D-EXA-SS-011"]
    P(f"1. **Coletor da coifa A (D-EXA-SS-011, {c1['rotulo']}) estrangula a Exaustão 1.** Como desenhado, o trecho final leva as duas descidas somadas: "
      f"{br(c1['Q_base'], 0)} m³/h a {br(c1['v_base'])} m/s (cenário 1) e {br(c1['v_placa'])} m/s (placa); a vazão máxima a 12,5 m/s nessa seção seria {br(c1['Qmax'], 0)} m³/h. "
      f"As duas descidas EC-50x30 já ficam em {br(L['D-EXA-SS-015']['v_base'])} m/s. Só esse trecho responde por cerca de {br(S('S1','VM-COZ01')['total'] - o['sens']['coletor_A'][('S1','base')]['total'], 0)} Pa "
      f"dos {br(S('S1','VM-COZ01')['total'], 0)} Pa requeridos; com a seção da prumada (0,70 × 0,50) a pressão cairia para {br(o['sens']['coletor_A'][('S1','base')]['total'], 0)} Pa. "
      f"O rótulo EC-50x30 pode referir-se só aos captores: **medir o coletor em campo**.")
    f2 = L["D-EXA-SS-013"]
    P(f"2. **Exaustão 2: a prumada E-60x50 passa de 12,5 m/s se o ventilador entregar a vazão de placa.** Com {br(FAN_Q['VM-COZ02'], 0)} m³/h: {br(f2['v_placa'])} m/s; "
      f"com a vazão da coifa C da prancha de 2006 ({br(cen['S1']['fans']['VM-COZ02']['Q'], 0)} m³/h): {br(f2['v_base'])} m/s. "
      f"Os 13,28 m/s e 17,15 m/s do relatório (DIV-013) correspondem a {br(Q_REL['Método I'], 0)} e {br(Q_REL['Método II'], 0)} m³/h nessa seção. "
      f"Vazão máxima a 12,5 m/s: {br(f2['Qmax'], 0)} m³/h.")
    q3 = cen["S1"]["fans"]["VM-COZ03"]["Q"]
    P(f"3. **Exaustão 3: as coifas somam {br(q3, 0)} m³/h e o ventilador GTS 560-9 entrega {br(FAN_Q['VM-COZ03'], 0)} m³/h** "
      f"({br(100 * FAN_Q['VM-COZ03'] / q3, 0)} % da soma, antes de considerar a curva). A coifa B não tem ligação desenhada e a E2 depende do ramal removido (DIV-009).")
    def curto(ids): return ", ".join(i.replace("D-EXA-", "").replace("D-EXG-", "") for i in ids)
    lista = ", ".join(f"{r['id']} ({r['rotulo']}, {br(r['v_base'])} m/s)" for r in ac) or "nenhum"
    P(f"4. **Dutos de exaustão acima de 12,5 m/s no cenário 1:** {lista}." + (f" **No cenário 2 (placa), mais {len(ac2)} trechos**, a {br(min(r['v_placa'] for r in ac2))}{'' if round(min(r['v_placa'] for r in ac2), 1) == round(max(r['v_placa'] for r in ac2), 1) else ' a ' + br(max(r['v_placa'] for r in ac2))} m/s: "
      + curto([r['id'] for r in ac2]) + " (toda a Exaustão 2 e as descidas da coifa A, que sobem 1,15x e 1,49x quando o ventilador entrega a vazão de placa)." if ac2 else ""))
    P(f"5. **Balanço de ar.** Exaustão das coifas {br(B['exaustao_coifas'], 0)} m³/h (placa dos três ventiladores: {br(B['exaustao_placa'], 0)}); "
      f"insuflamento {br(B['insuflamento'], 0)} + ar exterior {br(B['ar_exterior'], 0)} = {br(B['insuflamento'] + B['ar_exterior'], 0)} m³/h. "
      f"Reposição/exaustão: {br(100 * B['razao_coifas'], 0)} % (coifas) ou {br(100 * B['razao_placa'], 0)} % (placa). Não inclui a exaustão geral (exaustor não identificado, DIV-011) nem infiltração.")
    ar = [r for r in linhas if r["sistema"] in ("INS", "AEX") and (r["v_base"] or 0) > LIM["ref_ar"]]
    ae1 = L["D-AEX-SS-001"]
    P(f"6. **Ar exterior: o AE-70x30 (D-AEX-SS-001) leva {br(ae1['Q_base'], 0)} m³/h a {br(ae1['v_base'])} m/s** se os dois ventiladores (VM-COZ05/06, AE-100x40 a {br(L['D-AEX-SS-006']['v_base'])} m/s na prumada) alimentarem só essa rede; "
      f"a 9 m/s essa seção comporta {br(9 * ae1['A'] * 3600, 0)} m³/h. Ou parte do ar exterior segue por outra rede fora do recorte, ou a seção está subdimensionada (a associação da prumada AE a esta rede é INFERIDA)."
      + (f" Insuflamento/ar exterior acima de 10 m/s (referência usual): " + "; ".join(f"{r['id']} ({r['rotulo']}, {br(r['v_base'])} m/s)" for r in ar) + "." if ar else ""))
    P("\n## Insuflamento e ar exterior (perda só nos dutos, sem difusor, filtro nem serpentina)\n")
    P("| Rede | Vazão (m³/h) | Pressão nos dutos, base (Pa) (baixo–alto) | Maior velocidade | Caminho crítico |\n|---|---:|---|---|---|")
    for cod, rotulo in (("INS", "Insuflamento"), ("AEX", "Ar exterior (igual por terminal)"), ("AEX_alt", "Ar exterior (tudo nas descidas da coifa A)")):
        for f, d in o["cen"][cod]["fans"].items():
            sis = "INS" if cod == "INS" else "AEX"; qa = o["cen"][cod]["qa"]; R = o["redes"][sis]
            vm = max(((qa.get(i, 0) / 3600 / (e["W"] * e["H"]), e["duto"]) for i, e in enumerate(R.E) if e["pai"] is not None and (o["raiz_fan"][sis].get(R.arv.get(e["pai"])) and f.split(" + ")[0] in o["raiz_fan"][sis][R.arv[e["pai"]]])), default=(0, ""))
            b = d["casos"]["base"]
            P(f"| {rotulo} — {f} | {br(d['Q'], 0)} | {br(b['total'], 0)} ({br(d['casos']['baixo']['total'], 0)}–{br(d['casos']['alto']['total'], 0)}) | {br(vm[0])} m/s ({vm[1]}) | {b['critico']} |")
    P("\nAs derivações para os difusores não estão desenhadas: cada difusor foi ligado ao duto de insuflamento mais próximo (distâncias em `calculo_dutos.json`/abaixo). "
      "A vazão nos ramais depende dessa hipótese; a do tronco (prumada) não.\n")
    dist = sorted((t for t in o["redes"]["INS"].taps), key=lambda t: -t["dist"])[:3]
    P("Difusores mais distantes do duto de ligação adotado: " + ", ".join(f"{t['id']} → {t['duto']} ({br(t['dist'], 1)} m)" for t in dist) + ".\n")
    P("## Vazão específica das coifas (consistência da prancha de 2006)\n")
    P("| Coifa | Vazão (m³/h) | Área em planta (m²) | m³/h por m² | Velocidade de face (m/s) |\n|---|---:|---:|---:|---:|")
    for k in COIFA_Q: P(f"| {k} | {br(COIFA_Q[k], 0)} | {br(COIFA_AREA[k], 2)} | {br(COIFA_Q[k] / COIFA_AREA[k], 0)} | {br(COIFA_Q[k] / COIFA_AREA[k] / 3600, 2)} |")
    P("\nB, C, D e E seguem a mesma regra (≈ 0,41 m/s sobre a área em planta); a coifa A (ilha) usa ≈ 0,63 m/s.\n")
    P("## Premissas e parâmetros\n")
    for s in INFERENCIAS: P(f"- {s}")
    P(f"- Ar a 20 °C: ρ = {br(AR['rho'], 2)} kg/m³, μ = 1,81·10⁻⁵ Pa·s. Atrito: Darcy-Weisbach com Colebrook e diâmetro hidráulico; rugosidade {br(CASOS['baixo']['eps']*1e3, 2)} / {br(CASOS['base']['eps']*1e3, 2)} / {br(CASOS['alto']['eps']*1e3, 2)} mm (baixo/base/alto).")
    P(f"- K base: cotovelo 90° {br(K0['cotovelo90'], 1)}, derivação {br(K0['ramal'], 1)}, passante {br(K0['passante'], 1)}, redução {br(K0['contracao'], 1)}, saída livre {br(K0['saida'], 1)}; multiplicadores 0,5× / 1× / 2× nos casos baixo / base / alto. Perda da coifa com filtros: 80 / 125 / 200 Pa.")
    P(f"- Critérios: 12,5 m/s é o limite citado no relatório PA-COZINHA-003 (DIV-013). Os 7,5 m/s de piso na exaustão foram **adotados e precisam ser confirmados na NBR 14518 vigente**; os 10 m/s para insuflamento são só referência usual.")
    P("- Alturas, shafts e descargas seguem as premissas P12–P13 do modelo (traçado acima do térreo INFERIDO, sem cotovelos).\n")
    return "\n".join(out)

def gerar():
    o = calcular(); linhas, pecas, B = escrever(o)
    md = relatorio(o, linhas, B); open(os.path.join(SAIDA, "calculo_dutos.md"), "w", encoding="utf-8").write(md)
    print(f"ok: {len(linhas)} dutos, {len(pecas)} peças; ver saida/calculo_dutos.(csv|json|md) e calculo_ventiladores.csv")
    return o

if __name__ == "__main__":
    gerar()
