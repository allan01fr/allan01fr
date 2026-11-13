"""Contrato de prestação de serviços e recibo em DOCX (bloco B6). Modelos para revisão jurídica."""

import datetime
import json
import copy
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from .exportar_docx import RAIZ, _data_br, _linhas_escopo, _linhas_prazos, _pagamento, moeda, pct_br

AVISO = "Modelo — revisar com assessoria jurídica."
_UN = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze",
       "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_DEZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_CEN = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos",
        "oitocentos", "novecentos"]


def _ate999(n):
    if n == 100:
        return "cem"
    c, r = divmod(n, 100)
    partes = [_CEN[c]] if c else []
    if r:
        partes.append(_UN[r] if r < 20 else _DEZ[r // 10] + (f" e {_UN[r % 10]}" if r % 10 else ""))
    return " e ".join(partes)


def _inteiro_extenso(n):
    if n == 0:
        return "zero"
    mi, resto = divmod(n, 1_000_000)
    mil, un = divmod(resto, 1000)
    partes = []
    if mi:
        partes.append("um milhão" if mi == 1 else f"{_ate999(mi)} milhões")
    if mil:
        partes.append("mil" if mil == 1 else f"{_ate999(mil)} mil")
    if un:
        partes.append(_ate999(un))
    if len(partes) > 1 and (un < 100 or un % 100 == 0 or (not un and (mil < 100 or mil % 100 == 0))):
        return " ".join(partes[:-1]) + " e " + partes[-1]
    return " ".join(partes)


def extenso(valor):
    """Valor em reais por extenso (pt-BR), até 999.999.999,99."""
    cent = round(float(valor) * 100)
    if not 0 <= cent <= 99_999_999_999:
        raise ValueError("valor fora do intervalo suportado")
    reais, cts = divmod(cent, 100)
    partes = []
    if reais or not cts:
        texto = _inteiro_extenso(reais)
        de = " de" if reais and reais % 1_000_000 == 0 else ""
        partes.append(f"{texto}{de} {'real' if reais == 1 else 'reais'}")
    if cts:
        partes.append(f"{_inteiro_extenso(cts)} {'centavo' if cts == 1 else 'centavos'}")
    return " e ".join(partes)


def _org():
    try:
        with open(os.path.join(RAIZ, "dados", "kaptek_org.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _titulo(texto, revisao):
    return texto + (f" — Rev. {int(revisao):02d}" if revisao and int(revisao) > 0 else "")


def _doc(titulo):
    d = Document()
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(10.5)
    h = d.add_heading(titulo, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return d


def _assinaturas(d, linhas):
    d.add_paragraph("\n")
    for nome, papel in linhas:
        d.add_paragraph("_" * 45)
        d.add_paragraph(f"{nome}\n{papel}")


MODELO_CONTRATO = os.path.join(RAIZ, "modelos", "contrato_padrao.docx")
MODELO_RECIBO = os.path.join(RAIZ, "modelos", "recibo_padrao.docx")
_PH = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_DASH = re.compile(r"^—\s+")


def listar_placeholders(caminho):
    """Conjunto de nomes de `{{placeholder}}` de um modelo DOCX (corpo, tabelas, cabeçalho e rodapé).

    Para quem edita o próprio modelo: escreva `{{nome}}` onde o dado deve entrar. Em parágrafo que contém só um
    placeholder de várias linhas, cada linha vira um parágrafo (com o mesmo estilo, ex. marcador de lista).

    Contrato: cliente_nome, cliente_cnpj, cliente_endereco, cliente_signatario, empresa_nome, empresa_cnpj,
    empresa_endereco, empresa_resp, objeto, escopo*, fases*, valor_total, valor_extenso, pagamento*,
    prazo_pagamento_dias, prazo*, arts*, foro, data, numero, revisao (" — Rev. 02", vazio na revisão 0).
    Recibo: cliente_nome, cliente_cnpj, empresa_nome, empresa_cnpj, valor_total, valor_extenso, referente,
    numero, data, proposta_numero.  (* = várias linhas)
    """
    return {m for p in _paragrafos(Document(caminho)) for m in _PH.findall(p.text)}


def _paragrafos(doc):
    def de_corpo(parte):
        for p in parte.paragraphs:
            yield p
        for t in parte.tables:
            for r in t.rows:
                for c in r.cells:
                    yield from de_corpo(c)

    yield from de_corpo(doc)
    for sec in doc.sections:
        for parte in (sec.header, sec.footer):
            yield from de_corpo(parte)


def _preencher(doc, valores):
    """Troca `{{chave}}` por `valores[chave]` (str ou lista de linhas). Junta os runs do parágrafo antes de trocar."""
    vistos = set()
    for par in list(_paragrafos(doc)):
        if id(par._p) in vistos or not _PH.search(par.text):
            continue
        vistos.add(id(par._p))
        texto = par.text
        unico = _PH.fullmatch(_DASH.sub("", texto.strip()))
        v = valores.get(unico.group(1)) if unico else None
        if isinstance(v, (list, tuple)):
            linhas = [str(x) for x in v] or [""]
            _definir_texto(par, linhas[0])
            ant = par
            for extra in linhas[1:]:
                novo = copy.deepcopy(par._p)
                ant._p.addnext(novo)
                ant = type(par)(novo, par._parent)
                _definir_texto(ant, extra)
            continue

        def sub(m):
            x = valores.get(m.group(1))
            if x is None:
                return m.group(0)
            return "\n".join(map(str, x)) if isinstance(x, (list, tuple)) else str(x)

        _definir_texto(par, _PH.sub(sub, texto))


def _definir_texto(par, texto):
    runs = par.runs
    if len(runs) >= 2 and runs[0].text.startswith("—") and not runs[0].text.strip("— "):
        texto = _DASH.sub("", texto)       # item de lista do modelo: run 0 é o travessão, mantido
        runs = runs[1:]
    if not runs:
        par.add_run(texto)
        return
    runs[0].text = texto
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def _forma_cobranca(fr):
    """Como a fase é cobrada, em linguagem de cliente."""
    cob = fr.get("cobranca")
    if cob == "percentual":
        hp = fr["percentual"]
        return (f"{pct_br(hp['pct'])} sobre o valor da execução (valor estimado da obra {moeda(hp['base'])}); "
                f"honorários estimados em {moeda(fr['preco'])}")
    if cob == "pacote":
        pk = fr["pacote"]
        return (f"pacote de {pk['horas']:.0f} horas, estimado pelas horas da obra ({pk['meses']} meses), "
                f"{moeda(fr['preco'] - fr.get('preco_fornec', 0))}")
    return f"escopo fechado, {moeda(fr['preco'])}"


def _linhas_fases(res):
    return [f"Fase {n} — {fr['nome']}: {_forma_cobranca(fr)}." for n, fr in enumerate(res["fases"], 1)]


def _prazo_execucao(proposta, res):
    ids = {f["id"] for o in proposta.get("opcoes", []) if o.get("id") == res.get("id") for f in o.get("fases", [])
           if f.get("modulo") == "execucao" and f.get("ativa", True)}
    etapas = [e for e in res.get("cronograma", []) if e.get("fase") in ids]
    if not etapas:
        return None
    meses = next((e["meses"] for e in etapas if e.get("meses")), None)
    dias = sum(e["dias_corridos"] for e in etapas)
    return f"Prazo de execução da obra: {f'{meses} meses ({dias} dias corridos)' if meses else f'{dias} dias corridos'}."


def _linhas_arts(res):
    saida = []
    for a in res.get("arts") or []:
        saida.append(a if isinstance(a, str) else
                     " — ".join(str(a[k]) for k in ("tipo", "modalidade", "atividades") if a.get(k)))
    return saida


def _contexto_contrato(proposta, res, revisao):
    org, cl = _org(), proposta.get("cliente", {})
    escopo = [f"{num} — {t}" + (f" Entregáveis: {e}." if e else "") for num, t, e in _linhas_escopo(res)]
    prazo = [f"{rot}: {dur} ({marco})." for rot, dur, marco in _linhas_prazos(res)]
    pe = _prazo_execucao(proposta, res)
    if pe:
        prazo.append(pe)
    arts = _linhas_arts(res)
    return {
        "cliente_nome": cl.get("razao") or "[contratante]", "cliente_cnpj": cl.get("cnpj") or "[CNPJ]",
        "cliente_endereco": cl.get("endereco") or "[endereço]", "cliente_signatario": cl.get("signatario") or "[signatário]",
        "empresa_nome": org.get("razao") or "[contratada]", "empresa_cnpj": org.get("cnpj", "[CNPJ]"),
        "empresa_endereco": org.get("endereco", "[endereço]"), "empresa_resp": org.get("resp", "[responsável]"),
        "objeto": proposta.get("objeto") or "Prestação de serviços de engenharia, conforme proposta.",
        "escopo": escopo, "fases": _linhas_fases(res),
        "valor_total": moeda(res["preco"]), "valor_extenso": extenso(res["preco"]),
        "pagamento": _pagamento(res), "prazo_pagamento_dias": str(proposta.get("prazo_pagamento_dias", 15)),
        "prazo": prazo,
        "arts": (["ARTs previstas:"] + arts) if arts else
                ["As Anotações de Responsabilidade Técnica (ART) exigidas serão emitidas junto ao CREA, conforme a proposta."],
        "foro": proposta.get("foro") or "[foro]", "data": _data_br(proposta.get("data", "")),
        "numero": str(proposta.get("numero", "—")), "revisao": f" — Rev. {int(revisao):02d}" if revisao and int(revisao) > 0 else "",
    }


def _modelo_valido(modelo, padrao):
    m = modelo or (padrao if os.path.exists(padrao) else None)
    return m if m and os.path.exists(m) else None


def gerar_contrato(proposta, res, caminho, revisao=0, modelo=None):
    """Contrato a partir de `modelo` (DOCX com {{placeholders}}) ou de modelos/contrato_padrao.docx, se existir;
    sem modelo, monta o documento em código. Veja `listar_placeholders`."""
    cfg = {f["id"]: f for o in proposta.get("opcoes", []) if o.get("id") == res.get("id") for f in o.get("fases", [])}
    for fr in res["fases"]:
        fr.setdefault("_cfg_desempenho", cfg.get(fr["id"], {}).get("desempenho", {}))
    mod = _modelo_valido(modelo, MODELO_CONTRATO)
    if mod:
        d = Document(mod)
        _preencher(d, _contexto_contrato(proposta, res, revisao))
        d.save(caminho)
        return caminho
    return _contrato_em_codigo(proposta, res, caminho, revisao)


def _contrato_em_codigo(proposta, res, caminho, revisao):
    org, cl = _org(), proposta.get("cliente", {})
    ctx = _contexto_contrato(proposta, res, revisao)
    d = _doc(_titulo("Contrato de prestação de serviços", revisao))
    p = d.add_paragraph()
    p.add_run(AVISO).italic = True
    d.add_paragraph(f"Proposta nº {ctx['numero']} — {ctx['data']}")

    d.add_heading("1. Partes", 1)
    d.add_paragraph(f"CONTRATADA: {ctx['empresa_nome']}, CNPJ {ctx['empresa_cnpj']}, "
                    f"com sede em {ctx['empresa_endereco']}, representada por {ctx['empresa_resp']}.")
    d.add_paragraph(f"CONTRATANTE: {ctx['cliente_nome']}, CNPJ {ctx['cliente_cnpj']}, {ctx['cliente_endereco']}, "
                    f"representada por {ctx['cliente_signatario']}.")

    d.add_heading("2. Objeto", 1)
    d.add_paragraph(ctx["objeto"])
    for linha in ctx["escopo"]:
        d.add_paragraph(linha, style="List Bullet")

    d.add_heading("3. Valor e forma de pagamento", 1)
    d.add_paragraph(f"Valor total: {ctx['valor_total']} ({ctx['valor_extenso']}).")
    for linha in ctx["fases"]:
        d.add_paragraph(linha, style="List Bullet")
    for item in ctx["pagamento"]:
        d.add_paragraph(item, style="List Bullet")
    d.add_paragraph(f"Pagamento em até {ctx['prazo_pagamento_dias']} dias da emissão da cobrança.")

    d.add_heading("4. Prazo", 1)
    for linha in ctx["prazo"]:
        d.add_paragraph(linha, style="List Bullet")

    d.add_heading("5. Responsabilidade técnica (ARTs)", 1)
    arts = ctx["arts"]
    d.add_paragraph(arts[0])
    for a in arts[1:]:
        d.add_paragraph(a, style="List Bullet")

    d.add_heading("6. Obrigações das partes", 1)
    d.add_paragraph("A CONTRATADA executará os serviços com diligência técnica e sigilo. A CONTRATANTE fornecerá "
                    "acessos e documentação, efetuará os pagamentos nos prazos e aprovará as entregas.", style="List Bullet")

    d.add_heading("7. Rescisão", 1)
    d.add_paragraph("Qualquer parte pode rescindir com aviso prévio de 15 dias, pagando-se os serviços já executados "
                    "e os custos incorridos.")

    d.add_heading("8. Foro", 1)
    d.add_paragraph(f"Fica eleito o foro da comarca de {ctx['foro']} para dirimir questões deste contrato.")

    _assinaturas(d, [(org.get("razao", "CONTRATADA"), "CONTRATADA"), (cl.get("razao", "CONTRATANTE"), "CONTRATANTE"),
                     ("Testemunha 1", ""), ("Testemunha 2", "")])
    d.save(caminho)
    return caminho


def gerar_recibo(proposta, valor, referente, caminho, data=None, numero=None, modelo=None):
    """Recibo a partir de `modelo` ou de modelos/recibo_padrao.docx, se existir; sem modelo, monta em código."""
    org, cl = _org(), proposta.get("cliente", {})
    data = data or datetime.date.today().isoformat()
    mod = _modelo_valido(modelo, MODELO_RECIBO)
    if mod:
        d = Document(mod)
        _preencher(d, {
            "cliente_nome": cl.get("razao") or "[cliente]", "cliente_cnpj": cl.get("cnpj") or "[CNPJ]",
            "empresa_nome": org.get("razao", "CONTRATADA"), "empresa_cnpj": org.get("cnpj", ""),
            "valor_total": moeda(valor), "valor_extenso": extenso(valor), "referente": referente,
            "numero": str(numero or ""), "data": _data_br(str(data)), "proposta_numero": str(proposta.get("numero", "—")),
        })
        d.save(caminho)
        return caminho
    d = _doc(_titulo("Recibo", 0) + (f" nº {numero}" if numero else ""))
    d.add_paragraph(f"Valor: {moeda(valor)}")
    d.add_paragraph(f"Recebemos de {cl.get('razao') or '[cliente]'} a importância de {moeda(valor)} "
                    f"({extenso(valor)}), referente a {referente}.")
    d.add_paragraph(f"Proposta nº {proposta.get('numero', '—')}. Data: {_data_br(str(data))}.")
    _assinaturas(d, [(org.get("razao", "CONTRATADA"), f"CNPJ {org.get('cnpj', '')}")])
    d.save(caminho)
    return caminho
