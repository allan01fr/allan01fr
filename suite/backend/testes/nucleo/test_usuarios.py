from sqlalchemy import select

from app.nucleo.modelos import Auditoria, Usuario
from app.nucleo.perfis import Perfil
from testes.fabricas import SENHA_TESTE, entrar, nova_empresa, novo_usuario

NOVO = {
    "nome": "Bia",
    "email": "Bia@A.com",
    "senha": "senha-nova-12345",
    "perfis": ["comercial", "campo"],
}


def _admin_logado(cliente_http, sessao, empresa=None):
    empresa = empresa or nova_empresa(sessao)
    admin = novo_usuario(sessao, empresa, {Perfil.ADMIN})
    sessao.commit()
    entrar(cliente_http, admin.email)
    return empresa, admin


def test_admin_cria_usuario_na_propria_empresa(cliente_http, sessao):
    emp, admin = _admin_logado(cliente_http, sessao)
    r = cliente_http.post("/api/nucleo/usuarios", json=NOVO)
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["email"] == "bia@a.com" and corpo["ativo"] is True
    assert corpo["perfis"] == ["campo", "comercial"]
    assert "senha" not in corpo and "senha_hash" not in corpo
    criado = sessao.scalar(select(Usuario).where(Usuario.email == "bia@a.com"))
    assert criado.empresa_id == emp.id
    acao = sessao.scalar(select(Auditoria).where(Auditoria.acao == "usuario.criar"))
    assert acao.usuario_id == admin.id and acao.entidade_id == criado.id
    assert "senha" not in str(acao.dados)
    # o novo usuário consegue entrar
    cliente_http.delete("/api/nucleo/sessao")
    entrar(cliente_http, "bia@a.com", "senha-nova-12345")


def test_corpo_nao_escolhe_a_empresa(cliente_http, sessao):
    _admin_logado(cliente_http, sessao)
    outra = nova_empresa(sessao, "B")
    r = cliente_http.post("/api/nucleo/usuarios", json={**NOVO, "empresa_id": str(outra.id)})
    assert r.status_code == 422


def test_email_repetido_da_409(cliente_http, sessao):
    _admin_logado(cliente_http, sessao)
    assert cliente_http.post("/api/nucleo/usuarios", json=NOVO).status_code == 201
    r = cliente_http.post("/api/nucleo/usuarios", json=NOVO)
    assert r.status_code == 409 and r.json()["codigo"] == "conflito"


def test_entradas_invalidas(cliente_http, sessao):
    _admin_logado(cliente_http, sessao)
    for mudanca in (
        {"senha": "curta"},
        {"perfis": []},
        {"perfis": ["chefe"]},
        {"email": "nao-e-email"},
        {"nome": "  "},
    ):
        r = cliente_http.post("/api/nucleo/usuarios", json={**NOVO, **mudanca})
        assert r.status_code == 422, mudanca


