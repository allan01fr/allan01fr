"""Critérios de conforto e verificação de conformidade do resultado."""

CRITERIOS_PADRAO = {
    "pmv_max": 0.5,           # ISO 7730 categoria B: -0,5 < PMV < +0,5
    "ppd_max": 10.0,          # ISO 7730 categoria B
    "dr_max": 20.0,           # ISO 7730 categoria B: DR < 20 %
    "dT_vertical_max": 3.0,   # ISO 7730 categoria B: < 3 K entre 0,1 e 1,1 m
    "ur_min": 0.35,           # faixa usual de conforto (ver NBR 16401-2)
    "ur_max": 0.65,
    "vel_max": 0.25,          # m/s - referência usual de projeto; ajuste à norma aplicável
}


def conformidade(resultado, criterios):
    ind = resultado["indicadores"]
    c = criterios
    linhas = [
        ("PMV médio na zona ocupada", ind["PMV_medio"], f"entre -{c['pmv_max']} e +{c['pmv_max']}",
         abs(ind["PMV_medio"]) <= c["pmv_max"], "ISO 7730 / NBR 16401-2"),
        ("PPD médio [%]", ind["PPD_medio"], f"≤ {c['ppd_max']}", ind["PPD_medio"] <= c["ppd_max"], "ISO 7730"),
        ("Risco de corrente de ar DR máximo [%]", ind["DR_max"], f"≤ {c['dr_max']}",
         ind["DR_max"] <= c["dr_max"], "ISO 7730"),
        ("Estratificação 0,1-1,1 m [K]", ind["dT_vertical"], f"≤ {c['dT_vertical_max']}",
         abs(ind["dT_vertical"]) <= c["dT_vertical_max"], "ISO 7730"),
        ("Umidade relativa média [%]", ind["UR_ocupada"] * 100, f"{c['ur_min'] * 100:.0f} a {c['ur_max'] * 100:.0f}",
         c["ur_min"] <= ind["UR_ocupada"] <= c["ur_max"], "NBR 16401-2"),
        ("Velocidade máxima do ar [m/s]", ind["vel_max_ocupada"], f"≤ {c['vel_max']}",
         ind["vel_max_ocupada"] <= c["vel_max"], "critério de projeto"),
    ]
    return [{"critério": a, "resultado": round(b, 2), "limite": l, "atende": ok, "referência": r}
            for a, b, l, ok, r in linhas]
