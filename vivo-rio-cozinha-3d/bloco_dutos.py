# -*- coding: utf-8 -*-
# Bloco de dutos (exaustão e ventilação mecânica) — executado dentro de build_data.py (usa M, AMB_D, ambiente_de, REG, novo_id).
# Fonte: fonte/dutos_subsolo.py (digitalização do as-built "Planta baixa subsolo cozinha dutos exaustão", Fase 2, 1:35).
import json as _json, math as _m

_ns = {}
exec(open(F("fonte", "dutos_subsolo.py"), encoding="utf-8").read(), _ns)
FLUXO = "TDM001-ARC-PJ-E-R-012 (fluxogramas)"
ASB = "As-built exaustão subsolo · Fase 2 (Anexo D)"
ASB_LONGO = "PLANTA BAIXA SUBSOLO COZINHA DUTOS EXAUSTÃO — AS BUILT PARA ADEQUAÇÕES (Kaptek, 27/08/2026, 1:35)"

# Registro da prancha do as-built sobre o modelo: pontos de controle (faces internas das salas de lavagem),
# escala conferida em 4 medidas (lavagem de louças 5,544 × 6,977 m; lavagem de panelas 3,135 m; vão total 25,514 m).
REG_D = dict(mpp=0.012357, x_ref=(111.3, 316.6), y_ref=(392.5, 921.4))
def MD(x, y):
    xp = REG_D["x_ref"][1] + (x - REG_D["x_ref"][0]) * REG_D["mpp"] / MPP
    yp = REG_D["y_ref"][1] + (y - REG_D["y_ref"][0]) * REG_D["mpp"] / MPP
    return M(xp, yp), (xp, yp)

Z_LAJE_TEC = 8.36     # laje técnica (fluxograma / relatório PA-COZINHA-003)
Z_COBERT = 20.93      # cobertura (fluxograma / relatório)
TOPO = {"AEX": 1.20, "INS": 1.20, "EXA": 0.60, "EXG": 0.60}   # topo do duto por camada (INFERIDO)
H_COIFA_BASE = 2.00   # borda inferior da coifa sobre o piso (memorial 2006: 1,90 a 2,10 m)
H_COIFA = 0.60        # altura da coifa (rótulos "x60")
SIS_D = {"EXA": "Exaustão da cozinha", "EXG": "Exaustão geral (E-)", "INS": "Insuflamento", "AEX": "Ar exterior / compensação"}
PA0 = AMB_D["COZ"]["pa"]
Z_COIFA_TOPO = round(PA0 + H_COIFA_BASE + H_COIFA, 3)

DUTOS_M, _ends = [], []
def _id(prefix, key):
    if key not in REG:
        REG[key] = novo_id(prefix)
    return REG[key]
def _passagem(sis, a, b, tipo):
    if tipo == "horizontal":
        return f"horizontal, sob a laje do térreo, topo a {TOPO[sis] - PA0:.2f} m do piso (cota {TOPO[sis]:+.2f})"
    if tipo == "descida":
        return f"vertical, da rede até a coifa ({a[2] - PA0:.2f} → {b[2] - PA0:.2f} m do piso)"
    if tipo == "prumada":
        return f"vertical, do duto até a laje do térreo e pelo shaft até a laje técnica ({a[2]:+.2f} → {b[2]:+.2f})"
    if tipo == "descarga":
        return f"vertical, do ventilador na laje técnica até a cobertura ({a[2]:+.2f} → {b[2]:+.2f})"
    return tipo
def duto(did, sis, rot, W, H, a, b, status, nota, tipo, exaustor="", fonte=ASB, memoria=""):
    L = _m.dist(a, b)
    DUTOS_M.append(dict(id=did, sistema=sis, sistema_nome=SIS_D[sis], rotulo=rot, W=W, H=H, a=[round(v, 3) for v in a], b=[round(v, 3) for v in b],
                        comprimento=round(L, 3), tipo=tipo, status=status, nota=nota, exaustor=exaustor, prancha=fonte,
                        passagem=_passagem(sis, a, b, tipo), memoria=memoria))

