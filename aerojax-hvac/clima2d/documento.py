"""Documento do projeto: valores padrão, completar chaves ausentes e arquivo JSON."""

import copy
import json
import math

from .criterios import CRITERIOS_PADRAO
from .malha import dimensoes_da_malha

FORMATO_PROJETO = "clima2d-projeto"
VERSAO_ESQUEMA = 1

SECOES_OBJETO = ("sala", "superficies", "condicao", "insuflamento", "simulacao", "criterios")
SECOES_LISTA = ("aberturas", "fontes", "obstaculos")
PAREDES = ("esquerda", "direita", "teto", "piso")
TIPOS_ABERTURA = ("insuflamento", "retorno")
POSITIVOS_SIMULACAO = ("malha_cm", "tempo_s", "tempo_media_s", "nu_efetiva")
# Limites derivados das faixas da interface (app/app.py); cada teto fica no máximo do app.
# Malha: o maior caso que o app permite é largura 50 m (L165) x pé-direito 15 m (L166) com a
# malha mais fina, 2,5 cm (L298): 2.000 x 600 = 1.200.000 células (nx * ny, já com o mínimo
# de 8 por eixo da montagem).
MAX_CELULAS = 1_200_000
# Tempo simulado: máximo de 240 min (app/app.py L301) = 14.400 s.
MAX_TEMPO_S = 240 * 60.0
# Tempo de média: máximo de 120 min (app/app.py L303) = 7.200 s (e nunca maior que tempo_s).
MAX_TEMPO_MEDIA_S = 120 * 60.0
# Vazão de insuflamento: máximo de 50.000 m3/h (app/app.py L266).
MAX_VAZAO_M3H = 50_000.0
# Total de passos de tempo explícitos. Caso extremo dentro das faixas do app (malha 5 cm,
# 240 min, 50.000 m3/h na sala de exemplo) dá ~4,4e7 passos; o teto é ~2x isso. Bloqueia
# combinações (viscosidade enorme, profundidade ínfima) que deixariam o passo quase nulo.
MAX_PASSOS = 100_000_000
LIMITES_SUPERIORES = (("simulacao", "tempo_s", MAX_TEMPO_S),
                      ("simulacao", "tempo_media_s", MAX_TEMPO_MEDIA_S),
                      ("insuflamento", "vazao_m3h", MAX_VAZAO_M3H))
# Campos obrigatórios de cada item de lista (todos numéricos, exceto os de texto abaixo).
OBRIGATORIOS_ABERTURA = ("inicio", "fim")
OBRIGATORIOS_FONTE = ("x0", "x1", "y0", "y1", "sensivel_w", "latente_w")
OBRIGATORIOS_OBSTACULO = ("x0", "x1", "y0", "y1")


class ErroProjeto(ValueError):
    """Projeto inválido; str(erro) é a mensagem para o usuário."""


def projeto_padrao():
    """Escritório de exemplo (mesmo caso dos exemplos 02-04)."""
    return {
        "formato": FORMATO_PROJETO,
        "versao": VERSAO_ESQUEMA,
        "nome": "Escritório - exemplo",
        "responsavel": "",
        "sala": {"largura": 5.0, "altura": 2.8, "profundidade": 4.0},
        "aberturas": [
            {"parede": "esquerda", "inicio": 2.35, "fim": 2.45, "tipo": "insuflamento"},
            {"parede": "esquerda", "inicio": 2.55, "fim": 2.75, "tipo": "retorno"},
        ],
        "fontes": [
            {"nome": "2 pessoas", "x0": 2.8, "x1": 3.2, "y0": 0.0, "y1": 1.2,
             "sensivel_w": 150.0, "latente_w": 110.0},
            {"nome": "Computador", "x0": 3.6, "x1": 3.9, "y0": 0.75, "y1": 0.85,
             "sensivel_w": 100.0, "latente_w": 0.0},
        ],
        "obstaculos": [
            {"nome": "Mesa", "x0": 3.3, "x1": 4.3, "y0": 0.70, "y1": 0.75},
        ],
        "superficies": {"fluxo_esquerda": 0.0, "fluxo_direita": 40.0,
                        "fluxo_piso": 0.0, "fluxo_teto": 10.0},
        "iluminacao_w_m2": 0.0,
        "condicao": {"T_alvo": 24.0, "UR_alvo": 0.50, "met": 1.1, "clo": 0.5},
        "insuflamento": {"vazao_m3h": 600.0, "angulo_graus": 30.0, "temperatura": 19.6,
                         "ur_saida": 0.64},
        "simulacao": {"malha_cm": 10.0, "tempo_s": 1800.0, "tempo_media_s": 600.0,
                      "nu_efetiva": 1.5e-3},
        "criterios": dict(CRITERIOS_PADRAO),
    }


