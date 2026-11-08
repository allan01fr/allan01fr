"""Cargas térmicas do ambiente e dimensionamento do insuflamento."""

from . import psicrometria as psi

# Ganho de calor por pessoa [W] - valores típicos (ASHRAE Fundamentals, cap. 18, tab. 1;
# mesma base da ABNT NBR 16401-1). Confira a tabela da norma para o seu caso.
ATIVIDADES = {
    "Sentado, trabalho leve (escritório)": (70.0, 45.0, 1.1),
    "Escritório, atividade moderada": (75.0, 55.0, 1.2),
    "Em pé, trabalho leve / caminhando devagar": (75.0, 70.0, 1.6),
    "Trabalho leve em bancada": (80.0, 140.0, 2.0),
}


def areas(projeto):
    s = projeto["sala"]
    lat = s["altura"] * s["profundidade"]
    hor = s["largura"] * s["profundidade"]
    return {"esquerda": lat, "direita": lat, "piso": hor, "teto": hor}


def cargas_totais(projeto):
    """Cargas do ambiente [W]: dicionário com parcelas, sensível e latente totais."""
    a = areas(projeto)
    sup = projeto["superficies"]
    parcelas = {}
    for f in projeto["fontes"]:
        parcelas[f.get("nome") or "fonte"] = (float(f["sensivel_w"]), float(f["latente_w"]))
    for parede in ("esquerda", "direita", "piso", "teto"):
        q = float(sup.get("fluxo_" + parede, 0.0)) * a[parede]
        if q:
            parcelas[f"Superfície {parede}"] = (q, 0.0)
    ilum = float(projeto.get("iluminacao_w_m2", 0.0)) * a["piso"]
    if ilum:
        parcelas["Iluminação"] = (ilum, 0.0)
    sens = sum(v[0] for v in parcelas.values())
    lat = sum(v[1] for v in parcelas.values())
    return {"parcelas": parcelas, "sensivel": sens, "latente": lat, "total": sens + lat}


def dimensionar_insuflamento(projeto):
    """Estado de insuflamento que mantém T_alvo/UR_alvo com a vazão informada."""
    c = projeto["condicao"]
    cg = cargas_totais(projeto)
    vazao = float(projeto["insuflamento"]["vazao_m3h"])
    w_amb = psi.umidade_absoluta(c["T_alvo"], c["UR_alvo"])
    t_ins, w_ins = psi.estado_insuflamento(c["T_alvo"], w_amb, cg["sensivel"], cg["latente"], vazao)
    ur_ins = psi.umidade_relativa(t_ins, w_ins)
    return {
        "temperatura": float(t_ins),
        "umidade_abs": float(w_ins),
        "ur_saida": float(ur_ins),
        "ponto_orvalho": float(psi.ponto_orvalho(w_ins)),
        "delta_T": float(c["T_alvo"] - t_ins),
        "capacidade_W": cg["total"],
        "capacidade_btuh": cg["total"] * 3.41214,
        "capacidade_TR": cg["total"] / 3516.85,
        "trocas_hora": vazao / (projeto["sala"]["largura"] * projeto["sala"]["altura"]
                                * projeto["sala"]["profundidade"]),
    }
