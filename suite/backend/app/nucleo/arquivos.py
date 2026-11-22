"""Arquivos no S3: conteúdo no balde, metadados na tabela `arquivo`, sempre por empresa."""

import re
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from urllib.parse import quote
from uuid import UUID, uuid4

import boto3
from botocore.client import Config as ConfigBoto
from sqlalchemy.orm import Session

from app.nucleo.config import Configuracao, obter_configuracao
from app.nucleo.erros import ErroDominio
from app.nucleo.esquemas import ArquivoSaida, UrlAssinadaSaida
from app.nucleo.modelos import Arquivo
from app.nucleo.repositorio import RepositorioBase

TIPO_GENERICO = "application/octet-stream"
NOME_PADRAO = "arquivo"
TAMANHO_MAXIMO_NOME = 255
_TIPO_VALIDO = re.compile(r"^[A-Za-z0-9][\w.+-]*/[A-Za-z0-9][\w.+-]*$")


class Armazenamento:
    """Cliente do S3. Dois clientes: o interno fala com o S3; o público só assina URLs."""

    def __init__(self, cfg: Configuracao):
        self.balde = cfg.s3_balde
        self.url_assinada_segundos = cfg.url_assinada_segundos
        comum = {
            "region_name": cfg.s3_regiao,
            "aws_access_key_id": cfg.s3_chave,
            "aws_secret_access_key": cfg.s3_segredo,
            "config": ConfigBoto(signature_version="s3v4", s3={"addressing_style": "path"}),
        }
        self.interno = boto3.client("s3", endpoint_url=cfg.s3_endpoint, **comum)
        self.publico = boto3.client("s3", endpoint_url=cfg.s3_endpoint_publico, **comum)

    def guardar(self, chave: str, conteudo: bytes, tipo_conteudo: str) -> None:
        self.interno.put_object(
            Bucket=self.balde, Key=chave, Body=conteudo, ContentType=tipo_conteudo
        )

    def ler(self, chave: str) -> bytes:
        return self.interno.get_object(Bucket=self.balde, Key=chave)["Body"].read()

    def url_assinada(self, chave: str, nome_download: str) -> str:
        return self.publico.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.balde,
                "Key": chave,
                "ResponseContentDisposition": _disposicao(nome_download),
            },
            ExpiresIn=self.url_assinada_segundos,
        )


@lru_cache
def obter_armazenamento() -> Armazenamento:
    return Armazenamento(obter_configuracao())


class ArquivoRepositorio(RepositorioBase[Arquivo]):
    modelo = Arquivo


def _disposicao(nome: str) -> str:
    """Cabeçalho Content-Disposition que força o download (nunca abre no navegador)."""
    ascii_seguro = re.sub(r"[^A-Za-z0-9._-]", "_", nome)
    return f"attachment; filename=\"{ascii_seguro}\"; filename*=UTF-8''{quote(nome, safe='')}"


def _nome_base(nome: str) -> str:
    """Só o último trecho do nome, sem separadores de pasta nem caracteres de controle."""
    base = re.split(r"[/\\]", nome)[-1]
    base = "".join(c for c in base if c.isprintable()).strip()
    if base in ("", ".", ".."):
        return NOME_PADRAO
    return base[:TAMANHO_MAXIMO_NOME]


def _tipo_seguro(tipo: str) -> str:
    return tipo if len(tipo) <= 100 and _TIPO_VALIDO.match(tipo) else TIPO_GENERICO


def _saida(arquivo: Arquivo) -> ArquivoSaida:
    return ArquivoSaida(
        id=arquivo.id,
        nome=arquivo.nome,
        tipo_conteudo=arquivo.tipo_conteudo,
        tamanho_bytes=arquivo.tamanho_bytes,
        criado_em=arquivo.criado_em,
    )


def guardar_arquivo(
    sessao: Session,
    armazenamento: Armazenamento,
    empresa_id: UUID,
    usuario_id: UUID | None,
    nome: str,
    tipo_conteudo: str,
    conteudo: bytes,
) -> Arquivo:
    if len(conteudo) > obter_configuracao().arquivo_max_bytes:
        raise ErroDominio("arquivo_grande_demais", "Arquivo maior que o limite permitido.", 413)
    arquivo_id = uuid4()
    arquivo = ArquivoRepositorio(sessao, empresa_id).adicionar(
        Arquivo(
            id=arquivo_id,
            nome=_nome_base(nome),
            tipo_conteudo=_tipo_seguro(tipo_conteudo),
            tamanho_bytes=len(conteudo),
            chave=f"{empresa_id}/{arquivo_id}",  # a chave nunca vem do nome enviado
            criado_por=usuario_id,
        )
    )
    # Se o S3 falhar, a exceção desfaz a linha do banco junto com a requisição.
    armazenamento.guardar(arquivo.chave, conteudo, arquivo.tipo_conteudo)
    sessao.refresh(arquivo)
    return arquivo


def _obter(sessao: Session, empresa_id: UUID, arquivo_id: UUID) -> Arquivo:
    # Arquivo de outra empresa não é achado pelo repositório: 404, nunca 403.
    return ArquivoRepositorio(sessao, empresa_id).obter_ou_erro(
        arquivo_id, "Arquivo não encontrado."
    )


def obter_arquivo(sessao: Session, empresa_id: UUID, arquivo_id: UUID) -> ArquivoSaida:
    return _saida(_obter(sessao, empresa_id, arquivo_id))


def url_de_download(
    sessao: Session, armazenamento: Armazenamento, empresa_id: UUID, arquivo_id: UUID
) -> UrlAssinadaSaida:
    arquivo = _obter(sessao, empresa_id, arquivo_id)
    url = armazenamento.url_assinada(arquivo.chave, arquivo.nome)
    expira_em = datetime.now(UTC) + timedelta(seconds=armazenamento.url_assinada_segundos)
    return UrlAssinadaSaida(url=url, expira_em=expira_em)
