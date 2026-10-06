"""
Simulador CFD 2D de ambiente climatizado em JAX: velocidade, temperatura e umidade.

Usa os mesmos princípios do solver do AeroJAX (passo puro, estado como PyTree,
rollout com jax.lax.scan, diferenciável com jax.grad), mas com o que um projeto de
climatização precisa e o AeroJAX não tem: sala fechada com insuflamento e retorno
em qualquer parede, empuxo térmico (Boussinesq com temperatura virtual, ou seja,
o vapor d'água também altera a densidade), transporte de umidade absoluta,
fontes de calor sensível e latente (pessoas, equipamentos) e fluxo de calor nas
paredes (fachada, cobertura).

Método numérico:
- malha deslocada (MAC): u nas faces verticais, v nas horizontais, p/T/W nos centros;
- advecção conservativa com limitador TVD van Leer;
- difusão com viscosidade efetiva constante (laminar + turbulenta, parâmetro de calibração);
- Runge-Kutta SSP de 2ª ordem, projeção de pressão em cada estágio;
- Poisson com Neumann resolvido exatamente por transformada cosseno (DCT-II),
  portanto o campo de velocidade sai com divergência nula até o erro de máquina;
- obstáculos (móveis) por penalização de Brinkman.

Hipótese 2D: o corte representa uma sala de profundidade `profundidade` [m] com o
difusor ocupando toda essa profundidade (difusor linear). A vazão volumétrica
informada é preservada, logo os balanços de energia e de umidade estão corretos.
Para um split real (saída de ~0,8 m) o alcance do jato tende a ser subestimado.
"""

from dataclasses import dataclass, field
from functools import partial
from typing import NamedTuple, Optional, Sequence, Tuple

import jax
import jax.numpy as jnp
from jax.scipy.fft import dctn, idctn

from . import psicrometria as psi
from . import conforto

G = 9.81
RHO = 1.2           # kg/m³ (referência Boussinesq)
CP = 1006.0         # J/(kg K)


# ---------------------------------------------------------------------------
# Definição do caso
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Abertura:
    """Abertura em uma parede: insuflamento ou retorno.

    parede: 'esquerda', 'direita', 'piso' ou 'teto'
    inicio, fim: posição ao longo da parede [m] (altura para paredes laterais,
                 coordenada x para piso/teto)
    tipo: 'insuflamento' ou 'retorno'
    """
    parede: str
    inicio: float
    fim: float
    tipo: str


@dataclass(frozen=True)
class FonteCalor:
    """Região retangular que libera calor sensível [W] e latente [W] (pessoas, equipamentos).

    Os valores são o total da sala; são divididos pela profundidade do modelo 2D.
    """
    x0: float
    x1: float
    y0: float
    y1: float
    sensivel_w: float
    latente_w: float = 0.0


@dataclass(frozen=True)
class Obstaculo:
    """Bloco sólido retangular (móvel, armário) por penalização de Brinkman."""
    x0: float
    x1: float
    y0: float
    y1: float


@dataclass(frozen=True)
class Sala:
    """Geometria e cargas fixas da sala. Parâmetros de projeto ficam em `Insuflamento`."""
    largura: float = 5.0
    altura: float = 2.8
    profundidade: float = 4.0
    nx: int = 100
    ny: int = 56
    aberturas: Tuple[Abertura, ...] = (
        Abertura('esquerda', 2.35, 2.45, 'insuflamento'),
        Abertura('esquerda', 2.55, 2.75, 'retorno'),
    )
    fontes: Tuple[FonteCalor, ...] = ()
    obstaculos: Tuple[Obstaculo, ...] = ()
    # Fluxo de calor que entra pelas superfícies [W/m²] (fachada, cobertura, piso)
    fluxo_esquerda: float = 0.0
    fluxo_direita: float = 0.0
    fluxo_piso: float = 0.0
    fluxo_teto: float = 0.0
    # Viscosidade efetiva [m²/s]: molecular (1,5e-5) + turbulenta. Calibrar com medição
    # ou com uma simulação 3D de referência. Valores típicos de 5e-4 a 5e-3.
    nu_efetiva: float = 1.5e-3
    prandtl_turbulento: float = 0.9
    schmidt_turbulento: float = 0.9
    pressao: float = psi.P_ATM

    @property
    def dx(self):
        return self.largura / self.nx

    @property
    def dy(self):
        return self.altura / self.ny


