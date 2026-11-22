"""
Psicrometria do ar úmido em JAX (diferenciável).

Equações do ASHRAE Handbook - Fundamentals (2017), cap. 1.
Unidades: temperatura em °C, pressão em Pa, umidade absoluta W em kg_vapor/kg_ar_seco,
umidade relativa UR em fração (0-1), entalpia em kJ/kg_ar_seco.

Todas as funções aceitam escalares ou arrays e funcionam com jax.grad / jax.vmap.
"""

import jax
import jax.numpy as jnp

P_ATM = 101325.0          # Pa, nível do mar
R_AR = 287.042            # J/(kg K), ar seco
CP_AR = 1006.0            # J/(kg K), ar seco
CP_VAPOR = 1860.0         # J/(kg K), vapor d'água
H_FG0 = 2501.0e3          # J/kg, calor latente de vaporização a 0 °C
RAZAO_MOLAR = 0.621945    # M_água / M_ar


def pressao_atmosferica(altitude_m):
    """Pressão atmosférica padrão [Pa] em função da altitude [m] (ASHRAE eq. 3)."""
    return 101325.0 * (1.0 - 2.25577e-5 * altitude_m) ** 5.2559


def pressao_saturacao(t):
    """Pressão de saturação do vapor d'água [Pa] (Hyland-Wexler, ASHRAE eqs. 5 e 6).

    Válida de -100 °C a 200 °C. Abaixo de 0 °C usa a curva sobre gelo.
    """
    T = jnp.asarray(t) + 273.15
    ln_gelo = (-5.6745359e3 / T + 6.3925247 - 9.6778430e-3 * T + 6.2215701e-7 * T**2
               + 2.0747825e-9 * T**3 - 9.4840240e-13 * T**4 + 4.1635019 * jnp.log(T))
    ln_agua = (-5.8002206e3 / T + 1.3914993 - 4.8640239e-2 * T + 4.1764768e-5 * T**2
               - 1.4452093e-8 * T**3 + 6.5459673 * jnp.log(T))
    return jnp.exp(jnp.where(T < 273.15, ln_gelo, ln_agua))


def umidade_absoluta(t, ur, p=P_ATM):
    """Umidade absoluta W [kg/kg] a partir de temperatura [°C] e UR [0-1]."""
    pw = ur * pressao_saturacao(t)
    return RAZAO_MOLAR * pw / (p - pw)


def umidade_relativa(t, w, p=P_ATM):
    """Umidade relativa [0-1] a partir de temperatura [°C] e W [kg/kg]."""
    pw = p * w / (RAZAO_MOLAR + w)
    return pw / pressao_saturacao(t)


def umidade_absoluta_saturacao(t, p=P_ATM):
    """W de saturação [kg/kg] à temperatura t [°C]."""
    return umidade_absoluta(t, 1.0, p)


def entalpia(t, w):
    """Entalpia do ar úmido [kJ/kg ar seco] (ASHRAE eq. 32)."""
    return 1.006 * t + w * (2501.0 + 1.86 * t)


def volume_especifico(t, w, p=P_ATM):
    """Volume específico [m³/kg ar seco] (ASHRAE eq. 26)."""
    return R_AR * (t + 273.15) * (1.0 + 1.607858 * w) / p


def densidade(t, w, p=P_ATM):
    """Densidade do ar úmido [kg/m³ de mistura]."""
    return (1.0 + w) / volume_especifico(t, w, p)


def ponto_orvalho(w, p=P_ATM, iteracoes=30):
    """Temperatura de ponto de orvalho [°C] para W [kg/kg].

    Inverte pressao_saturacao por Newton (número fixo de iterações, diferenciável).
    """
    pw = p * w / (RAZAO_MOLAR + w)
    # Chute inicial: ASHRAE eq. 37 (válida 0-93 °C)
    a = jnp.log(pw / 1000.0)
    td = 6.54 + 14.526 * a + 0.7389 * a**2 + 0.09486 * a**3 + 0.4569 * (pw / 1000.0) ** 0.1984

    dpws = jax.grad(lambda x: pressao_saturacao(x))
    dpws = jnp.vectorize(dpws)

    def passo(td, _):
        return td - (pressao_saturacao(td) - pw) / dpws(td), None

    td, _ = jax.lax.scan(passo, td, None, length=iteracoes)
    return td


def umidade_absoluta_tbu(t, tbu, p=P_ATM):
    """W [kg/kg] a partir de bulbo seco t e bulbo úmido tbu [°C] (ASHRAE eq. 33, tbu > 0 °C)."""
    ws = umidade_absoluta_saturacao(tbu, p)
    return ((2501.0 - 2.326 * tbu) * ws - 1.006 * (t - tbu)) / (2501.0 + 1.86 * t - 4.186 * tbu)


def bulbo_umido(t, w, p=P_ATM, iteracoes=40):
    """Temperatura de bulbo úmido termodinâmico [°C] (ASHRAE eq. 33, t* > 0 °C).

    Resolvido por bisseção com número fixo de iterações entre o ponto de orvalho e t.
    """
    def residuo(tbu):
        ws = umidade_absoluta_saturacao(tbu, p)
        w_calc = ((2501.0 - 2.326 * tbu) * ws - 1.006 * (t - tbu)) / (2501.0 + 1.86 * t - 4.186 * tbu)
        return w_calc - w

    lo = ponto_orvalho(w, p) - 1.0
    hi = jnp.asarray(t, dtype=lo.dtype) + 0.0 * lo

    def passo(lims, _):
        lo, hi = lims
        mid = 0.5 * (lo + hi)
        acima = residuo(mid) > 0.0      # resíduo cresce com tbu
        return (jnp.where(acima, lo, mid), jnp.where(acima, mid, hi)), None

    (lo, hi), _ = jax.lax.scan(passo, (lo, hi), None, length=iteracoes)
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Processos de climatização
# ---------------------------------------------------------------------------

