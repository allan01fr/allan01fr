#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o caso OpenFOAM (ESI v1912) da coifa A (ilha dos fogões) a partir de saida/modelo.json.
Solver padrão: buoyantSimpleFoam (compressível, estacionário, k-epsilon); SOLVER_CFD=boussinesq troca por buoyantBoussinesqSimpleFoam.

Geometria vem do modelo (coifa A, captores CP-A1/A2, caixas de equipamento, piso e laje); o que NÃO vem do desenho está em PARAMS
e marcado como hipótese (cargas térmicas, ar de reposição, abertura de equilíbrio, espessura das chapas).
Uso: python3 gerar_caso.py <pasta_destino> [grossa|media|producao] [n_processos]
"""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(AQUI)
M = json.load(open(os.path.join(ROOT, "saida", "modelo.json"), encoding="utf-8"))

# ---------------------------------------------------------------- hipóteses do caso (não vêm do desenho)
PARAMS = dict(
    dominio=dict(x=(7.0, 15.4), y=(7.22, 12.42)),        # recorte da cozinha em torno da coifa A (parede sul real em y = 7,22)
    rampa=150,                                           # iterações para levar as vazões de 0 ao valor de projeto (partida robusta)
    chapa=0.06,                                          # espessura mínima das chapas da coifa e dos captores (m); vira >= 2 células: hipótese de modelagem
    solver=os.environ.get("SOLVER_CFD", "compressivel"),                                # buoyantBoussinesqSimpleFoam; o compressível (buoyantSimpleFoam) do pacote Ubuntu v1912 diverge em malhas com objetos
    T_amb=293.15, dT_quente=120.0,                       # K; topo dos fogões 120 K acima do ambiente (hipótese; Boussinesq limita ΔT)
    beta=3.41e-3, nu=1.5e-5, Pr=0.71, Prt=0.85,
    razao_reposicao=1.00,                                # ar de reposição pelo forro / exaustão; < 1 exige a abertura de equilíbrio abaixo (hipótese)
    difusores=[(8.29, 8.09), (12.09, 8.09), (12.53, 10.94)],   # DIF-04, DIF-05, DIF-03 do as-built (0,60 x 0,60 m)
    difusor_lado=0.6,
    abertura=None,                                       # ou dict(x=15.4, y=(11.0, 12.0), h=2.1): porta de equilíbrio na parede leste (hipótese; instável na partida do solver estacionário)
)
if PARAMS["solver"] == "compressivel": PARAMS["dT_quente"] = 230.0      # o compressível aceita o topo a 250 °C
NIVEIS = {   # nível de refinamento = h0 / 2^n ; h0 = 0,2 m (malha de fundo 42 x 26 x 21)
    "grossa":   dict(plume=1, perto=1, sup=2, bancada=1, camadas=False, iter=1500),
    "media":    dict(plume=2, perto=2, sup=3, bancada=2, camadas=False, iter=2000),
    "producao": dict(plume=2, perto=3, sup=4, bancada=2, camadas=False, iter=2500),
}

# ---------------------------------------------------------------- geometria a partir do modelo
def geometria():
    d = PARAMS["dominio"]; coz = next(a for a in M["ambientes"] if a["id"] == "COZ")
    zp = coz["pa"]; zt = max(w["z1"] for w in M["paredes"])
    g = dict(x0=d["x"][0], x1=d["x"][1], y0=d["y"][0], y1=d["y"][1], z0=zp, z1=zt)
    c = next(c for c in M["mec"]["coifas"] if c["id"] == "COIFA-A")
    g["hood"] = dict(x0=c["x"] - c["L"] / 2, x1=c["x"] + c["L"] / 2, y0=c["y"] - c["P"] / 2, y1=c["y"] + c["P"] / 2, z0=c["z0"], z1=c["z1"])
    capt = [k for k in M["mec"]["captores"] if k["coifa"] == "A" and k["sistema"] == "EXA"]
    dz = {(round(k["a"][0], 2), round(k["a"][1], 2)): k for k in M["dutos"] if k["tipo"] == "descida" and k["sistema"] == "EXA"}
    g["capt"] = []
    for k in capt:
        du = dz[(round(k["x"], 2), round(k["y"], 2))]
        g["capt"].append(dict(id=k["id"], x=k["x"], y=k["y"], W=du["W"], H=du["H"]))
    hx0, hx1, hy0, hy1 = g["hood"]["x0"], g["hood"]["x1"], g["hood"]["y0"], g["hood"]["y1"]
    g["ilha"], g["bancadas"] = [], []
    for e in M["equipamentos"]:
        xs = [p[0] for p in e["poly"]]; ys = [p[1] for p in e["poly"]]
        b = (max(min(xs), g["x0"]), min(max(xs), g["x1"]), max(min(ys), g["y0"]), min(max(ys), g["y1"]))
        if b[1] - b[0] < 0.05 or b[3] - b[2] < 0.05: continue
        item = dict(id=e["id"], x0=b[0], x1=b[1], y0=b[2], y1=b[3], z0=e["z0"], z1=e["z1"])
        (g["ilha"] if not (max(xs) < hx0 or min(xs) > hx1 or max(ys) < hy0 or min(ys) > hy1) else g["bancadas"]).append(item)
    g["limpeza"] = limpar(g)
    return g

def limpar(g, folga=0.15):
    """Limpeza de geometria para CFD: fecha frestas < 15 cm entre caixas e entre caixa e parede/domínio, funde as caixas da ilha."""
    log = []
    def encosta(b):
        for k, lim, nome in (("x0", g["x0"], "oeste"), ("y0", g["y0"], "sul")):
            if 0 < b[k] - lim < folga: log.append(f"{b['id']}: fresta de {b[k]-lim:.2f} m até a parede {nome} fechada"); b[k] = lim
        for k, lim, nome in (("x1", g["x1"], "leste"), ("y1", g["y1"], "norte")):
            if 0 < lim - b[k] < folga: log.append(f"{b['id']}: fresta de {lim-b[k]:.2f} m até a parede {nome} fechada"); b[k] = lim
    def funde(lista):
        mudou = True
        while mudou:
            mudou = False
            for i, a in enumerate(lista):
                for b in lista[i + 1:]:
                    gx = max(a["x0"], b["x0"]) - min(a["x1"], b["x1"]); gy = max(a["y0"], b["y0"]) - min(a["y1"], b["y1"])
                    if gx < folga and gy < folga and abs(a["z1"] - b["z1"]) < 1e-6:
                        log.append(f"{a['id']}+{b['id']}: fresta de {max(gx, gy, 0):.2f} m fechada (caixas fundidas)")
                        a.update(id=a["id"] + "+" + b["id"], x0=min(a["x0"], b["x0"]), x1=max(a["x1"], b["x1"]), y0=min(a["y0"], b["y0"]), y1=max(a["y1"], b["y1"]))
                        lista.remove(b); mudou = True; break
                if mudou: break
    for b in g["ilha"] + g["bancadas"]: encosta(b)
    funde(g["ilha"]); funde(g["bancadas"])
    return log

H0 = 0.2   # tamanho da célula de fundo em x e y (m); em z = (z1 - z0) / nz

def passos(g):
    nz = round((g["z1"] - g["z0"]) / H0)
    return dict(x=H0, y=H0, z=(g["z1"] - g["z0"]) / nz)

def alinhar(g, niv):
    """Arredonda as faces dos objetos à grade do nível em que cada superfície é refinada (<= meia célula): a malha sai hexaédrica e ortogonal,
    sem os cortes oblíquos do snappyHexMesh (que desestabilizavam o solver). Chapas ganham no mínimo 2 células de espessura."""
    L = NIVEIS[niv]; P = passos(g); log = []
    def q(v, eixo, nivel):
        o = g[eixo + "0"]; h = P[eixo] / 2 ** nivel; r = o + round((v - o) / h) * h
        lim0, lim1 = g[eixo + "0"], g[eixo + "1"]
        return min(max(r, lim0), lim1)
    def caixa_(b, nivel):
        for eixo in "xyz":
            for k in "01": b[eixo + k] = q(b[eixo + k], eixo, nivel)
    for b in g["ilha"]: caixa_(b, L["sup"])
    for b in g["bancadas"]: caixa_(b, L["bancada"])
    h = g["hood"]
    for eixo in "xyz":
        for k in "01": h[eixo + k] = q(h[eixo + k], eixo, L["sup"])
    for c in g["capt"]:
        for eixo, dim in (("x", "W"), ("y", "H")):
            a = q(c[eixo] - c[dim] / 2, eixo, L["sup"]); b = q(c[eixo] + c[dim] / 2, eixo, L["sup"])
            c[eixo], c[dim] = (a + b) / 2, b - a
    g["passo_sup"] = {e: P[e] / 2 ** L["sup"] for e in "xyz"}
    return g

# ---------------------------------------------------------------- STL
def caixa(x0, x1, y0, y1, z0, z1, regiao_topo=None, regiao=None):
    """Caixa fechada -> {região: [triângulos]}; normais para fora."""
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    f = {"zmax": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], "zmin": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
         "xmax": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], "xmin": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
         "ymax": [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], "ymin": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]}
    out = {}
    for nome, q in f.items():
        tri = [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
        fix = []
        for a, b, c in tri:
            n = (( (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])), ((b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])),
                 ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])))
            m = ((a[0] + b[0] + c[0]) / 3 - cx, (a[1] + b[1] + c[1]) / 3 - cy, (a[2] + b[2] + c[2]) / 3 - cz)
            fix.append((a, c, b) if sum(u * v for u, v in zip(n, m)) < 0 else (a, b, c))
        r = regiao_topo if (nome == "zmax" and regiao_topo) else regiao
        out.setdefault(r, []).extend(fix)
    return out
def escrever_stl(path, corpos):
    reg = {}
    for c in corpos:
        for r, t in c.items(): reg.setdefault(r, []).extend(t)
    with open(path, "w") as f:
        for r, tris in reg.items():
            f.write(f"solid {r}\n")
            for a, b, c in tris:
                n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]), (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
                L = math.sqrt(sum(v * v for v in n)) or 1.0
                f.write(f" facet normal {n[0]/L:.6g} {n[1]/L:.6g} {n[2]/L:.6g}\n  outer loop\n")
                for p in (a, b, c): f.write(f"   vertex {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
                f.write("  endloop\n endfacet\n")
            f.write(f"endsolid {r}\n")

def corpos_coifa(g):
    h = g["hood"]; zt = g["z1"]; R = "hoodWall"
    ps = g["passo_sup"]; tx = max(2, math.ceil(PARAMS["chapa"] / ps["x"])) * ps["x"]; ty = max(2, math.ceil(PARAMS["chapa"] / ps["y"])) * ps["y"]; tz = max(2, math.ceil(PARAMS["chapa"] / ps["z"])) * ps["z"]
    x0, x1, y0, y1, z0, z1 = h["x0"], h["x1"], h["y0"], h["y1"], h["z0"], h["z1"]
    c = [caixa(x0, x1, y0, y0 + ty, z0, z1 - tz, regiao=R), caixa(x0, x1, y1 - ty, y1, z0, z1 - tz, regiao=R),
         caixa(x0, x0 + tx, y0 + ty, y1 - ty, z0, z1 - tz, regiao=R), caixa(x1 - tx, x1, y0 + ty, y1 - ty, z0, z1 - tz, regiao=R)]
    furos = [(k["x"] - k["W"] / 2, k["x"] + k["W"] / 2, k["y"] - k["H"] / 2, k["y"] + k["H"] / 2) for k in g["capt"]]
    xs = sorted({x0, x1, *[v for f in furos for v in f[:2]]}); ys = sorted({y0, y1, *[v for f in furos for v in f[2:]]})
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            if any(f[0] < cx < f[1] and f[2] < cy < f[3] for f in furos): continue
            c.append(caixa(xa, xb, ya, yb, z1 - tz, z1, regiao=R))
    for fx0, fx1, fy0, fy1 in furos:          # chaminé de cada captor, do topo da coifa até a laje
        c += [caixa(fx0 - tx, fx0, fy0 - ty, fy1 + ty, z1, zt, regiao=R), caixa(fx1, fx1 + tx, fy0 - ty, fy1 + ty, z1, zt, regiao=R),
              caixa(fx0, fx1, fy0 - ty, fy0, z1, zt, regiao=R), caixa(fx0, fx1, fy1, fy1 + ty, z1, zt, regiao=R)]
    return c, furos

# ---------------------------------------------------------------- dicionários
def decompor(npro):
    """decomposeParDict geométrico (o pacote Ubuntu v1912 não traz Scotch): n = (nx ny nz) com nz = 1."""
    f = {1: (1, 1), 2: (2, 1), 3: (3, 1), 4: (2, 2), 6: (3, 2), 8: (4, 2), 12: (4, 3)}.get(npro, (npro, 1))
    return cab("dictionary", "decomposeParDict", "system") + f"numberOfSubdomains {npro};\nmethod          simple;\nsimpleCoeffs {{ n ({f[0]} {f[1]} 1); delta 0.001; }}\n"

def cab(classe, objeto, local=None):
    loc = f'    location    "{local}";\n' if local else ""
    return (f"FoamFile\n{{\n    version     2.0;\n    format      ascii;\n    class       {classe};\n{loc}    object      {objeto};\n}}\n\n")

def blockmesh(g, h0=0.2):
    nx, ny, nz = round((g["x1"] - g["x0"]) / h0), round((g["y1"] - g["y0"]) / h0), round((g["z1"] - g["z0"]) / h0)
    v = [(g["x0"], g["y0"], g["z0"]), (g["x1"], g["y0"], g["z0"]), (g["x1"], g["y1"], g["z0"]), (g["x0"], g["y1"], g["z0"]),
         (g["x0"], g["y0"], g["z1"]), (g["x1"], g["y0"], g["z1"]), (g["x1"], g["y1"], g["z1"]), (g["x0"], g["y1"], g["z1"])]
    vs = "\n".join(f"    ({a:.4f} {b:.4f} {c:.4f})" for a, b, c in v)
    return cab("dictionary", "blockMeshDict") + f"""convertToMeters 1;