def completar(projeto):
    """Preenche chaves ausentes com o padrão (projetos antigos/importados)."""
    p = copy.deepcopy(projeto)
    base = projeto_padrao()
    for k, v in base.items():
        if k not in p:
            p[k] = copy.deepcopy(v)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                p[k].setdefault(kk, vv)
    return p


def salvar_json(projeto):
    return json.dumps(projeto, ensure_ascii=False, indent=2)


def _exigir_objeto(valor, caminho):
    if not isinstance(valor, dict):
        raise ErroProjeto(f"{caminho} deve ser um objeto.")


def _exigir_lista(valor, caminho):
    if not isinstance(valor, list):
        raise ErroProjeto(f"{caminho} deve ser uma lista.")


def _exigir_numero(valor, caminho):
    # bool é int em Python, mas "true" não é uma medida.
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroProjeto(f"{caminho} deve ser um número.")
    try:
        finito = math.isfinite(valor)
    except OverflowError:  # inteiro gigante demais para virar float
        finito = False
    if not finito:
        raise ErroProjeto(f"{caminho} deve ser um número.")


def _exigir_texto(valor, caminho):
    if not isinstance(valor, str):
        raise ErroProjeto(f"{caminho} deve ser um texto.")


def _exigir_opcao(valor, opcoes, caminho):
    if valor not in opcoes:
        raise ErroProjeto(f"{caminho} deve ser um destes valores: {', '.join(opcoes)}.")


def _exigir_campos_numericos(item, campos, caminho):
    for campo in campos:
        if campo not in item:
            raise ErroProjeto(f"{caminho}.{campo} é obrigatório.")
        _exigir_numero(item[campo], f"{caminho}.{campo}")


def _validar_versao_e_formato(doc):
    tem_formato, tem_versao = "formato" in doc, "versao" in doc
    if not tem_formato and not tem_versao:
        return  # arquivo antigo (versão 0): completar() grava formato e versão atuais
    versao = doc.get("versao")
    if isinstance(versao, bool) or not isinstance(versao, int):
        raise ErroProjeto("A versão do projeto deve ser um número inteiro.")
    if versao > VERSAO_ESQUEMA:
        raise ErroProjeto(f"O projeto é da versão {versao}, mais nova que a suportada "
                          f"({VERSAO_ESQUEMA}). Atualize o Clima2D.")
    if versao < 1:
        raise ErroProjeto(f"Versão de projeto {versao} não é suportada.")
    if not tem_formato:
        raise ErroProjeto(f'O projeto não informa o formato (esperado "{FORMATO_PROJETO}").')
    if doc["formato"] != FORMATO_PROJETO:
        raise ErroProjeto(f'Formato "{doc["formato"]}" não é de projeto do Clima2D '
                          f'(esperado "{FORMATO_PROJETO}").')


def _validar_itens(p):
    for n, a in enumerate(p["aberturas"], start=1):
        caminho = f"aberturas[{n}]"
        _exigir_objeto(a, caminho)
        for campo in ("parede", "tipo"):
            if campo not in a:
                raise ErroProjeto(f"{caminho}.{campo} é obrigatório.")
        _exigir_opcao(a["parede"], PAREDES, f"{caminho}.parede")
        _exigir_opcao(a["tipo"], TIPOS_ABERTURA, f"{caminho}.tipo")
        _exigir_campos_numericos(a, OBRIGATORIOS_ABERTURA, caminho)
    for secao, obrigatorios in (("fontes", OBRIGATORIOS_FONTE), ("obstaculos", OBRIGATORIOS_OBSTACULO)):
        for n, item in enumerate(p[secao], start=1):
            caminho = f"{secao}[{n}]"
            _exigir_objeto(item, caminho)
            if item.get("nome") is not None:
                _exigir_texto(item["nome"], f"{caminho}.nome")
            _exigir_campos_numericos(item, obrigatorios, caminho)


