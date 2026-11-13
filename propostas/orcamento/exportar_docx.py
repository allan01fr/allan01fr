"""
Proposta comercial no template aprovado da KAPTEK (modelos/proposta.docx).

Regra da marca: preencher o template, nunca remontar o documento. Este módulo só
substitui os campos entre colchetes e ajusta o número de linhas das tabelas e
dos itens de lista (escopo, exclusões, premissas, prazos, honorários,
pagamento), clonando a linha ou o parágrafo do próprio template.

Com várias fases, os honorários, os prazos e o pagamento saem por fase, e as fases de obra
trazem as regras do % sobre as medições, do pacote de horas e da taxa de desempenho. A
estimativa interna do valor global não gera proposta.

`substituir()` vem de kaptek-doc/scripts/preencher.py (habilidade KAPTEK).
"""

import copy
import io
import os
import re
import unicodedata

from docx import Document
from docx.text.paragraph import Paragraph

from . import catalogo as ct
from . import motor

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = os.path.join(RAIZ, "modelos", "proposta.docx")

FRASE_DESLOCAMENTO = ("Não estão inclusos deslocamentos fora da Região Metropolitana do Rio de Janeiro, "
                      "que serão orçados à parte mediante aprovação prévia.")
TEXTO_ART_NEUTRO = ("A Anotação de Responsabilidade Técnica (ART) de execução não está incluída neste preço; "
                    "quando exigida, será recolhida e cobrada à parte.")
FRASE_ART_MISTA = "A ART cobre as fases de serviços de engenharia e não inclui a execução."
FRASE_ART_EXECUCAO = "As ARTs cobrem as fases de projeto, acompanhamento e execução desta proposta."
PREMISSAS_FINAIS = [
    "Os prazos são contados em dias corridos a partir do cumprimento cumulativo das premissas acima.",
    "Atraso na liberação de acesso ou de documentação suspende a contagem dos prazos, sem ônus para a contratada.",
]


# ----------------------------------------------------------------------------- texto
def substituir(par, de, para):
    """Troca texto no parágrafo preservando a formatação (de kaptek-doc/scripts/preencher.py).
    Se o trecho estiver fragmentado entre runs, consolida no primeiro run."""
    if de not in par.text or not par.runs:
        return False
    for r in par.runs:
        if de in r.text:
            r.text = r.text.replace(de, para)
            return True
    novo = par.text.replace(de, para)
    par.runs[0].text = novo
    for r in par.runs[1:]:
        r.text = ""
    return True


def _definir(par, texto):
    """Troca todo o texto de um parágrafo mantendo a formatação do primeiro run."""
    if not par.runs:
        par.add_run(texto)
        return
    par.runs[0].text = texto
    for r in par.runs[1:]:
        r.text = ""


def _definir_item(par, texto):
    """Item de lista do template: run 0 é o travessão cobre, run 1 o texto grafite."""
    if len(par.runs) >= 2:
        par.runs[1].text = texto
        for r in par.runs[2:]:
            r.text = ""
    else:
        _definir(par, "—   " + texto)


def _todos_paragrafos(doc):
    yield from doc.paragraphs
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                yield from c.paragraphs


def moeda(v):
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct_br(p):
    v = round(p * 100, 1)
    return (f"{v:.0f}" if v == int(v) else f"{v:.1f}".replace(".", ",")) + "%"


def _data_br(iso):
    try:
        a, m, d = iso.split("-")
        return f"{d}/{m}/{a}"
    except (ValueError, AttributeError):
        return str(iso)


def slug(texto):
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-")
    return t[:40] or "cliente"


# ----------------------------------------------------------------------------- estrutura
def _listas_por_secao(doc):
    """Itens de lista (parágrafos que começam com travessão) agrupados pelo título da seção."""
    secoes, atual = {}, None
    for p in doc.paragraphs:
        if p.style is not None and p.style.name.startswith("Heading"):
            atual = p.text.upper()
            continue
        if atual and p.text.startswith("—"):
            secoes.setdefault(atual, []).append(p)
    return secoes


def _lista(secoes, chave):
    for titulo, pars in secoes.items():
        if chave in titulo:
            return pars
    raise KeyError(f"seção '{chave}' não encontrada no template")