# --- trechos horizontais digitalizados
for d in _ns["DUTOS"]:
    zc = round(TOPO[d["sis"]] - d["H"] / 2, 3)
    pts = [MD(*q) for q in d["pts"]]
    for k, ((pa, ptA), (pb, ptB)) in enumerate(zip(pts, pts[1:])):
        did = _id(f"D-{d['sis']}-SS", f"DUTO|{d['id']}|{k}")
        mem = (f"Eixo = linha média das linhas paralelas do vetor; folha do as-built ({d['pts'][k][0]:.1f}; {d['pts'][k][1]:.1f}) → "
               f"({d['pts'][k+1][0]:.1f}; {d['pts'][k+1][1]:.1f}) pt; registro sobre o modelo por pontos de controle (1:{REG_D['mpp']/0.000352778:.1f}). "
               f"Z = topo da camada {TOPO[d['sis']]:+.2f} − H/2 (INFERIDO: dutos interrompidos no desenho passam por baixo dos que cruzam).")
        duto(did, d["sis"], d["rot"], d["W"], d["H"], (pa[0], pa[1], zc), (pb[0], pb[1], zc), d["status"], d["nota"], "horizontal",
             d.get("exaustor", ""), memoria=mem)

# --- prumadas (caixas com X), shaft e ventiladores
MEC = dict(coifas=[], ventiladores=[], difusores=[], captores=[])
FANS = {"VM-COZ01": ("Exaustão 1 — coifa A (fogões)", "15.200 m³/h de placa (relatório)", "E-60x60"),
        "VM-COZ02": ("Exaustão 2 — coifa C (parede)", "15.200 m³/h de placa (relatório)", "E-60x60"),
        "VM-COZ03": ("Exaustão 3 — lavadoras e fornos", "GTS 560-9, 9.600 m³/h (relatório)", "E-60x60"),
        "AC-COZ01": ("Insuflamento da cozinha", "9.000 m³/h (fluxograma)", None),
        "AC-COZ02": ("Insuflamento da cozinha", "9.000 m³/h (fluxograma)", None)}
for r in _ns["PRUMADAS"]:
    (X, Y), _ = MD(r["x"], r["y"])
    zc = round(TOPO[r["sis"]] - r["H"] / 2, 3)
    did = _id(f"D-{r['sis']}-SS", f"PRUMADA|{r['id']}|0")
    duto(did, r["sis"], r["rot"], r["W"], r["H"], (X, Y, zc), (X, Y, Z_TERREO), r["status"], r["nota"], "prumada", r["exaustor"],
         memoria=f"XY: centro da caixa com X no as-built ({r['x']:.1f}; {r['y']:.1f}) pt. Z: do eixo do duto até o térreo +{Z_TERREO:.2f}.")
    if r["exaustor"] in ("não identificado",):
        continue
    did2 = _id(f"D-{r['sis']}-SH", f"SHAFT|{r['id']}")
    duto(did2, r["sis"], r["rot"], r["W"], r["H"], (X, Y, Z_TERREO), (X, Y, Z_LAJE_TEC), "INFERIDO",
         "Traçado do shaft entre o térreo e a laje técnica não desenhado em planta; adotado vertical sobre a caixa da prumada (fluxograma: prumadas paralelas no mesmo shaft).",
         "prumada", r["exaustor"], fonte=FLUXO)
    fans = ["VM-COZ05", "VM-COZ06"] if r["exaustor"] == "VM-COZ05/06" else [r["exaustor"]]
    for k, fn in enumerate(fans):
        fx = X + (k - (len(fans) - 1) / 2) * 1.5
        MEC["ventiladores"].append(dict(id=fn, nome=FANS.get(fn, ("Ar exterior / compensação", "6.500 m³/h cada (fluxograma)", None))[0],
                                        dados=FANS.get(fn, (None, "6.500 m³/h cada (fluxograma)", None))[1], sistema=r["sis"],
                                        x=round(fx, 3), y=round(Y, 3), z0=Z_LAJE_TEC, z1=Z_LAJE_TEC + 1.2, L=1.2, P=1.2, status="INFERIDO",
                                        motivo="Ventilador na laje técnica (+8,36, fluxograma). Posição em planta adotada sobre a prumada: a planta parcial da laje técnica (Anexo E) não tem referência comum com o subsolo."))
        if r["sis"] == "EXA":
            did3 = _id("D-EXA-DS", f"DESCARGA|{fn}")
            duto(did3, "EXA", "E-60x60", 0.60, 0.60, (fx, Y, Z_LAJE_TEC + 1.2), (fx, Y, Z_COBERT), "INFERIDO",
                 "Descarga do ventilador até a cobertura (+20,93) em E-60x60 (fluxograma); traçado em planta não disponível, adotado vertical.",
                 "descarga", fn, fonte=FLUXO)

