"""
Motor de orçamento: formulário → horas → custo → preço → cronograma → pagamento.

Horas de uma atividade, por perfil:
    h = (fixo + unid × q^b) × fatores × fator_manual × calibração
onde q é o driver avaliado sobre o formulário do serviço e os fatores vêm do
contexto da proposta (complexidade, documentação, acesso, urgência) ou de campos
de opções do próprio serviço (nível 2D/3D/BIM, fase, sistema...).

Escopo fechado:
    preço dos serviços = (MO + overhead + diretos) × (1 + contingência) ÷ (1 − impostos − margem)
    preço total        = preço dos serviços + Σ fornecimentos × (1 + BDI da categoria)

A opção da proposta é uma sequência de fases (ex.: laudo, estudo de viabilidade, projeto,
assessoria de obra), cada uma com a sua cobrança: escopo fechado, hora técnica, % da obra ou
pacote de horas (cobranca.py). Cada fase é precificada sozinha, com a sua ART, porque pode ser
contratada separadamente. A opção "estimativa" é o valor global da obra, interno: base do % da
assessoria e do CAPEX da viabilidade.

A planilha exportada repete estas mesmas contas em fórmulas; os testes conferem
que as duas dão o mesmo resultado.
"""

import math

from . import catalogo as ct
from . import cobranca as cb
from . import expressao
from . import parametros as pm

UFS_SEM_VISTO = ("RJ", "SP")


# ----------------------------------------------------------------------------- horas
def fatores_atividade(cat, proposta, item, ativ, ctx):
    det = {}
    for f in ativ.get("fatores", []):
        if f in cat["fatores"]:
            chave = item.get("ajustes", {}).get(f) or proposta["contexto"][f]
            det[f] = ct.fator_global(cat, f, chave)
        else:
            det[f] = ctx[f]
    manual = float(item.get("fator_manual", 1.0) or 1.0)
    if manual != 1.0:
        det["manual"] = manual
    calib = float(ativ.get("calibracao", 1.0) or 1.0)
    if calib != 1.0:
        det["calibracao"] = calib
    total = 1.0
    for v in det.values():
        total *= v
    return total, det


def linhas_item(cat, proposta, item, indice):
    """Atividades (com horas) e custos diretos de um serviço da opção."""
    serv = ct.servico(cat, item["servico"])
    ctx = ct.contexto(serv, item["dados"], proposta["contexto"])
    perfis = list(cat["perfis"])
    nome_serv = item.get("descricao") or serv["nome"]
    linhas = []
    for a in serv["atividades"]:
        q = max(expressao.avaliar(a.get("driver"), ctx), 0.0) if a.get("driver") else 0.0
        b = float(a.get("b", 1.0))
        fator, det = fatores_atividade(cat, proposta, item, a, ctx)
        fixo = {p: float(a.get("fixo", {}).get(p, 0)) for p in perfis}
        unid = {p: float(a.get("unid", {}).get(p, 0)) for p in perfis}
        horas = {p: (fixo[p] + unid[p] * q ** b) * fator for p in perfis}
        total = sum(horas.values())
        if total <= 0:
            continue
        linhas.append({
            "item": indice, "servico": serv["id"], "servico_nome": nome_serv,
            "disciplina": serv["disciplina"], "atividade": a["id"], "nome": a["nome"],
            "entregavel": a.get("entregavel", ""), "etapa": a["etapa"],
            "q": q, "b": b, "fator": fator, "fatores_det": det,
            "fixo": fixo, "unid": unid, "horas": horas, "total_h": total,
        })
    diretos = []
    for d in serv.get("diretos", []):
        qtd = max(expressao.avaliar(d["qtd"], ctx), 0.0)
        if qtd <= 0:
            continue
        diretos.append({
            "item": indice, "descricao": d["nome"], "servico_nome": nome_serv,
            "unid": d.get("unid", "un"), "qtd": qtd, "valor_unit": float(d["valor_unit"]),
            "valor": qtd * float(d["valor_unit"]),
        })
    return linhas, diretos


