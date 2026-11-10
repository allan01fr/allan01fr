"""
Módulos de escopo: a proposta é montada por escopos separados (só projeto, só acompanhamento de obra,
execução, só inspeção com laudo de conformidade ou avaliação de desempenho), cada um numa fase própria
que pode ser ligada e desligada. Sem Streamlit e sem I/O.
"""

from . import catalogo as ct
from . import proposta as pp

MODULOS = {
    "projeto": {
        "nome": "Projeto",
        "descricao": "Cálculo de carga térmica e projeto executivo do sistema, para escopo fechado.",
        "cobranca": "fechado",
        "servicos": ["hvac.carga_termica", "hvac.projeto"],
    },
    "acompanhamento": {
        "nome": "Acompanhamento de obra",
        "descricao": "Fiscalização e assessoria técnica durante a obra, vendida como pacote de horas mensal.",
        # Pacote com horas_mes = 0 e horas = 0 não precisa de padrão próprio: cobranca.pacote deriva as horas
        # do serviço (horas dos serviços da fase / meses), então o módulo já precifica > 0 com os padrões.
        "cobranca": "pacote",
        "servicos": ["geral.acompanhamento_obra"],
    },
    "execucao": {
        "nome": "Execução",
        "descricao": "Execução da obra. Hoje, materiais e mão de obra entram como fornecimentos desta fase "
                     "(aba 3); a aba própria de execução vem depois.",
        "cobranca": "fechado",
        "servicos": [],
    },
    "inspecao_laudo": {
        "nome": "Inspeção com laudo de conformidade",
        "descricao": "Inspeção do sistema existente com laudo de conformidade às normas aplicáveis.",
        "cobranca": "fechado",
        "servicos": ["hvac.inspecao_conformidade"],
    },
    "desempenho": {
        "nome": "Avaliação de desempenho",
        "descricao": "Medições e análise do desempenho do sistema em operação, com relatório.",
        "cobranca": "fechado",
        "servicos": ["hvac.desempenho"],
    },
}


def modulo(modulo_id):
    try:
        return MODULOS[modulo_id]
    except KeyError:
        raise KeyError(f"Módulo de escopo desconhecido: {modulo_id!r}. Válidos: {', '.join(MODULOS)}.") from None


def _nome_livre(opcao, nome):
    usados = {f["nome"] for f in opcao["fases"]}
    if nome not in usados:
        return nome
    n = 2
    while f"{nome} {n}" in usados:
        n += 1
    return f"{nome} {n}"


def _fase_inicial_intocada(opcao):
    fases = opcao["fases"]
    if len(fases) != 1 or fases[0].get("modulo"):
        return False
    fid = fases[0]["id"]
    return not any(x.get("fase") == fid for x in opcao["itens"] + opcao["fornecimentos"])


def incluir(opcao, modulo_id, cat, params):
    """Cria (ou reaproveita a fase inicial vazia) a fase do módulo e seus serviços; devolve a fase."""
    m = modulo(modulo_id)
    if opcao.get("modalidade") == "estimativa":
        raise ValueError("Módulos de escopo valem para propostas em fases, não para a estimativa interna.")
    servicos = [ct.servico(cat, sid) for sid in m["servicos"]]     # falha antes de alterar a opção
    nome = _nome_livre(opcao, m["nome"])
    if _fase_inicial_intocada(opcao):
        fase = opcao["fases"][0]
        fase.update(nome=nome, cobranca=m["cobranca"], modulo=modulo_id)
    else:
        fase = pp.nova_fase(pp.proxima_fase(opcao), params, nome=nome, cobranca=m["cobranca"])
        fase["modulo"] = modulo_id
        opcao["fases"].append(fase)
    for serv in servicos:
        opcao["itens"].append(pp.novo_item(serv, fase=fase["id"]))
    return fase


def modulos_da_opcao(opcao):
    return [f.get("modulo", "") for f in opcao["fases"]]
