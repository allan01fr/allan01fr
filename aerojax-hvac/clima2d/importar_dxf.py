"""
Importação de desenhos DXF (AutoCAD, Revit, DraftSight, LibreCAD, QCAD...).

Convenção de layers (o nome só precisa CONTER a palavra, sem diferenciar maiúsculas;
ex.: "HVAC-INSUFLAMENTO" funciona):

    AMBIENTE      contorno do ambiente (polilinha fechada ou linhas)
    INSUFLAMENTO  difusor/grelha de insuflamento
    RETORNO       grelha de retorno
    PESSOA        uma entidade (retângulo, círculo ou bloco) por pessoa ou posto
    EQUIPAMENTO   equipamento que dissipa calor
    OBSTACULO     móveis e outros sólidos (OBSTÁCULO também é aceito)

Dois tipos de desenho:

- CORTE (vista vertical): x = horizontal, y = altura. Tudo é lido na posição desenhada.
  Aberturas devem ser desenhadas sobre a parede (linha ou retângulo fino junto ao contorno).
- PLANTA (vista de cima): o modelo 2D é um corte da planta ao longo do eixo escolhido
  (x ou y). Alturas não existem na planta, então vêm de parâmetros (pé-direito, faixa do
  difusor, altura das pessoas etc.). Difusores junto às paredes perpendiculares ao corte
  viram aberturas laterais; difusores no interior do ambiente viram difusores de teto.

Unidades: lidas do cabeçalho do DXF ($INSUNITS). Se ausente, desenhos com mais de
100 unidades são considerados em milímetros.
"""

import os
import tempfile

import ezdxf
from ezdxf import bbox as ezbbox

CAMADAS = {
    "ambiente": ("AMBIENTE",),
    "insuflamento": ("INSUFLAMENTO",),
    "retorno": ("RETORNO",),
    "pessoa": ("PESSOA",),
    "equipamento": ("EQUIPAMENTO",),
    "obstaculo": ("OBSTACULO", "OBSTÁCULO"),
}

_UNIDADES = {1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0, 14: 0.1}


def ler_dxf(conteudo: bytes):
    """Abre DXF a partir de bytes (upload) ou caminho."""
    if isinstance(conteudo, (str, os.PathLike)):
        return ezdxf.readfile(conteudo)
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        f.write(conteudo)
        caminho = f.name
    try:
        return ezdxf.readfile(caminho)
    finally:
        os.unlink(caminho)


def _classificar(layer):
    nome = layer.upper()
    for chave, palavras in CAMADAS.items():
        if any(p in nome for p in palavras):
            return chave
    return None


def extrair_caixas(doc):
    """Agrupa as entidades do model space por categoria; retorna caixas (x0, y0, x1, y1) e escala."""
    msp = doc.modelspace()
    caixas = {k: [] for k in CAMADAS}
    for e in msp:
        cat = _classificar(e.dxf.layer)
        if cat is None:
            continue
        ext = ezbbox.extents([e])
        if not ext.has_data:
            continue
        caixas[cat].append((ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y))
    if not caixas["ambiente"]:
        raise ValueError("Nenhuma entidade no layer AMBIENTE. Desenhe o contorno do ambiente nesse layer.")
    ux = min(c[0] for c in caixas["ambiente"])
    uy = min(c[1] for c in caixas["ambiente"])
    vx = max(c[2] for c in caixas["ambiente"])
    vy = max(c[3] for c in caixas["ambiente"])
    unid = doc.header.get("$INSUNITS", 0)
    if unid in _UNIDADES:
        escala = _UNIDADES[unid]
    else:
        escala = 0.001 if max(vx - ux, vy - uy) > 100 else 1.0
    # Converte para metros com origem no canto inferior esquerdo do ambiente
    for k in caixas:
        caixas[k] = [((a - ux) * escala, (b - uy) * escala, (c - ux) * escala, (d - uy) * escala)
                     for a, b, c, d in caixas[k]]
    return caixas, ((vx - ux) * escala, (vy - uy) * escala)


def _parede_mais_proxima(c, L, H, tol):
    x0, y0, x1, y1 = c
    dist = {"esquerda": x0, "direita": L - x1, "piso": y0, "teto": H - y1}
    parede = min(dist, key=dist.get)
    return parede if dist[parede] <= tol else None


def _limitar(v, a, b):
    return max(a, min(b, v))


