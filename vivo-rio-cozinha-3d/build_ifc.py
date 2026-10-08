# Gera saida/modelo.ifc (IFC4) e saida/divergencias.bcf (BCF 2.1) a partir de saida/modelo.json.
# Mesma fonte única de dados do HTML: nada é medido aqui, só convertido.
# Requer: pip install ifcopenshell
import json, math, os, uuid, zipfile, datetime, io
from xml.sax.saxutils import escape as xesc
import ifcopenshell, ifcopenshell.api as api, ifcopenshell.guid

ROOT = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(ROOT, "saida")
SNAP = os.path.join(ROOT, "verificacao", "bcf_snapshots")
M = json.load(open(os.path.join(SAIDA, "modelo.json"), encoding="utf-8"))
AUTOR = "contato@kaptek.com.br"
NS = uuid.UUID("6f1c2a52-9d0e-4c57-9a43-7b1f0c3e5a10")   # GUIDs estáveis: o mesmo ID gera o mesmo GlobalId a cada build

def gid(key): return ifcopenshell.guid.compress(uuid.uuid5(NS, key).hex)

# ---------------------------------------------------------------- arquivo, unidades, contexto
f = api.run("project.create_file", version="IFC4")
f.header.file_name.name = "modelo.ifc"
f.header.file_name.author = (AUTOR,)
f.header.file_name.organization = ("Kaptek Engenharia e Tecnologia",)
f.header.file_description.description = ("ViewDefinition [DesignTransferView]",)
proj = api.run("root.create_entity", f, ifc_class="IfcProject", name=M["meta"]["projeto"])
proj.GlobalId = gid("projeto"); proj.Description = M["meta"]["obra"]; proj.LongName = M["meta"]["folha"]
units = [api.run("unit.add_si_unit", f, unit_type=t) for t in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT")]
units.append(f.createIfcSIUnit(None, "PLANEANGLEUNIT", None, "RADIAN"))
api.run("unit.assign_unit", f, units=units)
ctx = api.run("context.add_context", f, context_type="Model")
body = api.run("context.add_context", f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=ctx)

def P3(p): return f.createIfcCartesianPoint([float(v) for v in p])
def D3(v): return f.createIfcDirection([float(x) for x in v])
def ax3(o, z=(0, 0, 1), x=(1, 0, 0)): return f.createIfcAxis2Placement3D(P3(o), D3(z), D3(x))
def place(rel, o=(0, 0, 0)): return f.createIfcLocalPlacement(rel, ax3(o))

# ---------------------------------------------------------------- estrutura espacial
site = api.run("root.create_entity", f, ifc_class="IfcSite", name="Vivo Rio")
building = api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Vivo Rio — casa de espetáculos")
site.GlobalId, building.GlobalId = gid("site"), gid("edificio")
site.Description = M["origem"]["texto"]
addr = f.createIfcPostalAddress(None, None, None, None, M["meta"]["endereco"].split(" — "), None,
                                "Rio de Janeiro", "RJ", None, "Brasil")
building.BuildingAddress = addr; site.SiteAddress = addr
site.ObjectPlacement = place(None); building.ObjectPlacement = place(site.ObjectPlacement)
api.run("aggregate.assign_object", f, relating_object=proj, products=[site])
api.run("aggregate.assign_object", f, relating_object=site, products=[building])

PAV = [("SS", "Subsolo — cozinha de banquetes", -2.87), ("TER", "Térreo (laje +1,50)", 1.50),
       ("LT", "Laje técnica (+8,36)", 8.36), ("COB", "Cobertura (+20,93)", 20.93)]
storeys = {}
for k, nome, z in PAV:
    s = api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name=nome)
    s.GlobalId = gid("pav-" + k); s.Elevation = z; s.ObjectPlacement = place(building.ObjectPlacement, (0, 0, z))
    storeys[k] = (s, z)
api.run("aggregate.assign_object", f, relating_object=building, products=[s for s, _ in storeys.values()])
def storey_of(z):
    k = "SS" if z < 1.50 - 1e-6 else "TER" if z < 8.36 - 1e-6 else "LT" if z < 20.93 - 1e-6 else "COB"
    return storeys[k]
contained = {}   # storey -> [produtos]

