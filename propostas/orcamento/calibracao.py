"""
Calibração das produtividades com as horas realizadas.

Ao fechar um projeto, registre as horas reais por atividade. O fator sugerido de
cada atividade é a mediana de  realizado ÷ (estimado sem calibração)  em todos os
registros. Aplicar o fator grava `calibracao` na atividade do catálogo; como a
razão é tomada sobre a estimativa sem calibração, aplicar de novo não acumula.
"""

import json
import os
import statistics

from . import catalogo as ct
from . import parametros as pm

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMINHO_PADRAO = os.path.join(RAIZ, "dados", "historico.json")


def carregar(caminho=None):
    caminho = caminho or CAMINHO_PADRAO
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def salvar(hist, caminho=None):
    with open(caminho or CAMINHO_PADRAO, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=1)


def _calibracao_atual(cat, sid, aid):
    for a in ct.servico(cat, sid)["atividades"]:
        if a["id"] == aid:
            return float(a.get("calibracao", 1.0) or 1.0)
    return 1.0


def registrar(hist, cat, proposta, res, realizados):
    """Acrescenta um registro. `realizados`: {(índice da linha em res['linhas']): horas reais}."""
    regs = []
    for i, l in enumerate(res["linhas"]):
        if i not in realizados or realizados[i] is None:
            continue
        regs.append({
            "servico": l["servico"], "atividade": l["atividade"], "nome": l["nome"],
            "estimado_h": round(l["total_h"], 3),
            "calibracao_usada": l["fatores_det"].get("calibracao", 1.0),
            "realizado_h": float(realizados[i]),
        })
    if not regs:
        raise ValueError("nenhuma hora realizada informada")
    reg = {"proposta": proposta["numero"], "opcao": res["id"], "data": pm.hoje().isoformat(), "registros": regs}
    hist.append(reg)
    return reg


def fatores_sugeridos(cat, hist):
    razoes = {}
    nomes = {}
    for reg in hist:
        for r in reg["registros"]:
            base = r["estimado_h"] / (r.get("calibracao_usada") or 1.0)
            if base <= 0:
                continue
            chave = (r["servico"], r["atividade"])
            razoes.setdefault(chave, []).append(r["realizado_h"] / base)
            nomes[chave] = r.get("nome", r["atividade"])
    saida = []
    for (sid, aid), lista in sorted(razoes.items()):
        try:
            atual = _calibracao_atual(cat, sid, aid)
        except KeyError:
            continue
        saida.append({"servico": sid, "atividade": aid, "nome": nomes[(sid, aid)], "amostras": len(lista),
                      "fator_atual": atual, "fator_sugerido": round(statistics.median(lista), 3)})
    return saida


def aplicar(cat, sugestoes, minimo_amostras=1):
    aplicados = 0
    for s in sugestoes:
        if s["amostras"] < minimo_amostras:
            continue
        for a in ct.servico(cat, s["servico"])["atividades"]:
            if a["id"] == s["atividade"]:
                a["calibracao"] = s["fator_sugerido"]
                aplicados += 1
    return aplicados