# ----------------------------------------------------------------------------- custos da opção
def dias_campo(cat, params, linhas):
    campo = {e["id"] for e in cat["etapas"] if e.get("campo")}
    h = sum(l["total_h"] for l in linhas if l["etapa"] in campo)
    if h <= 0:
        return 0
    d = params["deslocamento"]
    return math.ceil(h / (params["cronograma"]["horas_dia"] * max(1, d["pessoas_campo"])))


def deslocamento(params, dist_km, dias):
    """Custo de deslocamento: isento perto da base, ida e volta diária até o raio de pernoite,
    acima disso uma viagem com diárias para a equipe de campo."""
    d = params["deslocamento"]
    if dias <= 0 or dist_km <= d["raio_isento_km"]:
        return 0.0, ""
    if dist_km <= d["raio_pernoite_km"]:
        return dias * 2 * dist_km * d["rs_km"], f"{dias} dia(s) de campo × ida e volta de {dist_km:.0f} km"
    valor = 2 * dist_km * d["rs_km"] + dias * d["pessoas_campo"] * d["diaria"]
    return valor, f"1 viagem de {dist_km:.0f} km + {dias} diária(s) × {d['pessoas_campo']} pessoa(s)"


CATEGORIAS_EQUIP = ("equipamento", "material")
CATEGORIAS_EXEC = ("mo_execucao", "subcontrato")


def valor_art(params, valor_contrato):
    """Taxa de ART pela faixa do valor do contrato (Tabela A do Confea) ou valor fixo."""
    art = params["art"]
    if art.get("modo", "fixo") != "faixas" or not art.get("faixas"):
        return float(art["valor"])
    for f in art["faixas"]:
        if f.get("ate") is None or valor_contrato <= float(f["ate"]):
            return float(f["valor"])
    return float(art["faixas"][-1]["valor"])


def eh_estimativa(opcao):
    return opcao.get("modalidade") == "estimativa"


def checklist_turnkey(cat, opcao):
    """Etapas da obra completa consideradas na estimativa do valor global: atendida, dispensada
    (fora da estimativa), opcional ou faltando."""
    tipos = {ct.servico(cat, it["servico"])["tipo"] for it in opcao["itens"]}
    sids = {it["servico"] for it in opcao["itens"]}
    cats = {f["categoria"] for f in opcao.get("fornecimentos", [])
            if float(f.get("qtd") or 0) * float(f.get("custo_unit") or 0) > 0}
    dispensas = set(opcao.get("turnkey_dispensas", []))
    saida = []
    for e in cat["turnkey"]["etapas"]:
        ok = bool(tipos & set(e.get("tipos", []))) or bool(sids & set(e.get("servicos", []))) \
            or bool(cats & set(e.get("categorias", [])))
        if ok:
            status = "atendida"
        elif e["id"] in dispensas:
            status = "dispensada"
        elif e.get("opcional"):
            status = "opcional"
        else:
            status = "faltando"
        saida.append({"id": e["id"], "rotulo": e["rotulo"], "status": status})
    return saida


def _fornecimentos(params, fornecimentos):
    fornec = []
    for f in fornecimentos:
        custo = float(f.get("qtd", 0) or 0) * float(f.get("custo_unit", 0) or 0)
        bdi = float(params["bdi_fornecimento"][f["categoria"]])
        fornec.append({**f, "custo": custo, "bdi": bdi, "preco": custo * (1 + bdi)})
    return fornec


def _overhead(params, custo_mo, total_h):
    if params["overhead"]["metodo"] == "hora":
        return total_h * pm.overhead_por_hora(params)
    return custo_mo * float(params["overhead"]["pct"])


