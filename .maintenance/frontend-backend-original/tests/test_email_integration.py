"""
Testes da integração de e-mail (secções 9, 10, 30).

Não fazem ligações de rede reais (isso exigiria um servidor IMAP/OAuth real).
Cobrem a validação de payload e o estado antes/depois de ligar uma conta.
"""


def test_connect_imap_without_password_is_rejected(client, recruiter_headers):
    response = client.post("/api/email/connect", json={
        "email_address": "recrutamento@techmoz.co.mz",
        "provider": "imap",
        "imap_host": "imap.techmoz.co.mz",
        # imap_password em falta de propósito
    }, headers=recruiter_headers)
    assert response.status_code == 422


def test_connect_oauth_without_access_token_is_rejected(client, recruiter_headers):
    response = client.post("/api/email/connect", json={
        "email_address": "recrutamento@techmoz.co.mz",
        "provider": "gmail",
        # oauth_access_token em falta de propósito
    }, headers=recruiter_headers)
    assert response.status_code == 422


def test_status_without_connected_account_returns_404(client, recruiter_headers):
    response = client.get("/api/email/status", headers=recruiter_headers)
    assert response.status_code == 404


def test_connect_imap_with_unreachable_host_marks_account_as_error(client, recruiter_headers):
    """
    A conta é criada mesmo que a ligação inicial falhe (secção 10: o estado
    fica 'error' com uma mensagem, em vez de rejeitar o pedido). Usa
    localhost numa porta sem nada à escuta, para uma falha rápida e
    determinística (connection refused) em vez de um timeout de rede.
    """
    response = client.post("/api/email/connect", json={
        "email_address": "recrutamento@techmoz.co.mz",
        "provider": "imap",
        "imap_host": "127.0.0.1",
        "imap_port": 1,
        "imap_password": "qualquer-password",
    }, headers=recruiter_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "error"
