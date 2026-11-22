"""Erros de entrada com código estável (para a interface) e mensagem em português."""


class ErroEntrada(ValueError):
    def __init__(self, codigo: str, mensagem: str, detalhes: dict | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes or {}