# --- coifas (pontos da prancha de 2006: dimensões do texto, posição sobre os equipamentos)
COIFAS = [("A", "Coifa A — ilha sobre os fogões", (767.75, 1055.4), 4.15, 1.40, "COIFA 415x140x60cm, VAZÃO 220,78 m³/min", "VM-COZ01"),
          ("C", "Coifa C — parede (fornos, chapas, fritadeiras)", (810.0, 936.9), 6.65, 1.05, "COIFA 665x105x60cm, VAZÃO 169,81 m³/min", "VM-COZ02"),
          ("B", "Coifa B — forno elétrico", (669.0, 940.0), 1.25, 1.35, "COIFA 125x135x60cm, VAZÃO 41,04 m³/min", "VM-COZ03"),
          ("D", "Coifa D — caldeirões", (1027.0, 941.0), 2.70, 1.45, "COIFA 270x145x60cm, VAZÃO 95,21 m³/min", "VM-COZ03"),
          ("E1", "Coifa E — lavadora de louças 1", (408.1, 1034.3), 0.90, 0.90, "COIFA 90x90x60, 20 m³/min CADA", "VM-COZ03"),
          ("E2", "Coifa E — lavadora de louças 2", (467.7, 1034.3), 0.90, 0.90, "COIFA 90x90x60, 20 m³/min CADA", "VM-COZ03")]
for cid, nome, (px, py), Lx, Ly, txt, ex in COIFAS:
    X, Y = M(px, py)
    MEC["coifas"].append(dict(id=f"COIFA-{cid}", nome=nome, x=X, y=Y, L=Lx, P=Ly, z0=round(PA0 + H_COIFA_BASE, 3), z1=Z_COIFA_TOPO,
                              texto=txt, exaustor=ex, status="INFERIDO",
                              motivo=("Dimensões do texto da prancha de pontos (2006); posição adotada no centro dos equipamentos atendidos; "
                                      f"borda inferior a {H_COIFA_BASE:.2f} m do piso (memorial 2006: 1,90 a 2,10 m). O as-built (Anexo C) registra a coifa C com 8,30 m.")))
# --- captores: descida do duto até o topo da coifa
for c in _ns["CAPTORES"]:
    (X, Y), _ = MD(c["x"], c["y"])
    sis = c["sis"]
    hpar = next((d["H"] for d in _ns["DUTOS"] if any(abs(q[0] - c["x"]) < 40 and abs(q[1] - c["y"]) < 40 for q in d["pts"]) and d["sis"] == sis), 0.3)
    zt = round(TOPO[sis] - hpar, 3)
    st = "PENDENTE" if c["id"] == "CP-E1" else "EXTRAÍDO"
    did = _id(f"D-{sis}-SS", f"CAPTOR|{c['id']}")
    duto(did, sis, f"{'EC' if sis=='EXA' else 'AE'}-{round(c['W']*100)}x{round(c['H']*100)}", c["W"], c["H"], (X, Y, zt), (X, Y, Z_COIFA_TOPO), st,
         c["nota"] + (" Trecho removido — refazer (legenda do as-built)." if st == "PENDENTE" else ""), "descida", "",
         memoria=f"XY: centro da caixa do captor ({c['x']:.1f}; {c['y']:.1f}) pt. Z: da face inferior do duto ({zt:+.2f}) ao topo da coifa ({Z_COIFA_TOPO:+.2f}), INFERIDO.")
    MEC["captores"].append(dict(id=c["id"], coifa=c["coifa"], x=X, y=Y, sistema=sis))
