"""
Testes do histórico de processamento (secção 31): cada CV analisado (ou
falhado) deve deixar um registo em ProcessingLog, consultável e filtrável.
"""
import io

import pytest

docx = pytest.importorskip("docx", reason="python-docx não instalado neste ambiente")


def _upload_and_analyze(client, headers, job_id, email):
    document = docx.Document()
    document.add_paragraph("Desenvolveu APIs REST utilizando Laravel e PostgreSQL.")
    document.add_paragraph("4 anos de experiência. PHP e Git no dia a dia.")
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    upload = client.post(
        f"/api/jobs/{job_id}/cvs", headers=headers,
        data={"candidate_name": "Candidato", "candidate_email": email},
        files={"file": ("cv.docx", buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    resume_id = upload.json()["resumes"][0]["id"]
    return client.post(f"/api/cvs/{resume_id}/analyze", headers=headers)


def test_successful_analysis_creates_processed_log(client, recruiter_headers, job):
    _upload_and_analyze(client, recruiter_headers, job.id, "log-sucesso@example.com")

    response = client.get("/api/processing-logs", headers=recruiter_headers)
    assert response.status_code == 200
    logs = response.json()
    assert any(
        log["candidate_email"] == "log-sucesso@example.com" and log["status"] == "processed"
        for log in logs
    )


def test_processing_logs_require_authentication(client):
    response = client.get("/api/processing-logs")
    assert response.status_code == 401


def test_processing_logs_can_be_filtered_by_status(client, recruiter_headers, job):
    _upload_and_analyze(client, recruiter_headers, job.id, "log-filtro@example.com")

    response = client.get("/api/processing-logs", params={"status": "processed"}, headers=recruiter_headers)
    assert response.status_code == 200
    assert all(log["status"] == "processed" for log in response.json())

    response = client.get("/api/processing-logs", params={"status": "error"}, headers=recruiter_headers)
    assert all(log["status"] == "error" for log in response.json())


def test_recruiter_only_sees_own_company_logs(client, db_session, recruiter_headers, job):
    from app.models.company import Company
    from app.models.user import User, UserRole
    from app.models.job import Job, JobStatus, JobType, JobModality
    from app.models.job_requirement import JobRequirement, RequirementCategory
    from app.core.security import hash_password

    other_company = Company(name="Outra Empresa")
    db_session.add(other_company)
    db_session.flush()

    other_job = Job(
        company_id=other_company.id, title="Outra Vaga", code="VAG-OUTRA-LOG",
        description="...", job_type=JobType.FULL_TIME, modality=JobModality.REMOTE,
        status=JobStatus.PUBLISHED,
    )
    db_session.add(other_job)
    db_session.flush()
    db_session.add(JobRequirement(job_id=other_job.id, name="Python", category=RequirementCategory.TECHNICAL_SKILL, weight=1.0, is_mandatory=True))

    other_recruiter = User(
        name="Outro Recrutador", email="outro@outraempresa.co.mz",
        password_hash=hash_password("Outro@123"), role=UserRole.RECRUITER, company_id=other_company.id,
    )
    db_session.add(other_recruiter)
    db_session.commit()

    other_login = client.post("/api/auth/login", json={"email": "outro@outraempresa.co.mz", "password": "Outro@123"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    _upload_and_analyze(client, recruiter_headers, job.id, "empresa-a@example.com")
    _upload_and_analyze(client, other_headers, other_job.id, "empresa-b@example.com")

    response = client.get("/api/processing-logs", headers=recruiter_headers)
    emails = [log["candidate_email"] for log in response.json()]
    assert "empresa-a@example.com" in emails
    assert "empresa-b@example.com" not in emails