def _ajustar_lista(pars, textos):
    textos = list(textos) or ["Não se aplica."]
    ultimo = pars[-1]
    for i, t in enumerate(textos):
        if i < len(pars):
            alvo = pars[i]
        else:
            novo = copy.deepcopy(pars[0]._p)
            ultimo._p.addnext(novo)
            alvo = Paragraph(novo, pars[0]._parent)
            ultimo = alvo
        _definir_item(alvo, t)
    for p in pars[len(textos):]:
        p._p.getparent().remove(p._p)


def _tabela(doc, primeiro_cabecalho, segundo=None):
    for t in doc.tables:
        cab = [c.text.strip() for c in t.rows[0].cells]
        if cab and cab[0] == primeiro_cabecalho and (segundo is None or (len(cab) > 1 and cab[1] == segundo)):
            return t
    raise KeyError(f"tabela '{primeiro_cabecalho}' não encontrada no template")


def _preencher_linhas(tabela, linhas, manter_ultima=False):
    """Recria as linhas de dados clonando a primeira linha de dados do template."""
    trs = tabela._tbl.tr_lst
    proto = trs[1]
    ancora = trs[-1] if manter_ultima else None
    for tr in trs[1:len(trs) - (1 if manter_ultima else 0)]:
        if tr is not proto:
            tabela._tbl.remove(tr)
    for valores in linhas:
        novo = copy.deepcopy(proto)
        if ancora is not None:
            ancora.addprevious(novo)
        else:
            tabela._tbl.append(novo)
    tabela._tbl.remove(proto)
    inicio = 1
    for i, valores in enumerate(linhas):
        row = tabela.rows[inicio + i]
        for c, v in zip(row.cells, valores):
            if c.paragraphs:
                _definir(c.paragraphs[0], str(v))
                for extra in c.paragraphs[1:]:
                    extra._p.getparent().remove(extra._p)


# ----------------------------------------------------------------------------- conteúdo
def _rateio_servicos(opcao, res):
    """Preço dos serviços repartido por serviço, na proporção do custo direto de cada um.
    Devolve (índice do item, nome, valor); a soma fecha exatamente com o preço dos serviços."""
    pesos = []
    for i, it in enumerate(opcao["itens"]):
        mo = sum(l["custo_mo"] for l in res["linhas"] if l["item"] == i)
        dr = sum(d["valor"] for d in res["diretos"] if d["item"] == i)
        nome = next((l["servico_nome"] for l in res["linhas"] if l["item"] == i), None)
        if nome and mo + dr > 0:
            pesos.append((i, nome, mo + dr))
    total = sum(p for *_, p in pesos) or 1
    valores = [round(res["preco_servicos"] * p / total, 2) for *_, p in pesos]
    if valores:
        valores[-1] = round(res["preco_servicos"] - sum(valores[:-1]), 2)
    return [(i, n, v) for (i, n, _), v in zip(pesos, valores)]


def _h(v):
    return f"{v:,.0f}".replace(",", ".") + " h"


def _linhas_percentual(fr, prefixo):
    hp = fr["percentual"]
    pct, base = pct_br(hp["pct"]), moeda(hp["base"])
    if hp["forma"] == "fixo_global":
        return [(f"{prefixo}{pct} sobre o valor global estimado da obra ({base}), faturado conforme as medições",
                 pct, "—", moeda(hp["fixo"]))]
    linhas = []
    if hp["forma"] == "fixo_mais_medicoes" and hp["parcela_fixa"] > 0:
        linhas.append((f"{prefixo}parcela fixa (mobilização e planejamento inicial)", "1", moeda(hp["parcela_fixa"]),
                       moeda(hp["parcela_fixa"])))
    linhas.append((f"{prefixo}{pct} sobre o valor de cada medição da obra (valor global estimado em {base})",
                   pct, "—", f"≈ {moeda(hp['estimado'])} (estimado)"))
    return linhas


def _linhas_pacote(fr, prefixo):
    pk = fr["pacote"]
    if pk["forma"] == "mensal":
        desc = f"{prefixo}pacote de {pk['horas_mes']:.0f} h/mês × {pk['meses']} meses ({_h(pk['horas'])})"
    else:
        desc = f"{prefixo}pacote de {_h(pk['horas'])}, a consumir em até {pk['meses']} meses"
    total = fr["preco"] - fr["preco_fornec"]
    return [(desc, _h(pk["horas"]), moeda(total / pk["horas"]) if pk["horas"] else "—", moeda(total)),
            ("Hora excedente ao pacote (sob demanda, mediante autorização prévia)", "1 h", moeda(pk["taxa_excedente"]),
             "sob demanda")]