def importar_corte(conteudo, profundidade=4.0, tolerancia=0.25, carga_pessoa=(70.0, 45.0),
                   carga_equipamento=150.0):
    """Lê um CORTE em DXF. Retorna (dados parciais do projeto, avisos)."""
    doc = ler_dxf(conteudo)
    cx, (L, H) = extrair_caixas(doc)
    avisos = []
    aberturas = []
    for tipo in ("insuflamento", "retorno"):
        for c in cx[tipo]:
            parede = _parede_mais_proxima(c, L, H, tolerancia)
            if parede is None:
                avisos.append(f"{tipo} em ({c[0]:.2f}, {c[1]:.2f}) m não está junto a nenhuma parede: ignorado.")
                continue
            ini, fim = (c[1], c[3]) if parede in ("esquerda", "direita") else (c[0], c[2])
            comp = H if parede in ("esquerda", "direita") else L
            aberturas.append({"parede": parede, "inicio": round(_limitar(ini, 0, comp), 3),
                              "fim": round(_limitar(fim, 0, comp), 3), "tipo": tipo})
    fontes = []
    for i, c in enumerate(cx["pessoa"]):
        fontes.append({"nome": f"Pessoa {i + 1}", "x0": round(c[0], 3), "x1": round(c[2], 3),
                       "y0": round(max(c[1], 0), 3), "y1": round(c[3], 3),
                       "sensivel_w": carga_pessoa[0], "latente_w": carga_pessoa[1]})
    for i, c in enumerate(cx["equipamento"]):
        fontes.append({"nome": f"Equipamento {i + 1}", "x0": round(c[0], 3), "x1": round(c[2], 3),
                       "y0": round(max(c[1], 0), 3), "y1": round(c[3], 3),
                       "sensivel_w": carga_equipamento, "latente_w": 0.0})
    obst = [{"nome": f"Obstáculo {i + 1}", "x0": round(c[0], 3), "x1": round(c[2], 3),
             "y0": round(c[1], 3), "y1": round(c[3], 3)} for i, c in enumerate(cx["obstaculo"])]
    if fontes:
        avisos.append("Cargas de pessoas/equipamentos preenchidas com valores padrão: confira na aba Cargas.")
    return {"sala": {"largura": round(L, 3), "altura": round(H, 3), "profundidade": profundidade},
            "aberturas": aberturas, "fontes": fontes, "obstaculos": obst}, avisos


def importar_planta(conteudo, eixo="x", pe_direito=2.8, faixa_parede_insuflamento=(2.35, 2.45),
                    faixa_parede_retorno=(2.55, 2.75), altura_pessoa=1.2, faixa_equipamento=(0.75, 0.95),
                    faixa_obstaculo=(0.70, 0.75), tolerancia=0.25, carga_pessoa=(70.0, 45.0),
                    carga_equipamento=150.0, largura_minima=0.3):
    """Lê uma PLANTA em DXF e gera o corte ao longo do `eixo` ('x' ou 'y').

    Retorna (dados parciais do projeto, avisos, caixas em planta para pré-visualização).
    """
    doc = ler_dxf(conteudo)
    cx, (Lx, Ly) = extrair_caixas(doc)
    avisos = []
    if eixo == "x":
        L, D = Lx, Ly
        ao_longo = lambda c: (c[0], c[2])
        transv = lambda c: (c[1], c[3])
    else:
        L, D = Ly, Lx
        ao_longo = lambda c: (c[1], c[3])
        transv = lambda c: (c[0], c[2])

    aberturas = []
    for tipo, faixa in (("insuflamento", faixa_parede_insuflamento), ("retorno", faixa_parede_retorno)):
        for c in cx[tipo]:
            a0, a1 = ao_longo(c)
            t0, t1 = transv(c)
            if a0 <= tolerancia:
                aberturas.append({"parede": "esquerda", "inicio": faixa[0], "fim": faixa[1], "tipo": tipo})
            elif L - a1 <= tolerancia:
                aberturas.append({"parede": "direita", "inicio": faixa[0], "fim": faixa[1], "tipo": tipo})
            elif t0 <= tolerancia or D - t1 <= tolerancia:
                avisos.append(f"{tipo} na parede paralela ao corte (posição {a0:.2f}-{a1:.2f} m) não cabe "
                              f"no corte ao longo de {eixo}: ignorado. Use o outro eixo de corte.")
            else:
                aberturas.append({"parede": "teto", "inicio": round(a0, 3), "fim": round(a1, 3), "tipo": tipo})

    def faixa_x(c):
        a0, a1 = ao_longo(c)
        if a1 - a0 < largura_minima:
            m = 0.5 * (a0 + a1)
            a0, a1 = m - largura_minima / 2, m + largura_minima / 2
        return round(_limitar(a0, 0, L), 3), round(_limitar(a1, 0, L), 3)

    # Pessoas que caem na mesma faixa do corte viram uma única fonte ("N pessoas")
    grupos = {}
    for c in cx["pessoa"]:
        grupos[faixa_x(c)] = grupos.get(faixa_x(c), 0) + 1
    fontes = []
    for (x0, x1), n in sorted(grupos.items()):
        fontes.append({"nome": f"{n} pessoa(s)", "x0": x0, "x1": x1, "y0": 0.0, "y1": altura_pessoa,
                       "sensivel_w": n * carga_pessoa[0], "latente_w": n * carga_pessoa[1]})
    for i, c in enumerate(cx["equipamento"]):
        x0, x1 = faixa_x(c)
        fontes.append({"nome": f"Equipamento {i + 1}", "x0": x0, "x1": x1, "y0": faixa_equipamento[0],
                       "y1": faixa_equipamento[1], "sensivel_w": carga_equipamento, "latente_w": 0.0})
    obst = []
    for i, c in enumerate(cx["obstaculo"]):
        x0, x1 = faixa_x(c)
        obst.append({"nome": f"Obstáculo {i + 1}", "x0": x0, "x1": x1,
                     "y0": faixa_obstaculo[0], "y1": faixa_obstaculo[1]})
    avisos.append("Planta não tem alturas: confira alturas de difusores, pessoas, equipamentos e móveis.")
    if fontes:
        avisos.append("Cargas de pessoas/equipamentos preenchidas com valores padrão: confira na aba Cargas.")
    dados = {"sala": {"largura": round(L, 3), "altura": pe_direito, "profundidade": round(D, 3)},
             "aberturas": aberturas, "fontes": fontes, "obstaculos": obst}
    return dados, avisos, {"caixas": cx, "dimensoes": (Lx, Ly)}