# ---------------------------------------------------------------- estilos (cores do visualizador)
COR = {"HID-AF": "1f6fd1", "HID-AQ": "d43a2f", "SAN-ESG": "8b5a2b", "SAN-VENT": "6f7782", "DRE": "0fa3b8", "GAS": "d9a100",
       "EXA": "f07a12", "EXG": "b0602c", "INS": "c247d6", "AEX": "7a8ea3",
       "PEND": "e3157e", "PAREDE": "b8bec7", "VIDRO": "9fd8e3", "EQUIP": "d9dde3", "LOUCA": "eef1f4", "ESPACO": "e8ecf0"}
_styles = {}
def style(key, transp=0.0):
    k = (key, transp)
    if k not in _styles:
        h = COR[key]; rgb = f.createIfcColourRgb(None, *[int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
        rend = f.createIfcSurfaceStyleRendering(rgb, transp, None, None, None, None, None, None, "NOTDEFINED")
        _styles[k] = f.createIfcSurfaceStyle(f"{key}{' transp.' if transp else ''}", "BOTH", [rend])
    return _styles[k]

# ---------------------------------------------------------------- geometria
def rect_solid(o, z, x, W, H, L):
    prof = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(f.createIfcCartesianPoint([0., 0.]), None), float(W), float(H))
    return f.createIfcExtrudedAreaSolid(prof, ax3(o, z, x), D3((0, 0, 1)), float(L))
def circ_solid(o, z, x, r, L):
    prof = f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(f.createIfcCartesianPoint([0., 0.]), None), float(r))
    return f.createIfcExtrudedAreaSolid(prof, ax3(o, z, x), D3((0, 0, 1)), float(L))
def poly_solid(poly, z0, h):
    pts = [f.createIfcCartesianPoint([float(p[0]), float(p[1])]) for p in poly]
    prof = f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcPolyline(pts + [pts[0]]))
    return f.createIfcExtrudedAreaSolid(prof, ax3((0, 0, z0)), D3((0, 0, 1)), float(h))
def axis_frame(a, b):
    v = [b[i] - a[i] for i in range(3)]; L = math.sqrt(sum(c * c for c in v))
    z = [c / L for c in v]
    if math.hypot(z[0], z[1]) < 1e-6: x = (1, 0, 0)
    else: n = math.hypot(z[0], z[1]); x = (-z[1] / n, z[0] / n, 0)   # horizontal, perpendicular ao eixo
    return z, x, L
def box_xy(cx, cy, z0, z1, L, P):   # caixa alinhada aos eixos (coifas, ventiladores, difusores)
    return rect_solid((cx, cy, z0), (0, 0, 1), (1, 0, 0), L, P, max(0.02, z1 - z0))
def wall_solid(a, b, esp, z0, z1):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    return rect_solid(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z0), (0, 0, 1), (dx / L, dy / L, 0), L, esp, z1 - z0), L

def shift(items, dz):   # geometria em coordenadas do pavimento (o pavimento já está na sua cota)
    for it in items:
        loc = it.Position.Location; c = list(loc.Coordinates); c[2] -= dz
        it.Position = f.createIfcAxis2Placement3D(P3(c), it.Position.Axis, it.Position.RefDirection)
    return items

def element(cls, key, nome, items, z_ref, estilo, tag=None, desc=None, ptype=None, otype=None):
    e = api.run("root.create_entity", f, ifc_class=cls, name=nome, predefined_type=ptype or "NOTDEFINED")
    if otype:
        e.PredefinedType = "USERDEFINED"; e.ObjectType = otype
    e.GlobalId = gid(key); e.Description = desc
    if e.is_a("IfcElement"): e.Tag = tag or key
    st, zst = storey_of(z_ref)
    e.ObjectPlacement = place(st.ObjectPlacement)
    if items:
        shift(items, zst)
        rep = f.createIfcShapeRepresentation(body, "Body", "SweptSolid", items)
        for it in items: f.createIfcStyledItem(it, [estilo], None)
        e.Representation = f.createIfcProductDefinitionShape(None, None, [rep])
    contained.setdefault(st, []).append(e)
    return e

