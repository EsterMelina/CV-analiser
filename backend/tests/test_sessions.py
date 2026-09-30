def test_rotation_logout_and_reuse(client, recruiter_user):
    login = client.post("/api/auth/login", json={"email": recruiter_user.email, "password": "Recruta@123"}).json()
    first = login["refresh_token"]
    renewed = client.post("/api/auth/refresh", json={"refresh_token": first})
    assert renewed.status_code == 200
    second = renewed.json()["refresh_token"]
    assert second != first
    assert client.post("/api/auth/refresh", json={"refresh_token": first}).status_code == 401
    assert client.post("/api/auth/logout", json={"refresh_token": second}).status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": second}).status_code == 401


def test_company_change_invalidates_refresh(client, recruiter_user, other_company, db_session):
    tokens = client.post("/api/auth/login", json={"email": recruiter_user.email, "password": "Recruta@123"}).json()
    recruiter_user.company_id = other_company.id
    db_session.commit()
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