def _agrupar_execucao(fornecimentos):
    """Soma os fornecimentos de execução repetidos (mesma descrição, unidade e unitário); os demais ficam como estão."""
    saida, vistos = [], {}
    for f in fornecimentos:
        if f.get("origem") != "execucao":
            saida.append(f)
            continue
        qtd = float(f.get("qtd") or 0)
        chave = (f.get("descricao"), f.get("unid"), round(f["preco"] / qtd, 2) if qtd else None)
        if chave in vistos and qtd:
            vistos[chave]["qtd"] += qtd
            vistos[chave]["preco"] = round(vistos[chave]["preco"] + f["preco"], 2)
        else:
            vistos[chave] = dict(f)
            saida.append(vistos[chave])
    return saida


def _linhas_fase(cat, params, opcao, fr, prefixo="", detalhar=True):
    """Linhas de honorários de uma fase. `detalhar` (fase única) lista serviços, perfis e fornecimentos."""
    linhas = []
    cob = fr["cobranca"]
    if cob == "hora":
        if detalhar:
            for p, nome in cat["perfis"].items():
                h = fr["horas_perfil"][p]
                if h > 0:
                    taxa = float(params["perfis"][p]["taxa_venda_h"])
                    linhas.append((f"Hora técnica — {nome}", f"{h:.1f} h".replace(".", ","), moeda(taxa), moeda(h * taxa)))
            if fr["reembolso"] > 0:
                linhas.append(("Despesas reembolsáveis (estimativa, inclui ART)", "1", moeda(fr["reembolso"]), moeda(fr["reembolso"])))
        else:
            valor = fr["honorarios"]
            linhas.append((f"{prefixo}hora técnica (estimado, teto {moeda(fr['preco_hora_teto'] - fr['preco_fornec'])})",
                           _h(fr["total_h"]), moeda(valor / fr["total_h"]) if fr["total_h"] else "—", moeda(valor)))
    elif cob == "percentual":
        linhas += _linhas_percentual(fr, prefixo or "Honorários de engenharia — ")
    elif cob == "pacote":
        linhas += _linhas_pacote(fr, prefixo or "Fiscalização e planejamento — ")
    elif detalhar:
        for _, nome, v in _rateio_servicos(opcao, fr):
            linhas.append((f"Honorários de engenharia — {nome}", "1", moeda(v), moeda(v)))
    elif fr["servicos"]:
        linhas.append((f"{prefixo}escopo fechado", "1 vb", moeda(fr["preco_servicos"]), moeda(fr["preco_servicos"])))
    if fr["fornecimentos"]:
        if detalhar or not fr["servicos"]:      # fase só de fornecimentos (execução): item a item, como na fase única
            for f in _agrupar_execucao(fr["fornecimentos"]):
                qtd = float(f.get("qtd") or 0)
                unit = f["preco"] / qtd if qtd else f["preco"]
                q_txt = f"{qtd:g} {f.get('unid', '')}".strip().replace(".", ",")
                if f.get("origem") == "execucao" and f.get("unid") == "h":     # mão de obra: valor global, sem horas
                    q_txt, unit = "1 vb", f["preco"]
                linhas.append((prefixo + f.get("descricao", "Fornecimento"), q_txt, moeda(unit), moeda(f["preco"])))
        else:
            linhas.append((f"{prefixo}fornecimentos", "1 vb", moeda(fr["preco_fornec"]), moeda(fr["preco_fornec"])))
    if fr["desempenho"]:
        linhas.append((f"{prefixo}taxa de desempenho (variável, adicional; critérios nas condições de pagamento)",
                       "—", f"até {moeda(fr['desempenho']['teto'])}", "variável"))
    return linhas


def _linhas_honorarios(cat, params, opcao, res):
    fases = res["fases"]
    linhas = []
    if len(fases) == 1:
        linhas = _linhas_fase(cat, params, opcao, fases[0])
    else:
        for n, fr in enumerate(fases, 1):
            linhas += _linhas_fase(cat, params, opcao, fr, prefixo=f"Fase {n} — {fr['nome']}: ", detalhar=False)
    if any(d["descricao"].startswith("Taxa de ART") for d in res["diretos"]) and not \
            (len(fases) == 1 and fases[0]["cobranca"] == "hora"):
        sufixo = ""
        if len(fases) > 1:
            sufixo = " (uma por fase de serviços)" if any(motor.fase_so_fornecimentos(f) for f in fases) else " (uma por fase)"
        linhas.append(("Taxa de ART junto ao CREA" + sufixo, "1", "inclusa", "inclusa"))
    return linhas


