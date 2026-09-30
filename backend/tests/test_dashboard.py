"""Testes do resumo do dashboard (secção 5 do prompt mestre)."""
import io

import pytest

docx = pytest.importorskip("docx", reason="python-docx não instalado neste ambiente")


def _upload_and_analyze(client, headers, job_id, email, strong=True):
    document = docx.Document()
    if strong:
        document.add_paragraph("Desenvolveu APIs REST utilizando Laravel e PostgreSQL.")
        document.add_paragraph("4 anos de experiência. PHP e Git no dia a dia.")
    else:
        document.add_paragraph("Experiência em vendas.")
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    upload = client.post(
        f"/api/jobs/{job_id}/cvs", headers=headers,
        data={"candidate_name": "Candidato", "candidate_email": email},
        files={"file": ("cv.docx", buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    resume_id = upload.json()["resumes"][0]["id"]
    return client.post(f"/api/cvs/{resume_id}/analyze", headers=headers), upload.json()["id"]


def test_dashboard_summary_with_no_jobs(client, recruiter_headers, db_session, company, recruiter_user):
    # Sem a fixture "job": a empresa ainda não tem vagas.
    response = client.get("/api/dashboard/summary", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 0
    assert data["total_applications"] == 0


def test_dashboard_summary_counts_applications_and_recommendations(client, recruiter_headers, job):
    client.post(f"/api/jobs/{job.id}/publish", headers=recruiter_headers)

    _upload_and_analyze(client, recruiter_headers, job.id, "forte@example.com", strong=True)
    analysis, application_id = _upload_and_analyze(client, recruiter_headers, job.id, "fraco@example.com", strong=False)

    response = client.get("/api/dashboard/summary", headers=recruiter_headers)
    data = response.json()

    assert data["total_jobs"] == 1
    assert data["active_jobs"] == 1
    assert data["total_applications"] == 2
    assert data["total_candidates"] == 2
    assert data["analyzed_applications"] == 2
    assert data["recommended_applications"] == 1

    client.patch(
        f"/api/applications/{application_id}/status",
        json={"status": "interview_selected"}, headers=recruiter_headers,
    )
    response = client.get("/api/dashboard/summary", headers=recruiter_headers)
    assert response.json()["interview_selected_applications"] == 1


def test_applications_by_job(client, recruiter_headers, job):
    _upload_and_analyze(client, recruiter_headers, job.id, "candidato@example.com", strong=True)

    response = client.get("/api/dashboard/applications-by-job", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_code"] == job.code
    assert data[0]["total_applications"] == 1
    assert data[0]["recommended"] == 1


def test_dashboard_requires_authentication(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 401