def _custos(cat, proposta, opcao, indices, fornecimentos, garantia=False, com_art=True):
    """Horas, custos diretos e cadeia de preço de um conjunto de serviços (uma fase ou a estimativa)."""
    params = proposta["parametros"]
    perfis = list(cat["perfis"])
    linhas, diretos_base = [], []
    for i in indices:
        li, di = linhas_item(cat, proposta, opcao["itens"][i], i)
        linhas += li
        diretos_base += di

    dias = dias_campo(cat, params, linhas)
    v_desl, memoria = deslocamento(params, float(proposta["contexto"].get("dist_km", 0) or 0), dias)
    if v_desl > 0:
        diretos_base.append({"item": None, "descricao": "Deslocamento", "servico_nome": memoria,
                             "unid": "vb", "qtd": 1.0, "valor_unit": v_desl, "valor": v_desl})

    fornec = _fornecimentos(params, fornecimentos)
    custo_fornec = sum(f["custo"] for f in fornec)
    preco_fornec = sum(f["preco"] for f in fornec)
    if garantia and custo_fornec > 0 and params["turnkey"]["garantia_pct"] > 0:
        g = params["turnkey"]
        diretos_base.append({"item": None, "descricao": "Provisão de garantia", "garantia": True,
                             "servico_nome": f"{g['garantia_pct']:.1%} do custo de fornecimento e execução · "
                                             f"{g['garantia_meses']} meses".replace(".", ","),
                             "unid": "%", "qtd": custo_fornec, "valor_unit": float(g["garantia_pct"]),
                             "valor": custo_fornec * float(g["garantia_pct"])})

    horas_perfil = {p: sum(l["horas"][p] for l in linhas) for p in perfis}
    total_h = sum(horas_perfil.values())
    custo_h = {p: float(params["perfis"][p]["custo_h"]) for p in perfis}
    taxa_h = {p: float(params["perfis"][p]["taxa_venda_h"]) for p in perfis}
    for l in linhas:
        l["custo_mo"] = sum(l["horas"][p] * custo_h[p] for p in perfis)
    custo_mo = sum(horas_perfil[p] * custo_h[p] for p in perfis)
    overhead = _overhead(params, custo_mo, total_h)

    risco = proposta["contexto"]["risco"]
    cont_pct = float(params["contingencia"][risco])
    imp = pm.aliquota_impostos(params)
    margem = float(params["margem"])
    divisor = 1 - imp - margem
    if divisor <= 0.05:
        raise ValueError(f"impostos ({imp:.1%}) + margem ({margem:.1%}) deixam menos de 5% para o custo")

    def cadeia(art):
        diretos = list(diretos_base)
        if com_art and art > 0:
            diretos.append({"item": None, "descricao": "Taxa de ART junto ao CREA", "servico_nome": "",
                            "unid": "un", "qtd": 1.0, "valor_unit": art, "valor": art})
        diretos_total = sum(d["valor"] for d in diretos)
        custo_servicos = custo_mo + overhead + diretos_total
        contingencia = custo_servicos * cont_pct
        preco_servicos = (custo_servicos + contingencia) / divisor
        return diretos, diretos_total, custo_servicos, contingencia, preco_servicos

    # a ART depende do valor do contrato, que depende da ART: duas passadas bastam (faixas monotônicas)
    art = valor_art(params, 0.0)
    for _ in range(4):
        diretos, diretos_total, custo_servicos, contingencia, preco_servicos = cadeia(art)
        nova = valor_art(params, preco_servicos + preco_fornec)
        if nova == art:
            break
        art = nova

    honorarios_hora = sum(horas_perfil[p] * taxa_h[p] for p in perfis)
    reembolso = diretos_total * (1 + float(params["reembolsaveis_adm"])) / (1 - imp)
    return {
        "linhas": linhas, "diretos": diretos, "fornecimentos": fornec,
        "horas_perfil": horas_perfil, "total_h": total_h, "dias_campo": dias, "art": art if com_art else 0.0,
        "custo_h": custo_h, "taxa_h": taxa_h,
        "custo_mo": custo_mo, "overhead": overhead, "diretos_total": diretos_total,
        "custo_servicos": custo_servicos, "cont_pct": cont_pct, "contingencia": contingencia,
        "imp_pct": imp, "margem_pct": margem,
        "preco_servicos": preco_servicos, "impostos": preco_servicos * imp, "margem": preco_servicos * margem,
        "custo_fornec": custo_fornec, "preco_fornec": preco_fornec,
        "preco_fechado": preco_servicos + preco_fornec,
        "honorarios_hora": honorarios_hora, "reembolso": reembolso,
        "preco_hora": honorarios_hora + reembolso + preco_fornec,
        "preco_hora_teto": honorarios_hora * (1 + cont_pct) + reembolso + preco_fornec,
        "preco_minimo_servicos": custo_servicos / (1 - imp),
    }