class Insuflamento(NamedTuple):
    """Parâmetros de projeto (podem ser otimizados com jax.grad)."""
    vazao_m3h: jnp.ndarray       # vazão total de insuflamento [m³/h]
    angulo_graus: jnp.ndarray    # ângulo do jato em relação à normal da parede; + desvia para baixo/direita
    temperatura: jnp.ndarray     # temperatura de insuflamento [°C]
    umidade_abs: jnp.ndarray     # umidade absoluta de insuflamento [kg/kg]


class Estado(NamedTuple):
    u: jnp.ndarray   # (nx+1, ny)
    v: jnp.ndarray   # (nx, ny+1)
    T: jnp.ndarray   # (nx, ny) °C
    W: jnp.ndarray   # (nx, ny) kg/kg
    t: jnp.ndarray   # tempo [s]


# ---------------------------------------------------------------------------
# Máscaras geométricas (calculadas uma vez, fora do jit)
# ---------------------------------------------------------------------------

class Geometria(NamedTuple):
    sup_esq: jnp.ndarray   # (ny,) fração da face de insuflamento na parede esquerda
    sup_dir: jnp.ndarray
    sup_piso: jnp.ndarray  # (nx,)
    sup_teto: jnp.ndarray
    ret_esq: jnp.ndarray
    ret_dir: jnp.ndarray
    ret_piso: jnp.ndarray
    ret_teto: jnp.ndarray
    q_sens: jnp.ndarray    # (nx, ny) fonte de calor convertida em taxa de aquecimento [K/s]
    q_lat: jnp.ndarray     # (nx, ny) fonte de umidade [kg/kg/s]
    solido_c: jnp.ndarray  # (nx, ny)
    solido_u: jnp.ndarray  # (nx+1, ny)
    solido_v: jnp.ndarray  # (nx, ny+1)
    ocupada: jnp.ndarray   # (nx, ny) máscara da zona ocupada


def _cobertura_faces(n, h, inicio, fim):
    """Fração de cada face (de comprimento h) coberta pelo intervalo [inicio, fim]."""
    a = jnp.arange(n) * h
    b = a + h
    return jnp.clip((jnp.minimum(b, fim) - jnp.maximum(a, inicio)) / h, 0.0, 1.0)


def _retangulo(xc, yc, x0, x1, y0, y1):
    return ((xc >= x0) & (xc <= x1) & (yc >= y0) & (yc <= y1)).astype(jnp.float32)