def _total_texto(res):
    if len(res["fases"]) == 1 and res["fases"][0]["cobranca"] == "hora":
        return f"{moeda(res['preco'])} (estimado; teto {moeda(res['fases'][0]['preco_hora_teto'])})"
    if res["preco_estimado"] > 0:
        return f"{moeda(res['preco_fixo'])} + {moeda(res['preco_estimado'])} estimados"
    return moeda(res["preco"])


def _servicos_ativos(opcao, res):
    """Serviços das fases precificadas, pelos mesmos índices do motor (item sem fase válida cai na primeira fase)."""
    return [opcao["itens"][i]["servico"] for f in res["fases"] for i in f["servicos"]]


def _exclusoes(cat, opcao, res):
    return ct.textos_validos(cat, _servicos_ativos(opcao, res), bool(res["fornecimentos"]), "exclusoes")


def _premissas_fases(res):
    textos = []
    if len(res["fases"]) > 1:
        textos.append("As fases são sequenciais: cada fase se inicia após o aceite da anterior e pode ser contratada "
                      "separadamente, pelos valores indicados para ela.")
    for n, fr in enumerate(res["fases"], 1):
        nome = f"Fase {n} ({fr['nome']})" if len(res["fases"]) > 1 else fr["nome"]
        if fr["cobranca"] == "percentual":
            if fr["percentual"]["forma"] == "fixo_global":
                textos.append(f"{nome}: honorário fixo, calculado sobre o valor global estimado da obra; não se altera com "
                              "variações do valor da obra, salvo aditivo de escopo.")
            else:
                textos.append(f"{nome}: o valor das medições considerado é o aprovado pela fiscalização do contratante; "
                              "o honorário estimado acompanha o valor efetivamente medido.")
        elif fr["cobranca"] == "pacote":
            pk = fr["pacote"]
            if pk["forma"] == "mensal":
                saldo = "acumula para os meses seguintes, até o fim do contrato" if pk["acumula_saldo"] else \
                    "não acumula para os meses seguintes"
                textos.append(f"{nome}: pacote mensal de {pk['horas_mes']:.0f} horas, apontadas em relatório mensal de horas e "
                              f"atividades; o saldo não utilizado {saldo}.")
            else:
                textos.append(f"{nome}: pacote de {pk['horas']:.0f} horas, consumidas sob demanda em até {pk['meses']} meses "
                              "e apontadas em relatório mensal de horas e atividades.")
            textos.append(f"{nome}: horas excedentes, mediante autorização prévia, são cobradas a "
                          f"{moeda(pk['taxa_excedente'])} por hora.")
    return textos


def _premissas(cat, proposta, opcao, res):
    textos = [p for p in ct.textos_validos(cat, _servicos_ativos(opcao, res), bool(res["fornecimentos"]),
                                           "premissas") if p not in PREMISSAS_FINAIS]
    return textos + _premissas_fases(res) + PREMISSAS_FINAIS


def _clausulas_desempenho(n, fr, varias):
    d, cfg = fr["desempenho"], fr["_cfg_desempenho"]
    nome = f"da fase {n}" if varias else "da assessoria"
    criterios = []
    if cfg["economia_pct"] > 0:
        criterios.append(f"{pct_br(cfg['economia_pct'])} da economia apurada entre o valor global estimado da obra "
                         f"({moeda(d['base_global'])}) e o custo final")
    if cfg["prazo_pct_semana"] > 0:
        criterios.append(f"{pct_br(cfg['prazo_pct_semana'])} dos honorários {nome} por semana de antecipação da conclusão "
                         "em relação ao prazo previsto")
    if cfg["retrabalho_bonus_pct"] > 0:
        criterios.append(f"{pct_br(cfg['retrabalho_bonus_pct'])} dos honorários {nome} se o índice de retrabalho (custo de "
                         f"retrabalho ÷ valor medido) ficar igual ou abaixo de {pct_br(cfg['retrabalho_meta'])}")
    if not criterios:
        return []
    return [f"Taxa de desempenho {nome} (variável, adicional aos honorários): " + "; ".join(criterios) + ".",
            f"A taxa de desempenho é limitada a {pct_br(cfg['teto_pct'])} dos honorários {nome} ({moeda(d['teto'])}), apurada no "
            "encerramento da obra com base nas medições aprovadas e nos registros de prazo e de retrabalho, e paga na "
            "assinatura do termo de recebimento definitivo."]


