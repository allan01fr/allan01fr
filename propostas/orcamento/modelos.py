"""
Operações sobre a proposta que não mudam o modelo de dados: duplicar uma proposta com ids novos
e aplicar kits de execução (conjuntos de atividades-padrão) a uma opção.

Os kits ficam em dados/kits.json. Os valores lá são provisórios e devem ser ajustados com os dados da empresa.
"""

import copy
import json
import os
import uuid

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMINHO_KITS = os.path.join(RAIZ, "dados", "kits.json")


def _novo_id():
    return uuid.uuid4().hex[:8]


def duplicar_proposta(proposta):
    """Cópia independente da proposta. Ids de opções, fases e fornecimentos são novos; as referências
    entre eles (fase de cada item, base de obra, fase de execução) são reescritas para os ids novos.
    Número, revisão e data são zerados; o cliente perde o nome. `origem` guarda o identificador da original."""
    nova = copy.deepcopy(proposta)
    nova["origem"] = proposta.get("id", proposta.get("numero", ""))
    if "id" in nova:
        nova["id"] = _novo_id()
    for campo in ("numero", "revisao", "data"):
        if campo in nova:
            nova[campo] = ""
    cliente = nova.get("cliente")
    if isinstance(cliente, dict):
        for campo in ("razao", "nome"):
            if campo in cliente:
                cliente[campo] = ""

    opcoes = nova.get("opcoes", [])
    # ids de opção (A, B…) ficam: a tela nomeia "Opção A/B" por eles e a proposta nova já isola tudo.
    for o in opcoes:
        mapa_fases = {f["id"]: _novo_id() for f in o.get("fases", [])}
        for f in o.get("fases", []):
            f["id"] = mapa_fases[f["id"]]
            obra = f.get("obra") or {}
        for x in o.get("itens", []) + o.get("fornecimentos", []):
            if x.get("fase") in mapa_fases:
                x["fase"] = mapa_fases[x["fase"]]
            if "uid" in x:
                x["uid"] = _novo_id()
        cfg = o.get("execucao")
        if isinstance(cfg, dict) and cfg.get("fase") in mapa_fases:
            cfg["fase"] = mapa_fases[cfg["fase"]]
    return nova


def carregar_kits(caminho=None):
    """Lista de kits de execução (dados/kits.json, ou o arquivo informado)."""
    with open(caminho or CAMINHO_KITS, encoding="utf-8") as f:
        dados = json.load(f)
    return copy.deepcopy(dados["kits"] if isinstance(dados, dict) else dados)


def aplicar_kit(opcao, kit, fase_id=None):
    """Acrescenta os itens do kit à opção, na fase informada (padrão: a primeira fase).

    Os itens de kit são de execução (hh_unid e funcao, sem preço de fornecimento), por isso não entram em
    `fornecimentos`, que o motor precifica. Ficam em opcao["itens_execucao"], cada um com "fase" e "kit"."""
    fase = fase_id or (opcao["fases"][0]["id"] if opcao.get("fases") else "F1")
    destino = opcao.setdefault("itens_execucao", [])
    for it in kit.get("itens", []):
        destino.append({**copy.deepcopy(it), "fase": fase, "kit": kit["id"]})
    return opcao
