# Verifica saida/modelo.ifc e saida/divergencias.bcf contra saida/modelo.json.
# Uso: python3 verificacao/teste_ifc.py [pasta_com_xsd_bcf_2_1]
import json, os, sys, zipfile, collections, io
import numpy as np
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.element as ue
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); SAIDA = os.path.join(ROOT, "saida")
M = json.load(open(os.path.join(SAIDA, "modelo.json"), encoding="utf-8"))
f = ifcopenshell.open(os.path.join(SAIDA, "modelo.ifc"))
res = []
def ok(nome, cond, info=""):
    res.append((nome, bool(cond), info)); print(("OK  " if cond else "FALHA ") + nome, info)

# 1. contagens
cnt = collections.Counter(e.is_a() for e in f.by_type("IfcProduct"))
print(dict(cnt))
ok("pontos", sum(cnt[c] for c in ("IfcPipeFitting", "IfcWasteTerminal")) == len(M["pontos"]) + sum(n["tipo"] == "no" for n in M["nos"]))
ok("trechos de tubo", cnt["IfcPipeSegment"] == len(M["trechos"]), f'{cnt["IfcPipeSegment"]}/{len(M["trechos"])}')
ok("dutos", cnt["IfcDuctSegment"] == len(M["dutos"]), f'{cnt["IfcDuctSegment"]}/{len(M["dutos"])}')
ok("ventiladores", cnt["IfcFan"] == len(M["mec"]["ventiladores"]))
ok("coifas + difusores + captores", cnt["IfcAirTerminal"] == sum(len(M["mec"][k]) for k in ("coifas", "difusores", "captores")))
ok("louças", cnt["IfcSanitaryTerminal"] == len(M["loucas"]))
ok("ambientes", cnt["IfcSpace"] == len(M["ambientes"]))

# 2. geometria: tudo tessela e cai onde o JSON diz
st = ifcopenshell.geom.settings(); st.set("use-world-coords", True)
it = ifcopenshell.geom.iterator(st, f)
bbox = {}; falhas = []
if it.initialize():
    while True:
        s = it.get(); v = np.array(s.geometry.verts).reshape(-1, 3)
        if len(v): bbox[s.guid] = (v.min(0), v.max(0))
        if not it.next(): break
com_rep = [e for e in f.by_type("IfcProduct") if e.Representation]
ok("todos os elementos com geometria tesselam", len(bbox) == len(com_rep), f"{len(bbox)}/{len(com_rep)}")
G = json.load(open(os.path.join(SAIDA, "ifc_guids.json"), encoding="utf-8"))
def dentro(gid_, p, tol=0.02):
    lo, hi = bbox[gid_]; return all(lo[i] - tol <= p[i] <= hi[i] + tol for i in range(3))
erro = [t["id"] for t in M["trechos"] for s in t["segs"] for p in (s["a"], s["b"]) if not dentro(G[t["id"]], p)]
ok("tubos: extremidades de cada segmento dentro da geometria IFC", not erro, str(erro[:3]))
erro = [d["id"] for d in M["dutos"] for p in (d["a"], d["b"]) if not dentro(G[d["id"]], p)]
ok("dutos: extremidades do eixo dentro da geometria IFC", not erro, str(erro[:3]))
erro = []; alinhados = 0
for d in M["dutos"]:
    v = [abs(d["b"][i] - d["a"][i]) for i in range(3)]
    if sum(c > 0.005 for c in v) != 1: continue        # só dutos paralelos a um eixo têm caixa envolvente = seção × comprimento
    alinhados += 1; lo, hi = bbox[G[d["id"]]]
    if max(abs(a - b) for a, b in zip(sorted(hi - lo), sorted([d["W"], d["H"], max(v)]))) > 0.01: erro.append(d["id"])
ok("dutos: seção e comprimento conferem com o JSON", not erro, f"{alinhados} dutos alinhados aos eixos; {erro[:3]}")
erro = [p["id"] for p in M["pontos"] if not dentro(G[p["id"]], (p["x"], p["y"], p["z"]))]
ok("pontos na posição do JSON", not erro, str(erro[:3]))
erro = [w["id"] for w in M["paredes"] if not (dentro(G[w["id"]], (*w["a"], w["z0"]), .15) and dentro(G[w["id"]], (*w["b"], w["z1"]), .15))]
ok("paredes na posição do JSON", not erro, str(erro[:3]))

# 3. propriedades e sistemas
semps = [e.GlobalId for e in f.by_type("IfcElement") if "Pset_KaptekOrigem" not in ue.get_psets(e)]
ok("todo elemento tem Pset_KaptekOrigem (situação + memória)", not semps, str(semps[:3]))
pend = [e for e in f.by_type("IfcElement") if ue.get_psets(e).get("Pset_KaptekOrigem", {}).get("Situacao") == "PENDENTE"]
ok("PENDENTE filtrável por propriedade", len(pend) == sum(p["status"] == "PENDENTE" for p in M["pontos"]) + sum(d["status"] == "PENDENTE" for d in M["dutos"]), str(len(pend)))
sis = {s.Name: len(s.IsGroupedBy[0].RelatedObjects) for s in f.by_type("IfcDistributionSystem")}
ok("sistemas de distribuição", set(sis) == {p["sistema"] for p in M["pontos"]} | {d["sistema"] for d in M["dutos"]}, str(sis))
fora = [e.GlobalId for e in f.by_type("IfcElement") if not e.ContainedInStructure]
ok("todo elemento contido num pavimento", not fora, str(fora[:3]))

# 4. BCF
z = zipfile.ZipFile(os.path.join(SAIDA, "divergencias.bcf"))
topicos = {n.split("/")[0] for n in z.namelist() if n.endswith("markup.bcf")}
ok("BCF: um tópico por divergência", len(topicos) == len(M["divergencias"]), str(len(topicos)))
todos = {e.GlobalId for e in f.by_type("IfcRoot")}
import re
refs = set(re.findall(r'IfcGuid="([^"]+)"', "".join(z.read(n).decode() for n in z.namelist() if n.endswith(".bcfv"))))
ok("BCF: todos os componentes citados existem no IFC", refs <= todos, str(len(refs - todos)))
proj = re.findall(r'IfcProject="([^"]+)"', z.read(next(n for n in z.namelist() if n.endswith("markup.bcf"))).decode())
ok("BCF: aponta para o IfcProject do modelo", proj and proj[0] == f.by_type("IfcProject")[0].GlobalId)
snaps = [n for n in z.namelist() if n.endswith(".png")]
ok("BCF: imagem em cada tópico", len(snaps) == len(topicos), f"{len(snaps)}/{len(topicos)}")
XSD = sys.argv[1] if len(sys.argv) > 1 else None
if XSD:
    import xmlschema
    sch = {k: xmlschema.XMLSchema(os.path.join(XSD, k + ".xsd")) for k in ("markup", "visinfo", "version", "project")}
    erros = []
    for n in z.namelist():
        k = "markup" if n.endswith(".bcf") else "visinfo" if n.endswith(".bcfv") else "version" if n == "bcf.version" else "project" if n.endswith(".bcfp") else None
        if k:
            try: sch[k].validate(io.BytesIO(z.read(n)))
            except Exception as ex: erros.append(f"{n}: {str(ex)[:120]}")
    ok("BCF: XML válido contra os XSD oficiais 2.1", not erros, "; ".join(erros[:2]))

json.dump([{"teste": a, "ok": b, "info": c} for a, b, c in res], open(os.path.join(HERE, "resultado_ifc.json"), "w"), ensure_ascii=False, indent=1)
print(f"{sum(r[1] for r in res)} / {len(res)} ok")