def montar_geometria(sala: Sala, zona_ocupada=(0.5, 0.1, 1.8)) -> Geometria:
    """Pré-calcula máscaras de aberturas, fontes, obstáculos e zona ocupada.

    zona_ocupada = (afastamento das paredes [m], altura mínima [m], altura máxima [m]).
    Padrão inspirado na ABNT NBR 16401-2 / ASHRAE 55.
    """
    nx, ny, dx, dy = sala.nx, sala.ny, sala.dx, sala.dy
    D = sala.profundidade
    zeros_y, zeros_x = jnp.zeros(ny), jnp.zeros(nx)
    m = {k: (zeros_y if k[-3:] in ('esq', 'dir') else zeros_x)
         for k in ('sup_esq', 'sup_dir', 'sup_piso', 'sup_teto',
                   'ret_esq', 'ret_dir', 'ret_piso', 'ret_teto')}
    nomes = {'esquerda': 'esq', 'direita': 'dir', 'piso': 'piso', 'teto': 'teto'}
    for ab in sala.aberturas:
        lateral = ab.parede in ('esquerda', 'direita')
        cob = _cobertura_faces(ny if lateral else nx, dy if lateral else dx, ab.inicio, ab.fim)
        chave = ('sup_' if ab.tipo == 'insuflamento' else 'ret_') + nomes[ab.parede]
        m[chave] = m[chave] + cob

    for parede in ('esq', 'dir', 'piso', 'teto'):
        if bool(((m['sup_' + parede] > 0) & (m['ret_' + parede] > 0)).any()):
            raise ValueError(f"Insuflamento e retorno caem na mesma face da malha (parede '{parede}'). "
                             "Refine a malha ou afaste as aberturas.")
    if not any(bool((m[k] > 0).any()) for k in m if k.startswith('sup_')):
        raise ValueError("Nenhuma abertura de insuflamento ficou dentro da malha.")
    if not any(bool((m[k] > 0).any()) for k in m if k.startswith('ret_')):
        raise ValueError("Nenhuma abertura de retorno ficou dentro da malha.")

    xc = (jnp.arange(nx) + 0.5) * dx
    yc = (jnp.arange(ny) + 0.5) * dy
    Xc, Yc = jnp.meshgrid(xc, yc, indexing='ij')

    q_sens = jnp.zeros((nx, ny))
    q_lat = jnp.zeros((nx, ny))
    for f in sala.fontes:
        r = _retangulo(Xc, Yc, f.x0, f.x1, f.y0, f.y1)
        area = jnp.maximum(r.sum() * dx * dy, 1e-12)
        # W -> W/m³ (por metro de profundidade) -> K/s
        q_sens = q_sens + r * f.sensivel_w / D / area / (RHO * CP)
        # W latente -> kg vapor/s -> kg/kg/s
        q_lat = q_lat + r * f.latente_w / psi.H_FG0 / D / area / RHO

    # Fluxos de parede aplicados na primeira camada de células
    q_sens = q_sens.at[0, :].add(sala.fluxo_esquerda / (RHO * CP * dx))
    q_sens = q_sens.at[-1, :].add(sala.fluxo_direita / (RHO * CP * dx))
    q_sens = q_sens.at[:, 0].add(sala.fluxo_piso / (RHO * CP * dy))
    q_sens = q_sens.at[:, -1].add(sala.fluxo_teto / (RHO * CP * dy))

    solido_c = jnp.zeros((nx, ny))
    for o in sala.obstaculos:
        solido_c = jnp.maximum(solido_c, _retangulo(Xc, Yc, o.x0, o.x1, o.y0, o.y1))
    # Faces: sólidas se qualquer célula vizinha for sólida
    pad_x = jnp.pad(solido_c, ((1, 1), (0, 0)))
    solido_u = jnp.maximum(pad_x[:-1], pad_x[1:])
    pad_y = jnp.pad(solido_c, ((0, 0), (1, 1)))
    solido_v = jnp.maximum(pad_y[:, :-1], pad_y[:, 1:])

    afast, y_min, y_max = zona_ocupada
    ocupada = _retangulo(Xc, Yc, afast, sala.largura - afast, y_min, y_max) * (1.0 - solido_c)

    return Geometria(**m, q_sens=q_sens, q_lat=q_lat, solido_c=solido_c,
                     solido_u=solido_u, solido_v=solido_v, ocupada=ocupada)


# ---------------------------------------------------------------------------
# Condições de contorno
# ---------------------------------------------------------------------------

