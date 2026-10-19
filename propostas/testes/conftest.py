import glob
import os
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

from orcamento import catalogo as ct  # noqa: E402
from orcamento import parametros as pm  # noqa: E402
from orcamento import proposta as pp  # noqa: E402

EXEMPLOS = sorted(glob.glob(os.path.join(RAIZ, "exemplos", "*.json")))


@pytest.fixture(scope="session")
def cat():
    return ct.carregar()


@pytest.fixture(scope="session")
def params():
    return pm.carregar()


def abrir_exemplo(caminho, cat, params):
    with open(caminho, encoding="utf-8") as f:
        return pp.completar(pp.carregar_json(f.read()), cat, params)


@pytest.fixture(scope="session", autouse=True)
def base_referencias_temporaria(tmp_path_factory):
    """O app abre o banco de referências a cada execução: nos testes ele fica numa pasta temporária."""
    anterior = os.environ.get("KAPTEK_REFERENCIAS")
    os.environ["KAPTEK_REFERENCIAS"] = str(tmp_path_factory.mktemp("ref") / "referencias.sqlite")
    yield
    if anterior is None:
        os.environ.pop("KAPTEK_REFERENCIAS", None)
    else:
        os.environ["KAPTEK_REFERENCIAS"] = anterior
