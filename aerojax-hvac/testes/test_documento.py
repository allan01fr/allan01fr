"""Validação do documento do projeto na entrada: formato, versão e tipos."""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from clima2d import documento
from referencia import PROJETO_EXEMPLO

INVALIDOS = [
    ([], "O projeto deve ser um objeto JSON."),
    ({"sala": 5}, "sala deve ser um objeto."),
    ({"versao": 99, "sala": {}}, "mais nova que a suportada (1)"),
    ({"formato": "clima2d-projeto", "versao": 0}, "Versão de projeto 0 não é suportada."),
    ({"formato": "clima2d-projeto", "versao": "1"}, "deve ser um número inteiro"),
    ({"formato": "clima2d-projeto", "versao": True}, "deve ser um número inteiro"),
    ({"formato": "clima2d-projeto"}, "A versão do projeto deve ser um número inteiro."),
    ({"formato": "duct-dx-project", "versao": 1}, 'Formato "duct-dx-project"'),
    ({"versao": 1}, 'O projeto não informa o formato (esperado "clima2d-projeto").'),
    ({"sala": {"largura": "5"}}, "sala.largura deve ser um número."),
    ({"sala": {"largura": True}}, "sala.largura deve ser um número."),
    ({"iluminacao_w_m2": float("nan")}, "iluminacao_w_m2 deve ser um número."),
    ({"fontes": {}}, "fontes deve ser uma lista."),
    ({"aberturas": [5]}, "aberturas[1] deve ser um objeto."),
    ({"aberturas": [{"parede": "frente", "tipo": "retorno", "inicio": 0, "fim": 1}]},
     "aberturas[1].parede deve ser um destes valores: esquerda, direita, teto, piso."),
    ({"aberturas": [{"parede": "teto", "tipo": "ar", "inicio": 0, "fim": 1}]},
     "aberturas[1].tipo deve ser um destes valores: insuflamento, retorno."),
    ({"aberturas": [{"parede": "teto", "tipo": "retorno", "inicio": 0}]},
     "aberturas[1].fim é obrigatório."),
    ({"fontes": [{"x0": 0, "x1": 1, "y0": 0, "y1": 1, "sensivel_w": 1}]},
     "fontes[1].latente_w é obrigatório."),
    ({"fontes": [{"nome": 3, "x0": 0, "x1": 1, "y0": 0, "y1": 1,
                  "sensivel_w": 1, "latente_w": 1}]}, "fontes[1].nome deve ser um texto."),
    ({"obstaculos": [{"x0": 0, "x1": 1, "y0": 0}]}, "obstaculos[1].y1 é obrigatório."),
    ({"simulacao": {"malha_cm": 0}}, "simulacao.malha_cm deve ser maior que zero."),
    ({"simulacao": {"tempo_s": -1}}, "simulacao.tempo_s deve ser maior que zero."),
    ({"nome": 5}, "nome deve ser um texto."),
    ({"responsavel": 5}, "responsavel deve ser um texto."),
]
PROIBIDO = ("Traceback", "Error", "object has", "NoneType", "Expecting", "attribute")   # "objeto" é permitido


@pytest.mark.parametrize("doc, trecho", INVALIDOS)
def test_documento_invalido_e_recusado(doc, trecho):
    with pytest.raises(documento.ErroProjeto) as e:
        documento.validar_documento(doc)
    assert trecho in str(e.value)
    assert not any(p in str(e.value) for p in PROIBIDO)


@pytest.mark.parametrize("texto, trecho", [
    (b"\xff\xfe{}", "não está codificado em UTF-8"),
    ("{", "não é um JSON válido (linha 1, coluna 2)"),
    ('{"iluminacao_w_m2": NaN}', "Números não finitos"),
    ('{"iluminacao_w_m2": -Infinity}', "Números não finitos"),
    ('{"nome": "a", "nome": "b"}', 'Chave repetida no projeto: "nome".'),
])
def test_texto_invalido_e_recusado(texto, trecho):
    with pytest.raises(documento.ErroProjeto) as e:
        documento.carregar_json(texto)
    assert trecho in str(e.value)
    assert not any(p in str(e.value) for p in PROIBIDO)


def test_bom_utf8_e_aceito():
    texto = b"\xef\xbb\xbf" + documento.salvar_json(documento.projeto_padrao()).encode("utf-8")
    assert documento.carregar_json(texto) == documento.projeto_padrao()


def test_arquivo_antigo_sem_versao_e_aceito_e_migrado():
    antigo = json.loads(PROJETO_EXEMPLO.read_text(encoding="utf-8"))
    assert "versao" not in antigo
    p = documento.carregar_json(PROJETO_EXEMPLO.read_bytes())
    assert (p["formato"], p["versao"]) == ("clima2d-projeto", 1)


def test_validar_nao_altera_a_entrada_e_preserva_campos_desconhecidos():
    entrada = {"sala": {"largura": 6.0, "extra": "x"}, "observacao": "livre"}
    copia = copy.deepcopy(entrada)
    p = documento.validar_documento(entrada)
    assert entrada == copia
    assert p["sala"]["extra"] == "x" and p["observacao"] == "livre" and p["sala"]["altura"] == 2.8


def test_salvar_e_carregar_grava_formato_e_versao():
    texto = documento.salvar_json(documento.projeto_padrao())
    assert '"formato": "clima2d-projeto"' in texto and '"versao": 1' in texto
    assert documento.carregar_json(texto) == documento.projeto_padrao()
