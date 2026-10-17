# Leitor do internal.vtu (XML ascii) escrito por `foamToVTK -ascii`: centros de célula (média dos vértices), caixa envolvente de cada célula,
# campos por célula e o instante gravado no cabeçalho (o nome da pasta do foamToVTK traz o índice do passo, não o tempo).
import re, numpy as np

def _array(txt, nome):
    m = re.search(r"<DataArray[^>]*Name='%s'[^>]*>(.*?)</DataArray>" % re.escape(nome), txt, re.S)
    return np.array(m.group(1).split(), dtype=float) if m else None

def tempo(path):
    """Instante (s) gravado no comentário inicial do .vtu: <!-- case='x' region='region0' time='5' index='100' -->"""
    with open(path) as f: cab = f.read(400)
    return float(re.search(r"time='([^']+)'", cab).group(1))

def ler_completo(path):
    txt = open(path).read()
    i_cd = txt.index("<CellData"); i_pd = txt.index("<PointData") if "<PointData" in txt else len(txt)
    pts = _array(txt, "Points").reshape(-1, 3)
    conn = _array(txt, "connectivity").astype(np.int64); off = _array(txt, "offsets").astype(np.int64)
    ini = np.concatenate([[0], off[:-1]])
    P = pts[conn]
    # média dos vértices por célula (vetorizada)
    cel = np.repeat(np.arange(len(off)), off - ini)
    cx = np.zeros((len(off), 3)); np.add.at(cx, cel, P)
    cx /= (off - ini)[:, None]
    lo = np.minimum.reduceat(P, ini, axis=0); hi = np.maximum.reduceat(P, ini, axis=0)
    campos = {}
    cd = txt[i_cd:i_pd]
    for nome in re.findall(r"<DataArray[^>]*Name='(\w+)'", cd):
        a = _array(cd, nome); campos[nome] = a.reshape(len(off), -1) if a.size != len(off) else a
    return dict(centros=cx, lo=lo, hi=hi, campos=campos, pontos=pts)

def ler(path):
    r = ler_completo(path)
    return r["centros"], r["campos"], r["pontos"]
