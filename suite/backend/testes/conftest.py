import os

os.environ["SUITE_BANCO_URL"] = os.environ.get(
    "SUITE_BANCO_TESTE_URL", "postgresql+psycopg://suite:suite@localhost:5432/suite_teste"
)
os.environ["SUITE_SEGREDO_SESSAO"] = "x" * 40
os.environ["SUITE_COOKIE_SEGURO"] = "false"
os.environ["SUITE_S3_ENDPOINT"] = "https://s3.us-east-1.amazonaws.com"
os.environ["SUITE_S3_ENDPOINT_PUBLICO"] = "https://s3.us-east-1.amazonaws.com"
os.environ["SUITE_S3_BALDE"] = "teste"
os.environ["SUITE_S3_CHAVE"] = "teste"
os.environ["SUITE_S3_SEGREDO"] = "teste"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import criar_app  # noqa: E402


@pytest.fixture
def cliente_sem_banco():
    return TestClient(criar_app(), raise_server_exceptions=False)
