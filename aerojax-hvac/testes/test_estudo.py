"""Estudo de ponta a ponta: relatório em arquivo, rastreabilidade e linha de comando."""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

import clima2d
from clima2d import documento, estudo
from clima2d.__main__ import main
from referencia import PROJETO_EXEMPLO, PASTA_REFERENCIAS, normalizar_relatorio


@pytest.fixture(scope="module")
def estudo_exemplo(tmp_path_factory):
    destino = tmp_path_factory.mktemp("saida") / "sub" / "pasta" / "relatorio.html"   # pastas ainda não existem
    return destino, estudo.rodar_estudo(PROJETO_EXEMPLO.read_bytes(), destino)


def test_rodar_estudo_grava_relatorio_igual_ao_do_app(estudo_exemplo):
    destino, res = estudo_exemplo
    assert res["relatorio"] == destino and destino.is_file()
    esperado = (PASTA_REFERENCIAS / "relatorio_escritorio_rapido.html").read_text(encoding="utf-8")
    assert normalizar_relatorio(destino.read_text(encoding="utf-8")) == esperado


def test_rodar_estudo_devolve_rastreabilidade(estudo_exemplo):
    _, res = estudo_exemplo
    ras = res["rastreabilidade"]
    assert ras["motor"] == "clima2d" and ras["versao_motor"] == clima2d.__version__
    assert ras["normas"] == ["ISO 7730:2005", "ABNT NBR 16401-2:2008"]
    assert ras["data"] == datetime.date.today().isoformat()
    assert ras["entradas"] == documento.carregar_json(PROJETO_EXEMPLO.read_bytes())
    assert len(res["conformidade"]) == 6
    json.dumps({k: v for k, v in res.items() if k != "relatorio"})   # serializável para o banco


def test_rodar_estudo_avisa_edicao_superada(estudo_exemplo):
    _, res = estudo_exemplo
    assert any("16401-2:2008" in a and "2024" in a for a in res["avisos"])


def test_rodar_estudo_recusa_projeto_sem_retorno_antes_de_simular(tmp_path):
    p = documento.projeto_padrao()
    p["aberturas"] = [a for a in p["aberturas"] if a["tipo"] == "insuflamento"]
    destino = tmp_path / "relatorio.html"
    with pytest.raises(documento.ErroProjeto, match="não pode ser simulado.*retorno"):
        estudo.rodar_estudo(p, destino)
    assert not destino.exists()


def test_main_com_projeto_invalido_retorna_2(tmp_path, capsys):
    arq = tmp_path / "p.json"
    arq.write_text('{"sala": 5}', encoding="utf-8")
    assert main([str(arq), str(tmp_path / "r.html")]) == 2
    err = capsys.readouterr().err
    assert "Projeto inválido: sala deve ser um objeto." in err and "Traceback" not in err


def test_main_gera_relatorio(tmp_path, capsys):
    destino = tmp_path / "r.html"
    assert main([str(PROJETO_EXEMPLO), str(destino)]) == 0
    assert destino.is_file()
    assert f"Relatório gravado em {destino}" in capsys.readouterr().out
