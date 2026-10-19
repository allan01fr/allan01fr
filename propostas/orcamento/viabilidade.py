"""
Estudo de viabilidade para o cliente: CAPEX, OPEX, economia, breakeven, payback, VPL, TIR e LCC.

- Breakeven: quando as contas empatam, ou seja, a economia acumulada (sem desconto) iguala o CAPEX;
  é onde o custo acumulado do sistema atual cruza o da alternativa.
- Payback: quando o projeto se paga, ou seja, a economia acumulada descontada pela TMA devolve o
  investimento com o custo do capital (VPL acumulado = 0).

Linha de base = sistema atual. Pode ser descrita pela capacidade (TR × kW/TR medido × horas ×
fator de carga) ou pelo consumo anual direto. Com o kW/TR de projeto, o estudo mostra também
quanto o sistema consome além do que o projeto original previa e o custo anual dessa perda.

Cada alternativa reduz o consumo (%), pode gerar energia (FV, em kWh/ano) e muda o custo de
manutenção. Os paliativos (manutenção de emergência) são comuns a todas as alternativas: entram
no LCC, mas não no fluxo incremental.

Fluxo da alternativa, ano t (1..horizonte):
    economia_t = economia_energia × (1 + reajuste_energia)^(t-1) + economia_manutenção × (1 + reajuste_manut)^(t-1)
Ano 0 = −CAPEX. O CAPEX pode vir do preço de uma opção da proposta (ex.: o turnkey) mais um extra.

A planilha exportada (exportar_viabilidade.py) refaz estas contas em fórmulas.
"""

import copy
import math

VARIACOES_ECONOMIA = (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3)
VARIACOES_CAPEX = (-0.2, -0.1, 0.0, 0.1, 0.2)
VARIACOES_TARIFA = (-0.2, -0.1, 0.0, 0.1, 0.2)
HORIZONTE_MAX = 30


def padrao():
    return {
        "ativo": False,
        "titulo": "Estudo de viabilidade técnico-econômica",
        "base": {"modo": "tr", "tr": 75.0, "kw_tr_real": 1.30, "kw_tr_projeto": 1.00, "horas_ano": 3000.0,
                 "fator_carga": 0.6, "kwh_ano": 0.0, "tarifa": 0.85, "manutencao_ano": 48000.0, "paliativos": 0.0},
        "financeiro": {"tma": 0.12, "horizonte": 15, "reajuste_energia": 0.05, "reajuste_manutencao": 0.04},
        "alternativas": [],
    }


def nova_alternativa(nome="Alternativa"):
    return {"nome": nome, "descricao": "", "capex": 0.0, "capex_opcao": "", "capex_extra": 0.0,
            "reducao_pct": 0.0, "geracao_kwh": 0.0, "manutencao_ano": None}


def completar(v):
    base = padrao()
    v = copy.deepcopy(v or {})
    for k, val in base.items():
        if k not in v:
            v[k] = copy.deepcopy(val)
    v["base"] = {**base["base"], **v["base"]}
    v["financeiro"] = {**base["financeiro"], **v["financeiro"]}
    v["alternativas"] = [{**nova_alternativa(), **a} for a in v["alternativas"]]
    return v


# ----------------------------------------------------------------------------- base
def consumo_base(b):
    if b["modo"] == "tr":
        return float(b["tr"]) * float(b["kw_tr_real"]) * float(b["horas_ano"]) * float(b["fator_carga"])
    return float(b["kwh_ano"])


def consumo_projeto(b):
    """Consumo previsto pelo projeto original (só no modo TR, com o kW/TR de projeto)."""
    if b["modo"] != "tr" or not float(b.get("kw_tr_projeto") or 0):
        return None
    return float(b["tr"]) * float(b["kw_tr_projeto"]) * float(b["horas_ano"]) * float(b["fator_carga"])


def capex(alt, precos_opcoes=None):
    oid = alt.get("capex_opcao") or ""
    if oid and precos_opcoes and oid in precos_opcoes:
        return float(precos_opcoes[oid]) + float(alt.get("capex_extra") or 0)
    return float(alt.get("capex") or 0)


# ----------------------------------------------------------------------------- matemática financeira
def vpl(fluxo, taxa):
    return sum(f / (1 + taxa) ** t for t, f in enumerate(fluxo))


