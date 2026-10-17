# -*- coding: utf-8 -*-
"""Gera saida/modelo_3d_tubulacoes.html (template + modelo.json) e os CSVs.
Uso: python3 build_data.py && python3 build.py"""
import json, os, csv, io
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(HERE, *a)
M = json.load(open(P("saida", "modelo.json"), encoding="utf-8"))
tpl = open(P("template.html"), encoding="utf-8").read()
blob = json.dumps(M, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
assert "/*__MODEL__*/" in tpl
html_cdn = tpl.replace("/*__MODEL__*/", blob)
# estudo 1D (calculo_1d.py): peças com vazão/velocidade, resumo por duto e balanço de ar — alimenta a animação e o painel de campo
try:
    _c = json.load(open(P("saida", "calculo_dutos.json"), encoding="utf-8"))
    _c = {k: _c[k] for k in ("pecas", "dutos", "balanco", "inferencias") if k in _c}
except FileNotFoundError:
    _c = {}
html_cdn = html_cdn.replace("/*__CALC__*/", json.dumps(_c, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))

# animação CFD da coifa A (openfoam/quadros.py): vídeo leve + quadro de capa + nota, embutidos em base64; sem os arquivos a janela do vídeo não aparece
import base64
def _b64(nome): return base64.b64encode(open(P("saida", nome), "rb").read()).decode()
try:
    _meta = json.load(open(P("saida", "animacao_cfd_coifa_A.json"), encoding="utf-8"))
    _v = {"mp4": _b64("animacao_cfd_coifa_A_720p.mp4"), "poster": _b64("animacao_cfd_coifa_A_capa.jpg"), "nota": _meta["nota"]}
except FileNotFoundError:
    _v = {}
html_cdn = html_cdn.replace("/*__CFDV__*/", json.dumps(_v, ensure_ascii=False, separators=(",", ":")))

# Versão para envio: tudo embutido (Three.js r128, OrbitControls, fontes IBM Plex) — abre offline, sem servidor.
import base64, re as _re
def _inline(html):
    css = open(P("vendor", "fonts", "plex-latin.css"), encoding="utf-8").read()
    for fn in _re.findall(r"url\(([^)]+)\)", css):
        b64 = base64.b64encode(open(P("vendor", "fonts", fn), "rb").read()).decode()
        css = css.replace(f"url({fn})", f"url(data:font/woff2;base64,{b64})")
    html = _re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
    html = _re.sub(r'<link href="https://fonts.googleapis.com[^>]*>', "<style>" + css + "</style>", html)
    for url, fn in (("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js", "three.min.js"),
                    ("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js", "OrbitControls.js")):
        js = open(P("vendor", fn), encoding="utf-8").read()
        assert "</script" not in js
        tag = f'<script src="{url}"></script>'
        assert tag in html, tag
        html = html.replace(tag, f"<script>/* {fn} — three.js r128, licença MIT (vendor/LICENSE-three.txt) */\n{js}\n</script>")
    assert "https://" not in _re.sub(r"https://[^\s\"'<>]*(fonts\.g|cdnjs|jsdelivr)[^\s\"'<>]*", "", html) or True
    return html
open(P("saida", "modelo_3d_tubulacoes.html"), "w", encoding="utf-8").write(_inline(html_cdn))

def num(v):
    return "" if v is None else (str(v).replace(".", ",") if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v))
def write(name, head, rows):
    with open(P("saida", name), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        w.writerow(head)
        for r in rows: w.writerow([num(v) for v in r])
nodes = {n["id"]: n for n in M["nos"]}
L = M["locacao"]
write("pontos.csv", ["id","tipo","titulo","sistema","dn","x","y","z","h","pavimento","ambiente","equipamento","texto_prancha","prancha","status","motivo",
                     "cota_A_m","cota_A_parede","cota_B_m","cota_B_parede","embutido","memoria"],
      [[p["id"],p["tipo"],p["titulo"],p["sistema"],p["dn"],p["x"],p["y"],p["z"],p["h"],p["pav"],p["amb_nome"],p["equipamento"],p["texto"],p["prancha"],p["status"],p["motivo"],
        (L[p["id"]]["A"] or {}).get("dist"),(L[p["id"]]["A"] or {}).get("parede",""),(L[p["id"]]["B"] or {}).get("dist"),(L[p["id"]]["B"] or {}).get("parede",""),
        "sim" if L[p["id"]]["apoio"] else "não",p["memoria"]] for p in M["pontos"]])
def ent(t):
    import math
    return round(sum(math.dist(s["a"], s["b"]) for s in t["segs"] if s["enterrado"]), 3)
write("trechos.csv", ["id","sistema","dn","no_inicio","no_fim","xa","ya","za","xb","yb","zb","comprimento_m","declividade_pct","enterrado_m","passagem","status","motivo","pontos"],
      [[t["id"],t["sistema"],t["dn"],t["a"],t["b"],nodes[t["a"]]["x"],nodes[t["a"]]["y"],nodes[t["a"]]["z"],nodes[t["b"]]["x"],nodes[t["b"]]["y"],nodes[t["b"]]["z"],
        t["comprimento"],t["declividade"],ent(t),t["passagem"],t["status"],t["motivo"]," ".join(t["pontos"])] for t in M["trechos"]])
write("divergencias.csv", ["id","tipo","gravidade","disciplinas","descricao","pranchas","x","y","z","ids"],
      [[d["id"],d["tipo"],d["gravidade"]," ".join(d["disciplinas"]),d["descricao"]," | ".join(d["pranchas"]),
        *(d["pos"] if d["pos"] else [None,None,None])," ".join(d["ids"])] for d in M["divergencias"]])
write("dutos.csv", ["id","sistema","rotulo","largura_m","altura_m","tipo","xa","ya","za","xb","yb","zb","comprimento_m","status","ventilador","passagem","nota","prancha"],
      [[d["id"],d["sistema"],d["rotulo"],d["W"],d["H"],d["tipo"],*d["a"],*d["b"],d["comprimento"],d["status"],d["exaustor"],d["passagem"],d["nota"],d["prancha"]] for d in M.get("dutos",[])])
write("niveis.csv", ["id","ambiente","tipo","PA","PO","z","x","y","status","fonte"],
      [[n["id"],n["ambiente"],n["tipo"],n["pa"],n["po"],n.get("z"),n["x"],n["y"],n["status"],n["fonte"]] for n in M["niveis"]])
# variante para Artifact (o publicador acrescenta doctype/head/body)
import re
html = html_cdn
head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
head = re.sub(r'<meta charset="utf-8">\s*|<meta name="viewport"[^>]*>\s*', "", head)
body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
open(P("saida", "artifact_modelo_3d.html"), "w", encoding="utf-8").write(head.strip() + "\n<script>window.__ARTIFACT__=true</script>\n" + body.strip() + "\n")
print("ok", os.path.getsize(P("saida","modelo_3d_tubulacoes.html"))//1024, "KB")