# --- difusores / grelhas
for k, (dx, dy, s_) in enumerate(_ns["DIFUSORES"]):
    (X, Y), _ = MD(dx, dy)
    MEC["difusores"].append(dict(id=f"DIF-{k+1:02d}", x=X, y=Y, L=s_, z=round(TOPO["INS"] - 0.50, 3), status="INFERIDO",
                                 motivo="Posição em planta do as-built (quadrado com X); altura adotada na face inferior da camada de insuflamento (forro não cotado)."))

# --- verificação de continuidade dos dutos (em planta + Z): ponta toca outro duto, prumada, captor ou é terminal declarado
def _dist_seg(p, a, b):
    ax, ay, az = a; bx, by, bz = b; px, py, pz = p
    vx, vy, vz = bx - ax, by - ay, bz - az; L2 = vx * vx + vy * vy + vz * vz
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy + (pz - az) * vz) / L2))
    return _m.dist(p, (ax + vx * t, ay + vy * t, az + vz * t))
TERMINAIS = {("I-03", "fim"): "tampa do duto (desenho)", ("I-05", "fim"): "tampa do duto (desenho)", ("I-09", "fim"): "tampa do duto (desenho)",
             ("I-10", "ini"): "tampa do duto (desenho)", ("I-12", "fim"): "tampa do duto (desenho)", ("I-13", "ini"): "segue em prumada não identificada",
             ("I-13", "fim"): "segue pelo corredor (fora do recorte)", ("AE-02", "fim"): "segue fora do recorte (AE-40x20 / AE-30x…)",
             ("EG-02", "ini"): "grelha do Gelo", ("E1-01", "ini"): "tampa do coletor sobre a coifa A"}
pontas = []
for d in _ns["DUTOS"]:
    for lado, q in (("ini", d["pts"][0]), ("fim", d["pts"][-1])):
        (X, Y), _ = MD(*q); z = TOPO[d["sis"]] - d["H"] / 2; P = (X, Y, z)
        ok = None
        for o in DUTOS_M:
            if o["id"] in [REG.get(f"DUTO|{d['id']}|{k}") for k in range(len(d["pts"]) - 1)]:
                continue
            tol = max(o["W"], o["H"], d["W"]) / 2 + 0.25
            if _dist_seg(P, o["a"], o["b"]) <= tol + abs(o["a"][2] - z) * 0:
                ok = o["id"]; break
        if not ok and (d["id"], lado) in TERMINAIS:
            ok = "terminal: " + TERMINAIS[(d["id"], lado)]
        pontas.append(dict(duto=d["id"], lado=lado, ok=bool(ok), liga=ok or "", x=round(X, 3), y=round(Y, 3)))
VER_DUTOS = dict(pontas=pontas, soltas=[p for p in pontas if not p["ok"]],
                 resumo=f"{sum(1 for p in pontas if p['ok'])}/{len(pontas)} pontas ligadas ou declaradas")

# --- divergências dos dutos
def _pos(did):
    d = next(x for x in DUTOS_M if x["id"] == did); return [round((d["a"][0] + d["b"][0]) / 2, 3), round((d["a"][1] + d["b"][1]) / 2, 3), d["a"][2]]
