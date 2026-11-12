"""Contrato de prestação de serviços e recibo em DOCX (bloco B6). Modelos para revisão jurídica."""

import datetime
import json
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from .exportar_docx import RAIZ, _data_br, _linhas_escopo, _linhas_prazos, _pagamento, moeda

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


def gerar_contrato(proposta, res, caminho, revisao=0):
    org, cl = _org(), proposta.get("cliente", {})
    cfg = {f["id"]: f for o in proposta.get("opcoes", []) if o.get("id") == res.get("id") for f in o.get("fases", [])}
    for fr in res["fases"]:
        fr.setdefault("_cfg_desempenho", cfg.get(fr["id"], {}).get("desempenho", {}))
    d = _doc(_titulo("Contrato de prestação de serviços", revisao))
    p = d.add_paragraph()
    p.add_run(AVISO).italic = True
    d.add_paragraph(f"Proposta nº {proposta.get('numero', '—')} — {_data_br(proposta.get('data', ''))}")

    d.add_heading("1. Partes", 1)
    d.add_paragraph(f"CONTRATADA: {org.get('razao') or '[contratada]'}, CNPJ {org.get('cnpj', '[CNPJ]')}, "
                    f"com sede em {org.get('endereco', '[endereço]')}, representada por {org.get('resp', '[responsável]')}.")
    d.add_paragraph(f"CONTRATANTE: {cl.get('razao') or '[contratante]'}, {cl.get('endereco') or '[endereço]'}, "
                    f"representada por {cl.get('signatario') or '[signatário]'}.")

    d.add_heading("2. Objeto", 1)
    d.add_paragraph(proposta.get("objeto") or "Prestação de serviços de engenharia, conforme proposta.")
    for num, texto, entregavel in _linhas_escopo(res):
        d.add_paragraph(f"{num} — {texto}" + (f" Entregáveis: {entregavel}." if entregavel else ""), style="List Bullet")

    d.add_heading("3. Valor e forma de pagamento", 1)
    d.add_paragraph(f"Valor total: {moeda(res['preco'])} ({extenso(res['preco'])}).")
    for item in _pagamento(res):
        d.add_paragraph(item, style="List Bullet")
    d.add_paragraph(f"Pagamento em até {proposta.get('prazo_pagamento_dias', 15)} dias da emissão da cobrança.")

    d.add_heading("4. Prazo", 1)
    for rot, dur, marco in _linhas_prazos(res):
        d.add_paragraph(f"{rot}: {dur} ({marco}).", style="List Bullet")

    d.add_heading("5. Responsabilidade técnica (ARTs)", 1)
    arts = res.get("arts") or []
    if arts:
        for a in arts:
            d.add_paragraph(a if isinstance(a, str) else
                            " — ".join(str(a[k]) for k in ("tipo", "modalidade", "atividades") if a.get(k)), style="List Bullet")
    else:
        d.add_paragraph("As Anotações de Responsabilidade Técnica (ART) exigidas serão emitidas junto ao CREA, "
                        "conforme a proposta.")

    d.add_heading("6. Obrigações das partes", 1)
    d.add_paragraph("A CONTRATADA executará os serviços com diligência técnica e sigilo. A CONTRATANTE fornecerá "
                    "acessos e documentação, efetuará os pagamentos nos prazos e aprovará as entregas.", style="List Bullet")

    d.add_heading("7. Rescisão", 1)
    d.add_paragraph("Qualquer parte pode rescindir com aviso prévio de 15 dias, pagando-se os serviços já executados "
                    "e os custos incorridos.")

    d.add_heading("8. Foro", 1)
    d.add_paragraph("Fica eleito o foro da comarca de [foro] para dirimir questões deste contrato.")

    _assinaturas(d, [(org.get("razao", "CONTRATADA"), "CONTRATADA"), (cl.get("razao", "CONTRATANTE"), "CONTRATANTE"),
                     ("Testemunha 1", ""), ("Testemunha 2", "")])
    d.save(caminho)
    return caminho


def gerar_recibo(proposta, valor, referente, caminho, data=None, numero=None):
    org, cl = _org(), proposta.get("cliente", {})
    data = data or datetime.date.today().isoformat()
    d = _doc(_titulo("Recibo", 0) + (f" nº {numero}" if numero else ""))
    d.add_paragraph(f"Valor: {moeda(valor)}")
    d.add_paragraph(f"Recebemos de {cl.get('razao') or '[cliente]'} a importância de {moeda(valor)} "
                    f"({extenso(valor)}), referente a {referente}.")
    d.add_paragraph(f"Proposta nº {proposta.get('numero', '—')}. Data: {_data_br(str(data))}.")
    _assinaturas(d, [(org.get("razao", "CONTRATADA"), f"CNPJ {org.get('cnpj', '')}")])
    d.save(caminho)
    return caminho
