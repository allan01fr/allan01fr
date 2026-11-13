"""Simulação do projeto em blocos de tempo e estudo de independência de malha."""

import time

import numpy as np
import jax

from . import psicrometria as psi
from .cargas import cargas_totais
from .montagem import montar_modelo, plano_de_tempo
from .sala2d import (estado_inicial, simular, indicadores,
                     Medias)

def simular_projeto(projeto, progresso=None, malha_cm=None):
    """Roda a simulação em blocos de ~60 s (para mostrar progresso).

    progresso(fração, mensagem) é chamado a cada bloco.
    Retorna dicionário com campos médios (numpy), indicadores (float) e verificações.
    """
    p = projeto
    sala, geo, ins = montar_modelo(p, malha_cm)
    c = p["condicao"]
    dt, passos_bloco, n_bloco, t_bloco, n_blocos, n_media, _, v_face = plano_de_tempo(sala, geo, p)

    rodar = jax.jit(lambda e: simular(sala, geo, ins, e, t_bloco, dt, t_bloco, passos_por_bloco=passos_bloco))
    estado = estado_inicial(sala, c["T_alvo"], float(psi.umidade_absoluta(c["T_alvo"], c["UR_alvo"])))
    soma = None
    t0 = time.time()
    for k in range(n_blocos):
        estado, med = rodar(estado)
        if k >= n_blocos - n_media:
            soma = med if soma is None else Medias(*(a + b for a, b in zip(soma, med)))
        if progresso is not None:
            progresso((k + 1) / n_blocos, f"{(k + 1) * t_bloco / 60:.0f} de {n_blocos * t_bloco / 60:.0f} min simulados")
    medias = Medias(*(a / n_media for a in soma))
    ind = indicadores(sala, geo, ins, medias, met=c["met"], clo=c["clo"])
    cg = cargas_totais(p)

    campos = {k: np.asarray(v) for k, v in ind.pop("campos").items()}
    indf = {k: float(v) for k, v in ind.items()}
    erro_sens = (indf["capacidade_sensivel_W"] - cg["sensivel"]) / max(cg["sensivel"], 1.0)
    erro_lat = (indf["capacidade_latente_W"] - cg["latente"]) / max(cg["latente"], 1.0) if cg["latente"] > 0 else 0.0
    return {
        "indicadores": indf,
        "T": np.asarray(medias.T), "W": np.asarray(medias.W), "vel": np.asarray(medias.vel),
        "PMV": campos["PMV"], "DR": campos["DR"], "UR": campos["UR"],
        "u": np.asarray(estado.u), "v": np.asarray(estado.v),
        "ocupada": np.asarray(geo.ocupada), "solido": np.asarray(geo.solido_c),
        "malha": (sala.nx, sala.ny, sala.dx, sala.dy),
        "dt": dt, "tempo_simulado": n_blocos * t_bloco, "tempo_cpu": time.time() - t0,
        "erro_balanco_sensivel": erro_sens, "erro_balanco_latente": erro_lat,
        "v_face": v_face,
    }


def estudo_malha(projeto, malhas_cm=(10.0, 5.0), progresso=None):
    """Roda o mesmo caso em duas malhas e compara os principais indicadores."""
    res = []
    for i, m in enumerate(malhas_cm):
        cb = None if progresso is None else (lambda f, msg, i=i, m=m: progresso((i + f) / len(malhas_cm), f"malha {m:g} cm: {msg}"))
        res.append(simular_projeto(projeto, cb, malha_cm=m))
    chaves = ["T_ocupada", "UR_ocupada", "vel_media_ocupada", "PMV_medio", "DR_max", "dT_vertical"]
    tabela = []
    for k in chaves:
        a, b = res[0]["indicadores"][k], res[-1]["indicadores"][k]
        tabela.append({"indicador": k, f"malha {malhas_cm[0]:g} cm": a, f"malha {malhas_cm[-1]:g} cm": b,
                       "diferença": b - a})
    return res, tabela