def mistura(t1, w1, m1, t2, w2, m2):
    """Mistura adiabática de duas correntes (vazões mássicas m1, m2 de ar seco).

    Retorna (t, w) da mistura. Ex.: ar de retorno + ar externo.
    """
    w = (m1 * w1 + m2 * w2) / (m1 + m2)
    h = (m1 * entalpia(t1, w1) + m2 * entalpia(t2, w2)) / (m1 + m2)
    t = (h - 2501.0 * w) / (1.006 + 1.86 * w)
    return t, w


def serpentina_resfriamento(t_ent, w_ent, t_adp, fator_bypass, p=P_ATM):
    """Estado de saída de uma serpentina de resfriamento/desumidificação.

    Modelo clássico de ponto de orvalho do aparelho (ADP) e fator de bypass (BF):
    o ar de saída está sobre a reta que liga a entrada ao ADP (saturado),
    a uma fração BF da distância medida a partir do ADP.

    Se o ADP estiver acima do ponto de orvalho da entrada não há condensação
    (resfriamento sensível puro).
    """
    w_adp = umidade_absoluta_saturacao(t_adp, p)
    t_sai = t_adp + fator_bypass * (t_ent - t_adp)
    w_reta = w_adp + fator_bypass * (w_ent - w_adp)
    w_sai = jnp.minimum(w_ent, w_reta)
    return t_sai, w_sai


def adp_serpentina(t_ent, w_ent, t_sai, w_sai, p=P_ATM, iteracoes=60):
    """ADP e fator de bypass que levam o ar de (t_ent, w_ent) a (t_sai, w_sai).

    O ADP é a interseção do prolongamento da reta entrada -> saída (no plano t-W)
    com a curva de saturação. Resolvido por bisseção (robusto e diferenciável).
    Retorna (t_adp, fator_bypass).
    """
    def f(s):
        t = t_ent + s * (t_sai - t_ent)
        w = w_ent + s * (w_sai - w_ent)
        return w - umidade_absoluta_saturacao(t, p)     # > 0 enquanto acima da saturação

    def passo(lims, _):
        lo, hi = lims
        mid = 0.5 * (lo + hi)
        acima = f(mid) < 0.0       # ainda não saturado em mid -> raiz está além
        return (jnp.where(acima, mid, lo), jnp.where(acima, hi, mid)), None

    # Limite superior: reta até -40 °C ou até W = 0, o que vier primeiro
    s_t = (t_ent + 40.0) / (t_ent - t_sai)
    s_w = jnp.where(w_ent > w_sai, w_ent / jnp.maximum(w_ent - w_sai, 1e-12), s_t)
    hi = jnp.minimum(s_t, s_w)
    lo = jnp.ones_like(hi)
    (lo, hi), _ = jax.lax.scan(passo, (lo, hi), None, length=iteracoes)
    s = 0.5 * (lo + hi)
    t_adp = t_ent + s * (t_sai - t_ent)
    return t_adp, (t_sai - t_adp) / (t_ent - t_adp)


def cargas_serpentina(vazao_m3h, t_ent, w_ent, t_sai, w_sai, p=P_ATM):
    """Capacidade da serpentina [W]: (total, sensível, latente) e água condensada [kg/h].

    A vazão é volumétrica na condição de entrada.
    """
    m_ar = vazao_m3h / 3600.0 / volume_especifico(t_ent, w_ent, p)   # kg ar seco/s
    total = m_ar * (entalpia(t_ent, w_ent) - entalpia(t_sai, w_sai)) * 1000.0
    sensivel = m_ar * (CP_AR + CP_VAPOR * w_ent) * (t_ent - t_sai)
    latente = total - sensivel
    condensado = m_ar * (w_ent - w_sai) * 3600.0
    return total, sensivel, latente, condensado


def estado_insuflamento(t_ambiente, w_ambiente, carga_sensivel_w, carga_latente_w,
                        vazao_m3h, p=P_ATM):
    """Estado de insuflamento (t, w) necessário para retirar as cargas do ambiente.

    carga_sensivel_w, carga_latente_w: cargas térmicas do ambiente [W]
    vazao_m3h: vazão de insuflamento [m³/h]
    """
    t_aprox = t_ambiente - 5.0
    m_ar = vazao_m3h / 3600.0 / volume_especifico(t_aprox, w_ambiente, p)
    t_ins = t_ambiente - carga_sensivel_w / (m_ar * (CP_AR + CP_VAPOR * w_ambiente))
    w_ins = w_ambiente - carga_latente_w / (m_ar * H_FG0)
    return t_ins, w_ins


def fator_calor_sensivel(carga_sensivel_w, carga_latente_w):
    """FCS (SHR) = sensível / total."""
    return carga_sensivel_w / (carga_sensivel_w + carga_latente_w)