def lbl(v): return f.createIfcText(v) if len(v) > 255 else f.createIfcLabel(v)
def pset(e, nome, props):
    vals = []
    for k, v in props.items():
        if v is None or v == "" or v == []: continue
        if isinstance(v, bool): nv = f.createIfcBoolean(v)
        elif isinstance(v, (int, float)): nv = f.createIfcReal(float(v))
        elif isinstance(v, list): nv = lbl("; ".join(map(str, v)))
        else: nv = lbl(str(v))
        vals.append(f.createIfcPropertySingleValue(k, None, nv, None))
    if not vals: return
    ps = f.createIfcPropertySet(ifcopenshell.guid.new(), None, nome, None, vals)
    f.createIfcRelDefinesByProperties(ifcopenshell.guid.new(), None, None, None, [e], ps)

DIV_DE = {}
for d in M["divergencias"]:
    for i in d["ids"]: DIV_DE.setdefault(i, []).append(d["id"])
SITU = {"EXTRAÍDO": "Conforme projeto", "INFERIDO": "Confirmar antes de executar", "PENDENTE": "Não executar — pendente"}
def origem(e, oid, status, memoria=None, motivo=None, prancha=None, **extra):
    props = {"ID": oid, "Situacao": status, "SituacaoCampo": SITU.get(status), "MemoriaCalculo": memoria, "Motivo": motivo,
             "Prancha": prancha, "Divergencias": DIV_DE.get(oid, [])}
    props.update(extra); pset(e, "Pset_KaptekOrigem", props)

GUID = {}      # id do modelo -> GlobalId (para o BCF)
SIS_EL = {}    # sistema -> [elementos]
def reg(oid, e, sis=None):
    GUID[oid] = e.GlobalId
    if sis: SIS_EL.setdefault(sis, []).append(e)

PR_PONTOS = M["pranchas"][0]["codigo"]

# ---------------------------------------------------------------- arquitetura
for a in M["ambientes"]:
    e = element("IfcSpace", a["id"], a["id"], [poly_solid(a["poly"], a["pa"], 1.25 - a["pa"])], a["pa"], style("ESPACO", 0.85))
    e.LongName = a["nome"]; e.CompositionType = "ELEMENT"; e.PredefinedType = "INTERNAL"
    origem(e, a["id"], a["status"], motivo=a.get("fonte"), PisoAcabado=a["pa"], PisoOsso=a.get("po"))
    reg(a["id"], e)
for w in M["paredes"]:
    sol, L = wall_solid(w["a"], w["b"], w["esp"], w["z0"], w["z1"])
    if w.get("vidro"):
        e = element("IfcPlate", w["id"], "Painel de vidro", [sol], w["z0"], style("VIDRO", 0.6), ptype="CURTAIN_PANEL")
    else:
        e = element("IfcWall", w["id"], "Parede", [sol], w["z0"], style("PAREDE"), ptype="NOTDEFINED")
    origem(e, w["id"], "EXTRAÍDO", motivo=w.get("fonte"), prancha=PR_PONTOS, Espessura=w["esp"], Comprimento=round(L, 3))
    reg(w["id"], e)
for v in M["vaos"]:
    pecas = [("verga", v["z0"] + v["verga"], v["z1"])]
    if v["tipo"] == "janela": pecas.insert(0, ("peitoril", v["z0"], v["z0"] + v["peitoril"]))
    for nome, z0, z1 in pecas:
        if z1 - z0 < 0.01: continue
        sol, _ = wall_solid(v["a"], v["b"], v["esp"], z0, z1)
        e = element("IfcWall", f"{v['id']}-{nome}", f"{nome.capitalize()} do vão {v['id']}", [sol], v["z0"], style("PAREDE"))
        origem(e, v["id"], v["status"], motivo=v.get("motivo"), prancha=PR_PONTOS, Parede=v.get("parede"))
    if v["tipo"] == "janela":
        sol, _ = wall_solid(v["a"], v["b"], 0.01, v["z0"] + v["peitoril"], v["z0"] + v["verga"])
        e = element("IfcWindow", v["id"], "Janela / visor de vidro", [sol], v["z0"], style("VIDRO", 0.6), ptype="WINDOW")
        e.OverallWidth, e.OverallHeight = v["largura"], v["verga"] - v["peitoril"]
    else:
        e = element("IfcDoor", v["id"], "Porta (vão)", None, v["z0"], None, ptype="DOOR")
        e.OverallWidth, e.OverallHeight = v["largura"], v["verga"]
    origem(e, v["id"], v["status"], motivo=v.get("motivo"), prancha=PR_PONTOS, Parede=v.get("parede"), Etiqueta=v.get("etiqueta"))
    reg(v["id"], e)

