"""Download das séries mensais oficiais (variação % a.m.) do SGS do Banco Central e carga em `indices`."""
import datetime as dt
import json
import urllib.request

from . import referencias as rf

SERIES = {
    "IGP-M": 189,
    "INPC": 188,
    "IPCA": 433,
    "INCC-M": 192,  # VERIFICAR: 192 = INCC-M (variação mensal) no SGS; 7456 seria alternativa
}


def url_sgs(codigo, de=None, ate=None):
    """`de`/`ate`: date, 'AAAA-MM' ou 'dd/mm/aaaa'."""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
    if de:
        url += "&dataInicial=" + _dmy(de)
    if ate:
        url += "&dataFinal=" + _dmy(ate)
    return url


def _dmy(x):
    if isinstance(x, (dt.date, dt.datetime)):
        return x.strftime("%d/%m/%Y")
    x = str(x)
    if len(x) == 7 and x[4] == "-":
        return f"01/{x[5:7]}/{x[:4]}"
    return x


def parse_sgs(lista):
    saida = []
    for it in lista:
        d, v = str(it["data"]), str(it["valor"]).strip()
        if not v:
            continue
        v = v.replace(",", ".") if "," in v else v
        dia, mes, ano = d.split("/")
        saida.append((f"{ano}-{mes}", float(v)))
    return sorted(saida)


def _http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def baixar_serie(nome, de="2000-01", ate=None, http_get=None):
    if nome not in SERIES:
        raise ValueError(f"Índice desconhecido: {nome}. Opções: {', '.join(SERIES)}")
    get = http_get or _http_get
    url = url_sgs(SERIES[nome], de, ate)
    try:
        corpo = get(url)
        dados = json.loads(corpo) if isinstance(corpo, (str, bytes)) else corpo
        return parse_sgs(dados)
    except Exception as e:
        raise RuntimeError(f"Não foi possível baixar {nome} do Banco Central ({e}). "
                           "Baixe a série manualmente e use a importação de CSV (aba 10).") from e


def atualizar_banco(con, nome, de="2000-01"):
    var = baixar_serie(nome, de)
    indice = rf.indice_de_variacoes(var)
    con.execute("DELETE FROM indices WHERE nome=?", (nome,))
    rf.importar_indices(con, nome, indice)
    return len(var)


def fator_periodo(con, nome, data_base, data_alvo=None):
    if not data_alvo:
        r = con.execute("SELECT MAX(mes) AS m FROM indices WHERE nome=?", (nome,)).fetchone()
        data_alvo = r["m"] if r else None
    if not data_alvo:
        return None
    return rf.atualizar(con, 1.0, data_base, data_alvo, nome)[1]
