"""
Testes de candidatos/candidaturas (secções 8, 12, 13, 22): upload de CV,
listagem por vaga, deduplicação de candidatos e transição de estados.
"""
import io


def _upload_cv(client, headers, job_id, email="joao@example.com", name="João Silva", filename="cv_joao.pdf"):
    return client.post(
        f"/api/jobs/{job_id}/cvs",
        headers=headers,
        data={"candidate_name": name, "candidate_email": email, "candidate_phone": "+258840000000"},
        files={"file": (filename, io.BytesIO(b"%PDF-1.4 conteudo de teste"), "application/pdf")},
    )


def test_upload_cv_creates_candidate_and_application(client, recruiter_headers, job):
    response = _upload_cv(client, recruiter_headers, job.id)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "received"
    assert data["source"] == "upload"
    assert data["candidate"]["email"] == "joao@example.com"
    assert len(data["resumes"]) == 1
    assert data["resumes"][0]["original_filename"] == "cv_joao.pdf"


def test_upload_rejects_unsupported_extension(client, recruiter_headers, job):
    response = client.post(
        f"/api/jobs/{job.id}/cvs",
        headers=recruiter_headers,
        data={"candidate_name": "Ana", "candidate_email": "ana@example.com"},
        files={"file": ("cv_ana.txt", io.BytesIO(b"texto simples"), "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_file(client, recruiter_headers, job, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)  # qualquer ficheiro passa a exceder

    response = _upload_cv(client, recruiter_headers, job.id)
    assert response.status_code == 413


def test_same_email_reuses_existing_candidate(client, recruiter_headers, job, db_session):
    """Prevenção de duplicados (secção 13): mesmo e-mail = mesmo Candidate,
    mas cada upload cria uma nova Application (candidatura)."""
    from app.models.candidate import Candidate

    _upload_cv(client, recruiter_headers, job.id, email="repetido@example.com")
    _upload_cv(client, recruiter_headers, job.id, email="repetido@example.com", filename="cv_v2.pdf")

    candidates = db_session.query(Candidate).filter(Candidate.email == "repetido@example.com").all()
    assert len(candidates) == 1

    response = client.get(f"/api/jobs/{job.id}/candidates", headers=recruiter_headers)
    applications = response.json()
    assert len(applications) == 2
    assert all(a["candidate_id"] == candidates[0].id for a in applications)


def test_candidate_can_apply_to_multiple_jobs(client, recruiter_headers, job, db_session, company, recruiter_user):
    from app.models.job import Job, JobStatus, JobType, JobModality

    second_job = Job(
        company_id=company.id, created_by_id=recruiter_user.id, title="Engenheiro de Software",
        code="VAG-2026-020", description="...", job_type=JobType.FULL_TIME,
        modality=JobModality.REMOTE, status=JobStatus.DRAFT,
    )
    db_session.add(second_job)
    db_session.commit()

    _upload_cv(client, recruiter_headers, job.id, email="multi@example.com")
    _upload_cv(client, recruiter_headers, second_job.id, email="multi@example.com")

    from app.models.candidate import Candidate
    candidate = db_session.query(Candidate).filter(Candidate.email == "multi@example.com").first()

    response = client.get(f"/api/candidates/{candidate.id}/applications", headers=recruiter_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_application_status(client, recruiter_headers, job):
    upload = _upload_cv(client, recruiter_headers, job.id)
    application_id = upload.json()["id"]

    response = client.patch(
        f"/api/applications/{application_id}/status",
        json={"status": "interview_selected", "recruiter_notes": "Perfil muito forte"},
        headers=recruiter_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "interview_selected"
    assert data["recruiter_notes"] == "Perfil muito forte"


def test_list_job_candidates_requires_authentication(client, job):
    response = client.get(f"/api/jobs/{job.id}/candidates")
    assert response.status_code == 401
