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


def test_connect_imap_with_failed_authentication_marks_account_as_error(client, recruiter_headers, monkeypatch):
    """Simula recusa do servidor; não tenta abrir uma ligação real."""
    from unittest.mock import Mock
    from app.api import email as email_api

    provider = Mock()
    provider.test_connection.return_value = False
    factory = Mock(return_value=provider)
    monkeypatch.setattr(email_api, "get_provider_for_account", factory)

    response = client.post("/api/email/connect", json={
        "email_address": "recruitment@example.com",
        "provider": "imap",
        "imap_host": "imap.example.test",
        "imap_password": "fake-password",
    }, headers=recruiter_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    factory.assert_called_once()
    provider.test_connection.assert_called_once_with()
