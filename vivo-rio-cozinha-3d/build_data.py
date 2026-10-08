# -*- coding: utf-8 -*-
"""
Monta a fonte única de dados (modelo.json) do modelo 3D de tubulações da
Cozinha de Banquetes (subsolo) a partir das leituras da prancha
TOM001-COZ-PJ-E-R-006-R001 ("Cozinha - pontos elet. e hidr.").

Entradas (pasta fonte/):
  raw_points.py        leitura manual símbolo a símbolo (coords em pt da folha)
  circulos_hough.json  centros dos símbolos circulares (detecção no vetor rasterizado)
  walls_raw.json       pares de linhas paralelas (paredes) extraídos do vetor
  equip_rects.json     retângulos de equipamentos (camada cinza do layout)
  linhas_ciano.json    linhas da camada ciano (vidros / folhas de porta)
Saída: saida/modelo.json
"""
import json, math, os, re
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda *p: os.path.join(HERE, *p)

# ----------------------------------------------------------------------------
# 1. Sistema de coordenadas
# ----------------------------------------------------------------------------
# Escala medida: 5 câmaras frigoríficas com medidas internas no memorial
# (34-CÂMARA-FRIG): largura/comprimento do vetor x medida do memorial.
CAL = [  # (descrição, medida memorial m, medida vetor pt)
    ("Câmara semi-preparados 1 - largura interna", 2.20, 507.22 - 442.24),
    ("Câmara semi-preparados 1 - comprimento interno", 4.95, 1335.92 - 1189.76),
    ("Câmara resfriados - largura interna", 2.10, 913.30 - 851.38),
    ("Câmara congelados - largura interna", 2.10, 1043.26 - 981.34),
    ("Câmara hortifruti - largura x comprimento (3,05)", 3.05, 1335.90 - 1245.90),
]
MPP = round(sum(m / p for _, m, p in CAL) / len(CAL), 6)        # m por pt
OX, OY = 437.74, 1340.42   # origem: vértice externo inf. esq. do painel da câmara semi-preparados 1
def M(x, y):
    return (round((x - OX) * MPP, 3), round((OY - y) * MPP, 3))
def Mpoly(pts):
    return [list(M(x, y)) for x, y in pts]

PRANCHA = "TOM001-COZ-PJ-E-R-006-R001"
PR_CURTA = "COZ 006 · Pontos el./hidr. · Subsolo"

# ----------------------------------------------------------------------------
# 2. Níveis e ambientes
# ----------------------------------------------------------------------------
Z_TOPO_PAREDE_H = 3.00   # pé-direito adotado sobre o PA (INFERIDO)
H_DIST = 2.85            # altura adotada da distribuição de água/gás sobre o PA (INFERIDO)
H_ENTERRADO = 0.30       # profundidade adotada do ramal de esgoto sob o PA (INFERIDO)

MARCAS = [  # marcas de nível lidas na prancha (pt)
    dict(id="M1", pt=(826, 885), pa=-2.87, po=-3.44, onde="porta norte da cozinha (linha de cocção)"),
    dict(id="M2", pt=(1157, 1003), pa=-2.87, po=-3.24, onde="hall dos elevadores"),
    dict(id="M3", pt=(415, 1159), pa=-2.87, po=-3.24, onde="circulação / carros quentes"),
    dict(id="M4", pt=(1167, 975), pa=-2.87, po=-3.24, onde="hall (junto ao shaft)"),
    dict(id="M5", pt=(939, 1229), pa=-3.07, po=-3.44, onde="ante-câmara"),
    dict(id="M6", pt=(1175, 1118), pa=-2.87, po=-3.24, onde="circulação junto ao Gelo"),
    dict(id="M7", pt=(545, 1262), pa=-3.07, po=-3.44, onde="câmara semi-preparados 2"),
]

def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

