"""
Catálogo de serviços: disciplina → serviço → atividades.

Cada serviço traz o seu formulário (`dados`), as atividades com produtividade por
perfil, os custos diretos e os textos de exclusões, premissas e normas que vão
para a proposta. O arquivo é editável pela aba "Catálogo" do app; `validar()`
garante que toda expressão aponta para campos que existem.
"""

import json
import math
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


NUMERO_MAX = 1e12


def _numero(x, minimo=-NUMERO_MAX):
    """Número finito de tamanho razoável (o JSON aceita NaN, Infinity e inteiros de 400 dígitos)."""
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and minimo <= x <= NUMERO_MAX and math.isfinite(x))


def _campo(sid, c):
    """Tipos que o formulário usa para desenhar o campo."""
    erros = []
    if not isinstance(c["id"], str) or not isinstance(c["rotulo"], str) or c["tipo"] not in TIPOS_CAMPO:
        erros.append(f"{sid}: campo precisa de 'id' e 'rotulo' em texto e 'tipo' entre {list(TIPOS_CAMPO)}")
    elif c["tipo"] in ("int", "float") and not (_numero(c["padrao"]) and _numero(c.get("min", 0))):
        erros.append(f"{sid}.{c['id']}: 'padrao' e 'min' precisam ser números")
    elif c["tipo"] == "bool" and not isinstance(c["padrao"], bool):
        erros.append(f"{sid}.{c['id']}: 'padrao' precisa ser true ou false")
    elif any(not isinstance(o["valor"], str) or not isinstance(o["rotulo"], str) or not _numero(o["num"])
             for o in c.get("opcoes", [])):
        erros.append(f"{sid}.{c['id']}: cada opção precisa de 'valor' e 'rotulo' em texto e 'num' número")
    for chave in ("unidade", "ajuda"):
        if c.get(chave) is not None and not isinstance(c[chave], str):
            erros.append(f"{sid}.{c['id']}: '{chave}' precisa ser texto")
    return erros


def estrutura_servico(s):
    """Problemas de forma de um serviço (vazia quando dá para abrir o app com ele)."""
    if not isinstance(s, dict):
        return ["o serviço precisa ser um objeto JSON ({...})"]
    sid = s.get("id") if isinstance(s.get("id"), str) else "?"
    erros = [f"{sid}: falta o texto '{c}'" for c in CHAVES_SERVICO
             if not isinstance(s.get(c), str) or not s[c].strip()]
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
        else:
            erros += _campo(sid, c)
    for a in s.get("atividades", []):
        if faltam(a, CHAVES_ATIVIDADE):
            erros.append(f"{sid}: atividade sem {faltam(a, CHAVES_ATIVIDADE)}")
            continue
        aid = f"{sid}.{a['id']}"
        if not isinstance(a["id"], str) or not isinstance(a["nome"], str):
            erros.append(f"{aid}: 'id' e 'nome' precisam ser texto")
        for chave in ("b", "calibracao"):
            if chave in a and not (_numero(a[chave], 0) and 0 < a[chave] <= 10):
                erros.append(f"{aid}: '{chave}' precisa ser um número entre 0 e 10")
        for chave in ("fixo", "unid"):
            if not isinstance(a.get(chave, {}), dict) or not all(_numero(h, 0) for h in a.get(chave, {}).values()):
                erros.append(f"{aid}: '{chave}' precisa ser {{perfil: horas}}")
        if not isinstance(a.get("fatores", []), list) or not all(isinstance(f, str) for f in a.get("fatores", [])):
            erros.append(f"{aid}: 'fatores' precisa ser uma lista de nomes")
        if a.get("driver") is not None and not isinstance(a["driver"], (str, int, float)):
            erros.append(f"{aid}: 'driver' precisa ser uma expressão")
    for d in s.get("diretos", []):
        if faltam(d, CHAVES_DIRETO):
            erros.append(f"{sid}: custo direto sem {faltam(d, CHAVES_DIRETO)}")
        elif not isinstance(d["qtd"], (str, int, float)) or not _numero(d.get("valor_unit", 0), 0):
            erros.append(f"{sid}.{d['id']}: 'qtd' precisa ser uma expressão e 'valor_unit' um número")
    return erros


def _validar_servico(s, ids, tipos, etapas, perfis, fatores, ids_servicos):
    erros = []
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
    if not erros:       # conta com os valores padrão: estouro ou casas demais travam o Salvar
        ctx = contexto(s, valores_padrao(s))
        sem_zeros = {n: (v or 1.0) for n, v in ctx.items()}
        for x in s.get("atividades", []) + s.get("diretos", []):
            expr = x.get("driver") if "driver" in x else x.get("qtd")
            try:
                expressao.avaliar(expr, ctx)
            except expressao.DivisaoPorZero:
                # campo que vale zero no padrão não é erro do catálogo; refaz a conta sem zeros
                try:
                    expressao.avaliar(expr, sem_zeros)
                except expressao.DivisaoPorZero:
                    pass
                except expressao.ErroExpressao as e:
                    erros.append(f"{sid}.{x.get('id', '?')}: {e}")
            except expressao.ErroExpressao as e:
                erros.append(f"{sid}.{x.get('id', '?')}: {e}")
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
        try:
            erros += _validar_servico(s, ids, tipos, etapas, perfis, fatores, ids_servicos)
        except (TypeError, ValueError, AttributeError, KeyError, ArithmeticError) as e:
            erros.append(f"{s.get('id', '?')}: formato inválido ({type(e).__name__}: {e})")
    return erros
