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


def _projeto_com(**mudancas):
    p = documento.projeto_padrao()
    for secao, campos in mudancas.items():
        p[secao].update(campos)
    return p


def test_rodar_estudo_recusa_sala_gigante_sem_simular(tmp_path):
    destino = tmp_path / "r.html"
    with pytest.raises(documento.ErroProjeto, match="células"):
        estudo.rodar_estudo(_projeto_com(sala={"largura": 1e308}), destino)
    assert not destino.exists()


def test_rodar_estudo_recusa_malha_minuscula_sem_alocar(tmp_path):
    destino = tmp_path / "r.html"
    with pytest.raises(documento.ErroProjeto, match="células"):
        estudo.rodar_estudo(_projeto_com(simulacao={"malha_cm": 1e-9}), destino)
    assert not destino.exists()


def test_limite_de_celulas_aceita_o_exemplo_e_a_malha_mais_fina_do_app():
    documento.validar_documento(documento.projeto_padrao())
    documento.validar_documento(_projeto_com(simulacao={"malha_cm": 2.5}))   # 200 x 112 células


def test_rodar_estudo_converte_erro_aritmetico_da_montagem(tmp_path, monkeypatch):
    def estoura(projeto):
        raise OverflowError("cannot convert float infinity to integer")
    monkeypatch.setattr(estudo, "validar", estoura)
    with pytest.raises(documento.ErroProjeto, match="dimensões ou malha fora de faixa"):
        estudo.rodar_estudo(documento.projeto_padrao(), tmp_path / "r.html")


@pytest.mark.parametrize("entrada", [None, [], [1, 2], 42, 3.5])
def test_rodar_estudo_recusa_entrada_de_tipo_invalido(entrada, tmp_path):
    with pytest.raises(documento.ErroProjeto):
        estudo.rodar_estudo(entrada, tmp_path / "r.html")


def test_main_com_arquivo_inexistente_retorna_2(tmp_path, capsys):
    assert main([str(tmp_path / "nao_existe.json"), str(tmp_path / "r.html")]) == 2
    err = capsys.readouterr().err
    assert "Não foi possível ler o arquivo" in err and "Traceback" not in err


def test_main_com_destino_ilegivel_retorna_2_sem_simular(tmp_path, capsys, monkeypatch):
    def grava_falha(*args, **kwargs):
        raise OSError("sem permissão")
    monkeypatch.setattr(estudo, "simular_projeto", lambda projeto, progresso=None: {})   # evita o motor
    monkeypatch.setattr(estudo, "gravar_relatorio", grava_falha)
    arq = tmp_path / "p.json"
    arq.write_text(documento.salvar_json(documento.projeto_padrao()), encoding="utf-8")
    assert main([str(arq), str(tmp_path / "r.html")]) == 2
    err = capsys.readouterr().err
    assert "Não foi possível gravar o relatório em" in err and "Traceback" not in err


def test_main_com_pai_do_relatorio_sendo_arquivo_retorna_2(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(estudo, "simular_projeto", lambda projeto, progresso=None: {})   # evita o motor
    arq = tmp_path / "p.json"
    arq.write_text(documento.salvar_json(documento.projeto_padrao()), encoding="utf-8")
    pai = tmp_path / "arquivo"
    pai.write_text("x", encoding="utf-8")
    assert main([str(arq), str(pai / "r.html")]) == 2
    err = capsys.readouterr().err
    assert f"Não foi possível gravar o relatório em {pai / 'r.html'}." in err and "Traceback" not in err