def _pagamento(res):
    fases = res["fases"]
    varias = len(fases) > 1
    itens = []
    for n, fr in enumerate(fases, 1):
        pre = f"Fase {n} ({fr['nome']}): " if varias else ""
        for m in fr["pagamento"]:
            itens.append(f"{pre}{m['marco']}." if abs(m["pct"] - 1) < 1e-9 else f"{pre}{pct_br(m['pct'])} {m['marco']}.")
        if fr["desempenho"]:
            itens += _clausulas_desempenho(n, fr, varias)
    return [i[0].upper() + i[1:] for i in itens]


def _minuscula(texto):
    """Primeira letra minúscula, preservando siglas (TAB, PMOC, CFD...)."""
    if len(texto) > 1 and texto[1].islower():
        return texto[0].lower() + texto[1:]
    return texto


def _linhas_escopo(res):
    """Uma linha por serviço (numerada por fase quando há mais de uma) com atividades e entregáveis."""
    varias = len(res["fases"]) > 1
    saida = []
    for n, fr in enumerate(res["fases"], 1):
        grupos = []
        for l in fr["linhas"]:
            if not grupos or grupos[-1]["item"] != l["item"]:
                grupos.append({"item": l["item"], "nome": l["servico_nome"], "ativ": [], "entr": []})
            g = grupos[-1]
            g["ativ"].append(_minuscula(l["nome"]))
            if l["entregavel"] and l["entregavel"] not in g["entr"]:
                g["entr"].append(l["entregavel"])
        for k, g in enumerate(grupos, 1):
            num = f"{n}.{k}" if varias else f"{len(saida) + 1:02d}"
            saida.append((num, f"{g['nome']}: {'; '.join(g['ativ'])}.", "; ".join(g["entr"])))
        if not grupos and fr["cobranca"] != "pacote" and fr["preco_fornec"] > 0:
            num = f"{n}.1" if varias else f"{len(saida) + 1:02d}"
            saida.append((num, f"{fr['nome']}: fornecimento de materiais e mão de obra de execução, conforme os itens "
                               "relacionados na seção 7.", "Obra executada e entregue conforme os itens da seção 7"))
        if not grupos and fr["cobranca"] == "pacote":
            num = f"{n}.1" if varias else f"{len(saida) + 1:02d}"
            saida.append((num, f"{fr['nome']}: fiscalização e planejamento da obra sob demanda, dentro do pacote de horas.",
                          "Relatórios mensais de horas e atividades"))
    return saida


def _prazo_execucao(res, opcao, params):
    """(fase_id, dias úteis, dias corridos) da execução por itens de kit; None se a opção não tem plano."""
    if not opcao or not opcao.get("itens_execucao"):
        return None
    from . import execucao_itens as ei
    plano = ei.calcular_execucao(opcao, params).get("plano") or {}
    ids = [f["id"] for f in opcao["fases"] if f.get("modulo") == "execucao"]
    fr = next((f for f in res["fases"] if f["id"] in ids and not any(e["fase"] == f["id"] for e in res["cronograma"])), None)
    if fr is None or not plano.get("prazo_dias_corridos"):
        return None
    return fr["id"], int(plano["prazo_dias_uteis"]), int(plano["prazo_dias_corridos"])


