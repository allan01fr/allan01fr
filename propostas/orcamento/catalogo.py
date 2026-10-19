"""
Catálogo de serviços: disciplina → serviço → atividades.

Cada serviço traz o seu formulário (`dados`), as atividades com produtividade por
perfil, os custos diretos e os textos de exclusões, premissas e normas que vão
para a proposta. O arquivo é editável pela aba "Catálogo" do app; `validar()`
garante que toda expressão aponta para campos que existem.
"""

import json
import os
import shutil

from . import expressao

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAMINHO_PADRAO = os.path.join(RAIZ, "dados", "catalogo.json")

# variáveis da proposta disponíveis em qualquer expressão
GLOBAIS = ("dist_km", "area_ref")
TIPOS_CAMPO = ("int", "float", "opcoes", "bool")


def carregar(caminho=None):
    with open(caminho or CAMINHO_PADRAO, encoding="utf-8") as f:
        return json.load(f)


def salvar(cat, caminho=None):
    """Grava o catálogo, guardando a versão anterior em .bak.json."""
    caminho = caminho or CAMINHO_PADRAO
    erros = validar(cat)
    if erros:
        raise ValueError("catálogo inválido:\n- " + "\n- ".join(erros))
    if os.path.exists(caminho):
        shutil.copyfile(caminho, caminho.replace(".json", ".bak.json"))
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)


def servico(cat, sid):
    for s in cat["servicos"]:
        if s["id"] == sid:
            return s
    raise KeyError(f"serviço '{sid}' não existe no catálogo")


def etapa(cat, eid):
    for e in cat["etapas"]:
        if e["id"] == eid:
            return e
    raise KeyError(f"etapa '{eid}' não existe no catálogo")


def disciplinas(cat):
    vistos = []
    for s in cat["servicos"]:
        if s["disciplina"] not in vistos:
            vistos.append(s["disciplina"])
    return vistos


def filtrar(cat, disciplina=None, tipo=None):
    return [s for s in cat["servicos"]
            if (not disciplina or s["disciplina"] == disciplina) and (not tipo or s["tipo"] == tipo)]


def valores_padrao(serv):
    return {c["id"]: c["padrao"] for c in serv["dados"]}


def opcao(campo, valor):
    for o in campo["opcoes"]:
        if o["valor"] == valor:
            return o
    return campo["opcoes"][0]


def contexto(serv, valores, globais=None):
    """Variáveis numéricas para as expressões do serviço.

    Campo de opções vira o seu `num` e também uma flag por opção: nivel__bim = 1 ou 0.
    """
    ctx = {g: float((globais or {}).get(g, 0) or 0) for g in GLOBAIS}
    for c in serv["dados"]:
        v = valores.get(c["id"], c["padrao"])
        if c["tipo"] == "opcoes":
            escolhida = opcao(c, v)
            ctx[c["id"]] = float(escolhida["num"])
            for o in c["opcoes"]:
                ctx[f"{c['id']}__{o['valor']}"] = 1.0 if o["valor"] == escolhida["valor"] else 0.0
        elif c["tipo"] == "bool":
            ctx[c["id"]] = 1.0 if v else 0.0
        else:
            ctx[c["id"]] = float(v or 0)
    return ctx


def nomes_contexto(serv):
    """Nomes que as expressões do serviço podem usar."""
    nomes = set(GLOBAIS)
    for c in serv["dados"]:
        nomes.add(c["id"])
        if c["tipo"] == "opcoes":
            nomes.update(f"{c['id']}__{o['valor']}" for o in c["opcoes"])
    return nomes


def fator_global(cat, nome, chave):
    return float(opcao(cat["fatores"][nome], chave)["num"])


def texto_condicional(e):
    """Exclusão ou premissa como dict: texto, serviços que a anulam e se cai quando há fornecimento (turnkey)."""
    if isinstance(e, str):
        return {"texto": e, "exceto_se": [], "exceto_fornecimento": False}
    return {"texto": e["texto"], "exceto_se": list(e.get("exceto_se", [])),
            "exceto_fornecimento": bool(e.get("exceto_fornecimento", False))}