vertices
(
{vs}
);

blocks ( hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1) );

edges ();

boundary
(
    floor   {{ type wall; faces ((0 3 2 1)); }}
    ceiling {{ type wall; faces ((4 5 6 7)); }}
    west    {{ type wall; faces ((0 4 7 3)); }}
    east    {{ type wall; faces ((1 2 6 5)); }}
    south   {{ type wall; faces ((0 1 5 4)); }}
    north   {{ type wall; faces ((3 7 6 2)); }}
);
""", (nx, ny, nz)

def snappy(g, niv, loc):
    L = NIVEIS[niv]; h = g["hood"]
    box = lambda a, b: f"min ({a[0]:.3f} {a[1]:.3f} {a[2]:.3f}); max ({b[0]:.3f} {b[1]:.3f} {b[2]:.3f});"
    plume = box((h["x0"] - 0.7, h["y0"] - 0.7, g["z0"] - 0.1), (h["x1"] + 0.7, h["y1"] + 0.7, g["z1"] + 0.1))
    perto = box((h["x0"] - 0.35, h["y0"] - 0.35, h["z0"] - 1.2), (h["x1"] + 0.35, h["y1"] + 0.35, g["z1"] + 0.1))
    return cab("dictionary", "snappyHexMeshDict") + f"""castellatedMesh true;
