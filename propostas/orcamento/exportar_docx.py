"""
Proposta comercial no template aprovado da KAPTEK (modelos/proposta.docx).

Regra da marca: preencher o template, nunca remontar o documento. Este módulo só
substitui os campos entre colchetes e ajusta o número de linhas das tabelas e
dos itens de lista (escopo, exclusões, premissas, prazos, honorários,
pagamento), clonando a linha ou o parágrafo do próprio template.

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

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = os.path.join(RAIZ, "modelos", "proposta.docx")

FRASE_DESLOCAMENTO = ("Não estão inclusos deslocamentos fora da Região Metropolitana do Rio de Janeiro, "
                      "que serão orçados à parte mediante aprovação prévia.")
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
    """Preço dos serviços repartido por serviço, na proporção do custo direto de cada um."""
    pesos = []
    for i, it in enumerate(opcao["itens"]):
        mo = sum(l["custo_mo"] for l in res["linhas"] if l["item"] == i)
        dr = sum(d["valor"] for d in res["diretos"] if d["item"] == i)
        nome = next((l["servico_nome"] for l in res["linhas"] if l["item"] == i), None)
        if nome and mo + dr > 0:
            pesos.append((nome, mo + dr))
    total = sum(p for _, p in pesos) or 1
    valores = [round(res["preco_servicos"] * p / total, 2) for _, p in pesos]
    if valores:
        valores[-1] = round(res["preco_servicos"] - sum(valores[:-1]), 2)
    return [(n, v) for (n, _), v in zip(pesos, valores)]


def _linhas_honorarios(cat, params, opcao, res):
    linhas = []
    modelo = res["modelo_preco"]
    if modelo == "hora":
        for p, nome in cat["perfis"].items():
            h = res["horas_perfil"][p]
            if h > 0:
                taxa = float(params["perfis"][p]["taxa_venda_h"])
                linhas.append((f"Hora técnica — {nome}", f"{h:.1f} h".replace(".", ","), moeda(taxa), moeda(h * taxa)))
        if res["reembolso"] > 0:
            linhas.append(("Despesas reembolsáveis (estimativa, inclui ART)", "1", moeda(res["reembolso"]), moeda(res["reembolso"])))
    elif modelo == "fee" and res["preco_fee"] is not None:
        linhas.append((f"Honorários de engenharia — {pct_br(res['fee_pct'])} sobre o valor da obra estimado em {moeda(res['fee_base'])}",
                       "1", moeda(res["fee_honorarios"]), moeda(res["fee_honorarios"])))
    else:
        for nome, v in _rateio_servicos(opcao, res):
            linhas.append((f"Honorários de engenharia — {nome}", "1", moeda(v), moeda(v)))
    for f in res["fornecimentos"]:
        qtd = float(f.get("qtd") or 0)
        unit = f["preco"] / qtd if qtd else f["preco"]
        q_txt = f"{qtd:g} {f.get('unid', '')}".strip().replace(".", ",")
        linhas.append((f.get("descricao", "Fornecimento"), q_txt, moeda(unit), moeda(f["preco"])))
    if any(d["descricao"].startswith("Taxa de ART") for d in res["diretos"]) and modelo != "hora":
        linhas.append(("Taxa de ART junto ao CREA", "1", "inclusa", "inclusa"))
    return linhas


def _total_texto(res):
    if res["modelo_preco"] == "hora":
        return f"{moeda(res['preco_hora'])} (estimado; teto {moeda(res['preco_hora_teto'])})"
    return moeda(res["preco"])


def _exclusoes(cat, opcao, res):
    return ct.exclusoes_validas(cat, [it["servico"] for it in opcao["itens"]], bool(res["fornecimentos"]))


def _premissas(cat, opcao):
    textos = []
    for it in opcao["itens"]:
        for p in ct.servico(cat, it["servico"]).get("premissas", []):
            if p not in textos and p not in PREMISSAS_FINAIS:
                textos.append(p)
    return textos + PREMISSAS_FINAIS


def _minuscula(texto):
    """Primeira letra minúscula, preservando siglas (TAB, PMOC, CFD...)."""
    if len(texto) > 1 and texto[1].islower():
        return texto[0].lower() + texto[1:]
    return texto


def _linhas_escopo(res):
    """Uma linha por serviço: atividades e entregáveis da opção."""
    grupos = []
    for l in res["linhas"]:
        if not grupos or grupos[-1]["item"] != l["item"]:
            grupos.append({"item": l["item"], "nome": l["servico_nome"], "ativ": [], "entr": []})
        g = grupos[-1]
        g["ativ"].append(_minuscula(l["nome"]))
        if l["entregavel"] and l["entregavel"] not in g["entr"]:
            g["entr"].append(l["entregavel"])
    return [(f"{i + 1:02d}", f"{g['nome']}: {'; '.join(g['ativ'])}.", "; ".join(g["entr"]))
            for i, g in enumerate(grupos)]


def _texto_objeto(proposta, opcao, res, varias):
    nomes = []
    for l in res["linhas"]:
        if l["servico_nome"] not in nomes:
            nomes.append(l["servico_nome"])
    base = (proposta.get("objeto") or "serviços técnicos de engenharia").rstrip(".")
    sufixo = f" — {opcao['nome']}" if varias else ""
    return (f"Prestação de serviços técnicos de engenharia: {base}{sufixo}. "
            f"Compreende: {'; '.join(nomes)}, conforme as atividades e os entregáveis relacionados na seção 3.")


# ----------------------------------------------------------------------------- API
def gerar_opcao(cat, proposta, opcao, res, varias=False):
    """Preenche o template para uma opção. Devolve (bytes, nome_arquivo, pendencias)."""
    params = proposta["parametros"]
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
    for par in list(_todos_paragrafos(doc)):
        for de, para in campos.items():
            substituir(par, de, para)
        if par.text.startswith("[Descreva o serviço contratado"):
            _definir(par, _texto_objeto(proposta, opcao, res, varias))

    rev = _tabela(doc, "Rev.")
    _definir(rev.rows[1].cells[0].paragraphs[0], proposta.get("revisao", "00"))
    _definir(rev.rows[1].cells[1].paragraphs[0], _data_br(proposta["data"]))

    _preencher_linhas(_tabela(doc, "#", "Serviço"), _linhas_escopo(res))

    prazos = [(e["rotulo"], f"{e['dias_corridos']} dias", e["marco"]) for e in res["cronograma"]]
    prazos.append(("Prazo total estimado", f"{res['prazo_dias_corridos']} dias", "Conclusão dos serviços"))
    _preencher_linhas(_tabela(doc, "Etapa", "Prazo"), prazos)

    hon = _tabela(doc, "Descrição", "Qtd.")
    _preencher_linhas(hon, _linhas_honorarios(cat, params, opcao, res), manter_ultima=True)
    _definir(hon.rows[-1].cells[-1].paragraphs[0], _total_texto(res))

    secoes = _listas_por_secao(doc)
    _ajustar_lista(_lista(secoes, "EXCLUS"), _exclusoes(cat, opcao, res))
    _ajustar_lista(_lista(secoes, "PREMISSAS"), _premissas(cat, opcao))
    _ajustar_lista(_lista(secoes, "PAGAMENTO"), [f"{pct_br(m['pct'])} {m['marco']}." for m in res["pagamento"]])

    pendencias = sorted({m for p in _todos_paragrafos(doc) for m in re.findall(r"\[[^\]]{3,}\]", p.text)})
    buf = io.BytesIO()
    doc.save(buf)
    nome = f"KAPTEK-proposta-{slug(cl.get('razao'))}-{slug(proposta['numero'])}"
    nome += (f"-op{opcao['id']}" if varias else "") + f"-rev{proposta.get('revisao', '00')}.docx"
    return buf.getvalue(), nome, pendencias


def gerar(cat, proposta, resultado):
    """Uma proposta por opção: lista de (bytes, nome, pendencias)."""
    varias = len(proposta["opcoes"]) > 1
    return [gerar_opcao(cat, proposta, o, r, varias) for o, r in zip(proposta["opcoes"], resultado["opcoes"])]


def verificar(conteudo):
    """Verificação da habilidade KAPTEK: margens 3,2/3,0 e logo no cabeçalho."""
    d = Document(io.BytesIO(conteudo))
    s = d.sections[0]
    return {"margem_sup_cm": round(s.top_margin.cm, 1), "margem_esq_cm": round(s.left_margin.cm, 1),
            "logo": "graphicData" in s.header._element.xml}
