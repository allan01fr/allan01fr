import json

import pytest

from orcamento import indices_bcb as bcb
from orcamento import referencias as rf


@pytest.fixture
def con(tmp_path):
    c = rf.conectar(str(tmp_path / "ref.sqlite"))
    yield c
    c.close()


def fake(url):
    assert "bcdata.sgs.189" in url and "dataInicial=01/01/2024" in url
    return json.dumps([{"data": "01/02/2024", "valor": "2,00"}, {"data": "01/01/2024", "valor": "1.00"}])


def test_parse_e_url():
    assert bcb.parse_sgs([{"data": "01/01/2024", "valor": "0,57"}, {"data": "01/02/2024", "valor": "0.5"}]) == [
        ("2024-01", 0.57), ("2024-02", 0.5)]
    assert bcb.url_sgs(433, "2024-01").endswith("dados?formato=json&dataInicial=01/01/2024")


def test_atualizar_banco_e_fator(con):
    orig = bcb.baixar_serie
    bcb.baixar_serie = lambda nome, de="2000-01", ate=None, http_get=None: orig(nome, "2024-01", ate, fake)
    try:
        assert bcb.atualizar_banco(con, "IGP-M") == 2
        assert bcb.atualizar_banco(con, "IGP-M") == 2  # reimportar substitui
    finally:
        bcb.baixar_serie = orig
    assert con.execute("SELECT COUNT(*) FROM indices WHERE nome='IGP-M'").fetchone()[0] == 3
    assert bcb.fator_periodo(con, "IGP-M", "2023-12") == pytest.approx(1.0302)
    assert bcb.fator_periodo(con, "IGP-M", "2024-01", "2024-02") == pytest.approx(1.02)


def test_erro_rede():
    def falha(url):
        raise OSError("bloqueado")
    with pytest.raises(RuntimeError, match="CSV"):
        bcb.baixar_serie("IPCA", http_get=falha)