snap            false;
addLayers       false;

geometry
{{
    hood.stl    {{ type triSurfaceMesh; name hood;   regions {{ hoodWall {{ name hoodWall; }} }} }}
    island.stl  {{ type triSurfaceMesh; name island; regions {{ hotTop {{ name hotTop; }} islandWall {{ name islandWall; }} }} }}
    bench.stl   {{ type triSurfaceMesh; name bench;  regions {{ benchWall {{ name benchWall; }} }} }}
    plume       {{ type searchableBox; {plume} }}
    perto       {{ type searchableBox; {perto} }}
}}

castellatedMeshControls
{{
    maxLocalCells 4000000;
    maxGlobalCells 8000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 2;
    features ();
    refinementSurfaces
    {{
        hood   {{ level ({L['sup']} {L['sup']}); patchInfo {{ type wall; inGroups (hoodWalls); }} }}
        island
        {{
            level ({L['sup']} {L['sup']});
            regions
            {{
                hotTop     {{ level ({L['sup']} {L['sup']}); patchInfo {{ type wall; inGroups (hotWalls); }} }}
                islandWall {{ level ({L['sup']} {L['sup']}); patchInfo {{ type wall; inGroups (islandWalls); }} }}
            }}
        }}
        bench  {{ level ({L['bancada']} {L['bancada']}); patchInfo {{ type wall; inGroups (benchWalls); }} }}
    }}
    resolveFeatureAngle 30;
    refinementRegions
    {{
        plume {{ mode inside; levels ((1E15 {L['plume']})); }}
        perto {{ mode inside; levels ((1E15 {L['perto']})); }}
    }}
    locationInMesh ({loc[0]} {loc[1]} {loc[2]});
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
    nFeatureSnapIter 10;
    implicitFeatureSnap true;
    explicitFeatureSnap false;
    multiRegionFeatureSnap false;
}}