FONTE_COZ = "PA sem marca no ambiente: adotado o PA −2,87 das marcas M1 (porta da cozinha) e M3 (circulação); PO −3,44 da marca M1"
AMB = [  # id, nome, polígono (pt), PA, PO, status do nível, fonte
    ("REF", "Refeitório", R(176, 916, 303, 1180), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("LAVL", "Lavagem de louças", R(311, 916, 487, 1127), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("DIST", "Distribuição", R(491, 916, 556, 1127), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("COZ", "Cozinha / Montagem", [(559, 916), (1065, 916), (1065, 1043), (972, 1043), (972, 1127), (559, 1127)], -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("LAVP", "Lavagem de panelas", R(975, 1043, 1065, 1127), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("GELO", "Gelo", R(1068, 1043, 1132, 1127), -2.87, -3.24, "EXTRAÍDO", "marca M6 na circulação contígua (−2,87 / −3,24)"),
    ("CIRC", "Circulação / carros", R(303, 1130, 1240, 1182), -2.87, -3.24, "EXTRAÍDO", "marcas M3 e M6"),
    ("LLMP", "Louça limpa", R(207, 1185, 347, 1336), -2.87, -3.24, "INFERIDO", "sem marca; adotado o nível da circulação (M3)"),
    ("CARQ", "Carros quentes", R(352, 1185, 433, 1336), -2.87, -3.24, "INFERIDO", "sem marca; adotado o nível da circulação (M3)"),
    ("CSP1", "Câmara semi-preparados 1", R(442.24, 1189.76, 507.22, 1335.92), -3.07, -3.44, "INFERIDO", "nota 'prever rebaixo −20 cm' + marca M7 da câmara vizinha"),
    ("CSP2", "Câmara semi-preparados 2", R(510.28, 1189.76, 575.26, 1335.92), -3.07, -3.44, "EXTRAÍDO", "marca M7"),
    ("MFRI", "Montagem fria", R(584.6, 1185, 662.4, 1336), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("PSAL", "Preparo de saladas", R(667.4, 1185, 752.2, 1336), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("PCAR", "Preparo de carnes", R(757.1, 1185, 841.8, 1336), -2.87, -3.44, "INFERIDO", FONTE_COZ),
    ("CRES", "Câmara de resfriados", R(851.38, 1189.76, 913.3, 1335.92), -3.07, -3.44, "INFERIDO", "nota 'prever rebaixo −20 cm' + marca M5"),
    ("ACAM", "Ante-câmara", R(916.36, 1189.76, 978.28, 1243.0), -3.07, -3.44, "EXTRAÍDO", "marca M5"),
    ("CHF", "Câmara hortifruti", R(916.36, 1245.9, 978.28, 1335.9), -3.07, -3.44, "INFERIDO", "nota 'prever rebaixo −20 cm' + marca M5"),
    ("CCON", "Câmara de congelados", R(981.34, 1189.76, 1043.26, 1335.92), -3.07, -3.44, "INFERIDO", "nota 'prever rebaixo −20 cm' + marca M5"),
    ("DESP", "Despensa", R(1053, 1185, 1150, 1336), -2.87, -3.24, "INFERIDO", "sem marca; adotado o nível da circulação (M6)"),
    ("DBEB", "Depósito de bebidas", R(1153, 1185, 1240, 1336), -2.87, -3.24, "INFERIDO", "sem marca; adotado o nível da circulação (M6)"),
    ("GAL", "Galeria técnica", R(300, 1342, 1240, 1362), -2.87, -3.24, "INFERIDO", "galeria sem marca de nível; adotado −2,87 (limite da folha)"),
]
AMB_POLY = {a[0]: Polygon(a[2]) for a in AMB}
AMB_D = {a[0]: dict(id=a[0], nome=a[1], pa=a[3], po=a[4], status=a[5], fonte=a[6]) for a in AMB}

def ambiente_de(x, y):
    p = Point(x, y)
    for k, pol in AMB_POLY.items():
        if pol.contains(p):
            return k, None
    best = min(AMB_POLY.items(), key=lambda kv: kv[1].distance(p))
    return best[0], round(best[1].distance(p) * MPP, 3)

# ----------------------------------------------------------------------------
# 3. Pontos (leitura) + ajuste ao centro do símbolo
# ----------------------------------------------------------------------------
ns = {}
exec(open(F("fonte", "raw_points.py"), encoding="utf-8").read(), ns)
RAW = ns["P"]
CIRC = json.load(open(F("fonte", "circulos_hough.json")))
REDONDOS = {"AF", "AQ", "GAS", "ESG", "ESGI", "DRE"}

ITENS = {  # nº da prancha -> memorial de equipamentos (só correspondências seguras)
    "1": "Fogão a gás (item 01)", "2": "Banho-maria elétrico (item 02)", "3": "Forno combinado (item 03)",
    "7": "Tampo / pia inox (item 07)", "15": "Bancada com pia inox (item 15)", "20": "Caixa retentora de detritos (item 20)",
    "24": "Pia lavatório de mãos (item 24)", "34": "Câmara frigorífica (item 34)", "40": "Mesa de lavagem com cuba (item 40)",
    "41": "Lavadora de louças (item 41)", "44": "Balcão de distribuição quente (item 44)", "45": "Balcão de distribuição frio (item 45)",
    "47": "Máquina de café (item 47)", "48": "Bebedouro (item 48)", "49": "Fabricador de gelo (item 49)",
}

def snap(q):
    if q["t"] not in REDONDOS:
        return q["x"], q["y"], False
    best, bd = None, 9e9
    for cx, cy, r in CIRC:
        if r < 1.5:
            continue
        d = math.hypot(cx - q["x"], cy - q["y"])
        if d < bd:
            best, bd = (cx, cy), d
    if best and bd <= 2.2:
        return best[0], best[1], True
    return q["x"], q["y"], False

pts = []
for q in RAW:
    x, y, sn = snap(q)
    dup = next((p for p in pts if p["t"] == q["t"] and math.hypot(p["xp"] - x, p["yp"] - y) < 1.0), None)
    if dup:
        continue
    pts.append(dict(q, xp=round(x, 2), yp=round(y, 2), snapped=sn))

SIS = {"AF": "HID-AF", "AQ": "HID-AQ", "GAS": "GAS", "DRE": "DRE",
       "ESG": "SAN-ESG", "ESGI": "SAN-ESG", "ESGR": "SAN-ESG", "RS": "SAN-ESG", "RSG": "SAN-ESG", "RSIF": "SAN-ESG"}
DISC = {"HID-AF": "HID", "HID-AQ": "HID", "GAS": "GAS", "DRE": "DRE", "SAN-ESG": "SAN", "SAN-VENT": "SAN"}
DN_MM = {'3/4"': 20, '1"': 25, '1.1/2"': 40, '2"': 50}
def titulo(q):
    t = q["t"]
    if t == "AF": return "Ponto de água fria"
    if t == "AQ": return "Ponto de água quente"
    if t == "GAS": return "Ponto de gás"
    if t == "DRE": return "Dreno de evaporador"
    if t == "ESG": return "Ponto de esgoto no piso" if (q["h"] or 0) <= 0.1 else "Ponto de esgoto na parede"
    if t == "ESGI": return "Saída de esgoto indireto"
    if t == "ESGR": return "Ponto de esgoto (altura do rodapé)"
    if t == "RS": return "Ralo seco"
    if t == "RSG": return "Ralo seco grande"
    if t == "RSIF": return "Ralo sifonado"
    return t

# IDs estáveis: registro persistente chave -> ID
REG_F = F("fonte", "registro_ids.json")
REG = json.load(open(REG_F)) if os.path.exists(REG_F) else {}
def key_of(q):
    return f'{q["t"]}@{q["xp"]:.1f},{q["yp"]:.1f}'
seq = {}
for v in REG.values():
    m = re.match(r"(.+)-(\d{3})$", v)
    if m:
        seq[m.group(1)] = max(seq.get(m.group(1), 0), int(m.group(2)))
def novo_id(prefix):
    seq[prefix] = seq.get(prefix, 0) + 1
    return f"{prefix}-{seq[prefix]:03d}"

PONTOS = []
pts.sort(key=lambda q: (q["yp"], q["xp"]))
for q in pts:
    amb, dist_amb = ambiente_de(q["xp"], q["yp"])
    A = AMB_D[amb]
    sis = SIS[q["t"]]
    disc = DISC[sis]
    k = key_of(q)
    if k not in REG:
        REG[k] = novo_id(f"{disc}-SS-{amb}")
    pid = REG[k]
    X, Y = M(q["xp"], q["yp"])
    h, st, regra = q["h"], "EXTRAÍDO", None
    if q["t"] in ("RS", "RSG", "RSIF"):
        h = 0.0
    if q["t"] == "ESGI":
        h, st = 0.15, "INFERIDO"
        regra = "Altura não cotada: saída da lavadora (68×71×142 cm, memorial item 41) adotada a 0,15 m do piso (valor usual de mercado)."
    if q["t"] == "ESGR":
        h, st = 0.10, "INFERIDO"
        regra = "Texto 'H=RODAPÉ' sem valor numérico: adotada a altura usual de rodapé, 0,10 m."
    Z = round(A["pa"] + h, 3)
    mem = (f'XY: centro do símbolo na folha ({q["xp"]:.2f}; {q["yp"]:.2f}) pt'
           + (" — ajustado ao centro do círculo vetorial" if q["snapped"] else " — posição lida no desenho")
           + f'; X=(x−{OX})·{MPP}; Y=({OY}−y)·{MPP} (escala medida, ver premissa P2). '
           + f'Z = PA {A["pa"]:+.2f} ({AMB_D[amb]["status"].lower()}: {A["fonte"]}) + h {h:.2f}'
           + (f' (texto da prancha: "{q["txt"]}")' if q["h"] is not None else "") + ".")
    if dist_amb:
        mem += f" Símbolo fora dos polígonos de ambiente (sobre parede); atribuído a {A['nome']} (a {dist_amb:.2f} m)."
    PONTOS.append(dict(
        id=pid, tipo=q["t"], titulo=titulo(q), sistema=sis, disciplina=disc,
        dn=q["dn"] or "", dn_mm=DN_MM.get(q["dn"], 100 if q["t"] in ("RSIF", "RSG") else 50 if q["t"] in ("RS",) else 25),
        x=X, y=Y, z=Z, h=h, pav="Subsolo", amb=amb, amb_nome=A["nome"], prancha=PRANCHA, prancha_curta=PR_CURTA,
        item=q["item"], equipamento=ITENS.get(q["item"], (f"nº {q['item']} na prancha (sem correspondência segura no memorial)" if q["item"] else "")),
        texto=q["txt"], memoria=mem, status=st, motivo=regra or "", pt=[q["xp"], q["yp"]],
    ))

# Pendência: canaleta de descarga das lavadoras (citada, não desenhada)
for q in [p for p in PONTOS if p["tipo"] == "ESGI"]:
    k = f'CANALETA@{q["pt"][0]:.1f},{q["pt"][1]:.1f}'
    if k not in REG:
        REG[k] = novo_id(f"SAN-SS-{q['amb']}")
    PONTOS.append(dict(
        id=REG[k], tipo="CANAL", titulo="Canaleta de descarga (não desenhada)", sistema="SAN-ESG", disciplina="SAN",
        dn="", dn_mm=100, x=q["x"], y=round(q["y"] - 0.25, 3), z=AMB_D[q["amb"]]["pa"], h=0.0, pav="Subsolo",
        amb=q["amb"], amb_nome=q["amb_nome"], prancha=PRANCHA, prancha_curta=PR_CURTA, item="41",
        equipamento=ITENS["41"], texto="ESG. INDIRETO 1.1/2\" DESCARREGA SOBRE CANALETA AQ@93°C",
        memoria="Posição marcada 0,25 m à frente da saída indireta apenas para referência visual; a canaleta é citada no texto mas não aparece na planta.",
        status="PENDENTE", motivo="A canaleta que recebe o esgoto indireto da lavadora é citada no texto, mas não está desenhada: posição, comprimento e destino indeterminados.",
        pt=q["pt"]))

PID = {p["id"]: p for p in PONTOS}

# ----------------------------------------------------------------------------
# 4. Nós e trechos
# ----------------------------------------------------------------------------
NOS = {}
def no(nid, x, y, z, tipo="no", ref=None):
    NOS[nid] = dict(id=nid, x=round(x, 3), y=round(y, 3), z=round(z, 3), tipo=tipo, ref=ref)
    return nid
TRECHOS = []
def trecho(sis, dn, a, b, status, motivo, passagem, pontos=(), amb=None):
    A, B = NOS[a], NOS[b]
    L = math.dist((A["x"], A["y"], A["z"]), (B["x"], B["y"], B["z"]))
    Lh = math.hypot(B["x"] - A["x"], B["y"] - A["y"])
    decl = round(abs(A["z"] - B["z"]) / Lh * 100, 2) if Lh > 0.05 else None
    k = f"T|{a}|{b}"
    if k not in REG:
        REG[k] = novo_id(f"T-{DISC[sis]}-SS-{amb or 'X'}")
    TRECHOS.append(dict(id=REG[k], sistema=sis, disciplina=DISC[sis], dn=dn, dn_mm=DN_MM.get(dn, 40),
                        a=a, b=b, comprimento=round(L, 3), declividade=decl, vertical=Lh <= 0.05,
                        status=status, motivo=motivo, passagem=passagem, pontos=list(pontos), amb=amb))

MOT_DESC = ("Traçado não desenhado na prancha de pontos: descida vertical embutida na parede, do ponto até a "
            f"distribuição adotada a {H_DIST:.2f} m sobre o piso (acima do ponto mais alto cotado, aquecedores a 2,75 m). "
            "A rede de distribuição está no projeto hidrossanitário, não disponível.")
MOT_ESG = ("Traçado não desenhado na prancha de pontos: descida vertical do ponto até "
           f"{H_ENTERRADO:.2f} m abaixo do piso acabado, dentro do enchimento entre PA −2,87 e PO −3,44 (0,57 m). "
           "Ramal e coletor estão no projeto hidrossanitário, não disponível.")
for p in PONTOS:
    if p["tipo"] in ("CANAL", "ESGI"):
        continue
    A = AMB_D[p["amb"]]
    pn = no("N-" + p["id"], p["x"], p["y"], p["z"], "ponto", p["id"])
    p["no"] = pn
    if p["tipo"] in ("AF", "AQ", "GAS"):
        zt = A["pa"] + H_DIST
        tn = no("N-" + p["id"] + "-D", p["x"], p["y"], zt, "limite", "Distribuição (projeto IHSD não disponível)")
        trecho(p["sistema"], p["dn"], tn, pn, "INFERIDO", MOT_DESC,
               f"vertical, embutido na parede, de {H_DIST:.2f} m até {p['h']:.2f} m do piso", [p["id"]], p["amb"])
    elif p["tipo"] in ("ESG", "ESGR", "RS", "RSG", "RSIF"):
        zb = A["pa"] - H_ENTERRADO
        bn = no("N-" + p["id"] + "-E", p["x"], p["y"], zb, "limite", "Ramal / coletor (projeto IHSD não disponível)")
        dn = p["dn"] or ('2"' if p["tipo"] != "RSIF" else "")
        pas = (f"vertical, na parede a partir de {p['h']:.2f} m e enterrado até {H_ENTERRADO:.2f} m sob o piso"
               if p["h"] > 0.06 else f"vertical, enterrado até {H_ENTERRADO:.2f} m sob o piso")
        trecho("SAN-ESG", dn or '2"', pn, bn, "INFERIDO", MOT_ESG, pas, [p["id"]], p["amb"])

# Drenos das câmaras -> ralo sifonado da galeria (traço do desenho passa junto ao ralo)
def ralo_mais_proximo(p):
    cands = [r for r in PONTOS if r["tipo"] == "RSIF" and r["amb"] == "GAL"]
    return min(cands, key=lambda r: math.hypot(r["x"] - p["x"], r["y"] - p["y"]))
DECL_DRE = 0.025
for p in [p for p in PONTOS if p["tipo"] == "DRE"]:
    r = ralo_mais_proximo(p)
    zr = r["z"] + 0.10
    L = abs(r["x"] - p["x"]) + abs(r["y"] - p["y"])
    z1 = zr + L * DECL_DRE
    n1 = no("N-" + p["id"] + "-B", p["x"], p["y"], z1)
    n2 = no("N-" + p["id"] + "-C", p["x"], r["y"], zr + abs(r["x"] - p["x"]) * DECL_DRE)
    n3 = no("N-" + p["id"] + "-R", r["x"], r["y"], zr)
    mot = ("Destino do dreno não indicado: ligado ao ralo sifonado da galeria técnica mais próximo "
           f"({r['id']}), para onde converge o traço do desenho; queda vertical junto à parede da câmara e "
           f"trecho horizontal com caimento de {DECL_DRE*100:.0f}% (faixa adotada 2–5% para Ø<100).")
    trecho("DRE", '1"', p["no"], n1, "INFERIDO", mot, f"vertical, na parede da câmara, de 1,80 m até {z1 - AMB_D[p['amb']]['pa']:.2f} m do piso", [p["id"]], p["amb"])
    trecho("DRE", '1"', n1, n2, "INFERIDO", mot, "horizontal, atravessa a parede da câmara para a galeria", [], p["amb"])
    trecho("DRE", '1"', n2, n3, "INFERIDO", mot, "horizontal, na galeria técnica até o ralo", [], "GAL")
    trecho("DRE", '1"', n3, r["no"], "INFERIDO", mot, "descarga livre sobre o ralo sifonado", [r["id"]], "GAL")

# Segmentos (divisão no plano do piso -> enterrado)
def segmentos(t):
    A, B = NOS[t["a"]], NOS[t["b"]]
    amb = t["amb"] or "COZ"
    zp = AMB_D[amb]["pa"]
    pa = [A["x"], A["y"], A["z"]]; pb = [B["x"], B["y"], B["z"]]
    out = []
    if (A["z"] - zp) * (B["z"] - zp) < -1e-9:
        f = (zp - A["z"]) / (B["z"] - A["z"])
        pm = [A["x"] + f * (B["x"] - A["x"]), A["y"] + f * (B["y"] - A["y"]), zp]
        out.append(dict(a=pa, b=[round(v, 3) for v in pm], enterrado=A["z"] < zp))
        out.append(dict(a=[round(v, 3) for v in pm], b=pb, enterrado=B["z"] < zp))
    else:
        out.append(dict(a=pa, b=pb, enterrado=max(A["z"], B["z"]) <= zp + 1e-9 and min(A["z"], B["z"]) < zp - 1e-9))
    return out
for t in TRECHOS:
    t["segs"] = segmentos(t)

# ----------------------------------------------------------------------------
# 5. Paredes, vãos, equipamentos
# ----------------------------------------------------------------------------
WR = json.load(open(F("fonte", "walls_raw.json")))
def wall_dir(w):
    a = math.atan2(w[3] - w[1], w[2] - w[0]) % math.pi
    return a
merged = []
for w in sorted(WR, key=lambda w: -math.hypot(w[2] - w[0], w[3] - w[1])):
    a = wall_dir(w); ux, uy = math.cos(a), math.sin(a)
    done = False
    for m in merged:
        if abs(((m["a"] - a + math.pi / 2) % math.pi) - math.pi / 2) > 0.02:
            continue
        mx, my = m["p0"]
        nx, ny = -m["uy"], m["ux"]
        dperp = abs((w[0] - mx) * nx + (w[1] - my) * ny)
        if dperp > max(m["t"], w[4]) / 2 + 0.6:
            continue
        s0 = (w[0] - mx) * m["ux"] + (w[1] - my) * m["uy"]
        s1 = (w[2] - mx) * m["ux"] + (w[3] - my) * m["uy"]
        lo, hi = min(s0, s1), max(s0, s1)
        if hi < m["s0"] - 0.5 or lo > m["s1"] + 0.5:
            continue
        m["s0"], m["s1"] = min(m["s0"], lo), max(m["s1"], hi)
        m["t"] = max(m["t"], w[4])
        done = True
        break
    if not done:
        s1 = math.hypot(w[2] - w[0], w[3] - w[1])
        merged.append(dict(a=a, ux=ux, uy=uy, p0=(w[0], w[1]), s0=0.0, s1=s1, t=w[4]))
# Linhas ciano: (a) acabamento (revestimento) colado às faces da parede -> soma à espessura;
# (b) pares ciano sem parede correspondente -> painel de vidro fixo (legenda: 1,30 a 2,10 m).
CYL = [l for l in json.load(open(F("fonte", "linhas_ciano.json"))) if math.hypot(l[2]-l[0], l[3]-l[1]) > 8]
cpairs = []
for i in range(len(CYL)):
    for j in range(i + 1, len(CYL)):
        s_, t_ = CYL[i], CYL[j]
        a1 = math.atan2(s_[3]-s_[1], s_[2]-s_[0]) % math.pi; a2 = math.atan2(t_[3]-t_[1], t_[2]-t_[0]) % math.pi
        if abs(((a1 - a2 + math.pi/2) % math.pi) - math.pi/2) > 0.01: continue
        ux, uy = math.cos(a1), math.sin(a1); nx, ny = -uy, ux
        d = (t_[0]-s_[0])*nx + (t_[1]-s_[1])*ny; d2 = (t_[2]-s_[0])*nx + (t_[3]-s_[1])*ny
        if not (2.4 <= abs(d) <= 10.5) or abs(d - d2) > 0.3: continue
        p0, p1 = 0, (s_[2]-s_[0])*ux + (s_[3]-s_[1])*uy
        q0, q1 = (t_[0]-s_[0])*ux + (t_[1]-s_[1])*uy, (t_[2]-s_[0])*ux + (t_[3]-s_[1])*uy
        lo, hi = max(min(p0,p1), min(q0,q1)), min(max(p0,p1), max(q0,q1))
        if hi - lo < 8: continue
        mx, my = s_[0] + nx*d/2, s_[1] + ny*d/2
        cpairs.append(dict(a=a1, ux=ux, uy=uy, A=(mx+ux*lo, my+uy*lo), B=(mx+ux*hi, my+uy*hi), t=abs(d)))
camaras_pt = unary_union([Polygon(a[2]).buffer(6) for a in AMB if a[0] in ("CSP1","CSP2","CRES","ACAM","CHF","CCON")])
PAINEIS = []
for c in cpairs:
    hit = None
    for m in merged:
        if abs(((m["a"] - c["a"] + math.pi/2) % math.pi) - math.pi/2) > 0.02: continue
        mx, my = m["p0"]; nx, ny = -m["uy"], m["ux"]
        if abs((c["A"][0]-mx)*nx + (c["A"][1]-my)*ny) > 1.5: continue
        s0 = (c["A"][0]-mx)*m["ux"] + (c["A"][1]-my)*m["uy"]; s1 = (c["B"][0]-mx)*m["ux"] + (c["B"][1]-my)*m["uy"]
        ov = min(max(s0,s1), m["s1"]) - max(min(s0,s1), m["s0"])
        if ov > 0.5 * abs(s1 - s0):
            hit = m; break
    if hit:
        continue
    L = LineString([c["A"], c["B"]])
    if camaras_pt.contains(L) or L.length < 12: continue
    if any(LineString([q["A"], q["B"]]).buffer(1.5).contains(L) for q in PAINEIS): continue
    PAINEIS = [q for q in PAINEIS if not L.buffer(1.5).contains(LineString([q["A"], q["B"]]))]
    PAINEIS.append(c)
# acabamento por face: linha ciano isolada, paralela, colada à face (até 1,5 pt fora dela)
for m in merged:
    mx, my = m["p0"]; nx, ny = -m["uy"], m["ux"]; ext = {1: 0.0, -1: 0.0}
    for l in CYL:
        al = math.atan2(l[3]-l[1], l[2]-l[0]) % math.pi
        if abs(((al - m["a"] + math.pi/2) % math.pi) - math.pi/2) > 0.02: continue
        d1 = (l[0]-mx)*nx + (l[1]-my)*ny; d2 = (l[2]-mx)*nx + (l[3]-my)*ny
        if abs(d1 - d2) > 0.3: continue
        side = 1 if d1 > 0 else -1; e = abs(d1) - m["t"]/2
        if not (0.15 < e <= 1.5): continue
        s0 = (l[0]-mx)*m["ux"] + (l[1]-my)*m["uy"]; s1 = (l[2]-mx)*m["ux"] + (l[3]-my)*m["uy"]
        ov = min(max(s0, s1), m["s1"]) - max(min(s0, s1), m["s0"])
        if ov < 0.5 * (m["s1"] - m["s0"]): continue
        ext[side] = max(ext[side], e)
    if ext[1] or ext[-1]:
        sh = (ext[1] - ext[-1]) / 2
        m["p0"] = (mx + nx*sh, my + ny*sh); m["t"] = m["t"] + ext[1] + ext[-1]; m["acab"] = round((ext[1] + ext[-1]) * MPP, 3)

PAREDES = []
for i, m in enumerate(sorted(merged, key=lambda m: (round(m["a"], 2), m["p0"][1], m["p0"][0]))):
    ax = m["p0"][0] + m["ux"] * m["s0"]; ay = m["p0"][1] + m["uy"] * m["s0"]
    bx = m["p0"][0] + m["ux"] * m["s1"]; by = m["p0"][1] + m["uy"] * m["s1"]
    if math.hypot(bx - ax, by - ay) * MPP < 0.15:
        continue
    mid = ((ax + bx) / 2, (ay + by) / 2)
    nx, ny = -m["uy"], m["ux"]
    off = m["t"] / 2 + 3
    lados = [ambiente_de(mid[0] + nx * off, mid[1] + ny * off), ambiente_de(mid[0] - nx * off, mid[1] - ny * off)]
    pa = min(AMB_D[l[0]]["pa"] for l in lados)
    pa_alto = max(AMB_D[l[0]]["pa"] for l in lados)
    PAREDES.append(dict(id=f"PAR-{len(PAREDES)+1:03d}", a=list(M(ax, ay)), b=list(M(bx, by)),
                        esp=round(m["t"] * MPP, 3), z0=pa, z1=round(pa_alto + Z_TOPO_PAREDE_H, 3),
                        pt=[[round(ax, 2), round(ay, 2)], [round(bx, 2), round(by, 2)]],
                        fonte="par de linhas paralelas da camada de paredes (vetor), eixo = linha média"))

# Painéis de vidro fixo (pares ciano sem parede): peitoril 0–1,30 m, vidro 1,30–2,10 m, verga acima (legenda/nota)
VIDROS = []
for c in PAINEIS:
    mid = ((c["A"][0]+c["B"][0])/2, (c["A"][1]+c["B"][1])/2)
    nx, ny = -c["uy"], c["ux"]; off = c["t"]/2 + 3
    l1, l2 = ambiente_de(mid[0]+nx*off, mid[1]+ny*off), ambiente_de(mid[0]-nx*off, mid[1]-ny*off)
    pa = min(AMB_D[l1[0]]["pa"], AMB_D[l2[0]]["pa"]); pa_alto = max(AMB_D[l1[0]]["pa"], AMB_D[l2[0]]["pa"])
    w = dict(id=f"PAR-{len(PAREDES)+1:03d}", a=list(M(*c["A"])), b=list(M(*c["B"])), esp=round(c["t"]*MPP, 3),
             z0=pa, z1=round(pa_alto + Z_TOPO_PAREDE_H, 3), pt=[[round(v, 2) for v in c["A"]], [round(v, 2) for v in c["B"]]],
             fonte="painel de vidro fixo (par de linhas ciano); peitoril até 1,30 m e verga a partir de 2,10 m (legenda da prancha)", vidro=True)
    PAREDES.append(w)

# Painéis das câmaras frigoríficas (camada ciano): espessura medida no vetor = 4,5 pt (ex.: 437,74 → 442,24)
T_PAINEL = 4.5
for a in AMB:
    if a[0] not in ("CSP1", "CSP2", "CRES", "ACAM", "CHF", "CCON"):
        continue
    x0, y0 = a[2][0]; x1, y1 = a[2][2]
    o = T_PAINEL / 2
    for (ax, ay, bx, by) in ((x0 - T_PAINEL, y0 - o, x1 + T_PAINEL, y0 - o), (x0 - T_PAINEL, y1 + o, x1 + T_PAINEL, y1 + o),
                             (x0 - o, y0, x0 - o, y1), (x1 + o, y0, x1 + o, y1)):
        PAREDES.append(dict(id=f"PAR-{len(PAREDES)+1:03d}", a=list(M(ax, ay)), b=list(M(bx, by)), esp=round(T_PAINEL * MPP, 3),
                            z0=a[3], z1=round(a[3] + 2.50 + 0.15, 3), pt=[[ax, ay], [bx, by]],
                            fonte=f"painel isotérmico da {a[1]} (camada ciano); espessura medida 4,5 pt = {T_PAINEL*MPP:.2f} m; altura 2,50 m interna (memorial) + 0,15"))

# Vãos: intervalo entre trechos colineares de parede (mesmo eixo, mesma espessura)
CY = json.load(open(F("fonte", "linhas_ciano.json")))
VAOS = []
_PV = [w for w in PAREDES if not w.get("vidro")]
for i, p1 in enumerate(_PV):
    for p2 in _PV[i + 1:]:
        a1 = math.atan2(p1["b"][1] - p1["a"][1], p1["b"][0] - p1["a"][0]) % math.pi
        a2 = math.atan2(p2["b"][1] - p2["a"][1], p2["b"][0] - p2["a"][0]) % math.pi
        if abs(((a1 - a2 + math.pi / 2) % math.pi) - math.pi / 2) > 0.02 or abs(p1["esp"] - p2["esp"]) > 0.05:
            continue
        ux, uy = math.cos(a1), math.sin(a1); nx, ny = -uy, ux
        if abs((p2["a"][0] - p1["a"][0]) * nx + (p2["a"][1] - p1["a"][1]) * ny) > 0.03:
            continue
        s = lambda P: (P[0] - p1["a"][0]) * ux + (P[1] - p1["a"][1]) * uy
        r1 = sorted([s(p1["a"]), s(p1["b"])]); r2 = sorted([s(p2["a"]), s(p2["b"])])
        if r1[1] <= r2[0]: g0, g1 = r1[1], r2[0]
        elif r2[1] <= r1[0]: g0, g1 = r2[1], r1[0]
        else: continue
        gap = g1 - g0
        if not (0.6 <= gap <= 2.8):
            continue
        # já existe parede no meio?
        A = (p1["a"][0] + ux * g0, p1["a"][1] + uy * g0); B = (p1["a"][0] + ux * g1, p1["a"][1] + uy * g1)
        # janela: linhas ciano paralelas dentro do vão
        seg = LineString([A, B]).buffer(p1["esp"] / 2 + 0.02)
        nc = 0
        for l in CY:
            la, lb = M(l[0], l[1]), M(l[2], l[3])
            ls = LineString([la, lb])
            if ls.length < 0.3: continue
            al = math.atan2(lb[1] - la[1], lb[0] - la[0]) % math.pi
            if abs(((al - a1 + math.pi / 2) % math.pi) - math.pi / 2) > 0.05: continue
            if seg.contains(ls) or seg.intersection(ls).length > 0.7 * ls.length:
                nc += 1
        tipo = "janela" if nc >= 2 else "porta"
        VAOS.append(dict(id=f"VAO-{len(VAOS)+1:03d}", tipo=tipo, a=[round(v, 3) for v in A], b=[round(v, 3) for v in B],
                         largura=round(gap, 2), esp=p1["esp"], z0=min(p1["z0"], p2["z0"]), z1=max(p1["z1"], p2["z1"]),
                         peitoril=1.30 if tipo == "janela" else 0.0, verga=2.10,
                         status="EXTRAÍDO" if tipo == "janela" else "INFERIDO",
                         motivo=("Painel de vidro fixo de 1,30 m a 2,10 m (nota/legenda da prancha)." if tipo == "janela"
                                 else "Vão sem etiqueta legível e sem quadro de esquadrias: verga adotada a 2,10 m."),
                         etiqueta=""))
for w in [w for w in PAREDES if w.get("vidro")]:
    VAOS.append(dict(id="", tipo="janela", a=w["a"], b=w["b"], largura=round(math.dist(w["a"], w["b"]), 2), esp=w["esp"],
                     z0=w["z0"], z1=w["z1"], peitoril=1.30, verga=2.10, status="EXTRAÍDO", parede=w["id"],
                     motivo="Painel de vidro fixo de 1,30 m a 2,10 m (nota/legenda da prancha).", etiqueta=""))
# remove vãos duplicados / sobrepostos
_v = []
for v in sorted(VAOS, key=lambda v: v["largura"]):
    L = LineString([v["a"], v["b"]])
    if any(LineString([w["a"], w["b"]]).buffer(0.05).contains(L) or L.buffer(0.05).contains(LineString([w["a"], w["b"]])) for w in _v):
        continue
    _v.append(v)
for i, v in enumerate(_v): v["id"] = f"VAO-{i+1:03d}"
VAOS = _v

# Equipamentos: retângulos da camada de layout + câmaras (painéis)
ER = json.load(open(F("fonte", "equip_rects.json")))
ALTOS = {"CSP1", "CSP2", "CRES", "CHF", "CCON", "DESP", "DBEB", "CARQ", "LLMP"}
EQUIP = []
for r in ER:
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    amb, _ = ambiente_de(cx, cy)
    alto = amb in ALTOS
    EQUIP.append(dict(id=f"EQ-{len(EQUIP)+1:03d}", tipo="estante / carro" if alto else "bancada / equipamento",
                      poly=Mpoly(R(*r)), z0=AMB_D[amb]["pa"], z1=round(AMB_D[amb]["pa"] + (1.80 if alto else 0.85), 3), amb=amb,
                      status="INFERIDO",
                      motivo=("Contorno retangular da camada de layout; altura 1,80 m adotada (estantes/carros, valor usual de mercado)." if alto
                              else "Contorno retangular da camada de layout; altura 0,85 m do memorial (bancadas '85 cm alt.')."),
                      pt=r))
for a in []:  # câmaras agora modeladas como paredes de painel (acima)
    if a[0] in ("CSP1", "CSP2", "CRES", "CHF", "CCON", "ACAM"):
        EQUIP.append(dict(id=f"EQ-{len(EQUIP)+1:03d}", tipo="câmara frigorífica (painéis)", poly=Mpoly(a[2]),
                          z0=a[3], z1=round(a[3] + 2.50, 3), amb=a[0], status="EXTRAÍDO",
                          motivo="Medidas internas do memorial 34-CÂMARA-FRIG (altura 2,50 m) e contorno dos painéis na planta.", pt=None))

# Louças/equipamentos atendidos: retângulo mais próximo de cada ponto de esgoto/água de pia
LOUCAS = []
def nome_louca(item):
    return ITENS.get(item, "Bancada / equipamento atendido")
usados = set()
for p in PONTOS:
    if p["tipo"] not in ("ESG",) or not p["item"]:
        continue
    P = Point(p["pt"])
    cand = [e for e in EQUIP if e["pt"] and e["tipo"].startswith("bancada")]
    if not cand: continue
    e = min(cand, key=lambda e: box(*e["pt"]).distance(P))
    d = box(*e["pt"]).distance(P) * MPP
    if d > 0.6 or e["id"] in usados:
        continue
    usados.add(e["id"])
    LOUCAS.append(dict(id=f"LC-{len(LOUCAS)+1:03d}", equip=e["id"], nome=nome_louca(p["item"]), item=p["item"],
                       ponto=p["id"], poly=e["poly"], z0=e["z0"], z1=e["z1"], amb=e["amb"]))

# ----------------------------------------------------------------------------
# 6. Verificações
# ----------------------------------------------------------------------------
TOL = 0.01
ends = {}
for t in TRECHOS:
    for n in (t["a"], t["b"]):
        ends.setdefault(n, []).append(t["id"])
soltas = []
for n, ts in ends.items():
    N = NOS[n]
    if N["tipo"] == "ponto" or len(ts) > 1:
        continue
    soltas.append(dict(no=n, x=N["x"], y=N["y"], z=N["z"], trechos=ts,
                       aceita=N["tipo"] == "limite", motivo=N["ref"] if N["tipo"] == "limite" else "ponta solta"))
pontos_sem_trecho = [dict(id=p["id"], motivo=("descarga livre sobre canaleta (esgoto indireto)" if p["tipo"] == "ESGI" else "item pendente"))
                     for p in PONTOS if not any(p["id"] in t["pontos"] or NOS[t["a"]]["ref"] == p["id"] or NOS[t["b"]]["ref"] == p["id"] for t in TRECHOS)]
decl = [dict(id=t["id"], declividade=t["declividade"], ok=2.0 - 1e-6 <= t["declividade"] <= 5.0 + 1e-6)
        for t in TRECHOS if t["declividade"] is not None and t["sistema"] in ("SAN-ESG", "DRE")]

# Louças x paredes
wall_polys = []
for w in PAREDES:
    wall_polys.append(LineString([w["a"], w["b"]]).buffer(w["esp"] / 2, cap_style=2))
WALLS_U = unary_union(wall_polys)
for l in LOUCAS:
    P = Polygon(l["poly"])
    l["invasao_m2"] = round(P.intersection(WALLS_U).area, 4)
    l["folga_m"] = round(P.distance(WALLS_U), 3)
    l["ilha"] = l["folga_m"] > 0.30
    l["ok"] = l["invasao_m2"] < 1e-4 and (l["folga_m"] <= 0.03 or l["ilha"])

# ----------------------------------------------------------------------------
# 7. Cotas de locação (mesmo algoritmo do visualizador)
# ----------------------------------------------------------------------------
def locacao(p):
    P = (p["x"], p["y"])
    res = []
    for w in PAREDES:
        ax, ay = w["a"]; bx, by = w["b"]
        L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L
        s = (P[0] - ax) * ux + (P[1] - ay) * uy
        if s < -0.02 or s > L + 0.02: continue
        fx, fy = ax + ux * s, ay + uy * s
        d = math.hypot(P[0] - fx, P[1] - fy)
        face = d - w["esp"] / 2
        res.append(dict(w=w, d=d, face=face, foot=(fx, fy), ang=math.atan2(uy, ux) % math.pi))
    def visivel(r):
        seg = LineString([P, r["foot"]])
        for o in res:
            if o is r: continue
            if o["face"] < -0.005: continue
            if seg.crosses(LineString([o["w"]["a"], o["w"]["b"]])): return False
        return True
    apoio = [r for r in res if r["face"] <= 0.02]
    apoio = min(apoio, key=lambda r: r["d"]) if apoio else None
    cands = sorted([r for r in res if r is not apoio and r["face"] > 0.02 and visivel(r)], key=lambda r: r["face"])
    def naoparalela(r, ref):
        da = abs(r["ang"] - ref["ang"]); da = min(da, math.pi - da)
        return da > math.radians(20)
    A = B = None
    if apoio:
        tr = [r for r in cands if naoparalela(r, apoio)]
        A = tr[0] if tr else None
        if A:
            B = next((r for r in tr[1:] if not naoparalela(r, A) and False), None)
    else:
        A = cands[0] if cands else None
        if A:
            B = next((r for r in cands[1:] if naoparalela(r, A)), None)
    f = lambda r: None if r is None else dict(parede=r["w"]["id"], dist=round(r["face"], 3),
                                              face=[round(r["foot"][0] - (r["foot"][0] - P[0]) / r["d"] * (r["w"]["esp"] / 2), 3),
                                                    round(r["foot"][1] - (r["foot"][1] - P[1]) / r["d"] * (r["w"]["esp"] / 2), 3)])
    return dict(apoio=apoio["w"]["id"] if apoio else None, A=f(A), B=f(B))
LOC = {}
for p in PONTOS:
    LOC[p["id"]] = locacao(p)

# ----------------------------------------------------------------------------
# 8. Divergências
# ----------------------------------------------------------------------------
DIV = []
def div(tipo, desc, gravidade, disciplinas, ids=(), pos=None, pranchas=(PRANCHA,)):
    DIV.append(dict(id=f"DIV-{len(DIV)+1:03d}", tipo=tipo, descricao=desc, gravidade=gravidade,
                    disciplinas=list(disciplinas), ids=list(ids), pos=pos, pranchas=list(pranchas)))
cx, cy = M(700, 1050)
div("Projeto ausente", "O projeto hidrossanitário predial (arquivo 'hidráulica.zip', 21 MB) não pôde ser obtido: o conector do Drive limita downloads a 10 MB. "
    "Redes de distribuição de AF/AQ, ramais e coletores de esgoto, ventilação, pluvial, colunas, caixas e isométricos NÃO estão modelados. "
    "Todos os trechos terminam em 'limite' (distribuição sobre o forro / coletor sob o piso).", "Alta", ["HID", "SAN", "DRE"],
    pos=[cx, cy, -2.87], pranchas=["hidráulica.zip (não disponível)"])
div("Escala", f"O carimbo indica escala 1:50, mas o PDF está plotado fora de escala: medido 1:{MPP/0.000352778:.0f} "
    f"(5 medidas internas de câmaras do memorial conferem a ±0,3%). Medir na folha impressa com escalímetro de 1:50 dá erro de ~48%.",
    "Média", ["ARQ", "HID", "SAN"], pos=list(M(475, 1262)) + [-3.07])
aq = [p["id"] for p in PONTOS if p["tipo"] == "AQ" and "SAI AQUECEDOR" in p["texto"]]
div("Nomenclatura", "Pontos com símbolo de ÁGUA QUENTE rotulados como 'AF 3/4\" H=2,75m SAI AQUECEDOR' (saída de aquecedor de passagem). "
    "Modelados como água quente; confirmar com o projetista.", "Média", ["HID"], aq, pos=[PID[aq[0]]["x"], PID[aq[0]]["y"], PID[aq[0]]["z"]] if aq else None)
esgi = [p["id"] for p in PONTOS if p["tipo"] in ("ESGI", "CANAL")]
if esgi:
    q = PID[esgi[0]]
    div("Elemento não desenhado", "Esgoto indireto das lavadoras 'descarrega sobre canaleta AQ@93°C', mas nenhuma canaleta está desenhada "
        "(o símbolo 'canaleta c/ grelha 31,5x... e ralo seco' consta só na legenda, com a dimensão truncada).", "Alta", ["SAN"], esgi, pos=[q["x"], q["y"], q["z"]])
quentes = [p["id"] for p in PONTOS if re.search(r"@ ?(8[5-9]|9\d)", p["texto"])]
if quentes:
    q = PID[quentes[0]]
    div("Especificação", "Ralos e esgotos que recebem água a 85–93 °C (texto da prancha). O material do ramal não está especificado nesta prancha; "
        "confirmar no projeto hidrossanitário um material compatível com essa temperatura antes de executar.", "Alta", ["SAN"], quentes, pos=[q["x"], q["y"], q["z"]])
dre = [p["id"] for p in PONTOS if p["tipo"] == "DRE"]
q = PID[dre[0]]
div("Destino não indicado", "Drenos 1\" PVC das câmaras (H=1,80 m) sem caixa de destino indicada. Modelados até o ralo sifonado mais próximo da galeria técnica (INFERIDO).",
    "Média", ["DRE"], dre, pos=[q["x"], q["y"], q["z"]])
ror = [p["id"] for p in PONTOS if p["tipo"] == "ESGR"]
if ror:
    q = PID[ror[0]]
    div("Cota ausente", "Ponto de esgoto com altura 'H=RODAPÉ' sem valor numérico. Adotado 0,10 m.", "Baixa", ["SAN"], ror, pos=[q["x"], q["y"], q["z"]])
seco = [p["id"] for p in PONTOS if p["tipo"] in ("RS", "RSG", "RSIF") and p["amb"] in ("REF",)]
if seco:
    q = PID[seco[0]]
    div("Ralo em ambiente seco", "Ralos no Refeitório (ambiente seco). Os dos balcões de distribuição (itens 44/45) se justificam pelo banho-maria; "
        "confirmar o ralo seco junto à bancada de duas cubas.", "Baixa", ["SAN", "ARQ"], seco, pos=[q["x"], q["y"], q["z"]])
div("Níveis não cotados", "Pé-direito, forro e fundo de laje não estão cotados. Adotados: topo de parede = PA + 3,00 m e distribuição a 2,85 m do piso (INFERIDO). "
    "PA dos ambientes da cozinha sem marca própria: adotado −2,87.", "Média", ["ARQ", "HID"], pos=[cx, cy, -2.87 + 2.85])
div("Esquadrias", "Não há quadro de esquadrias e as etiquetas dos vãos (PA…, JA…) são texto vetorizado não legível por máquina. "
    "Portas modeladas pelo vão, com verga a 2,10 m (INFERIDO); painéis de vidro fixo de 1,30 a 2,10 m conforme a legenda.", "Baixa", ["ARQ"])
div("Data da prancha", "A prancha de pontos é de 09/01/2006 (projeto executivo, R001). Existem as-builts posteriores (exaustão, 2026) que podem ter alterado o layout; "
    "conferir no local antes de executar.", "Média", ["ARQ", "HID", "SAN"])
gas = [p["id"] for p in PONTOS if p["tipo"] == "GAS"]
div("Registro não posicionado", "Nota da prancha: 'deixar um registro geral na entrada da tubulação de gás p/ a cozinha'. A posição do registro não está desenhada.",
    "Média", ["GAS"], gas[:1], pos=[PID[gas[0]]["x"], PID[gas[0]]["y"], PID[gas[0]]["z"]] if gas else None)
for l in LOUCAS:
    if not l["ok"]:
        c = Polygon(l["poly"]).centroid
        div("Louça x parede", f"{l['nome']} ({l['equip']}): " + (f"invade a parede em {l['invasao_m2']*1e4:.0f} cm²" if l["invasao_m2"] >= 1e-4
            else f"afastada {l['folga_m']*100:.0f} cm da face da parede (tolerância 3 cm)") + " no desenho de layout.",
            "Baixa", ["ARQ", "SAN"], [l["id"], l["ponto"]], pos=[round(c.x, 3), round(c.y, 3), l["z1"]])

# ----------------------------------------------------------------------------
# 9. Premissas, pranchas, níveis, saída
# ----------------------------------------------------------------------------
PREMISSAS = [
    dict(id="P1", texto="Origem (0; 0; 0): vértice externo inferior esquerdo do painel da câmara semi-preparados 1 (folha: x=437,74 pt; y=1340,42 pt). "
                        "X para a direita da folha, Y para o topo da folha, Z = cota de projeto (referência 0,00 das marcas de nível da prancha). Unidade: metro."),
    dict(id="P2", texto=f"Escala medida 1:{MPP/0.000352778:.1f} ({MPP} m por ponto de PDF), média de 5 medidas internas de câmaras do memorial 34-CÂMARA-FRIG; desvio máximo 0,3%."),
    dict(id="P3", texto="Níveis: PA −2,87 / PO −3,44 na cozinha (marca M1) e −2,87 / −3,24 nas circulações (M2, M3, M4, M6); câmaras e ante-câmara PA −3,07 / PO −3,44 (M5, M7, nota 'prever rebaixo −20 cm')."),
    dict(id="P4", texto="Alturas h dos pontos lidas nos textos 'H=…' da prancha (sobre o piso acabado). Ralos no piso (h = 0)."),
    dict(id="P5", texto=f"Distribuição de água e gás adotada a {H_DIST:.2f} m sobre o piso (acima dos aquecedores, H=2,75 m). Valor INFERIDO: confirmar no projeto hidrossanitário."),
    dict(id="P6", texto=f"Esgoto: descida até {H_ENTERRADO:.2f} m abaixo do piso acabado, dentro do enchimento de 0,57 m (PA −2,87 a PO −3,44). INFERIDO."),
    dict(id="P7", texto="Pé-direito não cotado: topo das paredes adotado a 3,00 m sobre o PA (INFERIDO)."),
    dict(id="P8", texto="Cores: a prancha usa um único verde para todos os pontos hidráulicos; as cores por sistema seguem a convenção usual (AF azul, AQ vermelho, esgoto marrom, dreno ciano, gás amarelo)."),
    dict(id="P9", texto="Faixa de declividade adotada para verificação: 2–5% para Ø<100 e 1–5% para Ø≥100 (a prancha de pontos não traz nota de declividade)."),
    dict(id="P10", texto="Ventilação e pluvial não aparecem na prancha de pontos e não foram modelados (dependem do projeto hidrossanitário)."),
]
PRANCHAS = [
    dict(codigo=PRANCHA, curta=PR_CURTA, disciplina="ARQ / HID / SAN / GÁS (pontos)", pavimento="Subsolo — Cozinha de banquetes",
         escala="1:50 (carimbo) — medida 1:%.0f" % (MPP / 0.000352778), rev="R001", data="09/01/2006",
         arquivo="TBM-COZ-PE-1pontos el.hid.-Model.pdf", vetorial="sim (44.617 objetos)", texto="não (texto convertido em traços — leitura visual)",
         uso="Fonte única de pontos, níveis (marcas PA/PO), paredes e layout"),
    dict(codigo="TOM001-COZ (equipamentos)", curta="COZ · Equipamentos · Subsolo", disciplina="ARQ (layout de equipamentos)", pavimento="Subsolo",
         escala="1:50 (carimbo)", rev="—", data="2006", arquivo="TBM-COZ-PE-1equipamento-Model.pdf", vetorial="sim (28.871 objetos)",
         texto="não", uso="Conferência do layout (mesma base da prancha de pontos)"),
    dict(codigo="Memorial COZINHA-SUBSOLO (50 fichas)", curta="Memorial de equipamentos", disciplina="Especificação", pavimento="Subsolo",
         escala="—", rev="—", data="2001–2006", arquivo="COZINHA-SUBSOLO.ZIP", vetorial="—", texto="sim (.DOC)",
         uso="Medidas de câmaras (calibração da escala) e alturas de bancadas"),
    dict(codigo="hidráulica.zip", curta="Projeto hidrossanitário", disciplina="HID / SAN / DRE", pavimento="todos",
         escala="—", rev="—", data="—", arquivo="PLANTAS/hidráulica.zip (21 MB)", vetorial="?", texto="?",
         uso="NÃO DISPONÍVEL — acima do limite de 10 MB do conector"),
]
NIVEIS = []
for m in MARCAS:
    X, Y = M(*m["pt"])
    NIVEIS.append(dict(id=m["id"], ambiente=m["onde"], tipo="PA / PO", pa=m["pa"], po=m["po"], x=X, y=Y,
                       fonte=f"marca de nível na prancha {PRANCHA}", status="EXTRAÍDO"))
for a in AMB:
    NIVEIS.append(dict(id=f"N-{a[0]}", ambiente=a[1], tipo="piso do ambiente", pa=a[3], po=a[4], x=None, y=None, fonte=a[6], status=a[5]))
NIVEIS.append(dict(id="N-DIST", ambiente="Distribuição de água/gás", tipo="tubulação", pa=None, po=None, x=None, y=None,
                   fonte=f"PA + {H_DIST:.2f} (premissa P5)", status="INFERIDO", z=-2.87 + H_DIST))
NIVEIS.append(dict(id="N-TOPO", ambiente="Topo das paredes / laje", tipo="laje", pa=None, po=None, x=None, y=None,
                   fonte="PA + 3,00 (premissa P7) — fundo de laje não cotado", status="PENDENTE", z=-2.87 + 3.0))

AMBIENTES = [dict(id=a[0], nome=a[1], poly=Mpoly(a[2]), pa=a[3], po=a[4], status=a[5], fonte=a[6]) for a in AMB]

ext = {}
for t in TRECHOS:
    ext[t["sistema"]] = round(ext.get(t["sistema"], 0) + t["comprimento"], 2)

modelo = dict(
    meta=dict(projeto="Vivo Rio — Cozinha de banquetes (subsolo)", obra="Casa de espetáculos — instalações da cozinha de banquetes",
              endereco="Av. Infante Dom Henrique, 85 — Parque do Flamengo", rev="R001 (pontos) · modelo v1", escala="1:50 (carimbo) / 1:96 medida",
              data="09/01/2006 (prancha) · modelo 08/10/2026", folha=PRANCHA, unidade="m"),
    origem=dict(texto=PREMISSAS[0]["texto"], pt=[OX, OY], mpp=MPP, calibracao=[dict(desc=d, memorial=m, pt=round(p, 2), mpp=round(m / p, 6)) for d, m, p in CAL]),
    pranchas=PRANCHAS, premissas=PREMISSAS, niveis=NIVEIS, ambientes=AMBIENTES, paredes=PAREDES, vaos=VAOS,
    equipamentos=EQUIP, loucas=LOUCAS, nos=list(NOS.values()), pontos=PONTOS, trechos=TRECHOS, divergencias=DIV,
    locacao=LOC,
    verificacoes=dict(
        pontas_soltas=soltas, pontas_soltas_nao_aceitas=[s for s in soltas if not s["aceita"]],
        pontos_sem_trecho=pontos_sem_trecho, declividades=decl, declividades_fora=[d for d in decl if not d["ok"]],
        loucas=[dict(id=l["id"], nome=l["nome"], invasao_m2=l["invasao_m2"], folga_m=l["folga_m"], ilha=l["ilha"], ok=l["ok"]) for l in LOUCAS],
        locacao_sem_referencia=[k for k, v in LOC.items() if not v["A"]],
        extensao=ext,
    ),
)
os.makedirs(F("saida"), exist_ok=True)
json.dump(modelo, open(F("saida", "modelo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(REG, open(REG_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print(f"MPP={MPP}  pontos={len(PONTOS)} trechos={len(TRECHOS)} nos={len(NOS)} paredes={len(PAREDES)} vaos={len(VAOS)} "
      f"equip={len(EQUIP)} loucas={len(LOUCAS)} div={len(DIV)}")
print("pontas soltas (não aceitas):", len(modelo["verificacoes"]["pontas_soltas_nao_aceitas"]), " limites:", len(soltas))
print("declividades fora:", len(modelo["verificacoes"]["declividades_fora"]), "/", len(decl))
print("louças:", [(l["id"], l["invasao_m2"], l["folga_m"]) for l in LOUCAS])
print("locação sem referência:", modelo["verificacoes"]["locacao_sem_referencia"])