def _velocidades_aberturas(sala: Sala, geo: Geometria, ins: Insuflamento):
    """Velocidades normais nas 4 paredes e componente tangencial do insuflamento.

    Convenção: u > 0 aponta para +x, v > 0 para +y. O retorno extrai exatamente a
    vazão insuflada (sala fechada, balanço de massa).
    """
    dx, dy, D = sala.dx, sala.dy, sala.profundidade
    q2d = ins.vazao_m3h / 3600.0 / D                       # m²/s por metro de profundidade
    area_sup = (geo.sup_esq.sum() + geo.sup_dir.sum()) * dy + (geo.sup_piso.sum() + geo.sup_teto.sum()) * dx
    area_ret = (geo.ret_esq.sum() + geo.ret_dir.sum()) * dy + (geo.ret_piso.sum() + geo.ret_teto.sum()) * dx
    vs = q2d / area_sup                                    # velocidade de face no insuflamento
    vr = q2d / area_ret
    ang = jnp.deg2rad(ins.angulo_graus)
    # A componente normal garante a vazão; a tangencial dá a direção do jato.
    vn, vt = vs, vs * jnp.tan(ang)
    # Normais (sinal = sentido para dentro da sala no insuflamento)
    u_esq = geo.sup_esq * vn - geo.ret_esq * vr
    u_dir = -geo.sup_dir * vn + geo.ret_dir * vr
    v_piso = geo.sup_piso * vn - geo.ret_piso * vr
    v_teto = -geo.sup_teto * vn + geo.ret_teto * vr
    # Tangenciais (jato inclinado): paredes laterais desviam para baixo, piso/teto para +x
    vt_esq = -geo.sup_esq * vt
    vt_dir = -geo.sup_dir * vt
    ut_piso = geo.sup_piso * vt
    ut_teto = geo.sup_teto * vt
    return (u_esq, u_dir, v_piso, v_teto), (vt_esq, vt_dir, ut_piso, ut_teto)


def _aplicar_normais(u, v, normais):
    u_esq, u_dir, v_piso, v_teto = normais
    u = u.at[0, :].set(u_esq).at[-1, :].set(u_dir)
    v = v.at[:, 0].set(v_piso).at[:, -1].set(v_teto)
    return u, v


# ---------------------------------------------------------------------------
# Operadores
# ---------------------------------------------------------------------------

def _van_leer(r):
    return (r + jnp.abs(r)) / (1.0 + jnp.abs(r))


def _fluxo_tvd(qp, vel):
    """Fluxo advectivo TVD (van Leer) ao longo do eixo 0.

    qp: valores com 2 células fantasmas de cada lado, forma (M+4, ...)
    vel: velocidade nas M+1 interfaces entre qp[f+1] e qp[f+2], forma (M+1, ...)
    """
    q0, q1, q2, q3 = qp[:-3], qp[1:-2], qp[2:-1], qp[3:]
    eps = 1e-12

    def lim(num, den):
        den_s = jnp.where(jnp.abs(den) < eps, eps, den)
        return jnp.where(jnp.abs(den) < eps, 0.0, _van_leer(num / den_s))

    d = q2 - q1
    face_pos = q1 + 0.5 * lim(q1 - q0, d) * d
    face_neg = q2 - 0.5 * lim(q3 - q2, d) * d
    return vel * jnp.where(vel >= 0.0, face_pos, face_neg)


def _laplaciano(qp, dx, dy):
    """Laplaciano de q com 1 fantasma de cada lado nos dois eixos."""
    c = qp[1:-1, 1:-1]
    return ((qp[2:, 1:-1] - 2 * c + qp[:-2, 1:-1]) / dx**2
            + (qp[1:-1, 2:] - 2 * c + qp[1:-1, :-2]) / dy**2)


