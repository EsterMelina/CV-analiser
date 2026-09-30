"""
Testes de autenticação (secção 3): login, tokens, /me, e controlo de
acesso por papel (admin vs recruiter).
"""


def test_login_success(client, recruiter_user):
    response = client.post("/api/auth/login", json={
        "email": "recrutamento@techmoz.co.mz", "password": "Recruta@123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, recruiter_user):
    response = client.post("/api/auth/login", json={
        "email": "recrutamento@techmoz.co.mz", "password": "password-errada",
    })
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post("/api/auth/login", json={
        "email": "ninguem@techmoz.co.mz", "password": "qualquer",
    })
    assert response.status_code == 401


def test_login_inactive_user_is_rejected(client, db_session, company):
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    user = User(
        name="Inativo", email="inativo@techmoz.co.mz",
        password_hash=hash_password("Password@123"),
        role=UserRole.RECRUITER, company_id=company.id, is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/auth/login", json={
        "email": "inativo@techmoz.co.mz", "password": "Password@123",
    })
    assert response.status_code == 403


def test_get_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_returns_current_user(client, recruiter_headers):
    response = client.get("/api/auth/me", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "recrutamento@techmoz.co.mz"
    assert data["role"] == "recruiter"


def test_refresh_token_issues_new_access_token(client, recruiter_user):
    login = client.post("/api/auth/login", json={
        "email": "recrutamento@techmoz.co.mz", "password": "Recruta@123",
    })
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_recruiter_cannot_manage_companies(client, recruiter_headers):
    """RBAC: gestão de empresas é exclusiva do admin (secção 3)."""
    response = client.post("/api/companies", json={"name": "Outra Empresa"}, headers=recruiter_headers)
    assert response.status_code == 403


def test_admin_can_manage_companies(client, admin_headers):
    response = client.post("/api/companies", json={"name": "Nova Empresa Lda"}, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Nova Empresa Lda"