def _linhas_prazos(res, opcao=None, params=None):
    fases = res["fases"]
    pe = _prazo_execucao(res, opcao, params)
    if len(fases) == 1:
        prazos = [(e["rotulo"], f"{e['dias_corridos']} dias", e["marco"]) for e in res["cronograma"]]
    else:
        prazos = []
        for n, fr in enumerate(fases, 1):
            etapas = [e for e in res["cronograma"] if e["fase"] == fr["id"]]
            meses = next((e["meses"] for e in etapas if e.get("meses")), None)
            dias = sum(e["dias_corridos"] for e in etapas)
            texto = f"durante a obra ({meses} meses)" if meses else (f"{dias} dias" if etapas else "a definir")
            marco = etapas[-1]["marco"] if etapas else "Conclusão da fase"
            if pe and fr["id"] == pe[0]:
                texto, marco = f"{pe[1]} dias úteis ({pe[2]} dias corridos)", "Conclusão da execução"
            prazos.append((f"Fase {n} — {fr['nome']}", texto, marco))
    sem_prazo = [fr["nome"] for fr in fases if not any(e["fase"] == fr["id"] for e in res["cronograma"])
                 and not (pe and fr["id"] == pe[0])]
    if pe:
        if sem_prazo:
            total = f"{res['prazo_dias_corridos'] + pe[2]} dias, sem {', '.join(sem_prazo)} (prazo a definir)"
        else:
            total = f"{res['prazo_dias_corridos'] + pe[2]} dias"
    elif not res["cronograma"]:
        total = "a definir"
    elif sem_prazo:
        total = f"{res['prazo_dias_corridos']} dias, sem {', '.join(sem_prazo)} (prazo a definir)"
    else:
        total = f"{res['prazo_dias_corridos']} dias"
    if len(fases) == 1 and not res["cronograma"]:
        if pe:
            prazos.append((fases[0]["nome"], f"{pe[1]} dias úteis ({pe[2]} dias corridos)", "Conclusão da execução"))
        else:
            prazos.append((fases[0]["nome"], "a definir", "Conclusão da fase"))
    prazos.append(("Prazo total estimado", total, "Conclusão dos serviços"))
    return prazos


def _texto_objeto(proposta, opcao, res, varias):
    nomes = []
    for l in res["linhas"]:
        if l["servico_nome"] not in nomes:
            nomes.append(l["servico_nome"])
    so_execucao = not nomes and any(fr["preco_fornec"] > 0 for fr in res["fases"]) \
        and all(fr["cobranca"] != "pacote" for fr in res["fases"])
    if not nomes:       # fase só de fornecimentos (execução): o objeto é o fornecimento e a mão de obra
        nomes = [f"{fr['nome']} (fornecimento de materiais e mão de obra)" for fr in res["fases"] if fr["preco_fornec"] > 0] \
            or [fr["nome"] for fr in res["fases"]]
    base = (proposta.get("objeto") or "").strip().rstrip(".")
    sufixo = f" — {opcao['nome']}" if varias else ""
    abertura = "Fornecimento e execução de instalações" if so_execucao else "Prestação de serviços técnicos de engenharia"
    if len(res["fases"]) > 1:
        fases = "; ".join(f"Fase {n} — {_minuscula(fr['nome'])}" for n, fr in enumerate(res["fases"], 1))
        cabeca = f"{abertura}, em {len(res['fases'])} fases" + (f": {base}{sufixo}" if base else sufixo)
        return f"{cabeca}. Compreende: {fases}, conforme as atividades e os entregáveis relacionados na seção 3."
    cabeca = f"{abertura}: {base}{sufixo}" if base else f"{abertura}{sufixo}"     # sem objeto, não repete a cláusula
    return f"{cabeca}. Compreende: {'; '.join(nomes)}, conforme as atividades e os entregáveis relacionados na seção 3."


# ----------------------------------------------------------------------------- API
def _inserir_arts(par, arts):
    """Seção curta "ARTs previstas" logo após o parágrafo da ART; sem plano de ARTs, não muda nada."""
    if not arts:
        return
    linhas = ["ARTs previstas:"]
    for a in arts:
        quem = "inclusa no preço" if a.get("no_preco") else "do subcontratado"
        ativ = a.get("atividades")
        ativ = ", ".join(str(x) for x in ativ) if isinstance(ativ, (list, tuple, set)) else (ativ or "")
        desc = " — ".join(x for x in (a.get("modalidade"), ativ) if x)
        linhas.append(f"• ART {desc or a.get('tipo', '')} ({quem})")
    ref = par
    for texto in linhas:
        novo = copy.deepcopy(par._p)
        ref._p.addnext(novo)
        ref = type(par)(novo, par._parent)
        _definir(ref, texto)


def _num_br(v):
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".").replace(",0", "") if v != int(v) else f"{int(v):,}".replace(",", ".")