def _margem_efetiva(honorarios, custo, imp):
    return (honorarios * (1 - imp) - custo) / honorarios if honorarios > 0 else None


def base_obra(fase, res_fase, estimativas):
    """Valor global da obra que serve de base ao % e à taxa de desempenho. Devolve (valor, origem)."""
    ob = fase["obra"]
    if ob.get("base_modo") == "opcao":
        e = (estimativas or {}).get(ob.get("base_opcao"))
        if e is None:
            return 0.0, f"estimativa {ob.get('base_opcao') or '—'} não encontrada"
        if ob.get("base_parte") == "global":
            return e["preco_fechado"], f"preço global da estimativa {e['id']}"
        return e["preco_fornec"], f"fornecimentos e execução da estimativa {e['id']}"
    if ob.get("base_modo") == "fornecimentos":
        return res_fase["custo_fornec"], "custo dos fornecimentos da fase"
    return float(ob.get("base_valor") or 0), "valor informado"


def _etapa_obra(fase, meses):
    return [{"etapa": "obra", "rotulo": f"{fase['nome']} — durante a obra ({meses} meses)",
             "marco": "Conclusão da obra e relatório final", "campo": True, "horas": 0.0, "meses": meses,
             "dias_uteis": 21 * meses, "dias_corridos": 30 * meses, "inicio": 1, "fim": 21 * meses}]


def precificar_fase(cat, proposta, opcao, fase, estimativas=None):
    params = proposta["parametros"]
    estimativa = eh_estimativa(opcao)
    cob = "fechado" if estimativa else fase["cobranca"]      # o valor global da obra é sempre um preço fechado
    if estimativa:   # a estimativa considera todos os serviços e fornecimentos da opção
        idx, forn = list(range(len(opcao["itens"]))), opcao["fornecimentos"]
    else:   # sem fase válida (arquivo feito à mão), o serviço ou fornecimento fica na primeira fase
        ids = [f["id"] for f in opcao["fases"]]

        def da_fase(x):
            return (x.get("fase") if x.get("fase") in ids else ids[0]) == fase["id"]
        idx = [i for i, it in enumerate(opcao["itens"]) if da_fase(it)]
        forn = [f for f in opcao["fornecimentos"] if da_fase(f)]
    r = _custos(cat, proposta, opcao, idx, forn, garantia=estimativa,
                com_art=bool(idx) or cob in ("percentual", "pacote"))
    r.update({"id": fase["id"], "nome": fase["nome"], "cobranca": cob, "servicos": idx,
              "horas_servicos": dict(r["horas_perfil"]), "desempenho": None})
    imp = r["imp_pct"]
    meses = None
    if cob == "hora":
        honorarios = r["honorarios_hora"] + r["reembolso"]
        r.update(preco=r["preco_hora"], preco_fixo=0.0, preco_estimado=r["preco_hora"])
    elif cob == "percentual":
        base, origem = base_obra(fase, r, estimativas)
        meses = int(fase["obra"].get("meses") or 0)      # 0 = prazo pelas horas dos serviços (% sem obra acompanhada)
        hp = cb.honorario_percentual(fase["percentual"], base, max(1, meses), fase["obra"].get("curva", "s"))
        honorarios = hp["total"]
        r.update(percentual=hp, base=base, base_origem=origem,
                 preco=honorarios + r["preco_fornec"], preco_fixo=hp["fixo"] + r["preco_fornec"], preco_estimado=hp["estimado"],
                 pct_minimo=r["preco_minimo_servicos"] / base if base > 0 else None,
                 pct_equivalente_fechado=r["preco_servicos"] / base if base > 0 else None)
    elif cob == "pacote":
        pk = cb.pacote(fase["pacote"], r["horas_servicos"], params["cobranca"]["pacote"]["mix_padrao"],
                       r["custo_h"], r["taxa_h"])
        meses = pk["meses"]
        # o custo do pacote é o das horas vendidas, não o das horas estimadas para os serviços
        custo_mo = sum(pk["horas_perfil"][p] * r["custo_h"][p] for p in pk["horas_perfil"])
        overhead = _overhead(params, custo_mo, pk["horas"])
        honorarios = pk["honorarios"] + r["reembolso"]
        pk["parcela"] = (pk["honorarios"] + r["reembolso"]) / pk["parcelas"]      # o cliente paga o pacote inteiro
        r.update(pacote=pk, horas_perfil=pk["horas_perfil"], total_h=pk["horas"], custo_mo=custo_mo, overhead=overhead,
                 custo_servicos=custo_mo + overhead + r["diretos_total"],
                 preco=honorarios + r["preco_fornec"], preco_fixo=honorarios + r["preco_fornec"], preco_estimado=0.0)
        r["preco_minimo_servicos"] = r["custo_servicos"] / (1 - imp)
        r["base"], r["base_origem"] = base_obra(fase, r, estimativas)
    else:
        honorarios = r["preco_servicos"]
        r.update(preco=r["preco_fechado"], preco_fixo=r["preco_fechado"], preco_estimado=0.0)
    r["honorarios"] = honorarios
    r["margem_efetiva"] = _margem_efetiva(honorarios, r["custo_servicos"], imp)

    de = fase.get("desempenho") or {}
    if cob in ("percentual", "pacote") and de.get("ativo"):
        r["desempenho"] = cb.taxa_desempenho(de, honorarios, r.get("base", 0.0))

    if meses:
        r["cronograma"] = _etapa_obra(fase, meses)
    else:
        r["cronograma"] = cronograma(cat, proposta, opcao, r)
    for e in r["cronograma"]:
        e["fase"] = fase["id"]
    if fase.get("pagamento") and cob in ("fechado", "hora"):
        r["pagamento"] = fase["pagamento"]
    elif cob == "percentual":
        r["pagamento"] = cb.marcos_percentual(r["percentual"])
    elif cob == "pacote":
        r["pagamento"] = cb.marcos_pacote(r["pacote"])
    elif cob == "hora":
        r["pagamento"] = [{"marco": "mensalmente, conforme as horas apontadas em relatório e os reembolsáveis comprovados, "
                                    "contra apresentação de nota fiscal", "pct": 1.0}]
    elif estimativa:
        r["pagamento"] = []
    else:
        r["pagamento"] = pagamento_padrao(proposta, r["cronograma"], r)
    return r


