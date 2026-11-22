from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

from app.main import criar_app
from app.nucleo.erros import Conflito


def test_saude(cliente_sem_banco):
    r = cliente_sem_banco.get("/api/saude")
    assert r.status_code == 200 and r.json() == {"situacao": "ok"}


def test_rota_inexistente_no_formato_unico(cliente_sem_banco):
    r = cliente_sem_banco.get("/api/nao-existe")
    assert r.status_code == 404
    assert r.json() == {
        "codigo": "nao_encontrado",
        "mensagem": "Recurso não encontrado.",
        "detalhes": {},
    }


def test_erro_de_dominio():
    app = criar_app()

    @app.get("/teste")
    def _rota():
        raise Conflito("Já existe.", {"campo": "cnpj_cpf"})

    r = TestClient(app, raise_server_exceptions=False).get("/teste")
    assert r.status_code == 409
    assert r.json() == {
        "codigo": "conflito",
        "mensagem": "Já existe.",
        "detalhes": {"campo": "cnpj_cpf"},
    }


def test_erro_inesperado_nao_vaza_rastreamento():
    app = criar_app()

    @app.get("/teste")
    def _rota():
        raise RuntimeError("segredo interno")

    r = TestClient(app, raise_server_exceptions=False).get("/teste")
    assert r.status_code == 500
    assert r.json() == {
        "codigo": "erro_interno",
        "mensagem": "Erro interno. Tente novamente.",
        "detalhes": {},
    }
    assert "segredo" not in r.text and "Traceback" not in r.text


def test_validacao_em_portugues():
    app = criar_app()

    class Corpo(BaseModel):
        model_config = ConfigDict(extra="forbid")
        nome: str
        quantidade: int = Field(gt=0)

    @app.post("/teste")
    def _rota(corpo: Corpo):
        return {}

    r = TestClient(app, raise_server_exceptions=False).post(
        "/teste", json={"quantidade": 0, "intruso": 1}
    )
    assert r.status_code == 422
    assert r.json() == {
        "codigo": "entrada_invalida",
        "mensagem": "Dados inválidos.",
        "detalhes": {
            "campos": [
                {"campo": "nome", "mensagem": "Campo obrigatório."},
                {"campo": "quantidade", "mensagem": "Deve ser maior que 0."},
                {"campo": "intruso", "mensagem": "Campo não permitido."},
            ]
        },
    }
