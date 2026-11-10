"""Módulos de escopo: projeto, acompanhamento, execução, inspeção com laudo e avaliação de desempenho."""
import copy

import pytest

from orcamento import catalogo as ct
from orcamento import escopos
from orcamento import motor
from orcamento import proposta as pp

IDS = ["projeto", "acompanhamento", "execucao", "inspecao_laudo", "desempenho"]


def nova(params):
    return pp.completar(pp.padrao(params), ct.carregar(), params)


def preco_opcao(cat, p):
    return motor.precificar(cat, p)["opcoes"][0]


def so(params, cat, mid):
    """Proposta com um único módulo."""
    p = nova(params)
    escopos.incluir(p["opcoes"][0], mid, cat, p["parametros"])
    return p


def test_modulos_ordem_e_ids():
    assert list(escopos.MODULOS) == IDS
    for m in escopos.MODULOS.values():
        assert m["nome"] and m["descricao"]
        assert m["cobranca"] in pp.COBRANCAS


def test_servicos_existem_no_catalogo(cat):
    for m in escopos.MODULOS.values():
        for sid in m["servicos"]:
            assert ct.servico(cat, sid)["id"] == sid


def test_descricao_da_execucao_avisa_sobre_fornecimentos():
    d = escopos.modulo("execucao")["descricao"].lower()
    assert "fornecimentos" in d and "aba 3" in d and "vem depois" in d


def test_modulo_desconhecido(cat, params):
    with pytest.raises(KeyError, match="projeto"):
        escopos.modulo("xyz")
    p = nova(params)
    with pytest.raises(KeyError):
        escopos.incluir(p["opcoes"][0], "xyz", cat, p["parametros"])


