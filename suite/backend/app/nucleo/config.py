"""Configuração da aplicação, lida de variáveis SUITE_* e de suite/.env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SUITE_", env_file="../.env", extra="ignore")

    banco_url: str
    segredo_sessao: str = Field(min_length=32)
    sessao_horas: int = 12
    cookie_seguro: bool = True
    s3_endpoint: str
    s3_endpoint_publico: str
    s3_regiao: str = "us-east-1"
    s3_balde: str
    s3_chave: str
    s3_segredo: str
    url_assinada_segundos: int = 300
    arquivo_max_bytes: int = 26214400
    worker_intervalo_s: float = 2.0


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
