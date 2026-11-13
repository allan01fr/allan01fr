import os

os.environ["SUITE_BANCO_URL"] = os.environ.get(
    "SUITE_BANCO_TESTE_URL", "postgresql+psycopg://suite:suite@localhost:5432/suite_teste"
)
os.environ["SUITE_AMBIENTE"] = "dev"
os.environ["SUITE_SEGREDO_SESSAO"] = "x" * 40
os.environ["SUITE_COOKIE_SEGURO"] = "false"
os.environ["SUITE_S3_ENDPOINT"] = "https://s3.us-east-1.amazonaws.com"
os.environ["SUITE_S3_ENDPOINT_PUBLICO"] = "https://s3.us-east-1.amazonaws.com"
os.environ["SUITE_S3_BALDE"] = "teste"
os.environ["SUITE_S3_CHAVE"] = "teste"
os.environ["SUITE_S3_SEGREDO"] = "teste"

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from moto import mock_aws  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.main import criar_app  # noqa: E402
from app.nucleo.arquivos import obter_armazenamento  # noqa: E402
from app.nucleo.banco import Base, obter_sessao  # noqa: E402
from app.nucleo.config import obter_configuracao  # noqa: E402
from app.registro import importar_modelos  # noqa: E402

RAIZ_BACKEND = Path(__file__).resolve().parent.parent


@pytest.fixture
def cliente_sem_banco():
    return TestClient(criar_app(), raise_server_exceptions=False)


@pytest.fixture(scope="session")
def motor():
    """Motor do banco de teste, recriado do zero pelas migrações."""
    engine = create_engine(os.environ["SUITE_BANCO_URL"])
    if not (engine.url.database or "").endswith("_teste"):
        pytest.exit("Recusado: o banco de testes deve ter nome terminado em '_teste'.")
    with engine.begin() as conexao:
        conexao.execute(text("DROP SCHEMA public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(RAIZ_BACKEND / "alembic.ini")), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def sessao(motor):
    """Sessão dentro de uma transação externa, desfeita ao fim do teste."""
    conexao = motor.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, join_transaction_mode="create_savepoint")
    yield sessao
    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture
def armazenamento():
    """S3 simulado (moto): API e worker dos testes usam o mesmo balde."""
    with mock_aws():
        obter_armazenamento.cache_clear()
        instancia = obter_armazenamento()
        instancia.interno.create_bucket(Bucket=obter_configuracao().s3_balde)
        yield instancia
    obter_armazenamento.cache_clear()


@pytest.fixture
def cliente_http(sessao, armazenamento):
    app = criar_app()

    def sessao_de_teste():
        # Mesmo contrato de obter_sessao; o rollback desfaz só o savepoint do teste.
        try:
            yield sessao
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise

    app.dependency_overrides[obter_sessao] = sessao_de_teste
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def banco_real(motor):
    """Sessões com commit real; ao fim, todas as tabelas são esvaziadas."""
    yield sessionmaker(bind=motor, expire_on_commit=False)
    importar_modelos()
    tabelas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with motor.begin() as conexao:
        conexao.execute(text(f"TRUNCATE {tabelas} CASCADE"))