exclusao = texto_condicional


def textos_validos(cat, servicos_na_opcao, tem_fornecimento, chave="exclusoes"):
    """Exclusões (ou premissas) dos serviços da opção, sem repetição e sem as que outro item anula."""
    textos = []
    for sid in servicos_na_opcao:
        for e in map(texto_condicional, servico(cat, sid).get(chave, [])):
            if set(e["exceto_se"]) & set(servicos_na_opcao):
                continue
            if e["exceto_fornecimento"] and tem_fornecimento:
                continue
            if e["texto"] not in textos:
                textos.append(e["texto"])
    return textos


def exclusoes_validas(cat, servicos_na_opcao, tem_fornecimento):
    return textos_validos(cat, servicos_na_opcao, tem_fornecimento, "exclusoes")


# chaves que a interface e o motor leem direto: sem elas o app quebra ao abrir, antes de mostrar qualquer aviso
CHAVES_SERVICO = ("id", "nome", "disciplina", "descricao", "tipo")
CHAVES_CAMPO = ("id", "rotulo", "tipo", "padrao")
CHAVES_OPCAO = ("valor", "rotulo", "num")
CHAVES_ATIVIDADE = ("id", "nome", "etapa")
CHAVES_DIRETO = ("id", "nome", "qtd")


def estrutura_servico(s):
    """Problemas de forma de um serviço (vazia quando dá para abrir o app com ele)."""
    if not isinstance(s, dict):
        return ["o serviço precisa ser um objeto JSON ({...})"]
    sid = s.get("id") if isinstance(s.get("id"), str) else "?"
    erros = [f"{sid}: falta o texto '{c}'" for c in CHAVES_SERVICO if not str(s.get(c) or "").strip()]
    for lista in ("dados", "atividades", "diretos", "exclusoes", "premissas", "normas"):
        if not isinstance(s.get(lista, []), list):
            erros.append(f"{sid}: '{lista}' precisa ser uma lista")
    if erros:
        return erros

    def faltam(x, chaves):
        return [c for c in chaves if not isinstance(x, dict) or c not in x]
    for c in s.get("dados", []):
        if faltam(c, CHAVES_CAMPO):
            erros.append(f"{sid}: campo do formulário sem {faltam(c, CHAVES_CAMPO)}")
        elif not isinstance(c.get("opcoes", []), list) or any(faltam(o, CHAVES_OPCAO) for o in c.get("opcoes", [])):
            erros.append(f"{sid}.{c['id']}: cada opção precisa de {list(CHAVES_OPCAO)}")
    for a in s.get("atividades", []):
        if faltam(a, CHAVES_ATIVIDADE):
            erros.append(f"{sid}: atividade sem {faltam(a, CHAVES_ATIVIDADE)}")
    for d in s.get("diretos", []):
        if faltam(d, CHAVES_DIRETO):
            erros.append(f"{sid}: custo direto sem {faltam(d, CHAVES_DIRETO)}")
    return erros