def tir(fluxo, lo=-0.99, hi=10.0, tol=1e-10):
    """TIR por bisseção; None quando não há troca de sinal (sem retorno ou sem investimento)."""
    if not fluxo or fluxo[0] >= 0 or max(fluxo[1:], default=0) <= 0:
        return None
    f_lo, f_hi = vpl(fluxo, lo), vpl(fluxo, hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(300):
        meio = (lo + hi) / 2
        f_m = vpl(fluxo, meio)
        if abs(f_m) < tol or hi - lo < tol:
            return meio
        if f_lo * f_m < 0:
            hi, f_hi = meio, f_m
        else:
            lo, f_lo = meio, f_m
    return (lo + hi) / 2


def tempo_ate_zerar(fluxo, taxa=None):
    """Anos até o acumulado (descontado, se houver taxa) zerar, interpolando no ano da virada.
    Sem taxa é o breakeven; descontado pela TMA é o payback.
    0 sem investimento; None quando não se paga dentro do horizonte."""
    if fluxo[0] >= 0:
        return 0.0
    acum, anterior = 0.0, None
    for t, f in enumerate(fluxo):
        v = f / (1 + taxa) ** t if taxa is not None else f
        anterior, acum = acum, acum + v
        if t > 0 and anterior < 0 <= acum:
            return (t - 1) + (-anterior) / v
    return None


# ----------------------------------------------------------------------------- estudo
def calcular(v, precos_opcoes=None):
    v = completar(v)
    b, fin = v["base"], v["financeiro"]
    tarifa = float(b["tarifa"])
    i = float(fin["tma"])
    h = max(1, min(int(fin["horizonte"]), HORIZONTE_MAX))
    ge, gm = float(fin["reajuste_energia"]), float(fin["reajuste_manutencao"])
    cb = consumo_base(b)
    cp = consumo_projeto(b)
    manut_base = float(b["manutencao_ano"])
    paliativos = float(b.get("paliativos") or 0)
    fe = [(1 + ge) ** (t - 1) for t in range(1, h + 1)]     # reajuste da energia no ano t
    fm = [(1 + gm) ** (t - 1) for t in range(1, h + 1)]
    fd = [1 / (1 + i) ** t for t in range(1, h + 1)]         # fator de desconto
    vp_energia_base = sum(cb * tarifa * a * d for a, d in zip(fe, fd))
    vp_manut_base = sum(manut_base * a * d for a, d in zip(fm, fd))
    lcc_base = paliativos + vp_energia_base + vp_manut_base

    alternativas = []
    for alt in v["alternativas"]:
        cap = capex(alt, precos_opcoes)
        consumo = max(cb * (1 - float(alt.get("reducao_pct") or 0)) - float(alt.get("geracao_kwh") or 0), 0.0)
        manut = manut_base if alt.get("manutencao_ano") is None else float(alt["manutencao_ano"])
        econ_e1 = (cb - consumo) * tarifa
        econ_m1 = manut_base - manut
        fluxo = [-cap] + [econ_e1 * a + econ_m1 * m for a, m in zip(fe, fm)]
        vp_e = sum(econ_e1 * a * d for a, d in zip(fe, fd))
        vp_m = sum(econ_m1 * m * d for m, d in zip(fm, fd))
        vp = vp_e + vp_m
        be = tempo_ate_zerar(fluxo) if econ_e1 + econ_m1 > 0 else None
        pb = tempo_ate_zerar(fluxo, i) if econ_e1 + econ_m1 > 0 else None
        valor_vpl = vp - cap
        if econ_e1 + econ_m1 <= 0:
            classe = "Sem economia"
        elif be is not None and be <= 2:
            classe = "Quick win"
        elif valor_vpl > 0:
            classe = "Viável"
        else:
            classe = "Inviável financeiramente"
        alternativas.append({
            "nome": alt["nome"], "descricao": alt.get("descricao", ""), "capex": cap,
            "capex_origem": (f"preço da opção {alt['capex_opcao']}" + (" + extra" if alt.get("capex_extra") else ""))
                            if alt.get("capex_opcao") and precos_opcoes and alt["capex_opcao"] in precos_opcoes else "informado",
            "reducao_pct": float(alt.get("reducao_pct") or 0), "geracao_kwh": float(alt.get("geracao_kwh") or 0),
            "consumo": consumo, "manutencao_ano": manut,
            "economia_energia_ano1": econ_e1, "economia_manutencao_ano1": econ_m1, "economia_ano1": econ_e1 + econ_m1,
            "fluxo": fluxo, "vp_economia": vp, "vp_energia": vp_e, "vp_manutencao": vp_m,
            "vpl": valor_vpl, "tir": tir(fluxo) if econ_e1 + econ_m1 > 0 else None,
            "breakeven": be, "breakeven_meses": math.ceil(be * 12) if be is not None else None,
            "payback": pb, "payback_meses": math.ceil(pb * 12) if pb is not None else None,
            "economia_minima": (econ_e1 + econ_m1) * cap / vp if vp > 0 else None,
            "margem_seguranca": vp / cap - 1 if cap > 0 else None,
            "lcc": lcc_base + cap - vp,
            "vs_projeto": consumo / cp - 1 if cp else None,
            "classificacao": classe,
            "sensibilidade": {
                "economia": {d: vp * (1 + d) - cap for d in VARIACOES_ECONOMIA},
                "capex": {d: vp - cap * (1 + d) for d in VARIACOES_CAPEX},
                "tarifa": {d: vp_e * (1 + d) + vp_m - cap for d in VARIACOES_TARIFA},
            },
        })
    return {
        "titulo": v["titulo"], "horizonte": h, "tma": i, "tarifa": tarifa,
        "consumo_base": cb, "consumo_projeto": cp,
        "excesso_vs_projeto": (cb / cp - 1) if cp else None,
        "perda_desempenho": (cb - cp) * tarifa if cp else None,
        "custo_energia_base": cb * tarifa, "manutencao_base": manut_base, "paliativos": paliativos,
        "lcc_base": lcc_base, "alternativas": alternativas,
    }