def _rhs_escalar(q, u, v, q_entrada_x, q_entrada_y, sup_x, sup_y, difus, dx, dy):
    """Advecção-difusão de escalar centrado (T ou W).

    Paredes: fluxo nulo (fantasma = cópia). Faces de insuflamento: fantasma = valor insuflado.
    sup_x = (máscara esquerda, máscara direita) em (ny,); sup_y = (piso, teto) em (nx,).
    """
    # Fantasmas em x
    esq = jnp.where(sup_x[0] > 0, q_entrada_x, q[0])
    dir_ = jnp.where(sup_x[1] > 0, q_entrada_x, q[-1])
    qx = jnp.concatenate([esq[None], esq[None], q, dir_[None], dir_[None]], axis=0)
    fx = _fluxo_tvd(qx, u)
    # Fantasmas em y
    pis = jnp.where(sup_y[0] > 0, q_entrada_y, q[:, 0])
    tet = jnp.where(sup_y[1] > 0, q_entrada_y, q[:, -1])
    qy = jnp.concatenate([pis[:, None], pis[:, None], q, tet[:, None], tet[:, None]], axis=1)
    fy = _fluxo_tvd(qy.T, v.T).T
    adv = (fx[1:] - fx[:-1]) / dx + (fy[:, 1:] - fy[:, :-1]) / dy
    qp = jnp.pad(q, 1, mode='edge')
    return -adv + difus * _laplaciano(qp, dx, dy)


def _rhs_momento(u, v, T, W, vt_bc, nu, dx, dy, T_ref):
    """Advecção + difusão + empuxo para u (nx+1, ny) e v (nx, ny+1). Paredes sem escorregamento."""
    vt_esq, vt_dir, ut_piso, ut_teto = vt_bc

    # ---- u ----
    # Fantasmas de u no piso/teto: sem escorregamento (u_parede = tangencial imposta, 0 fora do difusor)
    gp = 2.0 * _para_faces(ut_piso) - u[:, 0]
    gt = 2.0 * _para_faces(ut_teto) - u[:, -1]
    # x: interfaces nos centros das células, velocidade advectiva = média de u
    vel_x = jnp.pad(0.5 * (u[1:] + u[:-1]), ((1, 1), (0, 0)))         # (nx+2, ny)
    fx = _fluxo_tvd(jnp.pad(u, ((2, 2), (0, 0)), mode='edge'), vel_x)  # (nx+2, ny)
    # y: interfaces nos cantos (x_i, y_j), v interpolado
    vpad = jnp.pad(v, ((1, 1), (0, 0)), mode='edge')
    vel_y = 0.5 * (vpad[1:] + vpad[:-1])                               # (nx+1, ny+1)
    uy = jnp.concatenate([gp[:, None], gp[:, None], u, gt[:, None], gt[:, None]], axis=1)
    fy = _fluxo_tvd(uy.T, vel_y.T).T                                   # (nx+1, ny+1)
    adv_u = (fx[1:] - fx[:-1]) / dx + (fy[:, 1:] - fy[:, :-1]) / dy
    up = jnp.concatenate([gp[:, None], u, gt[:, None]], axis=1)
    lap_u = _laplaciano(jnp.pad(up, ((1, 1), (0, 0)), mode='edge'), dx, dy)
    rhs_u = -adv_u + nu * lap_u

    # ---- v ----
    # Fantasmas de v nas paredes laterais: tangencial imposta no insuflamento, senão zero
    ge = 2.0 * _para_faces(vt_esq) - v[0]
    gd = 2.0 * _para_faces(vt_dir) - v[-1]
    upad = jnp.pad(u, ((0, 0), (1, 1)), mode='edge')
    vel_x = 0.5 * (upad[:, 1:] + upad[:, :-1])                         # (nx+1, ny+1)
    vx = jnp.concatenate([ge[None], ge[None], v, gd[None], gd[None]], axis=0)
    fx = _fluxo_tvd(vx, vel_x)                                         # (nx+1, ny+1)
    vel_y = jnp.pad(0.5 * (v[:, 1:] + v[:, :-1]), ((0, 0), (1, 1)))    # (nx, ny+2)
    fy = _fluxo_tvd(jnp.pad(v, ((0, 0), (2, 2)), mode='edge').T, vel_y.T).T   # (nx, ny+2)
    adv_v = (fx[1:] - fx[:-1]) / dx + (fy[:, 1:] - fy[:, :-1]) / dy
    vp = jnp.concatenate([ge[None], v, gd[None]], axis=0)
    lap_v = _laplaciano(jnp.pad(vp, ((0, 0), (1, 1)), mode='edge'), dx, dy)
    # Empuxo com temperatura virtual (ar úmido é mais leve que ar seco)
    Tv = (T + 273.15) * (1.0 + 0.608 * W)
    Tv_ref = (T_ref[0] + 273.15) * (1.0 + 0.608 * T_ref[1])
    bp = jnp.pad(G * (Tv - Tv_ref) / Tv_ref, ((0, 0), (1, 1)), mode='edge')
    rhs_v = -adv_v + nu * lap_v + 0.5 * (bp[:, 1:] + bp[:, :-1])
    return rhs_u, rhs_v


