"""Documento do projeto: valores padrão, completar chaves ausentes e arquivo JSON."""

import copy
import json

from .criterios import CRITERIOS_PADRAO

def projeto_padrao():
    """Escritório de exemplo (mesmo caso dos exemplos 02-04)."""
    return {
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


def carregar_json(texto):
    return completar(json.loads(texto))