def _execucao_ativa(opcao, res):
    ids = {f["id"] for f in opcao["fases"] if f.get("modulo") == "execucao" and f.get("ativa", True)}
    return bool(opcao.get("itens_execucao")) and any(fr["id"] in ids for fr in res["fases"])


def _textos_acompanhamento(res, opcao):
    """Frases voltadas ao cliente sobre a cobrança do acompanhamento de obra (pacote "obra" ou % sobre a execução)."""
    cfg = {f["id"]: f for f in opcao["fases"]}
    saida = []
    for fr in res["fases"]:
        ob = (cfg.get(fr["id"], {}).get("obra") or {})
        if cfg.get(fr["id"], {}).get("modulo") != "acompanhamento":
            continue
        if fr["cobranca"] == "pacote" and (fr.get("pacote") or {}).get("forma") == "obra":
            pk = fr["pacote"]
            saida.append(f"{fr['nome']}: acompanhamento estimado em {_h(pk['horas'])} ({_num_br(pk['dias_obra'])} dias úteis de obra "
                         f"× {_num_br(pk['horas_dia_obra'])} h/dia + {_h(pk['horas_fixas'])} de mobilização e relatório); "
                         f"horas excedentes a {moeda(pk['taxa_excedente'])}/h.")
        elif fr["cobranca"] == "percentual" and ob.get("base_modo") == "execucao":
            saida.append(f"{fr['nome']}: {pct_br(fr['percentual']['pct'])} sobre o valor da execução.")
    return saida


def _textos_execucao(res, opcao, params):
    """Seção voltada ao cliente sobre a fase de execução: itens (sem HH nem custos), prazo, equipe e inclusões."""
    from . import execucao_itens as ei
    fases = [fr["id"] for fr in res["fases"] if any(f["id"] == fr["id"] and f.get("modulo") == "execucao" for f in opcao["fases"])]
    itens = {}
    for it in opcao.get("itens_execucao") or []:
        if not isinstance(it, dict) or it.get("fase") not in fases:
            continue
        qtd = float(it.get("qtd") or 0)
        if qtd > 0:
            chave = (it.get("descricao") or "Item de execução", it.get("unid") or "un")
            itens[chave] = itens.get(chave, 0.0) + qtd
    if not itens:
        return []
    linhas = ["Itens de execução:"]
    linhas += [f"• {d} — {_num_br(q)} {u}" for (d, u), q in itens.items()]
    plano = ei.calcular_execucao(opcao, params).get("plano") or {}
    if plano.get("prazo_dias_uteis"):
        linhas.append(f"Prazo de execução estimado: {int(plano['prazo_dias_uteis'])} dias úteis "
                      f"({int(plano.get('prazo_dias_corridos') or 0)} dias corridos).")
    if plano.get("equipe"):
        nomes = ei.ex.FUNCOES_PADRAO
        eq = "; ".join(f"{nomes.get(f, f)} × {int(n)}" for f, n in plano["equipe"].items() if n)
        linhas.append(f"Equipe prevista: {eq}.")
    linhas.append("Os materiais e equipamentos listados acima estão incluídos no preço da execução.")
    return linhas


def _inserir_apos(par, textos):
    ref = par
    for texto in textos:
        novo = copy.deepcopy(par._p)
        ref._p.addnext(novo)
        ref = type(par)(novo, par._parent)
        _definir(ref, texto)