def _para_faces(q):
    """Valores em n células -> n+1 faces (média, extremidades replicadas)."""
    p = jnp.pad(q, (1, 1), mode='edge')
    return 0.5 * (p[1:] + p[:-1])


def _autovalores_poisson(nx, ny, dx, dy):
    kx = jnp.arange(nx)
    ky = jnp.arange(ny)
    lx = (2.0 * jnp.cos(jnp.pi * kx / nx) - 2.0) / dx**2
    ly = (2.0 * jnp.cos(jnp.pi * ky / ny) - 2.0) / dy**2
    lam = lx[:, None] + ly[None, :]
    return lam.at[0, 0].set(1.0)


def _projetar(u, v, normais, dx, dy, lam, dt):
    """Projeção de pressão: torna (u, v) solenoidal mantendo as velocidades de contorno."""
    u, v = _aplicar_normais(u, v, normais)
    div = (u[1:] - u[:-1]) / dx + (v[:, 1:] - v[:, :-1]) / dy
    rhs = div / dt
    ph = dctn(rhs, type=2, norm='ortho') / lam
    ph = ph.at[0, 0].set(0.0)
    p = idctn(ph, type=2, norm='ortho')
    u = u.at[1:-1].add(-dt * (p[1:] - p[:-1]) / dx)
    v = v.at[:, 1:-1].add(-dt * (p[:, 1:] - p[:, :-1]) / dy)
    return u, v, p


# ---------------------------------------------------------------------------
# Passo de tempo e simulação
# ---------------------------------------------------------------------------

def passo(estado: Estado, sala: Sala, geo: Geometria, ins: Insuflamento, dt: float,
          T_ref=(24.0, 0.010)) -> Estado:
    """Um passo de tempo (SSP-RK2 com projeção em cada estágio). Função pura."""
    dx, dy = sala.dx, sala.dy
    nu = sala.nu_efetiva
    alfa = nu / sala.prandtl_turbulento
    difw = nu / sala.schmidt_turbulento
    lam = _autovalores_poisson(sala.nx, sala.ny, dx, dy)
    normais, tang = _velocidades_aberturas(sala, geo, ins)
    sup_x = (geo.sup_esq, geo.sup_dir)
    sup_y = (geo.sup_piso, geo.sup_teto)
    eta = 1e-3   # tempo de relaxação de Brinkman [s]

    def rhs(u, v, T, W):
        ru, rv = _rhs_momento(u, v, T, W, tang, nu, dx, dy, T_ref)
        rT = _rhs_escalar(T, u, v, ins.temperatura, ins.temperatura, sup_x, sup_y, alfa, dx, dy) + geo.q_sens
        rW = _rhs_escalar(W, u, v, ins.umidade_abs, ins.umidade_abs, sup_x, sup_y, difw, dx, dy) + geo.q_lat
        return ru, rv, rT, rW

    def brinkman(u, v):
        return u / (1.0 + dt * geo.solido_u / eta), v / (1.0 + dt * geo.solido_v / eta)

    u0, v0, T0, W0 = estado.u, estado.v, estado.T, estado.W
    ru, rv, rT, rW = rhs(u0, v0, T0, W0)
    u1, v1 = brinkman(u0 + dt * ru, v0 + dt * rv)
    u1, v1, _ = _projetar(u1, v1, normais, dx, dy, lam, dt)
    T1, W1 = T0 + dt * rT, W0 + dt * rW

    ru, rv, rT, rW = rhs(u1, v1, T1, W1)
    u2, v2 = brinkman(0.5 * (u0 + u1 + dt * ru), 0.5 * (v0 + v1 + dt * rv))
    u2, v2, _ = _projetar(u2, v2, normais, dx, dy, lam, 0.5 * dt)
    T2 = 0.5 * (T0 + T1 + dt * rT)
    W2 = 0.5 * (W0 + W1 + dt * rW)
    return Estado(u2, v2, T2, W2, estado.t + dt)