_rem = [d["id"] for d in DUTOS_M if d["status"] == "PENDENTE"]
DIV_DUTOS = [
    dict(tipo="Trecho removido", desc="O ramal de exaustão da lavadora de louças (EC-30x40 e captor) está marcado no as-built como 'removido / refazer'. "
         "Modelado como PENDENTE: não há duto instalado entre a coifa da lavadora e o coletor do corredor norte.", gravidade="Alta",
         disciplinas=["MEC"], ids=_rem, pos=_pos(_rem[0]) if _rem else None, pranchas=[ASB_LONGO]),
    dict(tipo="Shaft não desenhado", desc="As prumadas sobem da cozinha (subsolo) até a laje técnica (+8,36) e daí à cobertura (+20,93), mas o traçado do shaft entre lajes "
         "não está em nenhuma planta disponível; a planta parcial da laje técnica (Anexo E) não tem referência comum para registro. Prumadas, ventiladores e descargas "
         "foram modelados na vertical das caixas do subsolo (INFERIDO).", gravidade="Média", disciplinas=["MEC"],
         ids=[d["id"] for d in DUTOS_M if d["prancha"] == FLUXO][:6], pos=None, pranchas=[FLUXO, "Anexo E — laje técnica (1:25)"]),
    dict(tipo="Exaustor não identificado", desc="O duto E-85x50 (exaustão geral, ligado às grelhas do Gelo e ao corredor) sobe em prumada própria, mas o exaustor "
         "correspondente não aparece no fluxograma da cozinha.", gravidade="Média", disciplinas=["MEC"],
         ids=[d["id"] for d in DUTOS_M if d["sistema"] == "EXG"], pos=_pos(next(d["id"] for d in DUTOS_M if d["sistema"] == "EXG")), pranchas=[ASB_LONGO, FLUXO]),
    dict(tipo="Seção", desc="Coletor da coifa C: largura medida 0,50 m no as-built, rótulo 'EC-60x50' junto à descida de 0,60 m. Adotado 0,50 (largura) × 0,60 (altura); confirmar em campo.",
         gravidade="Baixa", disciplinas=["MEC"], ids=[REG["DUTO|E2-01|0"]], pos=_pos(REG["DUTO|E2-01|0"]), pranchas=[ASB_LONGO]),
    dict(tipo="Velocidade no duto", desc="Relatório PA-COZINHA-003 (seção 5.4): a prumada de sucção da Exaustão 2 (E-60x50) fica acima do limite de 12,5 m/s com a vazão "
         "de projeto da adequação (13,28 m/s pelo Método I; 17,15 m/s pelo Método II). A prumada modelada é a existente.", gravidade="Alta", disciplinas=["MEC"],
         ids=[REG["PRUMADA|PR-E2|0"]], pos=_pos(REG["PRUMADA|PR-E2|0"]), pranchas=["PA-COZINHA-003/2026 rev. 02"]),
    dict(tipo="Coifa (posição e tamanho)", desc="Coifas posicionadas com as dimensões da prancha de 2006 sobre os equipamentos. O as-built da Fase 2 (Anexo C) cota a coifa C com 8,30 m "
         "(2006: 6,65 m) e o relatório prevê ajustes de profundidade e de altura (coifa da lavadora a 0,50 m do equipamento). Conferir antes de fabricar.",
         gravidade="Média", disciplinas=["MEC", "ARQ"], ids=[c["id"] for c in MEC["coifas"]], pos=[MEC["coifas"][1]["x"], MEC["coifas"][1]["y"], Z_COIFA_TOPO],
         pranchas=[PRANCHA, "Anexo C — layout as-built (1:45)", "PA-COZINHA-003/2026 rev. 02"]),
    dict(tipo="Camadas de duto", desc=f"Altura dos dutos não cotada. Adotado: ar exterior e insuflamento com topo a {TOPO['AEX']:+.2f} (sob a laje), exaustão com topo a {TOPO['EXA']:+.2f} "
         "(o desenho interrompe a exaustão onde cruza os outros dutos, isto é, ela passa por baixo). Confirmar com levantamento.", gravidade="Média",
         disciplinas=["MEC"], ids=[], pos=None, pranchas=[ASB_LONGO]),
]
for v in VER_DUTOS["soltas"]:
    DIV_DUTOS.append(dict(tipo="Ponta de duto solta", desc=f"Extremidade '{v['lado']}' do duto {v['duto']} não encontra outro duto, prumada ou captor.", gravidade="Baixa",
                          disciplinas=["MEC"], ids=[], pos=[v["x"], v["y"], 0.4], pranchas=[ASB_LONGO]))