addLayersControls
{{
    relativeSizes true; layers {{}}; expansionRatio 1.0; finalLayerThickness 0.3; minThickness 0.1; nGrow 0;
    featureAngle 130; nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50;
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality 1e-15;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.05;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
    relaxed {{ maxNonOrtho 55; }}
}}

mergeTolerance 1e-6;
"""

def retangulos(g):
    """Faces do forro (z = laje) e da parede leste que viram patches: exaustão, reposição, abertura."""
    zt = g["z1"]; out = {}
    out["topoSet"] = []
    for i, (fx0, fx1, fy0, fy1) in enumerate(g["_furos"], 1):
        out["topoSet"].append((f"exaustao{i}", (fx0 + 0.02, fy0 + 0.02, zt - 0.02), (fx1 - 0.02, fy1 - 0.02, zt + 0.02)))
    s = PARAMS["difusor_lado"] / 2
    for i, (x, y) in enumerate(PARAMS["difusores"], 1):
        out["topoSet"].append((f"reposicao{i}", (x - s + 0.02, y - s + 0.02, zt - 0.02), (x + s - 0.02, y + s - 0.02, zt + 0.02)))
    a = PARAMS["abertura"]
    if a: out["topoSet"].append(("abertura", (a["x"] - 0.02, a["y"][0] + 0.02, g["z0"] - 0.02), (a["x"] + 0.02, a["y"][1] - 0.02, g["z0"] + a["h"] - 0.02)))
    return out

def topo_e_patches(g):
    r = retangulos(g)
    def acao(n, a, b):
        base = "ceiling" if not n.startswith("abertura") else "east"
        return (f"    {{ name {n}Set; type faceSet; action new; source patchToFace; sourceInfo {{ name {base}; }} }}\n"
                f"    {{ name {n}Set; type faceSet; action subset; source boxToFace; sourceInfo {{ box ({a[0]:.4f} {a[1]:.4f} {a[2]:.4f}) ({b[0]:.4f} {b[1]:.4f} {b[2]:.4f}); }} }}")
    acoes = "\n".join(acao(n, a, b) for n, a, b in r["topoSet"])
    topo = cab("dictionary", "topoSetDict") + f"actions\n(\n{acoes}\n);\n"
    pat = "\n".join(f"""    {{ name {n}; patchInfo {{ type patch; }} constructFrom set; set {n}Set; }}""" for n, a, b in r["topoSet"])
    cp = cab("dictionary", "createPatchDict") + f"pointSync false;\npatches\n(\n{pat}\n);\n"
    return topo, cp, [n for n, _, _ in r["topoSet"]]

def campos(g, nomes, Qex, Qrep):
    """Arquivos 0/ para buoyantBoussinesqSimpleFoam (p_rgh cinemático e manométrico). Patches carvados: exaustao*, reposicao*, abertura."""
    ex = [n for n in nomes if n.startswith("exaustao")]; rp = [n for n in nomes if n.startswith("reposicao")]
    T = PARAMS["T_amb"]; Ta = f"uniform {T}"; Th = T + PARAMS["dT_quente"]
    def bloco(wall, outros):
        s = f"    \"(floor|ceiling|west|east|south|north)\"\n    {{\n{wall}\n    }}\n"
        for grupo in ("hoodWalls", "islandWalls", "benchWalls"): s += f"    {grupo}\n    {{\n{wall}\n    }}\n"
        s += f"    hotWalls\n    {{\n{outros['hot']}\n    }}\n"
        for n in ex: s += f"    {n}\n    {{\n{outros['ex']}\n    }}\n"
        for n in rp: s += f"    {n}\n    {{\n{outros['rp']}\n    }}\n"
        if "abertura" in nomes: s += f"    abertura\n    {{\n{outros['ab']}\n    }}\n"
        return s
    def arq(classe, nome, dim, interno, corpo):
        return cab(classe, nome, "0") + f"dimensions      {dim};\n\ninternalField   {interno};\n\nboundaryField\n{{\n{corpo}}}\n"
    I = "        "
    def e(*linhas): return "\n".join(I + l for l in linhas)
    R = PARAMS["rampa"]; qe = -Qex / len(ex); qr = Qrep / len(rp)
    c = {}
    ffp = e("type fixedFluxPressure;", "value uniform 0;")
    c["p_rgh"] = arq("volScalarField", "p_rgh", "[0 2 -2 0 0 0 0]", "uniform 0", bloco(ffp, dict(hot=ffp, ex=ffp, rp=ffp, ab=e("type fixedValue;", "value uniform 0;"))))
    c["U"] = arq("volVectorField", "U", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", bloco(e("type noSlip;"), dict(hot=e("type noSlip;"),
        ex=e("type flowRateInletVelocity;", f"volumetricFlowRate table ((0 0) ({R} {qe:.12g}));", "value uniform (0 0 0);"),
        rp=e("type flowRateInletVelocity;", f"volumetricFlowRate table ((0 0) ({R} {qr:.12g}));", "value uniform (0 0 0);"),
        ab=e("type pressureInletOutletVelocity;", "value uniform (0 0 0);"))))
    c["T"] = arq("volScalarField", "T", "[0 0 0 1 0 0 0]", Ta, bloco(e("type zeroGradient;"), dict(hot=e("type fixedValue;", f"value uniform {Th};"),
        ex=e("type inletOutlet;", f"inletValue {Ta};", f"value {Ta};"), rp=e("type fixedValue;", f"value {Ta};"), ab=e("type inletOutlet;", f"inletValue {Ta};", f"value {Ta};"))))
    kw = e("type kqRWallFunction;", "value uniform 0.01;")
    c["k"] = arq("volScalarField", "k", "[0 2 -2 0 0 0 0]", "uniform 0.01", bloco(kw, dict(hot=kw, ex=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"),
        rp=e("type fixedValue;", "value uniform 0.03;"), ab=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"))))
    ew = e("type epsilonWallFunction;", "value uniform 0.01;")
    c["epsilon"] = arq("volScalarField", "epsilon", "[0 2 -3 0 0 0 0]", "uniform 0.01", bloco(ew, dict(hot=ew, ex=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"),
        rp=e("type fixedValue;", "value uniform 0.02;"), ab=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"))))
    nw = e("type nutkWallFunction;", "value uniform 0;"); cal = e("type calculated;", "value uniform 0;")
    c["nut"] = arq("volScalarField", "nut", "[0 2 -1 0 0 0 0]", "uniform 0", bloco(nw, dict(hot=nw, ex=cal, rp=cal, ab=cal)))
    c["alphat"] = arq("volScalarField", "alphat", "[0 2 -1 0 0 0 0]", "uniform 0", bloco(cal, dict(hot=cal, ex=cal, rp=cal, ab=cal)))
    return c

def campos_comp(g, nomes, Qex, Qrep):
    """0/ para buoyantSimpleFoam (compressível): p_rgh absoluto (p_rgh = p - rho*gh), p, T em K, alphat dinâmico."""
    ex = [n for n in nomes if n.startswith("exaustao")]; rp = [n for n in nomes if n.startswith("reposicao")]
    T = PARAMS["T_amb"]; Ta = f"uniform {T}"; Th = T + PARAMS["dT_quente"]
    def bloco(wall, outros):
        s = f"    \"(floor|ceiling|west|east|south|north)\"\n    {{\n{wall}\n    }}\n"
        for grupo in ("hoodWalls", "islandWalls", "benchWalls"): s += f"    {grupo}\n    {{\n{wall}\n    }}\n"
        s += f"    hotWalls\n    {{\n{outros['hot']}\n    }}\n"
        for n in ex: s += f"    {n}\n    {{\n{outros['ex']}\n    }}\n"
        for n in rp: s += f"    {n}\n    {{\n{outros['rp']}\n    }}\n"
        return s
    def arq(classe, nome, dim, interno, corpo):
        return cab(classe, nome, "0") + f"dimensions      {dim};\n\ninternalField   {interno};\n\nboundaryField\n{{\n{corpo}}}\n"
    I = "        "
    def e(*linhas): return "\n".join(I + l for l in linhas)
    R = PARAMS["rampa"]; rho0 = 1e5 / (287.1 * PARAMS["T_amb"]); qe = -rho0 * Qex / len(ex); qr = rho0 * Qrep / len(rp); c = {}   # vazão MÁSSICA: com o ar quente na exaustão, vazões volumétricas iguais não fecham a massa
    ffp = e("type fixedFluxPressure;", "value uniform 1e5;"); cal = e("type calculated;", "value uniform 0;"); cp_ = e("type calculated;", "value uniform 1e5;")
    c["p_rgh"] = arq("volScalarField", "p_rgh", "[1 -1 -2 0 0 0 0]", "uniform 1e5", bloco(ffp, dict(hot=ffp, ex=ffp, rp=ffp)))
    c["p"] = arq("volScalarField", "p", "[1 -1 -2 0 0 0 0]", "uniform 1e5", bloco(cp_, dict(hot=cp_, ex=cp_, rp=cp_)))
    c["U"] = arq("volVectorField", "U", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", bloco(e("type noSlip;"), dict(hot=e("type noSlip;"),
        ex=e("type flowRateInletVelocity;", f"massFlowRate table ((0 0) ({R} {qe:.12g}));", "rho rho;", "value uniform (0 0 0);"),
        rp=e("type flowRateInletVelocity;", f"massFlowRate table ((0 0) ({R} {qr:.12g}));", "rho rho;", "value uniform (0 0 0);"))))
    c["T"] = arq("volScalarField", "T", "[0 0 0 1 0 0 0]", Ta, bloco(e("type zeroGradient;"), dict(hot=e("type fixedValue;", f"value uniform {Th};"),
        ex=e("type inletOutlet;", f"inletValue {Ta};", f"value {Ta};"), rp=e("type fixedValue;", f"value {Ta};"))))
    kw = e("type kqRWallFunction;", "value uniform 0.01;")
    c["k"] = arq("volScalarField", "k", "[0 2 -2 0 0 0 0]", "uniform 0.01", bloco(kw, dict(hot=kw, ex=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"), rp=e("type fixedValue;", "value uniform 0.03;"))))
    ew = e("type epsilonWallFunction;", "value uniform 0.01;")
    c["epsilon"] = arq("volScalarField", "epsilon", "[0 2 -3 0 0 0 0]", "uniform 0.01", bloco(ew, dict(hot=ew, ex=e("type inletOutlet;", "inletValue uniform 0.01;", "value uniform 0.01;"), rp=e("type fixedValue;", "value uniform 0.02;"))))
    nw = e("type nutkWallFunction;", "value uniform 0;")
    c["nut"] = arq("volScalarField", "nut", "[0 2 -1 0 0 0 0]", "uniform 0", bloco(nw, dict(hot=nw, ex=cal, rp=cal)))
    aw = e("type compressible::alphatWallFunction;", "Prt 0.85;", "value uniform 0;")
    c["alphat"] = arq("volScalarField", "alphat", "[1 -1 -1 0 0 0 0]", "uniform 0", bloco(aw, dict(hot=aw, ex=cal, rp=cal)))
    return c

def constante_comp():
    return {"thermophysicalProperties": cab("dictionary", "thermophysicalProperties", "constant") + """thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie      { molWeight 28.96; }
    thermodynamics { Cp 1004.4; Hf 0; }
    transport   { mu 1.831e-05; Pr 0.705; }
}
""", "radiationProperties": cab("dictionary", "radiationProperties", "constant") + "radiationModel  none;\nsolverFreq      1;\n"}

def sistema_comp(niv, npro):
    n_it = NIVEIS[niv]["iter"]
    ctrl = cab("dictionary", "controlDict", "system") + f"""application     buoyantSimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {n_it};