SOMAS = ("total_h", "dias_campo", "art", "custo_mo", "overhead", "diretos_total", "custo_servicos", "contingencia",
         "preco_servicos", "impostos", "margem", "custo_fornec", "preco_fornec", "preco_fechado", "honorarios_hora",
         "reembolso", "preco_hora", "preco_hora_teto", "preco_minimo_servicos", "honorarios", "preco", "preco_fixo",
         "preco_estimado")


def precificar_opcao(cat, proposta, opcao, estimativas=None):
    params = proposta["parametros"]
    perfis = list(cat["perfis"])
    estimativa = eh_estimativa(opcao)
    fases_cfg = opcao["fases"][:1] if estimativa else opcao["fases"]
    fases = [precificar_fase(cat, proposta, opcao, f, estimativas) for f in fases_cfg]
    res = {k: sum(f[k] for f in fases) for k in SOMAS}
    # cronograma: as fases correm em sequência
    cron, inicio = [], 1
    for f in fases:
        for e in f["cronograma"]:
            e["inicio"], e["fim"] = inicio, inicio + e["dias_uteis"] - 1
            inicio += e["dias_uteis"]
            cron.append(e)
    imp = pm.aliquota_impostos(params)
    area = float(proposta["contexto"].get("area_ref", 0) or 0)
    cub = params.get("cub", {})
    ref_cub = (float(cub.get("pct_honorarios") or 0) * float(cub.get("valor") or 0) * area
               if float(cub.get("valor") or 0) > 0 and area > 0 else None)
    desemp = [f["desempenho"] for f in fases if f["desempenho"]]
    res.update({
        "id": opcao["id"], "nome": opcao["nome"],
        "modalidade": "estimativa" if estimativa else "fases", "interno": estimativa,
        "fases": fases,
        "linhas": [l for f in fases for l in f["linhas"]],
        "diretos": [d for f in fases for d in f["diretos"]],
        "fornecimentos": [x for f in fases for x in f["fornecimentos"]],
        "horas_perfil": {p: sum(f["horas_perfil"].get(p, 0) for f in fases) for p in perfis},
        "imp_pct": imp, "margem_pct": float(params["margem"]),
        "cont_pct": float(params["contingencia"][proposta["contexto"]["risco"]]),
        "margem_efetiva": _margem_efetiva(res["honorarios"], res["custo_servicos"], imp),
        "potencial_desempenho": sum(d["potencial"] for d in desemp),
        "teto_desempenho": sum(d["teto"] for d in desemp),
        "cronograma": cron,
        "prazo_dias_uteis": sum(e["dias_uteis"] for e in cron),
        "prazo_dias_corridos": sum(e["dias_corridos"] for e in cron),
        "ref_cub": ref_cub,
        "rs_h": res["preco_servicos"] / res["total_h"] if res["total_h"] > 0 else None,
        "rs_m2": res["preco"] / area if area > 0 else None,
        "checklist_turnkey": checklist_turnkey(cat, opcao) if estimativa else [],
    })
    if estimativa:
        res["valor_obra"] = res["preco_fornec"]
    return res