def test_lista_so_a_propria_empresa(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    novo_usuario(sessao, emp, {Perfil.CAMPO}, email="c@a.com")
    outra = nova_empresa(sessao, "B")
    novo_usuario(sessao, outra, {Perfil.ADMIN}, email="estranho@b.com")
    sessao.commit()
    r = cliente_http.get("/api/nucleo/usuarios")
    assert r.status_code == 200
    emails = {u["email"] for u in r.json()["itens"]}
    assert "c@a.com" in emails and "estranho@b.com" not in emails
    assert r.json()["total"] == 2
    assert cliente_http.get("/api/nucleo/usuarios?limite=1").json()["itens"].__len__() == 1
    assert cliente_http.get("/api/nucleo/usuarios?limite=201").status_code == 422


def test_desativar_outro_usuario_e_ele_perde_a_sessao(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    alvo = novo_usuario(sessao, emp, {Perfil.CAMPO})
    sessao.commit()
    r = cliente_http.patch(f"/api/nucleo/usuarios/{alvo.id}", json={"ativo": False})
    assert r.status_code == 200 and r.json()["ativo"] is False
    sessao.refresh(alvo)
    assert alvo.ativo is False
    login = cliente_http.post(
        "/api/nucleo/sessao", json={"email": alvo.email, "senha": SENHA_TESTE}
    )
    assert login.status_code == 401


def test_alterar_perfis_e_nome(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    alvo = novo_usuario(sessao, emp, {Perfil.CAMPO, Perfil.COMERCIAL})
    sessao.commit()
    r = cliente_http.patch(
        f"/api/nucleo/usuarios/{alvo.id}",
        json={"nome": "Novo Nome", "perfis": ["campo", "financeiro"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["perfis"] == ["campo", "financeiro"] and r.json()["nome"] == "Novo Nome"
    sessao.refresh(alvo)
    assert {p.perfil for p in alvo.perfis} == {"campo", "financeiro"}
    assert all(p.empresa_id == emp.id for p in alvo.perfis)


def test_patch_vazio_ou_com_perfis_vazios_e_recusado(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    alvo = novo_usuario(sessao, emp, {Perfil.CAMPO})
    sessao.commit()
    assert (
        cliente_http.patch(f"/api/nucleo/usuarios/{alvo.id}", json={"perfis": []}).status_code
        == 422
    )
    assert (
        cliente_http.patch(f"/api/nucleo/usuarios/{alvo.id}", json={"ativo": None}).status_code
        == 422
    )


def test_nao_desativa_a_si_mesmo(cliente_http, sessao):
    _, admin = _admin_logado(cliente_http, sessao)
    r = cliente_http.patch(f"/api/nucleo/usuarios/{admin.id}", json={"ativo": False})
    assert r.status_code == 422 and r.json()["codigo"] == "regra_negocio"
    assert r.json()["mensagem"] == "Você não pode remover o próprio acesso de administrador."


def test_nao_tira_o_proprio_admin_mas_pode_acrescentar_perfil(cliente_http, sessao):
    _, admin = _admin_logado(cliente_http, sessao)
    r = cliente_http.patch(f"/api/nucleo/usuarios/{admin.id}", json={"perfis": ["campo"]})
    assert r.status_code == 422 and r.json()["codigo"] == "regra_negocio"
    r = cliente_http.patch(f"/api/nucleo/usuarios/{admin.id}", json={"perfis": ["admin", "campo"]})
    assert r.status_code == 200 and r.json()["perfis"] == ["admin", "campo"]


def test_admin_pode_rebaixar_outro_admin(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    outro = novo_usuario(sessao, emp, {Perfil.ADMIN})
    sessao.commit()
    r = cliente_http.patch(f"/api/nucleo/usuarios/{outro.id}", json={"perfis": ["campo"]})
    assert r.status_code == 200


def test_usuario_de_outra_empresa_da_404_e_nada_muda(cliente_http, sessao):
    _admin_logado(cliente_http, sessao)
    outra = nova_empresa(sessao, "B")
    alvo = novo_usuario(sessao, outra, {Perfil.ADMIN})
    sessao.commit()
    r = cliente_http.patch(
        f"/api/nucleo/usuarios/{alvo.id}", json={"ativo": False, "perfis": ["campo"]}
    )
    assert r.status_code == 404 and r.json()["codigo"] == "nao_encontrado"
    sessao.refresh(alvo)
    assert alvo.ativo is True and {p.perfil for p in alvo.perfis} == {"admin"}


def test_nao_admin_nao_administra_usuarios(cliente_http, sessao):
    emp = nova_empresa(sessao)
    comum = novo_usuario(sessao, emp, {Perfil.COMERCIAL})
    sessao.commit()
    entrar(cliente_http, comum.email)
    assert cliente_http.get("/api/nucleo/usuarios").status_code == 403
    assert cliente_http.post("/api/nucleo/usuarios", json=NOVO).status_code == 403
    r = cliente_http.patch(f"/api/nucleo/usuarios/{comum.id}", json={"perfis": ["admin"]})
    assert r.status_code == 403


def test_sem_login_da_401(cliente_http):
    assert cliente_http.get("/api/nucleo/usuarios").status_code == 401


def test_auditoria_de_alteracao_inclui_o_nome(cliente_http, sessao):
    emp, _ = _admin_logado(cliente_http, sessao)
    alvo = novo_usuario(sessao, emp, {Perfil.CAMPO})
    sessao.commit()
    antigo = alvo.nome
    cliente_http.patch(f"/api/nucleo/usuarios/{alvo.id}", json={"nome": "Nome Novo"})
    acao = sessao.scalar(select(Auditoria).where(Auditoria.acao == "usuario.alterar"))
    assert acao.dados["antes"]["nome"] == antigo
    assert acao.dados["depois"]["nome"] == "Nome Novo"


def test_empresa_nao_pode_ficar_sem_admin_ativo(sessao):
    import pytest

    from app.nucleo.erros import RegraNegocio
    from app.nucleo.usuarios import garantir_admin_ativo

    emp = nova_empresa(sessao)
    admin = novo_usuario(sessao, emp, {Perfil.ADMIN})
    garantir_admin_ativo(sessao, emp.id)  # há um admin ativo: passa
    admin.ativo = False
    sessao.flush()
    with pytest.raises(RegraNegocio, match="pelo menos um administrador ativo"):
        garantir_admin_ativo(sessao, emp.id)
    admin.ativo = True
    admin.perfis = [p for p in admin.perfis if p.perfil != "admin"]
    sessao.flush()
    with pytest.raises(RegraNegocio):
        garantir_admin_ativo(sessao, emp.id)


def test_admin_de_outra_empresa_nao_conta(sessao):
    import pytest

    from app.nucleo.erros import RegraNegocio
    from app.nucleo.usuarios import garantir_admin_ativo

    a = nova_empresa(sessao, "A")
    b = nova_empresa(sessao, "B")
    novo_usuario(sessao, b, {Perfil.ADMIN})
    with pytest.raises(RegraNegocio):
        garantir_admin_ativo(sessao, a.id)
