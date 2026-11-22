import sqlite3

from orcamento import referencias as rf

REFS = [{"fonte": "A", "valor": 100}, {"fonte": "B", "valor": 110}, {"fonte": "C", "valor": 120},
        {"fonte": "D", "valor": 200}]


def test_nao_comparavel_fica_fora_dos_calculos():
    base = rf.cesta(REFS)
    c = rf.cesta(REFS + [{"fonte": "X", "valor": 1, "comparavel": False, "motivo": "outra região"}])
    assert c["valor"] == base["valor"] and c["menor"] == base["menor"] and c["media"] == base["media"]
    assert [f["fonte"] for f in c["fora"]] == ["X"] and c["fora"][0]["motivo"] == "outra região"
    assert c["n"] == 4


def test_n_fora_faixa_e_criterio():
    c = rf.cesta(REFS, "media")
    assert c["n_fora_faixa"] == 1 and c["criterio"] == "media" and c["fora"] == []


def test_so_nao_comparaveis():
    c = rf.cesta([{"fonte": "X", "valor": 5, "comparavel": False}])
    assert c["valor"] is None and len(c["fora"]) == 1


def test_migracao_banco_antigo(tmp_path):
    p = str(tmp_path / "velho.sqlite")
    old = sqlite3.connect(p)
    old.execute("CREATE TABLE itens (id INTEGER PRIMARY KEY, fonte TEXT, codigo TEXT, descricao TEXT, busca TEXT, "
                "unidade TEXT, valor REAL, data_base TEXT, uf TEXT, desonerado INTEGER, tipo TEXT, arquivo TEXT, importado_em TEXT)")
    old.commit(); old.close()
    for _ in range(2):
        con = rf.conectar(p)
        cols = {r["name"] for r in con.execute("PRAGMA table_info(itens)")}
        assert {"comparavel", "motivo"} <= cols
        con.close()
