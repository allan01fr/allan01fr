"""
Parâmetros comerciais da empresa: custo e taxa de venda por perfil, overhead,
impostos, margem, contingência por risco, BDI de fornecimento e deslocamento.

Ficam em dados/parametros.json. Cada proposta guarda uma cópia, para que o preço
de uma proposta antiga não mude quando a empresa reajustar os parâmetros.
"""

import copy
import json
import os
import shutil

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMINHO_PADRAO = os.path.join(RAIZ, "dados", "parametros.json")


def carregar(caminho=None):
    with open(caminho or CAMINHO_PADRAO, encoding="utf-8") as f:
        return json.load(f)


def salvar(params, caminho=None):
    caminho = caminho or CAMINHO_PADRAO
    if os.path.exists(caminho):
        shutil.copyfile(caminho, caminho.replace(".json", ".bak.json"))
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=1)


def mesclar(base, sobre):
    """Completa `sobre` com as chaves que faltam em relação a `base` (recursivo)."""
    saida = copy.deepcopy(base)
    for k, v in (sobre or {}).items():
        if isinstance(v, dict) and isinstance(saida.get(k), dict):
            saida[k] = mesclar(saida[k], v)
        else:
            saida[k] = copy.deepcopy(v)
    return saida


def aliquota_impostos(params):
    """Alíquota total sobre o faturamento de serviços.

    Simples Nacional: a alíquota efetiva informada (o DAS já inclui o ISS).
    Lucro Presumido: PIS + COFINS + IRPJ e CSLL sobre a base presumida de 32% + ISS.
    """
    imp = params["impostos"]
    if imp["regime"] == "simples":
        return float(imp["simples_aliquota"])
    return float(sum(imp["presumido"].values()) + imp["iss"])


def custo_hora_calculado(calc):
    """Custo/h a partir de salário (ou pró-labore), encargos, benefícios e horas produtivas."""
    horas = float(calc.get("horas_produtivas_mes") or 0)
    if horas <= 0:
        return 0.0
    mensal = float(calc.get("salario", 0)) * (1 + float(calc.get("encargos", 0))) + float(calc.get("beneficios", 0))
    return mensal / horas


def overhead_por_hora(params):
    o = params["overhead"]
    horas = float(o.get("horas_faturaveis_mes") or 0)
    return float(o["custo_fixo_mensal"]) / horas if horas > 0 else 0.0