deltaT          1;
writeControl    timeStep;
writeInterval   {n_it};
purgeWrite      1;
writeFormat     binary;
writePrecision  14;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable false;
"""
    fvs = cab("dictionary", "fvSchemes", "system") + """ddtSchemes      { default steadyState; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default             none;
    div(phi,U)          bounded Gauss upwind;
    div(phi,h)          bounded Gauss upwind;
    div(phi,K)          bounded Gauss upwind;
    div(phi,k)          bounded Gauss upwind;
    div(phi,epsilon)    bounded Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes   { default corrected; }
wallDist        { method meshWave; }
"""
    fvsol = cab("dictionary", "fvSolution", "system") + """solvers
{
    rho { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0.1; }
    p_rgh
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
        cacheAgglomeration true;
        nCellsInCoarsestLevel 100;
        agglomerator    faceAreaPair;
        mergeLevels     1;
    }
    "(U|h|k|epsilon)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0.1; }
}

SIMPLE
{
    momentumPredictor   yes;
    nNonOrthogonalCorrectors 0;
    pRefCell            0;
    pRefValue           1e5;
    residualControl { p_rgh 1e-4; U 1e-5; h 1e-5; "(k|epsilon)" 1e-5; }
}

relaxationFactors
{
    fields    { rho 1.0; p_rgh 0.7; }
    equations { U 0.3; h 0.3; "(k|epsilon)" 0.3; }
}
"""
    dec = decompor(npro)
    return {"controlDict": ctrl, "fvSchemes": fvs, "fvSolution": fvsol, "decomposeParDict": dec}

CONST = {
"g": cab("uniformDimensionedVectorField", "g", "constant") + "dimensions      [0 1 -2 0 0 0 0];\nvalue           (0 0 -9.81);\n",
"turbulenceProperties": cab("dictionary", "turbulenceProperties", "constant") + "simulationType  RAS;\nRAS\n{\n    RASModel        kEpsilon;\n    turbulence      on;\n    printCoeffs     on;\n}\n",
}
def transport():
    return (cab("dictionary", "transportProperties", "constant") + f"transportModel  Newtonian;\nnu              {PARAMS['nu']};\nbeta            {PARAMS['beta']};\n"
            f"TRef            {PARAMS['T_amb']};\nPr              {PARAMS['Pr']};\nPrt             {PARAMS['Prt']};\n")

def sistema(niv, npro, modo="simple", t_fim=60.0, dt=0.05, t_escreve=1.0):
    """system/: 'simple' = estacionário (buoyantBoussinesqSimpleFoam); 'pimple' = transiente (buoyantBoussinesqPimpleFoam)."""
    st = modo == "simple"
    n_it = NIVEIS[niv]["iter"]
    if st:
        tempo = f"""application     buoyantBoussinesqSimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {n_it};