def figura_planta(previa, eixo="x"):
    """Desenho da planta importada com a direção do corte."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    cx, (Lx, Ly) = previa["caixas"], previa["dimensoes"]
    fig, ax = plt.subplots(figsize=(7, 7 * Ly / Lx * 0.9 + 0.8))
    ax.add_patch(Rectangle((0, 0), Lx, Ly, fill=False, lw=2))
    estilos = {"insuflamento": "tab:blue", "retorno": "tab:red", "pessoa": "tab:orange",
               "equipamento": "tab:purple", "obstaculo": "0.5"}
    for cat, cor in estilos.items():
        for i, (a, b, c, d) in enumerate(cx[cat]):
            ax.add_patch(Rectangle((a, b), max(c - a, 0.05), max(d - b, 0.05), color=cor, alpha=0.7,
                                   label=cat if i == 0 else None))
    if eixo == "x":
        ax.annotate("", xy=(Lx, Ly / 2), xytext=(0, Ly / 2), arrowprops=dict(arrowstyle="->", lw=2, ls="--"))
    else:
        ax.annotate("", xy=(Lx / 2, Ly), xytext=(Lx / 2, 0), arrowprops=dict(arrowstyle="->", lw=2, ls="--"))
    ax.set_aspect("equal")
    ax.set_xlim(-0.3, Lx + 0.3)
    ax.set_ylim(-0.3, Ly + 0.3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8, frameon=False)
    ax.set_title(f"Planta importada - seta: direção do corte (eixo {eixo})")
    fig.tight_layout()
    return fig


def gerar_exemplos(pasta):
    """Cria DXFs de exemplo (planta e corte de um escritório) seguindo a convenção de layers."""
    os.makedirs(pasta, exist_ok=True)

    def ret(msp, x0, y0, x1, y1, layer):
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})

    # Corte em metros
    doc = ezdxf.new(units=6)
    msp = doc.modelspace()
    ret(msp, 0, 0, 5, 2.8, "AMBIENTE")
    msp.add_line((0, 2.35), (0, 2.45), dxfattribs={"layer": "INSUFLAMENTO"})
    msp.add_line((0, 2.55), (0, 2.75), dxfattribs={"layer": "RETORNO"})
    ret(msp, 2.8, 0, 3.2, 1.2, "PESSOA")
    ret(msp, 3.6, 0.75, 3.9, 0.85, "EQUIPAMENTO")
    ret(msp, 3.3, 0.70, 4.3, 0.75, "OBSTACULO")
    doc.saveas(os.path.join(pasta, "corte_escritorio.dxf"))

    # Planta em milímetros (como costuma vir de arquitetura)
    doc = ezdxf.new(units=4)
    msp = doc.modelspace()
    ret(msp, 0, 0, 5000, 4000, "AMBIENTE")
    ret(msp, 0, 1600, 80, 2400, "INSUFLAMENTO")        # split na parede esquerda
    ret(msp, 0, 1600, 80, 2400, "RETORNO")
    msp.add_circle((3000, 1300), 250, dxfattribs={"layer": "PESSOA"})
    msp.add_circle((3000, 2700), 250, dxfattribs={"layer": "PESSOA"})
    ret(msp, 3600, 1100, 3900, 1500, "EQUIPAMENTO")
    ret(msp, 3300, 900, 4300, 3100, "OBSTACULO")        # mesa
    doc.saveas(os.path.join(pasta, "planta_escritorio.dxf"))
