"""
Formas de cobrança das fases de obra: % do valor da obra, pacote de horas e taxa de desempenho.

% da obra (honorário sobre a base = valor global estimado da obra):
- "medicoes": % × valor de cada medição; a proposta mostra o total estimado = % × base;
- "fixo_global": valor fixo = % × base, faturado na proporção das medições;
- "fixo_mais_medicoes": parcela fixa (mobilização e planejamento) + % × cada medição.
As medições são projetadas mês a mês por uma curva S, (1 − cos πt) ÷ 2, ou linear.

Pacote de horas (fiscalização e planejamento):
- "mensal": h/mês × meses, mensalidade fixa;
- "total": N horas sob demanda dentro de um prazo de validade, pagas em parcelas.
Taxa do pacote = taxa média de venda do mix de perfis × (1 − desconto). Sem horas informadas,
o pacote usa as horas calculadas dos serviços da fase.

Taxa de desempenho (variável, fora do preço): participação na economia em relação ao valor
global estimado, % dos honorários por semana de antecipação e bônus por retrabalho dentro da
meta, limitada a um teto. O cenário informado dá o potencial.
"""

import math


def _pct(p):
    v = round(float(p) * 100, 2)
    return (f"{v:.0f}" if v == int(v) else f"{v:.2f}".rstrip("0").replace(".", ",")) + "%"


# ----------------------------------------------------------------------------- % da obra
def curva_medicoes(total, meses, curva="s"):
    """Valor medido em cada mês; a soma fecha exatamente o total."""
    n = max(1, int(meses or 1))
    if curva == "linear":
        acum = [k / n for k in range(n + 1)]
    else:
        acum = [(1 - math.cos(math.pi * k / n)) / 2 for k in range(n + 1)]
    valores = [total * (acum[k + 1] - acum[k]) for k in range(n)]
    valores[-1] = total - sum(valores[:-1])
    return valores


def honorario_percentual(cfg, base, meses, curva="s"):
    pct = float(cfg["pct"])
    forma = cfg.get("forma", "medicoes")
    sobre_medicoes = pct * base
    if forma == "fixo_global":
        fixo, estimado = sobre_medicoes, 0.0
    elif forma == "fixo_mais_medicoes":
        fixo, estimado = float(cfg.get("parcela_fixa") or 0), sobre_medicoes
    else:
        fixo, estimado = 0.0, sobre_medicoes
    medicoes = curva_medicoes(base, meses, curva)
    faturamento = [{"mes": k + 1, "medicao": m, "honorario": pct * m + (fixo if forma == "fixo_mais_medicoes" and k == 0 else 0.0)}
                   for k, m in enumerate(medicoes)]
    return {"pct": pct, "forma": forma, "base": base, "parcela_fixa": fixo if forma == "fixo_mais_medicoes" else 0.0,
            "fixo": fixo, "estimado": estimado, "total": fixo + estimado, "faturamento": faturamento}


def marcos_percentual(hp):
    texto_med = (f"mensalmente, {_pct(hp['pct'])} sobre o valor de cada medição aprovada da obra, contra apresentação "
                 "de nota fiscal")
    if hp["forma"] == "fixo_global":
        return [{"marco": "em parcelas mensais proporcionais ao avanço físico-financeiro da obra (medições aprovadas), "
                          "contra apresentação de nota fiscal", "pct": 1.0}]
    if hp["forma"] == "fixo_mais_medicoes" and hp["total"] > 0 and hp["parcela_fixa"] > 0:
        p_fixo = round(hp["parcela_fixa"] / hp["total"], 4)
        return [{"marco": "na mobilização, referente ao planejamento inicial da obra (parcela fixa)", "pct": p_fixo},
                {"marco": texto_med, "pct": round(1 - p_fixo, 4)}]
    return [{"marco": texto_med, "pct": 1.0}]


# ----------------------------------------------------------------------------- pacote de horas
def mix_perfis(horas_perfil, mix_padrao):
    """Proporção de horas por perfil: a dos serviços da fase, ou o mix padrão dos parâmetros."""
    total = sum(horas_perfil.values())
    if total > 0:
        return {p: h / total for p, h in horas_perfil.items()}
    soma = sum(mix_padrao.values()) or 1
    return {p: mix_padrao.get(p, 0) / soma for p in horas_perfil}


def pacote(cfg, horas_servicos, mix_padrao, custo_h, taxa_h):
    total_serv = sum(horas_servicos.values())
    mix = mix_perfis(horas_servicos, mix_padrao)
    if cfg.get("forma", "mensal") == "mensal":
        meses = max(1, int(cfg.get("meses") or 1))
        horas_mes = float(cfg.get("horas_mes") or 0) or total_serv / meses
        horas, parcelas = horas_mes * meses, meses
    else:
        horas = float(cfg.get("horas") or 0) or total_serv
        meses = max(1, int(cfg.get("validade_meses") or 1))
        horas_mes, parcelas = horas / meses, max(1, int(cfg.get("parcelas") or 1))
    taxa_cheia = sum(mix[p] * taxa_h[p] for p in mix)
    desconto = float(cfg.get("desconto") or 0)
    taxa = taxa_cheia * (1 - desconto)
    honorarios = horas * taxa
    return {"forma": cfg.get("forma", "mensal"), "horas": horas, "horas_mes": horas_mes, "meses": meses,
            "parcelas": parcelas, "mix": mix, "horas_perfil": {p: horas * mix[p] for p in mix},
            "taxa_cheia": taxa_cheia, "desconto": desconto, "taxa": taxa, "honorarios": honorarios,
            "parcela": honorarios / parcelas, "custo_medio_h": sum(mix[p] * custo_h[p] for p in mix),
            "taxa_excedente": taxa_cheia * (1 + float(cfg.get("excedente_pct") or 0)),
            "acumula_saldo": bool(cfg.get("acumula_saldo")), "validade_meses": int(cfg.get("validade_meses") or 0)}


def marcos_pacote(pk):
    if pk["forma"] == "mensal":
        return [{"marco": f"em {pk['meses']} parcelas mensais iguais (pacote de {pk['horas_mes']:.0f} h/mês), contra "
                          "apresentação de nota fiscal e do relatório de horas do mês", "pct": 1.0}]
    return [{"marco": f"em {pk['parcelas']} parcelas mensais iguais a partir da assinatura (pacote de {pk['horas']:.0f} h "
                      f"válido por {pk['meses']} meses), contra apresentação de nota fiscal", "pct": 1.0}]


# ----------------------------------------------------------------------------- taxa de desempenho
def taxa_desempenho(cfg, honorario, base_global):
    c = cfg.get("cenario", {})
    economia = float(cfg["economia_pct"]) * float(c.get("economia", 0)) * base_global
    prazo = float(cfg["prazo_pct_semana"]) * honorario * float(c.get("dias_antecipados", 0)) / 7
    retrabalho = float(cfg["retrabalho_bonus_pct"]) * honorario if c.get("retrabalho_ok") else 0.0
    teto = float(cfg["teto_pct"]) * honorario
    bruto = economia + prazo + retrabalho
    return {"economia": economia, "prazo": prazo, "retrabalho": retrabalho, "bruto": bruto, "teto": teto,
            "potencial": min(bruto, teto), "limitado": bruto > teto, "base_global": base_global, "honorario": honorario}