def validar(cat):
    """Lista de problemas do catálogo (vazia quando está tudo certo)."""
    erros = []
    perfis = set(cat.get("perfis", {}))
    etapas = {e["id"] for e in cat.get("etapas", [])}
    fatores = set(cat.get("fatores", {}))
    tipos = set(cat.get("tipos", {}))
    ids = set()
    if not perfis:
        erros.append("catálogo sem perfis")
    ids_servicos = {s.get("id") for s in cat.get("servicos", []) if isinstance(s, dict)}
    for e in cat.get("turnkey", {}).get("etapas", []):
        for t in e.get("tipos", []):
            if t not in tipos:
                erros.append(f"turnkey.{e['id']}: tipo '{t}' desconhecido")
        for sid in e.get("servicos", []):
            if sid not in ids_servicos:
                erros.append(f"turnkey.{e['id']}: serviço '{sid}' inexistente")
        for c in e.get("categorias", []):
            if c not in ("material", "equipamento", "mo_execucao", "subcontrato"):
                erros.append(f"turnkey.{e['id']}: categoria '{c}' desconhecida")
    for f, d in cat.get("fatores", {}).items():
        if not d.get("opcoes"):
            erros.append(f"fator global '{f}' sem opções")
    for s in cat.get("servicos", []):
        forma = estrutura_servico(s)
        if forma:
            erros += forma
            continue
        sid = s.get("id", "?")
        if sid in ids:
            erros.append(f"{sid}: id de serviço repetido")
        ids.add(sid)
        if s.get("tipo") not in tipos:
            erros.append(f"{sid}: tipo '{s.get('tipo')}' desconhecido")
        campos = set()
        for c in s.get("dados", []):
            if c["id"] in campos:
                erros.append(f"{sid}: campo '{c['id']}' repetido")
            campos.add(c["id"])
            if c.get("tipo") not in TIPOS_CAMPO:
                erros.append(f"{sid}.{c['id']}: tipo de campo '{c.get('tipo')}' inválido")
            if c.get("tipo") == "opcoes":
                if not c.get("opcoes"):
                    erros.append(f"{sid}.{c['id']}: campo de opções sem opções")
                elif c["padrao"] not in [o["valor"] for o in c["opcoes"]]:
                    erros.append(f"{sid}.{c['id']}: padrão '{c['padrao']}' não está entre as opções")
        nomes_ok = nomes_contexto(s)
        opcoes_servico = {c["id"] for c in s.get("dados", []) if c.get("tipo") == "opcoes"}
        aids = set()
        if not s.get("atividades"):
            erros.append(f"{sid}: serviço sem atividades")
        for a in s.get("atividades", []):
            aid = f"{sid}.{a.get('id', '?')}"
            if a.get("id") in aids:
                erros.append(f"{aid}: id de atividade repetido")
            aids.add(a.get("id"))
            if a.get("etapa") not in etapas:
                erros.append(f"{aid}: etapa '{a.get('etapa')}' desconhecida")
            b = a.get("b", 1.0)
            if not (0 < float(b) <= 1.5):
                erros.append(f"{aid}: expoente b={b} fora de (0; 1,5]")
            for chave in ("fixo", "unid"):
                for p, h in a.get(chave, {}).items():
                    if p not in perfis:
                        erros.append(f"{aid}: perfil '{p}' desconhecido em {chave}")
                    if float(h) < 0:
                        erros.append(f"{aid}: horas negativas em {chave}.{p}")
            if a.get("unid") and not a.get("driver"):
                erros.append(f"{aid}: horas por unidade sem driver")
            for f in a.get("fatores", []):
                if f not in fatores and f not in opcoes_servico:
                    erros.append(f"{aid}: fator '{f}' não é global nem campo de opções do serviço")
            if a.get("driver"):
                try:
                    faltam = expressao.nomes(a["driver"]) - nomes_ok
                    if faltam:
                        erros.append(f"{aid}: driver usa {sorted(faltam)} que não existem no formulário")
                except expressao.ErroExpressao as e:
                    erros.append(f"{aid}: {e}")
        for e in s.get("exclusoes", []) + s.get("premissas", []):
            if not isinstance(e, (str, dict)) or (isinstance(e, dict) and "texto" not in e):
                erros.append(f"{sid}: exclusão ou premissa sem texto")
                continue
            for outro in texto_condicional(e)["exceto_se"]:
                if outro not in ids_servicos:
                    erros.append(f"{sid}: exclusão ou premissa aponta para serviço inexistente '{outro}'")
        for d in s.get("diretos", []):
            try:
                faltam = expressao.nomes(d["qtd"]) - nomes_ok
                if faltam:
                    erros.append(f"{sid}.{d['id']}: quantidade usa {sorted(faltam)} que não existem")
            except expressao.ErroExpressao as e:
                erros.append(f"{sid}.{d.get('id', '?')}: {e}")
    return erros