deltaT          1;
writeControl    timeStep;
writeInterval   {n_it};
purgeWrite      1;"""
    else:
        tempo = f"""application     buoyantBoussinesqPimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {t_fim};
deltaT          {dt};
adjustTimeStep  yes;
maxCo           0.9;
maxDeltaT       0.25;
writeControl    adjustableRunTime;
writeInterval   {t_escreve};
purgeWrite      0;"""
    ctrl = cab("dictionary", "controlDict", "system") + tempo + """
writeFormat     binary;
writePrecision  14;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable false;
"""
    ddt = "steadyState" if st else "Euler"; b = "bounded " if st else ""
    fvs = cab("dictionary", "fvSchemes", "system") + f"""ddtSchemes      {{ default {ddt}; }}
gradSchemes     {{ default Gauss linear; }}
divSchemes
{{
    default             none;
    div(phi,U)          {b}Gauss {"upwind" if st else "linearUpwind grad(U)"};
    div(phi,T)          {b}Gauss {"upwind" if st else "limitedLinear 1"};
    div(phi,k)          {b}Gauss upwind;
    div(phi,epsilon)    {b}Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}}
laplacianSchemes {{ default Gauss linear corrected; }}
interpolationSchemes {{ default linear; }}
snGradSchemes   {{ default corrected; }}
wallDist        {{ method meshWave; }}
"""
    if st:
        alg = """SIMPLE
{
    momentumPredictor   no;
    nNonOrthogonalCorrectors 0;
    pRefCell            0;
    pRefValue           0;
    residualControl { p_rgh 1e-4; U 1e-5; T 1e-5; "(k|epsilon)" 1e-5; }
}

