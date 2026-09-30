"""
Testes de gestão de vagas (secções 6, 28): CRUD, publicar/encerrar,
pesquisa/filtro, e isolamento de dados por empresa (secção 3).
"""


def _job_payload(code="VAG-2026-099"):
    return {
        "title": "Data Analyst",
        "code": code,
        "description": "Análise de dados e construção de dashboards.",
        "department": "Dados",
        "location": "Maputo",
        "job_type": "full_time",
        "modality": "on_site",
        "min_experience_years": 1,
        "education_level": "Licenciatura",
    }


def test_create_job(client, recruiter_headers):
    response = client.post("/api/jobs", json=_job_payload(), headers=recruiter_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "VAG-2026-099"
    assert data["status"] == "draft"


def test_create_job_requires_recruiter_role(client):
    response = client.post("/api/jobs", json=_job_payload())
    assert response.status_code == 401  # sem token


def test_cannot_create_job_with_duplicate_code(client, recruiter_headers, job):
    response = client.post("/api/jobs", json=_job_payload(code=job.code), headers=recruiter_headers)
    assert response.status_code == 409


def test_list_jobs_returns_only_own_company(client, db_session, recruiter_headers, job):
    """Isolamento multi-empresa (secção 3): um recrutador só vê vagas da sua empresa."""
    from app.models.company import Company
    from app.models.job import Job, JobStatus, JobType, JobModality

    other_company = Company(name="Outra Empresa")
    db_session.add(other_company)
    db_session.flush()
    other_job = Job(
        company_id=other_company.id, title="Vaga de Outra Empresa", code="VAG-OUTRA-001",
        description="...", job_type=JobType.FULL_TIME, modality=JobModality.REMOTE,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(other_job)
    db_session.commit()

    response = client.get("/api/jobs", headers=recruiter_headers)
    assert response.status_code == 200
    codes = [j["code"] for j in response.json()]
    assert job.code in codes
    assert "VAG-OUTRA-001" not in codes


def test_recruiter_cannot_access_other_company_job(client, db_session, recruiter_headers):
    from app.models.company import Company
    from app.models.job import Job, JobStatus, JobType, JobModality

    other_company = Company(name="Outra Empresa")
    db_session.add(other_company)
    db_session.flush()
    other_job = Job(
        company_id=other_company.id, title="Vaga de Outra Empresa", code="VAG-OUTRA-002",
        description="...", job_type=JobType.FULL_TIME, modality=JobModality.REMOTE,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(other_job)
    db_session.commit()
    db_session.refresh(other_job)

    response = client.get(f"/api/jobs/{other_job.id}", headers=recruiter_headers)
    assert response.status_code == 403


def test_publish_job_without_requirements_fails(client, recruiter_headers):
    create = client.post("/api/jobs", json=_job_payload(code="VAG-SEM-REQ"), headers=recruiter_headers)
    job_id = create.json()["id"]

    response = client.post(f"/api/jobs/{job_id}/publish", headers=recruiter_headers)
    assert response.status_code == 400


def test_publish_job_with_requirements_succeeds(client, recruiter_headers, job):
    response = client.post(f"/api/jobs/{job.id}/publish", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"
    assert data["published_at"] is not None


def test_close_job(client, recruiter_headers, job):
    client.post(f"/api/jobs/{job.id}/publish", headers=recruiter_headers)
    response = client.post(f"/api/jobs/{job.id}/close", headers=recruiter_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_search_jobs_by_title(client, recruiter_headers, job):
    response = client.get("/api/jobs", params={"search": "Backend"}, headers=recruiter_headers)
    assert response.status_code == 200
    assert any(j["code"] == job.code for j in response.json())

    response = client.get("/api/jobs", params={"search": "Inexistente"}, headers=recruiter_headers)
    assert response.json() == []


def test_add_requirement_to_job(client, recruiter_headers, job):
    payload = {
        "name": "Docker", "category": "tool", "weight": 0.1,
        "is_mandatory": False, "expected_level": "intermediate",
    }
    response = client.post(f"/api/jobs/{job.id}/requirements", json=payload, headers=recruiter_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Docker"


def test_update_requirement(client, recruiter_headers, job):
    requirement_id = job.requirements[0].id
    response = client.put(
        f"/api/requirements/{requirement_id}", json={"weight": 0.5}, headers=recruiter_headers,
    )
    assert response.status_code == 200
    assert response.json()["weight"] == 0.5


def test_delete_requirement(client, recruiter_headers, job):
    requirement_id = job.requirements[0].id
    response = client.delete(f"/api/requirements/{requirement_id}", headers=recruiter_headers)
    assert response.status_code == 204

    response = client.get(f"/api/jobs/{job.id}/requirements", headers=recruiter_headers)
    assert requirement_id not in [r["id"] for r in response.json()]