def _validar_tamanho_da_malha(p):
    """Recusa salas/malhas cujo número de células é absurdo (ou não finito)."""
    try:
        nx, ny = dimensoes_da_malha(p["sala"]["largura"], p["sala"]["altura"],
                                    p["simulacao"]["malha_cm"])
    except (ArithmeticError, ValueError):  # razão infinita/não finita ou malha nula
        nx = ny = math.inf
    if nx * ny > MAX_CELULAS:
        raise ErroProjeto(f"A malha da simulação tem células demais (máximo {MAX_CELULAS:,}); "
                          "aumente simulacao.malha_cm ou reduza as dimensões da sala."
                          .replace(",", "."))


def _validar_limites_superiores(p):
    for secao, chave, teto in LIMITES_SUPERIORES:
        if p[secao][chave] > teto:
            raise ErroProjeto(f"{secao}.{chave} deve ser no máximo {teto:g}.")
    if p["simulacao"]["tempo_media_s"] > p["simulacao"]["tempo_s"]:
        raise ErroProjeto("simulacao.tempo_media_s não pode ser maior que simulacao.tempo_s.")


def validar_documento(documento):
    """Valida, completa e devolve uma cópia do projeto. Só lança ErroProjeto."""
    if not isinstance(documento, dict):
        raise ErroProjeto("O projeto deve ser um objeto JSON.")
    _validar_versao_e_formato(documento)
    for secao in SECOES_OBJETO:
        if secao in documento:
            _exigir_objeto(documento[secao], secao)
    for secao in SECOES_LISTA:
        if secao in documento:
            _exigir_lista(documento[secao], secao)

    p = completar(documento)
    for secao in SECOES_OBJETO:
        for chave in projeto_padrao()[secao]:
            _exigir_numero(p[secao][chave], f"{secao}.{chave}")
    _exigir_numero(p["iluminacao_w_m2"], "iluminacao_w_m2")
    for chave in POSITIVOS_SIMULACAO:
        if p["simulacao"][chave] <= 0:
            raise ErroProjeto(f"simulacao.{chave} deve ser maior que zero.")
    _validar_limites_superiores(p)
    for campo in ("nome", "responsavel"):
        _exigir_texto(p[campo], campo)
    _validar_itens(p)
    _validar_tamanho_da_malha(p)
    return p


def _recusar_nao_finito(constante):
    raise ErroProjeto("Números não finitos (NaN ou Infinity) não são permitidos.")


def _objeto_sem_chave_repetida(pares):
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ErroProjeto(f'Chave repetida no projeto: "{chave}".')
        objeto[chave] = valor
    return objeto


def carregar_json(texto):
    """Lê o JSON do projeto (texto ou bytes UTF-8) em modo estrito e o valida."""
    try:
        if isinstance(texto, (bytes, bytearray)):
            texto = bytes(texto).decode("utf-8-sig")
        doc = json.loads(texto, object_pairs_hook=_objeto_sem_chave_repetida,
                         parse_constant=_recusar_nao_finito)
    except UnicodeDecodeError:
        raise ErroProjeto("O arquivo não está codificado em UTF-8.") from None
    except json.JSONDecodeError as e:
        raise ErroProjeto(f"O arquivo não é um JSON válido (linha {e.lineno}, coluna {e.colno}).") from None
    except ErroProjeto:
        raise
    except (RecursionError, ValueError):  # aninhamento absurdo, número com milhares de dígitos
        raise ErroProjeto("O arquivo não é um JSON válido.") from None
    return validar_documento(doc)