LOUCA_DE_EQ = {l["equip"]: l for l in M["loucas"]}
for q in M["equipamentos"]:
    xs = [p[0] for p in q["poly"]]; ys = [p[1] for p in q["poly"]]
    sol = box_xy(min(xs), min(ys), q["z0"], q["z1"], max(xs) - min(xs), max(ys) - min(ys))
    sol.Position = ax3(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, q["z0"]))
    l = LOUCA_DE_EQ.get(q["id"])
    if l:
        pt = "WASHHANDBASIN" if "lavatório" in l["nome"].lower() else "SINK"
        e = element("IfcSanitaryTerminal", l["id"], l["nome"], [sol], q["z0"], style("LOUCA"), tag=l["id"], ptype=pt)
        origem(e, l["id"], q["status"], motivo=q.get("motivo"), prancha=PR_PONTOS, Equipamento=q["id"], PontoAtendido=l.get("ponto"),
               Item=l.get("item"), FolgaParede=l.get("folga_m"), InvasaoParede_m2=l.get("invasao_m2"), Ilha=l.get("ilha"))
        reg(l["id"], e); reg(q["id"], e)
    else:
        e = element("IfcFurniture", q["id"], q["tipo"].capitalize(), [sol], q["z0"], style("EQUIP", 0.3), otype=q["tipo"])
        origem(e, q["id"], q["status"], motivo=q.get("motivo"), prancha=PR_PONTOS, Ambiente=q.get("amb"))
        reg(q["id"], e)

# ---------------------------------------------------------------- tubulações
PONTO_CLS = {"RSIF": ("IfcWasteTerminal", "FLOORTRAP", None), "RSG": ("IfcWasteTerminal", "FLOORTRAP", None),
             "RS": ("IfcWasteTerminal", "FLOORWASTE", None), "CANAL": ("IfcWasteTerminal", None, "Canaleta")}
for p in M["pontos"]:
    cls, pt, ot = PONTO_CLS.get(p["tipo"], ("IfcPipeFitting", None, "Ponto de utilização / espera"))
    estilo = style("PEND") if p["status"] == "PENDENTE" else style(p["sistema"])
    if cls == "IfcWasteTerminal":
        r = 0.075 if p["tipo"] != "CANAL" else 0.10
        items = [circ_solid((p["x"], p["y"], p["z"] - 0.02), (0, 0, 1), (1, 0, 0), r, 0.02)]
    else:
        r = max((p.get("dn_mm") or 20) / 2000 * 1.6, 0.025)
        items = [circ_solid((p["x"], p["y"], p["z"] - 0.03), (0, 0, 1), (1, 0, 0), r, 0.06)]
    e = element(cls, p["id"], p["titulo"], items, p["z"], estilo, desc=p.get("texto"), ptype=pt, otype=ot)
    origem(e, p["id"], p["status"], memoria=p.get("memoria"), motivo=p.get("motivo"), prancha=p.get("prancha"),
           Sistema=p["sistema"], Disciplina=p["disciplina"], DN=p.get("dn"), DN_mm=p.get("dn_mm"), AlturaDoPiso=p.get("h"),
           CotaZ=p["z"], Ambiente=p.get("amb_nome"), TextoPrancha=p.get("texto"), Equipamento=p.get("equipamento"), Item=p.get("item"))
    reg(p["id"], e, p["sistema"])

NOS = {n["id"]: n for n in M["nos"]}
dn_no = {}
for t in M["trechos"]:
    for k in (t["a"], t["b"]): dn_no.setdefault(k, []).append((t["dn_mm"] or 20, t["sistema"]))
for n in M["nos"]:
    if n["tipo"] != "no": continue
    dmax, sis = max(dn_no.get(n["id"], [(20, None)]))
    r = dmax / 2000 * 1.3
    e = element("IfcPipeFitting", n["id"], "Junção / mudança de direção", [circ_solid((n["x"], n["y"], n["z"] - r), (0, 0, 1), (1, 0, 0), r, 2 * r)],
                n["z"], style(sis or "SAN-ESG"), ptype="JUNCTION")
    origem(e, n["id"], "INFERIDO", motivo="Nó do traçado inferido (ver trechos ligados).", Referencia=n.get("ref"))
    reg(n["id"], e, sis)

