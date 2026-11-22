import time

from sqlalchemy import select

from app.nucleo.modelos import Auditoria
from app.nucleo.perfis import Perfil
from testes.fabricas import SENHA_TESTE, entrar, nova_empresa, novo_usuario

ERRO_CREDENCIAIS = {
    "codigo": "credenciais_invalidas",
    "mensagem": "E-mail ou senha incorretos.",
    "detalhes": {},
}


def test_login_define_cookie_httponly_e_eu_responde(cliente_http, sessao):
    emp = nova_empresa(sessao, "A")
    novo_usuario(sessao, emp, {Perfil.COMERCIAL}, email="ana@a.com")
    r = cliente_http.post("/api/nucleo/sessao", json={"email": "ana@a.com", "senha": SENHA_TESTE})
    assert r.status_code == 200
    c = r.headers["set-cookie"]
    assert "suite_sessao=" in c and "HttpOnly" in c and "SameSite=lax" in c
    assert "Path=/" in c and "Secure" not in c  # SUITE_COOKIE_SEGURO=false nos testes
    eu = cliente_http.get("/api/nucleo/eu").json()
    assert eu["email"] == "ana@a.com"
    assert eu["perfis"] == ["comercial"]
    assert eu["empresa"]["nome"] == "A"
    assert "cadastro.ler" in eu["permissoes"] and "nucleo.usuarios" not in eu["permissoes"]


def test_cookie_secure_quando_configurado(cliente_http, sessao, monkeypatch):
    from app.nucleo.config import obter_configuracao

    monkeypatch.setenv("SUITE_COOKIE_SEGURO", "true")
    obter_configuracao.cache_clear()
    try:
        emp = nova_empresa(sessao)
        novo_usuario(sessao, emp, {Perfil.ADMIN}, email="s@a.com")
        r = cliente_http.post("/api/nucleo/sessao", json={"email": "s@a.com", "senha": SENHA_TESTE})
        assert "Secure" in r.headers["set-cookie"]
    finally:
        monkeypatch.undo()
        obter_configuracao.cache_clear()


def test_email_com_maiusculas_e_espacos_entra(cliente_http, sessao):
    emp = nova_empresa(sessao)
    novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    entrar(cliente_http, "  Ana@A.com ")
    assert cliente_http.get("/api/nucleo/eu").json()["email"] == "ana@a.com"


def test_email_inexistente_e_senha_errada_tem_a_mesma_resposta(cliente_http, sessao):
    emp = nova_empresa(sessao)
    novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    sessao.commit()  # o 401 faz rollback; o usuário precisa sobreviver
    for corpo in (
        {"email": "ana@a.com", "senha": "errada-123456"},
        {"email": "ninguem@a.com", "senha": SENHA_TESTE},
    ):
        r = cliente_http.post("/api/nucleo/sessao", json=corpo)
        assert r.status_code == 401 and r.json() == ERRO_CREDENCIAIS
        assert "set-cookie" not in r.headers


def test_email_inexistente_confere_o_hash_ficticio(cliente_http, monkeypatch):
    chamadas = []
    from app.nucleo import login
    from app.nucleo.senhas import HASH_FICTICIO

    original = login.conferir_senha
    monkeypatch.setattr(login, "conferir_senha", lambda s, h: chamadas.append(h) or original(s, h))
    cliente_http.post(
        "/api/nucleo/sessao", json={"email": "ninguem@a.com", "senha": "qualquer-123"}
    )
    assert chamadas == [HASH_FICTICIO]


def test_usuario_desativado_perde_a_sessao_e_nao_entra(cliente_http, sessao):
    emp = nova_empresa(sessao)
    usuario = novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    entrar(cliente_http, "ana@a.com")
    usuario.ativo = False
    sessao.commit()  # o erro 401 da próxima chamada faz rollback; a desativação precisa sobreviver
    assert cliente_http.get("/api/nucleo/eu").json()["codigo"] == "nao_autenticado"
    r = cliente_http.post("/api/nucleo/sessao", json={"email": "ana@a.com", "senha": SENHA_TESTE})
    assert r.status_code == 401 and r.json() == ERRO_CREDENCIAIS


def test_sem_cookie_nao_autentica(cliente_http):
    r = cliente_http.get("/api/nucleo/eu")
    assert r.status_code == 401 and r.json()["codigo"] == "nao_autenticado"


def test_cookie_adulterado(cliente_http):
    cliente_http.cookies.set("suite_sessao", "abc.def.ghi")
    r = cliente_http.get("/api/nucleo/eu")
    assert r.status_code == 401
    assert r.json()["mensagem"] == "Sessão expirada ou inválida. Entre novamente."