def estado_inicial(sala: Sala, T0=26.0, W0=0.012) -> Estado:
    nx, ny = sala.nx, sala.ny
    return Estado(u=jnp.zeros((nx + 1, ny)), v=jnp.zeros((nx, ny + 1)),
                  T=jnp.full((nx, ny), T0, dtype=jnp.float32), W=jnp.full((nx, ny), W0, dtype=jnp.float32),
                  t=jnp.asarray(0.0))


def dt_estavel(sala: Sala, velocidade_max: float, cfl=0.4):
    """Passo de tempo estável (convecção e difusão explícitas)."""
    h = min(sala.dx, sala.dy)
    dt_conv = cfl * h / max(velocidade_max, 1e-6)
    dt_dif = 0.2 * h**2 / sala.nu_efetiva
    return min(dt_conv, dt_dif)


def velocidade_face_insuflamento(sala: Sala, geo: Geometria, vazao_m3h):
    (u_esq, u_dir, v_piso, v_teto), _ = _velocidades_aberturas(
        sala, geo, Insuflamento(jnp.asarray(vazao_m3h), 0.0, 20.0, 0.008))
    return float(jnp.max(jnp.abs(jnp.concatenate([u_esq, u_dir, v_piso, v_teto]))))


class Medias(NamedTuple):
    """Campos médios no tempo (centrados nas células)."""
    T: jnp.ndarray
    W: jnp.ndarray
    vel: jnp.ndarray


def velocidade_centro(u, v):
    uc = 0.5 * (u[1:] + u[:-1])
    vc = 0.5 * (v[:, 1:] + v[:, :-1])
    return uc, vc


