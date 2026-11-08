"""Montagem do modelo 2D a partir do projeto e validação dos dados."""

import jax.numpy as jnp

from . import psicrometria as psi
from .sala2d import Sala, Abertura, FonteCalor, Obstaculo, Insuflamento, montar_geometria

def montar_modelo(projeto, malha_cm=None):
    """Converte o projeto em (Sala, Geometria, Insuflamento). Lança ValueError se inválido."""
    p = projeto
    s = p["sala"]
    h = (malha_cm or p["simulacao"]["malha_cm"]) / 100.0
    nx = max(8, int(round(s["largura"] / h)))
    ny = max(8, int(round(s["altura"] / h)))
    sup = dict(p["superficies"])
    sup["fluxo_teto"] = float(sup.get("fluxo_teto", 0.0)) + float(p.get("iluminacao_w_m2", 0.0))
    sala = Sala(
        largura=float(s["largura"]), altura=float(s["altura"]), profundidade=float(s["profundidade"]),
        nx=nx, ny=ny,
        aberturas=tuple(Abertura(a["parede"], float(a["inicio"]), float(a["fim"]), a["tipo"])
                        for a in p["aberturas"]),
        fontes=tuple(FonteCalor(float(f["x0"]), float(f["x1"]), float(f["y0"]), float(f["y1"]),
                                float(f["sensivel_w"]), float(f["latente_w"])) for f in p["fontes"]),
        obstaculos=tuple(Obstaculo(float(o["x0"]), float(o["x1"]), float(o["y0"]), float(o["y1"]))
                         for o in p["obstaculos"]),
        fluxo_esquerda=float(sup["fluxo_esquerda"]), fluxo_direita=float(sup["fluxo_direita"]),
        fluxo_piso=float(sup["fluxo_piso"]), fluxo_teto=float(sup["fluxo_teto"]),
        nu_efetiva=float(p["simulacao"]["nu_efetiva"]),
    )
    geo = montar_geometria(sala)
    i = p["insuflamento"]
    t_ins = float(i["temperatura"])
    ins = Insuflamento(vazao_m3h=jnp.asarray(float(i["vazao_m3h"])),
                       angulo_graus=jnp.asarray(float(i["angulo_graus"])),
                       temperatura=jnp.asarray(t_ins),
                       umidade_abs=psi.umidade_absoluta(t_ins, float(i["ur_saida"])))
    return sala, geo, ins


def validar(projeto):
    """Lista de problemas que impedem ou comprometem a simulação."""
    erros = []
    s = projeto["sala"]
    if min(s["largura"], s["altura"], s["profundidade"]) <= 0:
        erros.append("Dimensões da sala devem ser positivas.")
    tipos = [a["tipo"] for a in projeto["aberturas"]]
    if "insuflamento" not in tipos:
        erros.append("Inclua ao menos uma abertura de insuflamento.")
    if "retorno" not in tipos:
        erros.append("Inclua ao menos uma abertura de retorno.")
    for a in projeto["aberturas"]:
        comp = s["altura"] if a["parede"] in ("esquerda", "direita") else s["largura"]
        if not (0 <= a["inicio"] < a["fim"] <= comp + 1e-9):
            erros.append(f"Abertura {a['tipo']} na parede {a['parede']}: início/fim fora da parede (0 a {comp} m).")
    if abs(float(projeto["insuflamento"]["angulo_graus"])) > 75:
        erros.append("Ângulo do jato deve estar entre -75° e 75°.")
    if not erros:
        try:
            montar_modelo(projeto)
        except ValueError as e:
            erros.append(str(e))
    return erros