relaxationFactors
{
    fields    { p_rgh 0.7; }
    equations { U 0.3; T 0.5; "(k|epsilon)" 0.5; }
}
"""
        suf = ""
    else:
        alg = """PIMPLE
{
    momentumPredictor   no;
    nOuterCorrectors    1;
    nCorrectors         2;
    nNonOrthogonalCorrectors 0;
    pRefCell            0;
    pRefValue           0;
}
"""
        suf = ".*"
    fvsol = cab("dictionary", "fvSolution", "system") + f"""solvers
{{
    "p_rgh{suf}"
    {{
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          {0.01 if st else 0.001};
        cacheAgglomeration true;
        nCellsInCoarsestLevel 100;
        agglomerator    faceAreaPair;
        mergeLevels     1;
    }}
    "(U|T|k|epsilon){suf}"
    {{
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.1;
    }}
}}

{alg}"""
    dec = decompor(npro)
    return {"controlDict": ctrl, "fvSchemes": fvs, "fvSolution": fvsol, "decomposeParDict": dec}

def gerar(dest, niv="grossa", npro=4):
    g = alinhar(geometria(), niv); os.makedirs(dest, exist_ok=True)
    for d in ("0", "constant/triSurface", "system"): os.makedirs(os.path.join(dest, d), exist_ok=True)
    cor, furos = corpos_coifa(g); g["_furos"] = furos
    h = g["hood"]
    escrever_stl(os.path.join(dest, "constant/triSurface/hood.stl"), cor)
    top = [caixa(i["x0"], i["x1"], i["y0"], i["y1"], i["z0"], i["z1"], regiao_topo="hotTop", regiao="islandWall") for i in g["ilha"]]
    escrever_stl(os.path.join(dest, "constant/triSurface/island.stl"), top)
    escrever_stl(os.path.join(dest, "constant/triSurface/bench.stl"), [caixa(i["x0"], i["x1"], i["y0"], i["y1"], i["z0"], i["z1"], regiao="benchWall") for i in g["bancadas"]])
    bm, n = blockmesh(g)
    Qex = next(float(__import__("re").search(r"(\d+(?:,\d+)?)\s*m³/min", c["texto"]).group(1).replace(",", ".")) for c in M["mec"]["coifas"] if c["id"] == "COIFA-A") / 60.0
    Qrep = PARAMS["razao_reposicao"] * Qex
    topo, cp, nomes = topo_e_patches(g)
    open(os.path.join(dest, "system/blockMeshDict"), "w").write(bm)
    loc = (g["x0"] + 0.9, g["y0"] + 0.9, 0.0)
    open(os.path.join(dest, "system/snappyHexMeshDict"), "w").write(snappy(g, niv, loc))
    open(os.path.join(dest, "system/topoSetDict"), "w").write(topo)
    open(os.path.join(dest, "system/createPatchDict"), "w").write(cp)
    comp = PARAMS["solver"] == "compressivel"
    for k, v in (sistema_comp(niv, npro) if comp else sistema(niv, npro)).items(): open(os.path.join(dest, "system", k), "w").write(v)
    for k, v in CONST.items(): open(os.path.join(dest, "constant", k), "w").write(v)
    if comp:
        for k, v in constante_comp().items(): open(os.path.join(dest, "constant", k), "w").write(v)
    else: open(os.path.join(dest, "constant", "transportProperties"), "w").write(transport())
    for k, v in (campos_comp if comp else campos)(g, nomes, Qex, Qrep).items(): open(os.path.join(dest, "0", k), "w").write(v)
    json.dump(dict(nivel=niv, solver=PARAMS["solver"], limpeza=g["limpeza"], dominio=g_resumo(g), Qexaustao_m3s=Qex, Qreposicao_m3s=Qrep, base=n, params={k: v for k, v in PARAMS.items()}, patches=nomes,
                   ilha=g["ilha"], bancadas=g["bancadas"], captores=g["capt"], coifa=h),
              open(os.path.join(dest, "caso.json"), "w"), indent=1, default=str)
    return g, n

def g_resumo(g): return {k: g[k] for k in ("x0", "x1", "y0", "y1", "z0", "z1")}

if __name__ == "__main__":
    dest = sys.argv[1]; niv = sys.argv[2] if len(sys.argv) > 2 else "grossa"; npro = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    g, n = gerar(dest, niv, npro)
    print(f"caso '{niv}' em {dest}: malha de fundo {n[0]}x{n[1]}x{n[2]}; ilha {len(g['ilha'])} caixas, bancadas {len(g['bancadas'])}, captores {len(g['capt'])}")