def simular(sala: Sala, geo: Geometria, ins: Insuflamento, estado0: Estado,
            tempo_total: float, dt: float, tempo_media: float, passos_por_bloco: int = 100,
            T_ref=(24.0, 0.010)):
    """Integra no tempo e devolve (estado_final, médias no intervalo final `tempo_media`).

    Usa scan aninhado com jax.checkpoint em cada bloco para que jax.grad através de
    milhares de passos caiba na memória.
    """
    n_total = int(round(tempo_total / dt))
    n_blocos = max(1, n_total // passos_por_bloco)
    n_media = int(round(tempo_media / dt))
    inicio_media = n_blocos * passos_por_bloco - n_media

    @jax.checkpoint
    def bloco(carry, ib):
        def interno(c, k):
            est, acc = c
            est = passo(est, sala, geo, ins, dt, T_ref)
            idx = ib * passos_por_bloco + k
            peso = (idx >= inicio_media).astype(est.T.dtype)
            uc, vc = velocidade_centro(est.u, est.v)
            vel = jnp.sqrt(uc**2 + vc**2 + 1e-12)   # +1e-12: derivada finita em velocidade nula
            acc = Medias(acc.T + peso * est.T, acc.W + peso * est.W, acc.vel + peso * vel)
            return (est, acc), None
        carry, _ = jax.lax.scan(interno, carry, jnp.arange(passos_por_bloco))
        return carry, None

    z = jnp.zeros_like(estado0.T)
    (est, acc), _ = jax.lax.scan(bloco, (estado0, Medias(z, z, z)), jnp.arange(n_blocos))
    n = max(n_media, 1)
    return est, Medias(acc.T / n, acc.W / n, acc.vel / n)


# ---------------------------------------------------------------------------
# Indicadores de projeto
# ---------------------------------------------------------------------------

def indicadores(sala: Sala, geo: Geometria, ins: Insuflamento, medias: Medias,
                met=1.1, clo=0.5, t_radiante=None, intensidade_turbulencia=0.4):
    """Indicadores de conforto e desempenho na zona ocupada (dicionário de arrays JAX)."""
    occ = geo.ocupada
    n = jnp.maximum(occ.sum(), 1.0)
    media = lambda f: (f * occ).sum() / n

    T, W, vel = medias.T, medias.W, medias.vel
    ur = jnp.clip(psi.umidade_relativa(T, W, sala.pressao), 0.0, 1.0)
    tr = T if t_radiante is None else t_radiante
    pmv_c = conforto.pmv(T, tr, jnp.maximum(vel, 0.05), ur, met, clo)
    dr_c = conforto.risco_corrente_ar(T, vel, intensidade_turbulencia)

    # Estratificação: diferença entre 1,1 m e 0,1 m (cabeça - tornozelo, pessoa sentada)
    j_cab = int(1.1 / sala.dy)
    j_tor = int(0.1 / sala.dy)
    colunas = occ[:, j_cab] * occ[:, j_tor]
    dT_vert = ((T[:, j_cab] - T[:, j_tor]) * colunas).sum() / jnp.maximum(colunas.sum(), 1.0)

    # Estado do ar de retorno (média nas células junto às grelhas de retorno)
    pesos_ret = jnp.zeros_like(T)
    pesos_ret = pesos_ret.at[0, :].add(geo.ret_esq).at[-1, :].add(geo.ret_dir)
    pesos_ret = pesos_ret.at[:, 0].add(geo.ret_piso).at[:, -1].add(geo.ret_teto)
    pr = jnp.maximum(pesos_ret.sum(), 1e-12)
    T_ret = (T * pesos_ret).sum() / pr
    W_ret = (W * pesos_ret).sum() / pr

    m_ar = ins.vazao_m3h / 3600.0 * RHO
    cap_total = m_ar * (psi.entalpia(T_ret, W_ret) - psi.entalpia(ins.temperatura, ins.umidade_abs)) * 1000.0
    cap_sens = m_ar * CP * (T_ret - ins.temperatura)
    cap_lat = m_ar * (W_ret - ins.umidade_abs) * psi.H_FG0

    # Eficácia de remoção de calor (ε_t = (T_ret - T_ins)/(T_occ - T_ins)); >1 é melhor que mistura perfeita
    T_occ = media(T)
    eficacia = (T_ret - ins.temperatura) / jnp.maximum(jnp.abs(T_occ - ins.temperatura), 1e-3)

    return {
        'T_ocupada': T_occ,
        'UR_ocupada': media(ur),
        'vel_media_ocupada': media(vel),
        'vel_max_ocupada': jnp.max(vel * occ),
        'PMV_medio': media(pmv_c),
        'PMV_desvio': jnp.sqrt(media((pmv_c - media(pmv_c)) ** 2) + 1e-12),
        'PPD_medio': media(conforto.ppd(pmv_c)),
        'DR_medio': media(dr_c),
        'DR_max': jnp.max(dr_c * occ),
        'dT_vertical': dT_vert,
        'T_retorno': T_ret,
        'W_retorno': W_ret,
        'UR_retorno': psi.umidade_relativa(T_ret, W_ret, sala.pressao),
        'capacidade_total_W': cap_total,
        'capacidade_sensivel_W': cap_sens,
        'capacidade_latente_W': cap_lat,
        'eficacia_remocao_calor': eficacia,
        'campos': {'PMV': pmv_c, 'DR': dr_c, 'UR': ur},
    }