for t in M["trechos"]:
    r = (t["dn_mm"] or 20) / 2000
    items = []
    for s in t["segs"]:
        z, x, L = axis_frame(s["a"], s["b"])
        if L > 0.005: items.append(circ_solid(s["a"], z, x, r, L))
    zmin = min(min(s["a"][2], s["b"][2]) for s in t["segs"])
    estilo = style("PEND") if t["status"] == "PENDENTE" else style(t["sistema"], 0.0 if t["status"] == "EXTRAÍDO" else 0.35)
    e = element("IfcPipeSegment", t["id"], f"Tubo {t['dn'] or ''} · {t['sistema']}".strip(), items, zmin, estilo, ptype="RIGIDSEGMENT")
    pontas = []
    for k in (t["a"], t["b"]):
        n = NOS.get(k)
        if n and n["tipo"] == "limite": pontas.append(f"{k}: limite — {n.get('ref')}")
    origem(e, t["id"], t["status"], motivo=t.get("motivo"), Sistema=t["sistema"], Disciplina=t["disciplina"], DN=t.get("dn"),
           DN_mm=t.get("dn_mm"), Comprimento=t.get("comprimento"), Declividade=t.get("declividade"), Vertical=t.get("vertical"),
           Passagem=t.get("passagem"), Pontos=t.get("pontos"), PontasEmLimite=pontas,
           Enterrado=any(s.get("enterrado") for s in t["segs"]))
    reg(t["id"], e, t["sistema"])

# ---------------------------------------------------------------- dutos e equipamentos de ar
for d in M["dutos"]:
    z, x, L = axis_frame(d["a"], d["b"])
    if L < 0.01: continue
    estilo = style("PEND") if d["status"] == "PENDENTE" else style(d["sistema"], 0.0 if d["status"] == "EXTRAÍDO" else 0.35)
    e = element("IfcDuctSegment", d["id"], f"Duto {d['rotulo']}", [rect_solid(d["a"], z, x, d["W"], d["H"], L)],
                min(d["a"][2], d["b"][2]), estilo, desc=d.get("nota"), ptype="RIGIDSEGMENT")
    origem(e, d["id"], d["status"], memoria=d.get("memoria"), motivo=d.get("nota"), prancha=d.get("prancha"), Sistema=d["sistema"],
           SistemaNome=d.get("sistema_nome"), Rotulo=d["rotulo"], Largura=d["W"], Altura=d["H"], Comprimento=d["comprimento"],
           Tipo=d["tipo"], Ventilador=d.get("exaustor"), Passagem=d.get("passagem"))
    reg(d["id"], e, d["sistema"])
MEC = M["mec"]
for c in MEC["coifas"]:
    e = element("IfcAirTerminal", c["id"], c["nome"], [box_xy(c["x"], c["y"], c["z0"], c["z1"], c["L"], c["P"])], c["z0"],
                style("EXA", 0.6), desc=c.get("texto"), otype="Coifa")
    origem(e, c["id"], c["status"], motivo=c.get("motivo"), TextoPrancha=c.get("texto"), Ventilador=c.get("exaustor"),
           Comprimento=c["L"], Profundidade=c["P"], AlturaBordaInferiorDoPiso=round(c["z0"] - (-2.87), 2))
    reg(c["id"], e, "EXA")
for v in MEC["ventiladores"]:
    e = element("IfcFan", v["id"], v["nome"], [box_xy(v["x"], v["y"], v["z0"], v["z1"], v["L"], v["P"])], v["z0"], style(v["sistema"]))
    origem(e, v["id"], v["status"], motivo=v.get("motivo"), Dados=v.get("dados"), Sistema=v["sistema"])
    reg(v["id"], e, v["sistema"])
for v in MEC["difusores"]:
    e = element("IfcAirTerminal", v["id"], "Difusor / grelha de insuflamento", [box_xy(v["x"], v["y"], v["z"] - 0.03, v["z"], v["L"], v["L"])],
                v["z"], style("INS"), ptype="DIFFUSER")
    origem(e, v["id"], v["status"], motivo=v.get("motivo"), Sistema="INS")
    reg(v["id"], e, "INS")
