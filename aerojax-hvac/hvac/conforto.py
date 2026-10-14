"""
Índices de conforto térmico em JAX (diferenciáveis).

- PMV / PPD conforme ISO 7730:2005 (adotada pela ABNT NBR 16401-2 e ASHRAE 55)
- Risco de corrente de ar (Draught Rate, DR) conforme ISO 7730:2005, eq. 6

Unidades: temperaturas em °C, velocidade do ar em m/s, UR em fração (0-1),
metabolismo em met, vestimenta em clo.
"""

import jax
import jax.numpy as jnp


def pmv(ta, tr, var, ur, met=1.2, clo=0.5, trabalho_met=0.0, iteracoes=60):
    """Voto Médio Estimado (PMV) - ISO 7730:2005, Anexo D.

    ta: temperatura do ar [°C]
    tr: temperatura radiante média [°C]
    var: velocidade relativa do ar [m/s]
    ur: umidade relativa [0-1]
    met: taxa metabólica [met] (1 met = 58,15 W/m²)
    clo: isolamento da vestimenta [clo] (1 clo = 0,155 m²K/W)

    A temperatura superficial da roupa é obtida por iteração de ponto fixo com
    número fixo de passos, o que mantém a função diferenciável.
    """
    ta = jnp.asarray(ta)
    pa = ur * 100.0 * 10.0 * jnp.exp(16.6536 - 4030.183 / (ta + 235.0))   # Pa
    icl = 0.155 * clo
    m = met * 58.15
    w = trabalho_met * 58.15
    mw = m - w
    fcl = jnp.where(icl <= 0.078, 1.0 + 1.29 * icl, 1.05 + 0.645 * icl)
    hcf = 12.1 * jnp.sqrt(jnp.maximum(var, 1e-8))
    taa = ta + 273.0
    tra = tr + 273.0

    tcla = taa + (35.5 - ta) / (3.5 * icl + 0.1)
    p1 = icl * fcl
    p2 = p1 * 3.96
    p3 = p1 * 100.0
    p4 = p1 * taa
    p5 = 308.7 - 0.028 * mw + p2 * (tra / 100.0) ** 4

    def passo(carry, _):
        xn, xf = carry
        xf = (xf + xn) / 2.0
        dif = jnp.abs(100.0 * xf - taa)
        hcn = 2.38 * (dif + 1e-9) ** 0.25
        hc = jnp.maximum(hcf, hcn)
        xn = (p5 + p4 * hc - p2 * xf**4) / (100.0 + p3 * hc)
        return (xn, xf), None

    xn0 = tcla / 100.0
    (xn, xf), _ = jax.lax.scan(passo, (xn0, tcla / 50.0), None, length=iteracoes)
    dif = jnp.abs(100.0 * xn - taa)
    hc = jnp.maximum(hcf, 2.38 * (dif + 1e-9) ** 0.25)
    tcl = 100.0 * xn - 273.0

    hl1 = 3.05e-3 * (5733.0 - 6.99 * mw - pa)                      # difusão pela pele
    hl2 = jnp.where(mw > 58.15, 0.42 * (mw - 58.15), 0.0)          # suor
    hl3 = 1.7e-5 * m * (5867.0 - pa)                               # respiração latente
    hl4 = 0.0014 * m * (34.0 - ta)                                 # respiração sensível
    hl5 = 3.96 * fcl * (xn**4 - (tra / 100.0) ** 4)                # radiação
    hl6 = fcl * hc * (tcl - ta)                                    # convecção

    ts = 0.303 * jnp.exp(-0.036 * m) + 0.028
    return ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)


def ppd(pmv_valor):
    """Percentual Estimado de Insatisfeitos [%] - ISO 7730 eq. 5."""
    return 100.0 - 95.0 * jnp.exp(-0.03353 * pmv_valor**4 - 0.2179 * pmv_valor**2)


def risco_corrente_ar(ta, v, intensidade_turbulencia=0.40):
    """Draught Rate DR [%] - ISO 7730 eq. 6.

    ta: temperatura local do ar [°C]; v: velocidade média local [m/s];
    intensidade_turbulencia: Tu em fração (0,40 = 40 %, valor típico de ambientes
    com mistura quando não medido). Categoria A: DR < 10 %; B: < 20 %; C: < 30 %.
    """
    tu = intensidade_turbulencia * 100.0
    # Abaixo de 0,05 m/s a norma manda usar 0,05, o que zera o DR. O "where duplo"
    # evita derivada infinita de x**0.62 em x = 0 (que viraria NaN no jax.grad).
    excesso = v - 0.05
    positivo = excesso > 0.0
    potencia = jnp.where(positivo, jnp.where(positivo, excesso, 1.0) ** 0.62, 0.0)
    dr = (34.0 - ta) * potencia * (0.37 * jnp.maximum(v, 0.05) * tu + 3.14)
    return jnp.clip(dr, 0.0, 100.0)
