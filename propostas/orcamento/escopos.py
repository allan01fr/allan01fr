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


def _nome_livre(opcao, nome, ignorar=None):
    """Primeiro nome livre; a fase `ignorar` (a que vai ser reaproveitada) não conta como ocupando o nome."""
    usados = {f["nome"] for f in opcao["fases"] if f is not ignorar}
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
    if _fase_inicial_intocada(opcao):
        fase = opcao["fases"][0]
        fase.update(nome=_nome_livre(opcao, m["nome"], ignorar=fase), cobranca=m["cobranca"], modulo=modulo_id,
                    ativa=True)
    else:
        nome = _nome_livre(opcao, m["nome"])
        fase = pp.nova_fase(pp.proxima_fase(opcao), params, nome=nome, cobranca=m["cobranca"])
        fase["modulo"] = modulo_id
        opcao["fases"].append(fase)
    for serv in servicos:
        opcao["itens"].append(pp.novo_item(serv, fase=fase["id"]))
    _ligar_acompanhamento_execucao(opcao, fase, modulo_id)
    return fase


def _acompanhamento_padrao(fase):
    """Acompanhamento ainda na configuração de fábrica (pacote mensal, sem base informada)."""
    pk, ob = fase["pacote"], fase["obra"]
    return (fase["cobranca"] == "pacote" and pk.get("forma", "mensal") == "mensal" and not float(pk.get("horas_mes") or 0)
            and ob.get("base_modo", "informado") == "informado" and not float(ob.get("base_valor") or 0))


def _ligar_acompanhamento_execucao(opcao, fase, modulo_id):
    """Acompanhamento + Execução na mesma opção: % sobre o valor da execução, com o pacote por horas da obra pronto.
    Só quando a opção já tem itens de execução ou fornecimentos de execução; sem eles a base seria zero."""
    if not (opcao.get("itens_execucao") or any(f.get("origem") == "execucao" for f in opcao.get("fornecimentos", []))):
        return
    if modulo_id == "acompanhamento":
        alvo = [fase] if any(f.get("modulo") == "execucao" for f in opcao["fases"]) else []
    elif modulo_id == "execucao":
        alvo = [f for f in opcao["fases"] if f.get("modulo") == "acompanhamento" and _acompanhamento_padrao(f)]
    else:
        return
    for f in alvo:
        if not _acompanhamento_padrao(f):
            continue
        f["cobranca"] = "percentual"
        f["obra"]["base_modo"] = "execucao"
        f["obra"]["base_parte"] = "obra"
        f["pacote"].update(forma="obra", horas_dia_obra=2.0, horas_fixas=8.0)


def modulos_da_opcao(opcao):
    return [f.get("modulo", "") for f in opcao["fases"]]


def ligar_acompanhamento_execucao(opcao):
    """Chamado quando a execução é levada ao preço: acompanhamentos ainda no padrão passam a % sobre a execução."""
    _ligar_acompanhamento_execucao(opcao, None, "execucao")


def dimensionar_acompanhamento(opcao, params):
    """Ajusta o acompanhamento ao tamanho da execução desta opção (obra pequena → poucas visitas).

    Duração em meses = ⌈dias corridos ÷ 30⌉. Obra de até um mês: 1 mês, uma visita a cada 5 dias úteis
    (mínimo 2: início e entrega), relatório final único. Obras maiores: 4 visitas/mês. Só mexe nos serviços
    geral.acompanhamento_obra das fases de acompanhamento ativas; devolve quantos itens ajustou."""
    import math
    from . import execucao_itens as ei
    plano = ei.calcular_execucao(opcao, params).get("plano")
    if not plano:
        return 0
    dias_uteis = int(plano.get("prazo_dias_uteis") or 0)
    dias_corridos = int(plano.get("prazo_dias_corridos") or 0)
    if dias_uteis <= 0:
        return 0
    fases_acomp = {f["id"] for f in opcao["fases"] if f.get("modulo") == "acompanhamento" and f.get("ativa", True)}
    n = 0
    for it in opcao.get("itens", []):
        if it.get("servico") != "geral.acompanhamento_obra" or it.get("fase") not in fases_acomp:
            continue
        d = it.setdefault("dados", {})
        if dias_corridos <= 30:
            d.update(meses=1, visitas_mes=max(2, math.ceil(dias_uteis / 5)))
        else:
            d.update(meses=math.ceil(dias_corridos / 30), visitas_mes=4)
        d["relatorio"] = True
        it["dimensionado_pela_execucao"] = {"dias_uteis": dias_uteis, "dias_corridos": dias_corridos}
        n += 1
    return n