# ----------------------------------------------------------------------------- prazo e pagamento
def prazos_minimos(opcao, res):
    """Dias úteis mínimos por etapa vindos dos fornecimentos: lead time dos equipamentos e prazo de execução."""
    cats = {f["categoria"] for f in res["fornecimentos"] if f["custo"] > 0}
    return {
        "suprimentos": int(opcao.get("prazo_fornecimento_dias") or 0) if cats & set(CATEGORIAS_EQUIP) else 0,
        "obra": int(opcao.get("prazo_execucao_dias") or 0) if cats else 0,
    }


def cronograma(cat, proposta, opcao, res):
    """Etapas em sequência (atividades da mesma etapa em paralelo), em dias úteis.

    Suprimentos (lead time dos equipamentos) e obra (prazo de execução) entram quando há fornecimento."""
    params = proposta["parametros"]
    cr = params["cronograma"]
    h_etapa = {}
    for l in res["linhas"]:
        h_etapa[l["etapa"]] = h_etapa.get(l["etapa"], 0) + l["total_h"]
    extras = prazos_minimos(opcao, res)
    etapas, inicio = [], 1
    for e in cat["etapas"]:
        h = h_etapa.get(e["id"], 0)
        extra = extras.get(e["id"], 0)
        if h <= 0 and extra <= 0:
            continue
        equipe = cr.get("equipe_etapa", {}).get(e["id"], cr["equipe"])
        dias = max(1, math.ceil(h / (cr["horas_dia"] * equipe))) if h > 0 else 0
        dias = max(dias, extra)
        etapas.append({"etapa": e["id"], "rotulo": e["rotulo"], "marco": e["marco"], "campo": e.get("campo", False),
                       "horas": h, "dias_uteis": dias, "dias_corridos": math.ceil(dias * 7 / 5),
                       "inicio": inicio, "fim": inicio + dias - 1})
        inicio += dias
    return etapas


def _arredonda_5(x):
    return round(x * 20) / 20


def pagamento_padrao(proposta, etapas, res):
    """Sinal + parcela na conclusão do campo/execução + saldo na entrega, proporcionais às horas."""
    sinal = float(proposta["parametros"]["pagamento"]["sinal"])
    h_campo = sum(e["horas"] for e in etapas if e["campo"])
    h_total = sum(e["horas"] for e in etapas) or 1
    tem_obra = any(e["etapa"] == "obra" for e in etapas)
    meio = (1 - sinal) * h_campo / h_total
    if res["preco_fornec"] > 0:   # há fornecimento: ele pesa na parcela de execução
        meio = (1 - sinal) * (res["preco_fornec"] + res["preco_servicos"] * h_campo / h_total) / res["preco_fechado"]
    meio = _arredonda_5(meio)
    texto_meio = "na conclusão da execução e do comissionamento" if tem_obra else "na conclusão das atividades de campo"
    marcos = [{"marco": "na assinatura do instrumento contratual ou no aceite formal desta proposta", "pct": sinal}]
    if meio > 0:
        marcos.append({"marco": texto_meio, "pct": meio})
    marcos.append({"marco": "na entrega do documento técnico, contra apresentação de nota fiscal",
                   "pct": round(1 - sinal - meio, 4)})
    return [m for m in marcos if m["pct"] > 0]


