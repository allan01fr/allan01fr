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

A planilha exportada repete estas mesmas contas em fórmulas; os testes conferem
que as duas dão o mesmo resultado.
"""

import math

from . import catalogo as ct
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


def eh_turnkey(opcao):
    return opcao.get("modalidade") == "turnkey"


def checklist_turnkey(cat, opcao):
    """Etapas do turnkey: atendida, dispensada (a cargo do contratante), opcional ou faltando."""
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


def _fornecimentos(params, opcao):
    fornec = []
    for f in opcao.get("fornecimentos", []):
        custo = float(f.get("qtd", 0) or 0) * float(f.get("custo_unit", 0) or 0)
        bdi = float(params["bdi_fornecimento"][f["categoria"]])
        fornec.append({**f, "custo": custo, "bdi": bdi, "preco": custo * (1 + bdi)})
    return fornec


def precificar_opcao(cat, proposta, opcao):
    params = proposta["parametros"]
    perfis = list(cat["perfis"])
    turnkey = eh_turnkey(opcao)
    linhas, diretos_base = [], []
    for i, it in enumerate(opcao["itens"]):
        li, di = linhas_item(cat, proposta, it, i)
        linhas += li
        diretos_base += di

    dias = dias_campo(cat, params, linhas)
    v_desl, memoria = deslocamento(params, float(proposta["contexto"].get("dist_km", 0) or 0), dias)
    if v_desl > 0:
        diretos_base.append({"item": None, "descricao": "Deslocamento", "servico_nome": memoria,
                             "unid": "vb", "qtd": 1.0, "valor_unit": v_desl, "valor": v_desl})

    fornec = _fornecimentos(params, opcao)
    custo_fornec = sum(f["custo"] for f in fornec)
    preco_fornec = sum(f["preco"] for f in fornec)
    if turnkey and custo_fornec > 0 and params["turnkey"]["garantia_pct"] > 0:
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
    if params["overhead"]["metodo"] == "hora":
        overhead = total_h * pm.overhead_por_hora(params)
    else:
        overhead = custo_mo * float(params["overhead"]["pct"])

    risco = proposta["contexto"]["risco"]
    cont_pct = float(params["contingencia"][risco])
    imp = pm.aliquota_impostos(params)
    margem = float(params["margem"])
    divisor = 1 - imp - margem
    if divisor <= 0.05:
        raise ValueError(f"impostos ({imp:.1%}) + margem ({margem:.1%}) deixam menos de 5% para o custo")

    def cadeia(art):
        diretos = list(diretos_base)
        if opcao["itens"] and art > 0:
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
    fee_base = float(opcao.get("fee_base") or 0) or custo_fornec
    fee_pct = float(opcao.get("fee_pct") or 0)
    fee_honorarios = fee_pct * fee_base

    def margem_efetiva(preco):
        return (preco * (1 - imp) - custo_servicos) / preco if preco > 0 else None

    area = float(proposta["contexto"].get("area_ref", 0) or 0)
    cub = params.get("cub", {})
    ref_cub = (float(cub.get("pct_honorarios") or 0) * float(cub.get("valor") or 0) * area
               if float(cub.get("valor") or 0) > 0 and area > 0 else None)
    preco_fechado = preco_servicos + preco_fornec
    return {
        "id": opcao["id"], "nome": opcao["nome"],
        "modalidade": "turnkey" if turnkey else "servicos",
        "modelo_preco": "fechado" if turnkey else opcao.get("modelo_preco", "fechado"),
        "linhas": linhas, "diretos": diretos, "fornecimentos": fornec,
        "horas_perfil": horas_perfil, "total_h": total_h, "dias_campo": dias, "art": art,
        "custo_mo": custo_mo, "overhead": overhead, "diretos_total": diretos_total,
        "custo_servicos": custo_servicos, "cont_pct": cont_pct, "contingencia": contingencia,
        "imp_pct": imp, "margem_pct": margem,
        "preco_servicos": preco_servicos, "impostos": preco_servicos * imp, "margem": preco_servicos * margem,
        "custo_fornec": custo_fornec, "preco_fornec": preco_fornec,
        "preco_fechado": preco_fechado,
        "honorarios_hora": honorarios_hora, "reembolso": reembolso,
        "preco_hora": honorarios_hora + reembolso + preco_fornec,
        "preco_hora_teto": honorarios_hora * (1 + cont_pct) + reembolso + preco_fornec,
        "fee_pct": fee_pct, "fee_base": fee_base, "fee_honorarios": fee_honorarios,
        "preco_fee": (fee_honorarios + preco_fornec) if fee_base > 0 else None,
        "preco_minimo_servicos": custo_servicos / (1 - imp),
        "margem_efetiva": {
            "fechado": margem_efetiva(preco_servicos),
            "hora": margem_efetiva(honorarios_hora + reembolso),
            "fee": margem_efetiva(fee_honorarios) if fee_base > 0 else None,
        },
        "capex_minimo_fee": (preco_servicos / fee_pct) if fee_pct > 0 else None,
        "ref_cub": ref_cub,
        "rs_h": preco_servicos / total_h if total_h > 0 else None,
        "rs_m2": preco_fechado / area if area > 0 else None,
        "checklist_turnkey": checklist_turnkey(cat, opcao) if turnkey else [],
    }


def preco_escolhido(res):
    """Preço da opção no modelo escolhido; turnkey é sempre preço global (escopo fechado)."""
    if res["modelo_preco"] == "hora":
        return res["preco_hora"]
    if res["modelo_preco"] == "fee" and res["preco_fee"] is not None:
        return res["preco_fee"]
    return res["preco_fechado"]


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


def pagamento_turnkey(cat, proposta, res):
    """Sinal, entrega dos equipamentos, conclusão da instalação e aceite, pelo peso de cada etapa no preço.
    O aceite retém no mínimo `turnkey.retencao_aceite` (padrão 10%), tirado primeiro da instalação e depois dos equipamentos."""
    sinal = float(proposta["parametros"]["pagamento"]["sinal"])
    retencao = float(proposta["parametros"]["turnkey"].get("retencao_aceite", 0.10))
    total = res["preco_fechado"] or 1
    equip = sum(f["preco"] for f in res["fornecimentos"] if f["categoria"] in CATEGORIAS_EQUIP)
    execu = sum(f["preco"] for f in res["fornecimentos"] if f["categoria"] in CATEGORIAS_EXEC)
    mo_obra = sum(l["custo_mo"] for l in res["linhas"] if ct.servico(cat, l["servico"])["tipo"] == "obra")
    if res["custo_mo"] > 0:
        execu += res["preco_servicos"] * mo_obra / res["custo_mo"]
    p_equip = _arredonda_5((1 - sinal) * equip / total)
    p_exec = _arredonda_5((1 - sinal) * execu / total)
    falta = round(retencao - (1 - sinal - p_equip - p_exec), 4)
    if falta > 0:
        tira = min(falta, p_exec)
        p_exec, falta = round(p_exec - tira, 4), round(falta - tira, 4)
        p_equip = round(max(p_equip - falta, 0.0), 4)
    marcos = [
        {"marco": "na assinatura do instrumento contratual ou no aceite formal desta proposta", "pct": sinal},
        {"marco": "na entrega dos equipamentos e materiais em obra", "pct": p_equip},
        {"marco": "na conclusão da instalação", "pct": p_exec},
        {"marco": "no comissionamento e na assinatura do termo de aceite, contra apresentação de nota fiscal",
         "pct": round(1 - sinal - p_equip - p_exec, 4)},
    ]
    return [m for m in marcos if m["pct"] > 0]


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


def pagamento(cat, proposta, opcao, etapas, res):
    if opcao.get("pagamento"):
        return opcao["pagamento"]
    if eh_turnkey(opcao) and res["fornecimentos"]:
        return pagamento_turnkey(cat, proposta, res)
    return pagamento_padrao(proposta, etapas, res)


# ----------------------------------------------------------------------------- proposta inteira
def avisos(proposta, resultados):
    av = []
    uf = (proposta["cliente"].get("uf") or "").strip().upper()
    if uf and uf not in UFS_SEM_VISTO:
        av.append(f"Serviço em {uf}: atuação fora de RJ e SP exige visto no CREA-{uf} (Lei 5.194/1966, art. 58).")
    for r in resultados:
        if not r["linhas"]:
            av.append(f"{r['nome']}: nenhum serviço com horas — adicione serviços na aba Escopo.")
        soma = sum(m["pct"] for m in r["pagamento"])
        if r["linhas"] and abs(soma - 1) > 0.001:
            av.append(f"{r['nome']}: as parcelas de pagamento somam {soma:.0%}, não 100%.")
        if r["modelo_preco"] == "fee" and r["preco_fee"] is None:
            av.append(f"{r['nome']}: modelo % sobre obra sem base — informe o valor da obra/CAPEX.")
        me = r["margem_efetiva"].get(r["modelo_preco"])
        if me is not None and me < 0:
            av.append(f"{r['nome']}: no modelo escolhido o preço não cobre o custo (margem efetiva {me:.0%}).")
        faltando = [e["rotulo"] for e in r["checklist_turnkey"] if e["status"] == "faltando"]
        if faltando:
            av.append(f"{r['nome']} (turnkey): faltam as etapas {', '.join(faltando)} — inclua no escopo ou marque "
                      "como fornecidas pelo contratante.")
    return av


def precificar(cat, proposta):
    resultados = []
    for o in proposta["opcoes"]:
        r = precificar_opcao(cat, proposta, o)
        r["cronograma"] = cronograma(cat, proposta, o, r)
        r["prazo_dias_uteis"] = sum(e["dias_uteis"] for e in r["cronograma"])
        r["prazo_dias_corridos"] = sum(e["dias_corridos"] for e in r["cronograma"])
        r["pagamento"] = pagamento(cat, proposta, o, r["cronograma"], r)
        r["preco"] = preco_escolhido(r)
        resultados.append(r)
    return {"opcoes": resultados, "avisos": avisos(proposta, resultados)}
