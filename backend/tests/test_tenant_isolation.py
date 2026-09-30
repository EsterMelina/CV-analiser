from test_candidates import _upload_cv


def test_same_email_is_independent_and_private(client, recruiter_headers, other_recruiter_headers, job, other_job):
    first = _upload_cv(client, recruiter_headers, job.id, name="Pessoa A").json()
    second = _upload_cv(client, other_recruiter_headers, other_job.id, name="Pessoa B").json()
    assert first["candidate_id"] != second["candidate_id"]
    assert client.get(f'/api/candidates/{first["candidate_id"]}', headers=recruiter_headers).json()["name"] == "Pessoa A"
    for headers, own, foreign in ((recruiter_headers, first, second), (other_recruiter_headers, second, first)):
        assert [c["id"] for c in client.get("/api/candidates", headers=headers).json()] == [own["candidate_id"]]
        for path in (f'/api/candidates/{foreign["candidate_id"]}',
                     f'/api/candidates/{foreign["candidate_id"]}/applications',
                     f'/api/cvs/{foreign["resumes"][0]["id"]}'):
            assert client.get(path, headers=headers).status_code == 403


def test_missing_or_inactive_company_blocks_existing_tokens(client, db_session, recruiter_headers, recruiter_user, company):
    company.is_active = False
    db_session.commit()
    assert client.get("/api/jobs", headers=recruiter_headers).status_code == 403
    company.is_active = True
    recruiter_user.company_id = None
    db_session.commit()
    assert client.get("/api/candidates", headers=recruiter_headers).status_code == 403
    assert client.post("/api/auth/login", json={"email": recruiter_user.email, "password": "Recruta@123"}).status_code == 403