def gerar_opcao(cat, proposta, opcao, res, varias=False):
    """Preenche o template para uma opção. Devolve (bytes, nome_arquivo, pendencias)."""
    params = proposta["parametros"]
    cfg_fases = {f["id"]: f for f in opcao["fases"]}
    for fr in res["fases"]:
        fr["_cfg_desempenho"] = cfg_fases.get(fr["id"], {}).get("desempenho", {})
    doc = Document(TEMPLATE)
    cl = proposta["cliente"]
    numero = proposta["numero"] + (f"-{opcao['id']}" if varias else "")
    campos = {
        "[Objeto — ex.: Laudo Técnico de Sistema de Climatização]": (proposta.get("objeto") or "Proposta de serviços de engenharia")
                                                                    + (f" — {opcao['nome']}" if varias else ""),
        "[PC-KTK-001/2026]": numero,
        "[__/__/____]": _data_br(proposta["data"]),
        "[15 dias corridos]": f"{proposta['validade_dias']} dias corridos",
        "[Razão social do contratante]": cl.get("razao") or "[Razão social do contratante]",
        "[Nome / cargo / e-mail / telefone]": cl.get("contato") or "[Nome / cargo / e-mail / telefone]",
        "[Logradouro, nº — Bairro — Cidade/UF]": cl.get("endereco") or "[Logradouro, nº — Bairro — Cidade/UF]",
        "[Razão social]": cl.get("razao") or "[Razão social]",
        "[Nome e cargo do signatário]": cl.get("signatario") or "[Nome e cargo do signatário]",
        "em __ dias da data": f"em {proposta.get('prazo_pagamento_dias', 15)} dias da data",
    }
    if any(d["descricao"] == "Deslocamento" for d in res["diretos"]):
        campos[FRASE_DESLOCAMENTO] = "Estão inclusos os deslocamentos previstos para as atividades de campo desta proposta."
    par_art = None
    for par in list(_todos_paragrafos(doc)):
        for de, para in campos.items():
            substituir(par, de, para)
        if par.text.startswith("[Descreva o serviço contratado"):
            _definir(par, _texto_objeto(proposta, opcao, res, varias))
        elif par.text.startswith("Os serviços serão acompanhados da devida Anotação"):
            par_art = par
            situacao = motor.situacao_art(res["fases"])
            if situacao == "sem_art":
                _definir(par, TEXTO_ART_NEUTRO)
            elif situacao == "mista":
                _definir(par, par.text + " " + (FRASE_ART_EXECUCAO if _execucao_ativa(opcao, res) else FRASE_ART_MISTA))
    if par_art is not None:
        _inserir_arts(par_art, res.get("arts"))

    rev = _tabela(doc, "Rev.")
    _definir(rev.rows[1].cells[0].paragraphs[0], proposta.get("revisao", "00"))
    _definir(rev.rows[1].cells[1].paragraphs[0], _data_br(proposta["data"]))

    _preencher_linhas(_tabela(doc, "#", "Serviço"), _linhas_escopo(res))
    _preencher_linhas(_tabela(doc, "Etapa", "Prazo"), _linhas_prazos(res, opcao, params))

    hon = _tabela(doc, "Descrição", "Qtd.")
    _preencher_linhas(hon, _linhas_honorarios(cat, params, opcao, res), manter_ultima=True)
    _definir(hon.rows[-1].cells[-1].paragraphs[0], _total_texto(res))

    extras = _textos_acompanhamento(res, opcao) + _textos_execucao(res, opcao, params)
    if extras:
        nota = next((p for p in _todos_paragrafos(doc) if p.text.startswith("Valores expressos em reais")), None)
        if nota is not None:
            _inserir_apos(nota, extras)

    secoes = _listas_por_secao(doc)
    _ajustar_lista(_lista(secoes, "EXCLUS"), _exclusoes(cat, opcao, res))
    _ajustar_lista(_lista(secoes, "PREMISSAS"), _premissas(cat, proposta, opcao, res))
    _ajustar_lista(_lista(secoes, "PAGAMENTO"), _pagamento(res))

    pendencias = sorted({m for p in _todos_paragrafos(doc) for m in re.findall(r"\[[^\]]{3,}\]", p.text)})
    buf = io.BytesIO()
    doc.save(buf)
    nome = f"KAPTEK-proposta-{slug(cl.get('razao'))}-{slug(proposta['numero'])}"
    nome += (f"-op{opcao['id']}" if varias else "") + f"-rev{proposta.get('revisao', '00')}.docx"
    return buf.getvalue(), nome, pendencias


def gerar(cat, proposta, resultado):
    """Uma proposta por opção ofertada (a estimativa interna não vira proposta): lista de (bytes, nome, pendencias)."""
    pares = [(o, r) for o, r in zip(proposta["opcoes"], resultado["opcoes"]) if not r["interno"]]
    varias = len(pares) > 1
    return [gerar_opcao(cat, proposta, o, r, varias) for o, r in pares]


def verificar(conteudo):
    """Verificação da habilidade KAPTEK: margens 3,2/3,0 e logo no cabeçalho."""
    d = Document(io.BytesIO(conteudo))
    s = d.sections[0]
    return {"margem_sup_cm": round(s.top_margin.cm, 1), "margem_esq_cm": round(s.left_margin.cm, 1),
            "logo": "graphicData" in s.header._element.xml}
