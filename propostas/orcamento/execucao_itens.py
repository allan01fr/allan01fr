"""Ponte entre os itens de kit da opção (opcao["itens_execucao"]) e o módulo de HH de execução.

Cada item de kit vira um item de `planejar_execucao` com chave própria ("kit_<n>") e uma linha de
produtividade (HH por unidade e função). Nenhuma conta nova de HH é feita aqui: o cálculo é o de execucao.py."""
import copy

from . import execucao as ex
from . import proposta as pp
from .erros import ErroEntrada

# Códigos curtos de função dos kits (dados/kits.json) -> chaves de FUNCOES_PADRAO.
MAPA_FUNCOES = {"TC": "mecanico_refrigeracao",   # técnico de climatização
                "ES": "ajudante",                # equipe de suporte / serviços gerais
                "PL": "encarregado"}             # planejamento / liderança
FUNCAO_DESCONHECIDA = "mecanico_refrigeracao"

# PROVISORIO: custo-hora (R$/h, sem encargos) usado quando params["execucao"]["custo_hora"] não existe.
CUSTO_HORA_PROVISORIO = {"encarregado": 72.0, "mecanico_refrigeracao": 54.0, "ajudante": 27.0,
                         "soldador": 60.0, "eletricista": 58.0, "tecnico_tab": 66.0}

_NEUTROS = {"altura": "ate_3m", "acesso": "livre", "ocupacao": "desocupado", "turno": "diurno"}


def _funcao(codigo):
    codigo = codigo or ""
    if codigo in ex.FUNCOES_PADRAO:
        return codigo
    return MAPA_FUNCOES.get(str(codigo).upper(), FUNCAO_DESCONHECIDA)


def _lista(opcao):
    return [it for it in (opcao.get("itens_execucao") or []) if isinstance(it, dict)]


def _fatores_opcao(opcao):
    """Fatores neutros, trocados pelos escolhidos na aba Execução (execucao.fator_padrao) quando válidos."""
    pad = (opcao.get("execucao") or {}).get("fator_padrao") or {}
    return {**_NEUTROS, **{n: v for n, v in pad.items() if v in ex.FATORES_PADRAO.get(n, {})}}


def itens_da_opcao(opcao):
    """Itens de kit da opção no formato de `planejar_execucao` (fatores neutros; material em
    custo_material_unit; a frente é o kit de origem)."""
    saida = []
    for n, it in enumerate(_lista(opcao)):
        saida.append({"id": str(n), "frente": it.get("kit") or "Execução", "item": f"kit_{n}",
                      "unidade": it.get("unid") or "un", "descricao": it.get("descricao", ""),
                      "quantidade": float(it.get("qtd") or 0), **_fatores_opcao(opcao),
                      "custo_material_unit": float(it.get("material") or 0), "categoria_material": "material"})
    return saida


def produtividade_da_opcao(opcao):
    """Linhas de produtividade (uma por item de kit) que acompanham `itens_da_opcao`."""
    return [{"item": f"kit_{n}", "funcao": _funcao(it.get("funcao")), "hh_por_unidade": float(it.get("hh_unid") or 0),
             "fator_calibracao": 1.0, "fonte": it.get("base") or "kit"} for n, it in enumerate(_lista(opcao))]


def config_da_opcao(opcao):
    """Configuração de execução da opção; cria o padrão (primeira fase ativa) quando ausente."""
    if not isinstance(opcao.get("execucao"), dict):
        fases = opcao.get("fases") or []
        fase = next((f["id"] for f in fases if f.get("ativa", True)), fases[0]["id"] if fases else "F1")
        opcao["execucao"] = ex.config_padrao(fase)
    return opcao["execucao"]


def _funcoes(params):
    cfg = (params.get("execucao") or {}).get("custo_hora") or {}
    custos = {**CUSTO_HORA_PROVISORIO, **{k: float(v) for k, v in cfg.items()}}
    return {k: {"nome": nome, "custo_hora": custos.get(k, 0.0)} for k, nome in ex.FUNCOES_PADRAO.items()}


def _encargos(params):
    return float((params.get("execucao") or {}).get("encargos", 1.0))


def calcular_execucao(opcao, params):
    """Plano de execução e custos da opção: {"plano", "custo_itens", "mao_obra", "material", "erro"}.
    custo_itens (descricao, custo) alimenta a curva ABC; erros de entrada voltam em "erro", em português."""
    r = {"plano": None, "custo_itens": [], "mao_obra": 0.0, "material": 0.0, "erro": None}
    itens = itens_da_opcao(opcao)
    if not itens:
        return r
    try:
        plano = ex.planejar_execucao(itens, produtividade_da_opcao(opcao), config_da_opcao(opcao))
        funcoes, enc = _funcoes(params), _encargos(params)
        for f, hh in plano["hh_funcao"].items():
            if hh > 0 and float(funcoes.get(f, {}).get("custo_hora", 0)) <= 0:
                raise ErroEntrada("funcao_sem_custo", f"A função '{f}' não tem custo-hora.", {"funcao": f})
        for lin in plano["linhas"]:
            it = itens[int(lin["item_id"])]
            mo = lin["hh"] * funcoes[lin["funcao"]]["custo_hora"] * enc
            r["mao_obra"] += mo
            r["custo_itens"].append({"descricao": it["descricao"] or it["item"], "custo": mo})
        for it in itens:
            mat = it["quantidade"] * it["custo_material_unit"]
            if mat > 0:
                r["material"] += mat
                r["custo_itens"].append({"descricao": it["descricao"] or it["item"], "custo": mat})
        r["plano"] = plano
    except (ErroEntrada, ValueError) as e:
        r.update({"plano": None, "custo_itens": [], "mao_obra": 0.0, "material": 0.0,
                  "erro": getattr(e, "mensagem", None) or str(e) or "Dados de execução inválidos."})
    return r


def sincronizar_fornecimentos(opcao, params):
    """Troca os fornecimentos de origem "execucao" pelos recalculados (HH e material dos itens de kit).
    Devolve quantos foram acrescentados; 0 (sem alterar nada) se não há itens ou há erro."""
    itens = itens_da_opcao(opcao)
    if not itens:
        return 0
    r = calcular_execucao(opcao, params)
    if r["erro"] or r["plano"] is None:
        return 0
    cfg = config_da_opcao(opcao)
    novos = ex.fornecimentos_execucao(r["plano"], itens, _funcoes(params), cfg["fase"], _encargos(params))
    for n in novos:
        n["origem"] = "execucao"
    forn = [f for f in opcao.setdefault("fornecimentos", []) if f.get("origem") != "execucao"]
    opcao["fornecimentos"] = forn + novos
    return len(novos)
