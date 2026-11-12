"""Preco por tabela de referencia (ex.: CEHOP-SE) com memoria de calculo."""

import json
import os

CAMINHO_PADRAO = os.path.join(os.path.dirname(__file__), "..", "dados", "tabelas", "cehop_se_2023.json")


def carregar(caminho=None):
    with open(caminho or CAMINHO_PADRAO, encoding="utf-8") as f:
        return json.load(f)


def _brl(v):
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _num(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _base(item, qtd, memoria):
    un = item["unidade"]
    faixas = item["faixas"]
    if item["modo"] == "cheia":
        for f in faixas:
            if f["ate"] is None or qtd <= f["ate"]:
                v = qtd * f["valor"]
                memoria.append(f"{_num(qtd)} {un} × {_brl(f['valor'])}/{un} (faixa que contém a quantidade) = {_brl(v)}")
                return v
    total, ini = 0.0, 0.0
    for f in faixas:
        fim = qtd if f["ate"] is None else min(qtd, f["ate"])
        parte = fim - ini
        if parte > 0:
            v = parte * f["valor"]
            memoria.append(f"{_num(parte)} {un} × {_brl(f['valor'])}/{un} = {_brl(v)}")
            total += v
        ini = fim
        if f["ate"] is None or qtd <= f["ate"]:
            break
    return total


def _pct_repeticao(regras, teto, n):
    """Percentual acumulado das repeticoes (n = numero de pavimentos iguais)."""
    pct = 0.0
    for k in range(2, n + 1):
        for r in regras:
            if k >= r["de"] and (r["ate"] is None or k <= r["ate"]):
                pct += r["pct"]
                break
    return min(pct, teto - 1)


def calcular(tabela, item_id, quantidade, acrescimos=(), km=0, fator_indice=1.0):
    """acrescimos: nomes de tabela['acrescimos'] ou ('repeticao', n_pavimentos)."""
    item = next((i for i in tabela["itens"] if i["id"] == item_id), None)
    if item is None:
        raise KeyError(f"item '{item_id}' não existe na tabela")
    memoria = [f"{item['descricao']} - {tabela['fonte']}, data-base {tabela['data_base']}"]
    valor = _base(item, quantidade, memoria)
    minimo = item.get("minimo")
    if minimo and valor < minimo:
        memoria.append(f"Valor mínimo aplicado: {_brl(minimo)} (calculado {_brl(valor)})")
        valor = minimo
    ac = tabela.get("acrescimos", {})
    for a in acrescimos:
        if isinstance(a, (tuple, list)) and a[0] == "repeticao":
            p = _pct_repeticao(ac["repeticao"], ac.get("repeticao_teto_multiplo", 5), int(a[1]))
            nome = f"repetição de {int(a[1])} pavimentos"
        else:
            p, nome = ac[a], a.replace("_", " ")
        valor *= 1 + p
        memoria.append(f"Acréscimo {nome}: +{_num(p * 100)}% = {_brl(valor)}")
    if km:
        d = 2 * km * tabela.get("deslocamento_rs_km", 0)
        valor += d
        memoria.append(f"Deslocamento: {_num(km)} km × 2 (ida e volta) × {_brl(tabela.get('deslocamento_rs_km', 0))}/km = {_brl(d)}")
    if fator_indice != 1.0:
        valor *= fator_indice
        memoria.append(f"Fator de correção (digitado): ×{fator_indice:g} = {_brl(valor)}")
    if tabela.get("provisorio"):
        memoria.append("Atenção: valores provisórios, a conferir com o PDF oficial.")
    return {"valor": round(valor, 2), "memoria": memoria,
            "data_base": tabela["data_base"], "provisorio": bool(tabela.get("provisorio"))}