PREMISSAS_DUTOS = [
    dict(id="P11", texto="Dutos: planta do as-built da Fase 2 (1:35) registrada sobre o modelo por pontos de controle nas faces internas das salas de lavagem; escala conferida em 4 medidas (desvio ≤ 0,1 %)."),
    dict(id="P12", texto=f"Alturas dos dutos (INFERIDO): ar exterior e insuflamento com topo a {TOPO['AEX']:+.2f}; exaustão com topo a {TOPO['EXA']:+.2f}; coifas com borda inferior a {H_COIFA_BASE:.2f} m do piso e 0,60 m de altura."),
    dict(id="P13", texto="Prumadas, ventiladores (laje técnica +8,36) e descargas (cobertura +20,93) seguem o fluxograma TDM001-ARC-PJ-E-R-012; o traçado em planta acima do térreo é INFERIDO (vertical)."),
]
PRANCHAS_DUTOS = [
    dict(codigo="Anexo D — dutos exaustão subsolo", curta=ASB, disciplina="MEC (exaustão, insuflamento, ar exterior)", pavimento="Subsolo",
         escala="1:35 (conferida)", rev="Fase 2", data="27/08/2026", arquivo="PA-COZINHA-003-2026_Anexo-D_Planta-Subsolo.pdf", vetorial="sim (30.007 objetos)",
         texto="só o carimbo (rótulos vetorizados)", uso="Traçado dos dutos, prumadas, captores e difusores"),
    dict(codigo="TDM001-ARC-PJ-E-R-012", curta="Fluxogramas de exaustão e ventilação", disciplina="MEC", pavimento="todos", escala="sem escala",
         rev="Projeto final", data="2006", arquivo="FLUXOGRAMAVENTILAÇÃO.pdf", vetorial="sim", texto="não (folha girada 180°)",
         uso="Topologia, seções das prumadas, níveis dos pavimentos e ventiladores"),
    dict(codigo="PA-COZINHA-003/2026 rev. 02", curta="Relatório de adequação", disciplina="MEC", pavimento="—", escala="—", rev="02", data="28/08/2026",
         arquivo="PA-COZINHA-003-2026.pdf", vetorial="—", texto="sim", uso="Níveis (−2,87 / +8,36 / +20,93), ventiladores e verificações de velocidade"),
    dict(codigo="Anexo C — layout as-built", curta="Layout as-built Fase 2", disciplina="ARQ", pavimento="Subsolo", escala="1:45", rev="Fase 2",
         data="27/08/2026", arquivo="PA-COZINHA-003-2026_Anexo-C_Planta-Terreo.pdf", vetorial="sim", texto="parcial", uso="Conferência das coifas (8,30 m da coifa C)"),
]
NIVEIS_DUTOS = [
    dict(id="N-LTEC", ambiente="Laje técnica (ventiladores)", tipo="laje", pa=Z_LAJE_TEC, po=None, x=None, y=None, fonte="fluxograma / relatório PA-COZINHA-003", status="EXTRAÍDO", z=Z_LAJE_TEC),
    dict(id="N-COB", ambiente="Cobertura (descarga)", tipo="laje", pa=Z_COBERT, po=None, x=None, y=None, fonte="fluxograma / relatório PA-COZINHA-003", status="EXTRAÍDO", z=Z_COBERT),
    dict(id="N-DUTO-AE", ambiente="Topo dos dutos de ar exterior e insuflamento", tipo="duto", pa=None, po=None, x=None, y=None, fonte="premissa P12", status="INFERIDO", z=TOPO["AEX"]),
    dict(id="N-DUTO-EX", ambiente="Topo dos dutos de exaustão", tipo="duto", pa=None, po=None, x=None, y=None, fonte="premissa P12", status="INFERIDO", z=TOPO["EXA"]),
    dict(id="N-COIFA", ambiente="Borda inferior das coifas", tipo="coifa", pa=None, po=None, x=None, y=None, fonte="memorial 2006 (1,90–2,10 m)", status="INFERIDO", z=round(PA0 + H_COIFA_BASE, 3)),
]