# ----------------------------------------------------------------------------- proposta inteira
ROTULO_COBRANCA = {"fechado": "escopo fechado", "hora": "hora técnica", "percentual": "% da obra",
                   "pacote": "pacote de horas"}


def avisos(proposta, resultados):
    av = []
    uf = (proposta["cliente"].get("uf") or "").strip().upper()
    if uf and uf not in UFS_SEM_VISTO:
        av.append(f"Serviço em {uf}: atuação fora de RJ e SP exige visto no CREA-{uf} (Lei 5.194/1966, art. 58).")
    ids_est = {r["id"] for r in resultados if r["interno"]}
    if resultados and len(ids_est) == len(resultados):
        av.append("Todas as opções são estimativas internas: nenhuma proposta será gerada para o cliente.")
    cfg_fases = {o["id"]: {f["id"]: f for f in o["fases"]} for o in proposta["opcoes"]}
    for r in resultados:
        if r["interno"]:
            faltando = [e["rotulo"] for e in r["checklist_turnkey"] if e["status"] == "faltando"]
            if faltando:
                av.append(f"{r['nome']} (estimativa): faltam as etapas {', '.join(faltando)} — inclua ou marque como "
                          "fora da estimativa.")
            continue
        if not r["linhas"] and not any(f["cobranca"] == "pacote" for f in r["fases"]):
            av.append(f"{r['nome']}: nenhum serviço com horas — adicione serviços na aba Escopo.")
        for f in r["fases"]:
            nome = f"{r['nome']} / {f['nome']}"
            soma = sum(m["pct"] for m in f["pagamento"])
            if f["pagamento"] and abs(soma - 1) > 0.001:
                av.append(f"{nome}: as parcelas de pagamento somam {soma:.0%}, não 100%.")
            if not f["linhas"] and f["cobranca"] in ("fechado", "hora"):
                av.append(f"{nome}: fase sem serviços.")
            if f["cobranca"] == "percentual" and f["base"] <= 0:
                av.append(f"{nome}: % da obra sem base ({f['base_origem']}) — informe o valor da obra ou vincule a "
                          "estimativa interna.")
            ob = cfg_fases[r["id"]][f["id"]]["obra"]
            if f["cobranca"] in ("percentual", "pacote") and ob.get("base_modo") == "opcao" and ob.get("base_opcao") not in ids_est:
                av.append(f"{nome}: a base aponta para a opção '{ob.get('base_opcao')}', que não é uma estimativa interna.")
            if f["cobranca"] == "pacote" and f["pacote"]["horas"] <= 0:
                av.append(f"{nome}: pacote sem horas — informe as horas ou inclua serviços na fase.")
            if f["margem_efetiva"] is not None and f["margem_efetiva"] < 0:
                av.append(f"{nome}: a cobrança ({ROTULO_COBRANCA[f['cobranca']]}) não cobre o custo "
                          f"(margem efetiva {f['margem_efetiva']:.0%}).")
    return av


def precificar(cat, proposta):
    """Estimativas primeiro: o % da assessoria e a taxa de desempenho usam o valor global delas."""
    estimativas = {o["id"]: precificar_opcao(cat, proposta, o) for o in proposta["opcoes"] if eh_estimativa(o)}
    resultados = [estimativas[o["id"]] if o["id"] in estimativas else precificar_opcao(cat, proposta, o, estimativas)
                  for o in proposta["opcoes"]]
    return {"opcoes": resultados, "avisos": avisos(proposta, resultados)}