for c in MEC["captores"]:
    co = next((k for k in MEC["coifas"] if k["id"].startswith("COIFA-" + c["coifa"])), None)
    zt = co["z1"] if co else -0.27
    e = element("IfcAirTerminal", c["id"], f"Captor da coifa {c['coifa']}", [box_xy(c["x"], c["y"], zt, zt + 0.05, 0.3, 0.3)], zt,
                style(c["sistema"]), otype="Captor (colarinho da coifa)")
    origem(e, c["id"], "INFERIDO", motivo="Posição em planta do as-built (Anexo D); geometria simbólica 0,30 × 0,30 m no topo da coifa.",
           Coifa=c["coifa"], Sistema=c["sistema"])
    reg(c["id"], e, c["sistema"])

for st, prods in contained.items():
    esp = [e for e in prods if e.is_a("IfcSpace")]; els = [e for e in prods if not e.is_a("IfcSpace")]
    if esp: api.run("aggregate.assign_object", f, relating_object=st, products=esp)
    if els: api.run("spatial.assign_container", f, relating_structure=st, products=els)

# ---------------------------------------------------------------- sistemas
SIS_IFC = {"HID-AF": ("Água fria", "DOMESTICCOLDWATER"), "HID-AQ": ("Água quente", "DOMESTICHOTWATER"),
           "SAN-ESG": ("Esgoto", "SEWAGE"), "SAN-VENT": ("Ventilação de esgoto", "VENT"), "DRE": ("Dreno (câmaras / ar-cond.)", "DRAINAGE"),
           "GAS": ("Gás", "GAS"), "EXA": ("Exaustão da cozinha", "EXHAUST"), "EXG": ("Exaustão geral (E-)", "EXHAUST"),
           "INS": ("Insuflamento", "VENTILATION"), "AEX": ("Ar exterior / compensação", "VENTILATION")}
for k, els in SIS_EL.items():
    nome, pt = SIS_IFC[k]
    s = f.createIfcDistributionSystem(gid("sis-" + k), None, k, None, None, nome, pt)
    f.createIfcRelAssignsToGroup(gid("sisrel-" + k), None, None, None, els, None, s)
    f.createIfcRelServicesBuildings(gid("sisbld-" + k), None, None, None, s, [building])

