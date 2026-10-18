"""
Modelo de dados da proposta (salvo e aberto como JSON pela barra lateral do app).

Uma proposta tem dados gerais, o contexto que gera os fatores (complexidade,
documentação, acesso, urgência, risco), uma cópia dos parâmetros comerciais e
N opções. Cada opção é uma lista de serviços do catálogo com o formulário
preenchido, mais fornecimentos, pagamento e o modelo de preço escolhido.
"""

import copy
import datetime as dt
import json
import string

from . import catalogo as ct
from . import parametros as pm

CONTEXTO_PADRAO = {
    "dist_km": 20.0,
    "area_ref": 0.0,
    "complexidade": "media",
    "documentacao": "parcial",
    "acesso": "livre",
    "urgencia": "normal",
    "risco": "medio",
}
CATEGORIAS_FORNECIMENTO = ("material", "equipamento", "mo_execucao", "subcontrato")
MODELOS_PRECO = ("fechado", "hora", "fee")


def nova_opcao(letra, params, nome=None):
    return {
        "id": letra,
        "nome": nome or f"Opção {letra}",
        "itens": [],
        "fornecimentos": [],
        "prazo_execucao_dias": 0,
        "pagamento": [],
        "modelo_preco": "fechado",
        "fee_pct": float(params.get("fee_pct_padrao", 0.06)),
        "fee_base": 0.0,
    }


def novo_item(serv):
    return {
        "servico": serv["id"],
        "dados": ct.valores_padrao(serv),
        "ajustes": {},          # sobrescreve fatores globais só neste serviço: {"complexidade": "alta"}
        "fator_manual": 1.0,
        "descricao": "",        # nome do serviço na proposta; vazio = nome do catálogo
    }


def padrao(params, numero=None):
    hoje = dt.date.today()
    return {
        "versao": 1,
        "numero": numero or f"PC-KTK-001/{hoje.year}",
        "revisao": "00",
        "data": hoje.isoformat(),
        "validade_dias": 15,
        "prazo_pagamento_dias": 15,
        "cliente": {"razao": "", "contato": "", "signatario": "", "endereco": "", "cidade": "Rio de Janeiro", "uf": "RJ"},
        "objeto": "",
        "contexto": dict(CONTEXTO_PADRAO),
        "parametros": copy.deepcopy(params),
        "opcoes": [nova_opcao("A", params)],
    }


def completar(p, cat, params):
    """Preenche chaves ausentes (arquivos antigos ou feitos à mão) sem mexer no que existe."""
    base = padrao(params, p.get("numero"))
    for k, v in base.items():
        if k not in p:
            p[k] = copy.deepcopy(v)
    p["cliente"] = {**base["cliente"], **p.get("cliente", {})}
    p["contexto"] = {**CONTEXTO_PADRAO, **p.get("contexto", {})}
    p["parametros"] = pm.mesclar(params, p.get("parametros"))
    if not p["opcoes"]:
        p["opcoes"] = [nova_opcao("A", params)]
    for o in p["opcoes"]:
        for k, v in nova_opcao(o.get("id", "A"), params).items():
            o.setdefault(k, copy.deepcopy(v))
        for it in o["itens"]:
            serv = ct.servico(cat, it["servico"])
            dados = ct.valores_padrao(serv)
            dados.update({k: v for k, v in it.get("dados", {}).items() if k in dados})
            it["dados"] = dados
            it.setdefault("ajustes", {})
            it.setdefault("fator_manual", 1.0)
            it.setdefault("descricao", "")
    return p


def salvar_json(p):
    return json.dumps(p, ensure_ascii=False, indent=1)


def carregar_json(texto):
    p = json.loads(texto)
    if not isinstance(p, dict) or "opcoes" not in p:
        raise ValueError("o arquivo não é uma proposta (falta a lista 'opcoes')")
    return p


def proxima_letra(p):
    usadas = {o["id"] for o in p["opcoes"]}
    for letra in string.ascii_uppercase:
        if letra not in usadas:
            return letra
    raise ValueError("limite de 26 opções")


def duplicar_opcao(p, indice, nivel=None, nome=None):
    """Copia uma opção; com `nivel`, troca o campo 'nivel' (2D/3D/BIM) de todos os serviços que o têm."""
    nova = copy.deepcopy(p["opcoes"][indice])
    nova["id"] = proxima_letra(p)
    nova["nome"] = nome or f"Opção {nova['id']}"
    nova["pagamento"] = []
    if nivel:
        for it in nova["itens"]:
            if "nivel" in it["dados"]:
                it["dados"]["nivel"] = nivel
    p["opcoes"].append(nova)
    return nova
