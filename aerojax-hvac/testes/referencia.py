"""Apoio dos testes de caracterização: caminhos e normalização do relatório."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROJETO_EXEMPLO = RAIZ / "exemplos" / "projetos" / "escritorio_rapido.json"
PASTA_REFERENCIAS = RAIZ / "testes" / "referencias"


def normalizar_relatorio(html: str) -> str:
    """Troca só o que muda a cada execução: a data do dia e os bytes da imagem."""
    html = re.sub(r"<b>Data:</b> \d{2}/\d{2}/\d{4}", "<b>Data:</b> DATA", html)
    return re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "data:image/png;base64,IMAGEM", html)
