import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select

from app.nucleo.arquivos import guardar_arquivo, obter_arquivo, url_de_download
from app.nucleo.config import obter_configuracao
from app.nucleo.erros import ErroDominio, NaoEncontrado
from app.nucleo.modelos import Arquivo
from app.nucleo.perfis import Perfil
from testes.fabricas import entrar, nova_empresa, novo_usuario

JPEG = b"\xff\xd8abc"


def _logado(cliente_http, sessao, perfil=Perfil.CAMPO, empresa=None):
    empresa = empresa or nova_empresa(sessao)
    usuario = novo_usuario(sessao, empresa, {perfil})
    sessao.commit()
    entrar(cliente_http, usuario.email)
    return empresa, usuario


def _enviar(cliente_http, nome="foto.jpg", conteudo=JPEG, tipo="image/jpeg"):
    return cliente_http.post("/api/nucleo/arquivos", files={"arquivo": (nome, conteudo, tipo)})


def test_upload_e_url_assinada(cliente_http, sessao, armazenamento):
    cfg = obter_configuracao()
    emp, usuario = _logado(cliente_http, sessao)
    r = _enviar(cliente_http)
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["nome"] == "foto.jpg" and corpo["tamanho_bytes"] == 5
    assert corpo["tipo_conteudo"] == "image/jpeg"
    assert set(corpo) == {"id", "nome", "tipo_conteudo", "tamanho_bytes", "criado_em"}
    u = cliente_http.get(f"/api/nucleo/arquivos/{corpo['id']}/url").json()
    assert u["url"].startswith(cfg.s3_endpoint_publico) and "X-Amz-Signature" in u["url"]
    assert u["expira_em"]
    assert armazenamento.ler(f"{emp.id}/{corpo['id']}") == JPEG
    linha = sessao.scalar(select(Arquivo).where(Arquivo.id == uuid.UUID(corpo["id"])))
    assert linha.empresa_id == emp.id and linha.criado_por == usuario.id
    assert linha.chave == f"{emp.id}/{corpo['id']}"


def test_url_forca_download_com_o_nome(cliente_http, sessao, armazenamento):
    _logado(cliente_http, sessao)
    arquivo_id = _enviar(cliente_http, nome="relatório final.pdf").json()["id"]
    url = cliente_http.get(f"/api/nucleo/arquivos/{arquivo_id}/url").json()["url"]
    disposicao = parse_qs(urlparse(url).query)["response-content-disposition"][0]
    assert disposicao.startswith("attachment;")
    assert "filename*=UTF-8''relat%C3%B3rio%20final.pdf" in disposicao


@pytest.mark.parametrize(
    ("enviado", "esperado"),
    [
        ("../../x.txt", "x.txt"),
        ("..\\..\\y.txt", "y.txt"),
        ("/etc/passwd", "passwd"),
        ("pasta/../", "arquivo"),
        ("..", "arquivo"),
    ],
)
def test_nome_com_caminho_vira_nome_base(cliente_http, sessao, armazenamento, enviado, esperado):
    emp, _ = _logado(cliente_http, sessao)
    r = _enviar(cliente_http, nome=enviado)
    assert r.status_code == 201, r.text
    assert r.json()["nome"] == esperado
    chave = sessao.scalar(select(Arquivo.chave).where(Arquivo.id == uuid.UUID(r.json()["id"])))
    assert ".." not in chave and chave == f"{emp.id}/{r.json()['id']}"


def test_nome_sem_caracteres_de_controle():
    from app.nucleo.arquivos import _nome_base

    assert _nome_base("a\r\nb\x00.txt") == "ab.txt"
    assert len(_nome_base("x" * 1000)) == 255


def test_tipo_de_conteudo_estranho_vira_generico(cliente_http, sessao, armazenamento):
    _logado(cliente_http, sessao)
    r = _enviar(cliente_http, tipo="text/html; <script>")
    assert r.status_code == 201 and r.json()["tipo_conteudo"] == "application/octet-stream"


def test_arquivo_grande_demais(cliente_http, sessao, armazenamento, monkeypatch):
    monkeypatch.setattr(obter_configuracao(), "arquivo_max_bytes", 4)
    emp, _ = _logado(cliente_http, sessao)
    r = _enviar(cliente_http)
    assert r.status_code == 413 and r.json()["codigo"] == "arquivo_grande_demais"
    assert r.json()["mensagem"] == "Arquivo maior que o limite permitido."
    assert sessao.scalar(select(Arquivo).where(Arquivo.empresa_id == emp.id)) is None
    assert _enviar(cliente_http, conteudo=b"abcd").status_code == 201  # no limite passa


def test_envio_sem_o_campo_arquivo_da_422(cliente_http, sessao, armazenamento):
    _logado(cliente_http, sessao)
    r = cliente_http.post("/api/nucleo/arquivos", data={"outro": "x"})
    assert r.status_code == 422 and r.json()["codigo"] == "entrada_invalida"


def test_arquivo_de_outra_empresa_da_404(cliente_http, sessao, armazenamento):
    outra = nova_empresa(sessao, "B")
    dono = novo_usuario(sessao, outra, {Perfil.CAMPO})
    arquivo = guardar_arquivo(sessao, armazenamento, outra.id, dono.id, "s.txt", "text/plain", b"s")
    sessao.commit()
    _logado(cliente_http, sessao)
    r = cliente_http.get(f"/api/nucleo/arquivos/{arquivo.id}/url")
    assert r.status_code == 404 and r.json()["codigo"] == "nao_encontrado"
    assert cliente_http.get(f"/api/nucleo/arquivos/{uuid.uuid4()}/url").status_code == 404


def test_servico_isola_por_empresa(sessao, armazenamento):
    a, b = nova_empresa(sessao, "A"), nova_empresa(sessao, "B")
    arquivo = guardar_arquivo(sessao, armazenamento, a.id, None, "a.txt", "text/plain", b"a")
    assert arquivo.criado_por is None
    assert obter_arquivo(sessao, a.id, arquivo.id).nome == "a.txt"
    assert url_de_download(sessao, armazenamento, a.id, arquivo.id).url
    with pytest.raises(NaoEncontrado, match="Arquivo não encontrado."):
        obter_arquivo(sessao, b.id, arquivo.id)
    with pytest.raises(NaoEncontrado):
        url_de_download(sessao, armazenamento, b.id, arquivo.id)


def test_servico_recusa_arquivo_grande(sessao, armazenamento, monkeypatch):
    monkeypatch.setattr(obter_configuracao(), "arquivo_max_bytes", 4)
    emp = nova_empresa(sessao)
    with pytest.raises(ErroDominio) as erro:
        guardar_arquivo(sessao, armazenamento, emp.id, None, "g.bin", "x/y", b"12345")
    assert erro.value.codigo == "arquivo_grande_demais" and erro.value.status == 413


def test_sem_login_da_401(cliente_http, armazenamento):
    assert _enviar(cliente_http).status_code == 401
    assert cliente_http.get(f"/api/nucleo/arquivos/{uuid.uuid4()}/url").status_code == 401