def test_primeiro_modulo_reaproveita_f1(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    f = escopos.incluir(o, "projeto", cat, p["parametros"])
    assert len(o["fases"]) == 1 and o["fases"][0] is f
    assert (f["id"], f["nome"], f["cobranca"], f["modulo"]) == ("F1", "Projeto", "fechado", "projeto")
    assert [i["servico"] for i in o["itens"]] == ["hvac.carga_termica", "hvac.projeto"]
    assert all(i["fase"] == "F1" for i in o["itens"])


def test_segundo_modulo_acrescenta_f2(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    escopos.incluir(o, "projeto", cat, p["parametros"])
    f2 = escopos.incluir(o, "acompanhamento", cat, p["parametros"])
    assert [f["id"] for f in o["fases"]] == ["F1", "F2"]
    assert f2["cobranca"] == "pacote" and f2["modulo"] == "acompanhamento"
    assert [i["fase"] for i in o["itens"]] == ["F1", "F1", "F2"]


def test_f1_com_item_nao_e_reaproveitada(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    o["itens"].append(pp.novo_item(ct.servico(cat, "hvac.projeto"), fase="F1"))
    escopos.incluir(o, "projeto", cat, p["parametros"])
    assert [f["id"] for f in o["fases"]] == ["F1", "F2"]
    assert o["fases"][0]["modulo"] == ""


def test_f1_com_fornecimento_nao_e_reaproveitada(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    o["fornecimentos"].append(pp.novo_fornecimento("Cabo", fase="F1"))
    escopos.incluir(o, "execucao", cat, p["parametros"])
    assert len(o["fases"]) == 2


def test_f1_ja_de_modulo_nao_e_reaproveitada(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    escopos.incluir(o, "execucao", cat, p["parametros"])     # sem itens, mas já tem módulo
    escopos.incluir(o, "desempenho", cat, p["parametros"])
    assert len(o["fases"]) == 2


def test_modulo_repetido_ganha_contador(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    for _ in range(3):
        escopos.incluir(o, "projeto", cat, p["parametros"])
    assert [f["nome"] for f in o["fases"]] == ["Projeto", "Projeto 2", "Projeto 3"]
    assert [f["id"] for f in o["fases"]] == ["F1", "F2", "F3"]


@pytest.mark.parametrize("mid", [m for m in IDS if m != "execucao"])
def test_cada_modulo_sozinho_tem_preco(cat, params, mid):
    assert preco_opcao(cat, so(params, cat, mid))["preco"] > 0


def test_pacote_do_acompanhamento_usa_horas_do_servico(cat, params):
    # horas_mes = 0 faz o motor derivar as horas do serviço: o módulo não precisa de padrões próprios.
    f = so(params, cat, "acompanhamento")["opcoes"][0]["fases"][0]
    assert f["pacote"]["horas_mes"] == 0
    r = preco_opcao(cat, so(params, cat, "acompanhamento"))
    assert r["fases"][0]["pacote"]["horas"] > 0


def test_execucao_vazia_precifica_zero_sem_erro(cat, params):
    r = preco_opcao(cat, so(params, cat, "execucao"))
    assert r["preco"] == 0
    assert r["fases"][0]["cobranca"] == "fechado"


def test_execucao_com_fornecimento_tem_preco(cat, params):
    p = so(params, cat, "execucao")
    p["opcoes"][0]["fornecimentos"].append(pp.novo_fornecimento("Split 12000", "equipamento", qtd=2, custo_unit=3000, fase="F1"))
    assert preco_opcao(cat, p)["preco"] > 6000


def test_soma_dos_modulos(cat, params):
    # Cada fase é precificada sozinha (com a sua ART): o total dos cinco módulos é a soma de cada um isolado.
    juntos = nova(params)
    o = juntos["opcoes"][0]
    for mid in IDS:
        escopos.incluir(o, mid, cat, juntos["parametros"])
    assert len(o["fases"]) == 5
    soma = sum(preco_opcao(cat, so(params, cat, mid))["preco"] for mid in IDS)
    assert preco_opcao(cat, juntos)["preco"] == pytest.approx(soma, abs=0.01)


def test_desligar_modulo_tira_so_o_seu_preco(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    for mid in ("projeto", "acompanhamento", "inspecao_laudo"):
        escopos.incluir(o, mid, cat, p["parametros"])
    total = preco_opcao(cat, p)["preco"]
    sozinho = preco_opcao(cat, so(params, cat, "acompanhamento"))["preco"]
    o["fases"][1]["ativa"] = False
    assert preco_opcao(cat, p)["preco"] == pytest.approx(total - sozinho, abs=0.01)


def test_estimativa_levanta(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    o["modalidade"] = "estimativa"
    antes = copy.deepcopy(o)
    with pytest.raises(ValueError, match="estimativa interna"):
        escopos.incluir(o, "projeto", cat, p["parametros"])
    assert o == antes


def test_modulos_da_opcao(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    assert escopos.modulos_da_opcao(o) == [""]
    escopos.incluir(o, "projeto", cat, p["parametros"])
    escopos.incluir(o, "desempenho", cat, p["parametros"])
    o["fases"].append(pp.nova_fase("F9", p["parametros"]))
    assert escopos.modulos_da_opcao(o) == ["projeto", "desempenho", ""]


def test_fase_inicial_renomeada_pelo_usuario_mantem_o_nome(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    o["fases"][0]["nome"] = "Projeto"
    f = escopos.incluir(o, "projeto", cat, p["parametros"])
    assert f is o["fases"][0] and f["nome"] == "Projeto"


def test_fase_inicial_desligada_reaproveitada_fica_ativa(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    o["fases"][0]["ativa"] = False
    f = escopos.incluir(o, "projeto", cat, p["parametros"])
    assert f["ativa"] is True


def test_fase_inicial_de_arquivo_antigo_sem_modulo_e_reaproveitada(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    del o["fases"][0]["modulo"]
    del o["fases"][0]["ativa"]
    f = escopos.incluir(o, "execucao", cat, p["parametros"])
    assert len(o["fases"]) == 1 and f["modulo"] == "execucao" and f["ativa"] is True


def test_excluir_fase_e_incluir_de_novo_nao_duplica_nome(cat, params):
    p = nova(params)
    o = p["opcoes"][0]
    for _ in range(3):
        escopos.incluir(o, "projeto", cat, p["parametros"])
    o["fases"] = [f for f in o["fases"] if f["nome"] != "Projeto 2"]
    o["itens"] = [i for i in o["itens"] if i["fase"] != "F2"]
    nova_f = escopos.incluir(o, "projeto", cat, p["parametros"])
    nomes = [f["nome"] for f in o["fases"]]
    assert nova_f["nome"] == "Projeto 2" and len(nomes) == len(set(nomes))
    assert len({f["id"] for f in o["fases"]}) == len(o["fases"])
