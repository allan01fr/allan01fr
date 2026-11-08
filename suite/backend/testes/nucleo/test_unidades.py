import re
from pathlib import Path

import pytest

from app.nucleo.unidades import (
    btu_h_para_w,
    c_para_f,
    cfm_para_m3_h,
    f_para_c,
    kg_para_lb,
    lb_para_kg,
    m3_h_para_cfm,
    m_para_pe,
    m_para_pol,
    pa_para_pol_h2o,
    pa_para_psi,
    pe_para_m,
    pol_h2o_para_pa,
    pol_para_m,
    psi_para_pa,
    tr_para_w,
    w_para_btu_h,
    w_para_tr,
)

RAIZ_APP = Path(__file__).resolve().parents[2] / "app"


def test_valores_de_referencia():
    assert tr_para_w(1) == pytest.approx(3516.85284, rel=1e-8)
    assert btu_h_para_w(12000) == pytest.approx(3516.85284, rel=1e-8)
    assert cfm_para_m3_h(1000) == pytest.approx(1699.01079552, rel=1e-10)
    assert pol_para_m(1) == 0.0254 and lb_para_kg(1) == 0.45359237
    assert psi_para_pa(1) == pytest.approx(6894.757, rel=1e-6)
    assert pe_para_m(1) == 0.3048
    assert pol_h2o_para_pa(1) == pytest.approx(249.0889)
    assert f_para_c(95) == pytest.approx(35.0) and c_para_f(-40) == pytest.approx(-40.0)


@pytest.mark.parametrize(
    "ida,volta",
    [
        (btu_h_para_w, w_para_btu_h),
        (tr_para_w, w_para_tr),
        (cfm_para_m3_h, m3_h_para_cfm),
        (pol_para_m, m_para_pol),
        (pe_para_m, m_para_pe),
        (lb_para_kg, kg_para_lb),
        (psi_para_pa, pa_para_psi),
        (pol_h2o_para_pa, pa_para_pol_h2o),
        (f_para_c, c_para_f),
    ],
)
def test_ida_e_volta(ida, volta):
    assert volta(ida(123.456)) == pytest.approx(123.456, rel=1e-12)


def test_constantes_so_existem_em_unidades():
    padrao = re.compile(r"0\.29307|3516\.85|1\.69901|0\.0254|0\.3048|0\.45359|6894\.75|249\.08")
    visitados = 0
    for arq in RAIZ_APP.rglob("*.py"):
        if arq.name != "unidades.py":
            visitados += 1
            assert not padrao.search(arq.read_text(encoding="utf-8")), arq
    assert visitados >= 1