IFC = os.path.join(SAIDA, "modelo.ifc")
f.write(IFC)
json.dump(GUID, open(os.path.join(SAIDA, "ifc_guids.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------------------------------------------------------------- BCF 2.1 (divergências)
def bcf_camera(d):
    alvo = d["pos"]; pts = []
    for i in d["ids"]:
        for col in ("pontos", "dutos"):
            o = next((x for x in M[col] if x["id"] == i), None)
            if o: pts.append([o["x"], o["y"], o["z"]] if col == "pontos" else [(o["a"][j] + o["b"][j]) / 2 for j in range(3)])
        o = next((x for x in MEC["coifas"] if x["id"] == i), None)
        if o: pts.append([o["x"], o["y"], o["z0"]])
    if not alvo and pts: alvo = [sum(p[j] for p in pts) / len(pts) for j in range(3)]
    if alvo:
        span = max([math.dist(alvo, p) for p in pts] + [0])
        dist = max(6.0, span * 2.2 + 3)
    else:
        alvo, dist = [8.9, 9.8, -2.0], 34.0      # visão geral da cozinha
    # perto do piso: câmera baixa, abaixo da camada de dutos; no forro e na visão geral: de cima
    v = [0.50, 0.80, -0.35] if alvo[2] < -1.0 and dist < 10 else [0.35, 0.55, -0.76]
    if alvo[2] < -1.0 and dist < 10: dist = 5.0
    n = math.sqrt(sum(c * c for c in v)); v = [c / n for c in v]
    eye = [alvo[j] - v[j] * dist for j in range(3)]
    up = [-v[0] * v[2], -v[1] * v[2], 1 - v[2] * v[2]]; nu = math.sqrt(sum(c * c for c in up)); up = [c / nu for c in up]
    return alvo, eye, v, up

def ligados(i):   # trechos que chegam ao ponto citado, para o destaque no BCF
    return [t["id"] for t in M["trechos"] if i in (t.get("pontos") or [])]

def xyz(tag, p): return f"<{tag}><X>{p[0]:.4f}</X><Y>{p[1]:.4f}</Y><Z>{p[2]:.4f}</Z></{tag}>"
agora = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
BCF = os.path.join(SAIDA, "divergencias.bcf")
CAMERAS = {}
with zipfile.ZipFile(BCF, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("bcf.version", '<?xml version="1.0" encoding="UTF-8"?>\n<Version VersionId="2.1"><DetailedVersion>2.1</DetailedVersion></Version>\n')
    z.writestr("project.bcfp", '<?xml version="1.0" encoding="UTF-8"?>\n<ProjectExtension><Project ProjectId="%s"><Name>%s</Name></Project><ExtensionSchema></ExtensionSchema></ProjectExtension>\n'
               % (uuid.uuid5(NS, "bcf-projeto"), xesc(M["meta"]["projeto"])))
    for idx, d in enumerate(M["divergencias"], 1):
        tg = str(uuid.uuid5(NS, "topic-" + d["id"])); vg = str(uuid.uuid5(NS, "vp-" + d["id"]))
        sel = []
        for i in d["ids"]:
            for k in [i] + ligados(i):
                if k in GUID and GUID[k] not in sel: sel.append(GUID[k])
        alvo, eye, v, up = bcf_camera(d)
        CAMERAS[d["id"]] = {"alvo": alvo, "olho": eye}
        desc = d["descricao"] + ("\n\nElementos: " + ", ".join(d["ids"]) if d["ids"] else "") + \
               "\nPranchas: " + "; ".join(d["pranchas"]) + "\nGravidade: " + d["gravidade"]
        labels = "".join(f"<Labels>{xesc(x)}</Labels>" for x in d["disciplinas"])
        snap = os.path.join(SNAP, d["id"] + ".png"); tem_snap = os.path.exists(snap)
        markup = f'''<?xml version="1.0" encoding="UTF-8"?>
<Markup>
<Header><File IfcProject="{proj.GlobalId}" isExternal="true"><Filename>modelo.ifc</Filename><Date>{agora}</Date></File></Header>
<Topic Guid="{tg}" TopicType="Issue" TopicStatus="Open">
<Title>{xesc(d["id"] + " · " + d["tipo"])}</Title>
<Priority>{xesc(d["gravidade"])}</Priority>
<Index>{idx}</Index>
{labels}
<CreationDate>{agora}</CreationDate>
<CreationAuthor>{AUTOR}</CreationAuthor>
<Description>{xesc(desc)}</Description>
</Topic>
<Viewpoints Guid="{vg}"><Viewpoint>viewpoint.bcfv</Viewpoint>{"<Snapshot>snapshot.png</Snapshot>" if tem_snap else ""}</Viewpoints>
</Markup>
'''
        comp = "".join(f'<Component IfcGuid="{g}"/>' for g in sel)
        vis = f'''<?xml version="1.0" encoding="UTF-8"?>
<VisualizationInfo Guid="{vg}">
<Components><ViewSetupHints SpacesVisible="false" SpaceBoundariesVisible="false" OpeningsVisible="false"/>
{"<Selection>" + comp + "</Selection>" if sel else ""}<Visibility DefaultVisibility="true"/>
{'<Coloring><Color Color="E3157E">' + comp + '</Color></Coloring>' if sel else ""}</Components>
<PerspectiveCamera>{xyz("CameraViewPoint", eye)}{xyz("CameraDirection", v)}{xyz("CameraUpVector", up)}<FieldOfView>60</FieldOfView></PerspectiveCamera>
</VisualizationInfo>
'''
        z.writestr(f"{tg}/markup.bcf", markup)
        z.writestr(f"{tg}/viewpoint.bcfv", vis)
        if tem_snap: z.write(snap, f"{tg}/snapshot.png")
json.dump(CAMERAS, open(os.path.join(ROOT, "verificacao", "bcf_cameras.json"), "w"), indent=1)
print(f"ok {os.path.getsize(IFC)//1024} KB IFC · {len(GUID)} ids · BCF {len(M['divergencias'])} tópicos ({os.path.getsize(BCF)//1024} KB)")