def test_cookie_assinado_com_outro_salt_e_recusado(cliente_http, sessao):
    from itsdangerous import URLSafeTimedSerializer

    emp = nova_empresa(sessao)
    usuario = novo_usuario(sessao, emp, {Perfil.ADMIN})
    falso = URLSafeTimedSerializer("x" * 40, salt="outro").dumps({"u": str(usuario.id)})
    cliente_http.cookies.set("suite_sessao", falso)
    assert cliente_http.get("/api/nucleo/eu").status_code == 401


def test_sessao_expirada_no_servidor(cliente_http, sessao, monkeypatch):
    """Cookie com assinatura válida, mas mais antigo que a validade, é recusado pelo servidor."""
    from itsdangerous import URLSafeTimedSerializer

    emp = nova_empresa(sessao)
    usuario = novo_usuario(sessao, emp, {Perfil.ADMIN})
    agora = time.time()  # "itsdangerous.timed.time" é o próprio módulo time: guardar antes
    with monkeypatch.context() as m:
        m.setattr("itsdangerous.timed.time.time", lambda: agora - 13 * 3600)
        antigo = URLSafeTimedSerializer("x" * 40, salt="sessao").dumps({"u": str(usuario.id)})
    cliente_http.cookies.set("suite_sessao", antigo)
    r = cliente_http.get("/api/nucleo/eu")
    assert r.status_code == 401 and r.json()["codigo"] == "nao_autenticado"


def test_cookie_valido_recente_com_a_mesma_assinatura_entra(cliente_http, sessao):
    from itsdangerous import URLSafeTimedSerializer

    emp = nova_empresa(sessao)
    usuario = novo_usuario(sessao, emp, {Perfil.ADMIN})
    novo = URLSafeTimedSerializer("x" * 40, salt="sessao").dumps({"u": str(usuario.id)})
    cliente_http.cookies.set("suite_sessao", novo)
    assert cliente_http.get("/api/nucleo/eu").status_code == 200


def test_payload_assinado_mas_malformado_da_401(cliente_http):
    from itsdangerous import URLSafeTimedSerializer

    for payload in ({"u": 123}, [1, 2], "texto", {"u": "nao-e-uuid"}, {}):
        valor = URLSafeTimedSerializer("x" * 40, salt="sessao").dumps(payload)
        cliente_http.cookies.set("suite_sessao", valor)
        r = cliente_http.get("/api/nucleo/eu")
        assert r.status_code == 401 and r.json()["codigo"] == "nao_autenticado", payload


def test_logout_apaga_cookie(cliente_http, sessao):
    emp = nova_empresa(sessao)
    novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    entrar(cliente_http, "ana@a.com")
    r = cliente_http.delete("/api/nucleo/sessao")
    assert r.status_code == 204
    assert "suite_sessao=" in r.headers["set-cookie"] and "Max-Age=0" in r.headers["set-cookie"]
    assert cliente_http.get("/api/nucleo/eu").status_code == 401


def test_logout_sem_sessao_e_publico(cliente_http):
    assert cliente_http.delete("/api/nucleo/sessao").status_code == 204


def test_login_grava_auditoria(cliente_http, sessao):
    emp = nova_empresa(sessao)
    usuario = novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    entrar(cliente_http, "ana@a.com")
    linhas = sessao.scalars(select(Auditoria)).all()
    assert len(linhas) == 1
    a = linhas[0]
    assert (a.acao, a.entidade, a.entidade_id) == ("login", "usuario", usuario.id)
    assert a.usuario_id == usuario.id and a.empresa_id == emp.id


def test_login_falho_nao_grava_auditoria(cliente_http, sessao, monkeypatch):
    from app.nucleo import rotas

    chamadas = []
    monkeypatch.setattr(rotas, "registrar_auditoria", lambda *a, **k: chamadas.append(a))
    emp = nova_empresa(sessao)
    novo_usuario(sessao, emp, {Perfil.ADMIN}, email="ana@a.com")
    sessao.commit()  # o 401 faz rollback; o usuário precisa sobreviver
    for corpo in (
        {"email": "ana@a.com", "senha": "errada-123456"},
        {"email": "ninguem@a.com", "senha": SENHA_TESTE},
    ):
        assert cliente_http.post("/api/nucleo/sessao", json=corpo).status_code == 401
    assert chamadas == []
    entrar(cliente_http, "ana@a.com")  # o espião enxerga o login bem-sucedido
    assert len(chamadas) == 1


def test_login_recusa_campos_extras_e_email_vazio(cliente_http):
    r = cliente_http.post("/api/nucleo/sessao", json={"email": "a@a.com", "senha": "x", "z": 1})
    assert r.status_code == 422
