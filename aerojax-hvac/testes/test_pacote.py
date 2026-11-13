import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_versao_do_pacote():
    import clima2d
    assert clima2d.__version__ == "0.1.0"


def test_nenhum_import_do_pacote_hvac():
    padrao = re.compile(r"^\s*(from|import)\s+hvac\b", re.M)
    achados = [str(p.relative_to(RAIZ)) for p in RAIZ.rglob("*.py")
               if ".venv" not in p.parts and padrao.search(p.read_text(encoding="utf-8"))]
    assert achados == []


def test_projeto_py_foi_dividido():
    assert not (RAIZ / "clima2d" / "projeto.py").exists()
