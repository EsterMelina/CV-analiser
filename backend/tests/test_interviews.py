"""
Testes de entrevistas (secção 23) e feedback do recrutador (secção 26).
"""
import io
from document_factory import pdf_bytes


def _create_application(client, headers, job_id, email="candidato@example.com"):
    response = client.post(
        f"/api/jobs/{job_id}/cvs",
        headers=headers,
        data={"candidate_name": "Candidato Teste", "candidate_email": email},
        files={"file": ("cv.pdf", io.BytesIO(pdf_bytes()), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_schedule_interview(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)

    response = client.post(
        f"/api/applications/{application_id}/interview",
        json={
            "scheduled_at": "2026-09-10T14:00:00",
            "interviewers": "Recrutadora TechMoz, CTO",
            "location_or_link": "https://meet.example.com/abc",
            "notes": "Focar em experiência com APIs REST",
        },
        headers=recruiter_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["result"] == "scheduled"
    assert data["application_id"] == application_id

    # O estado da candidatura deve refletir a seleção para entrevista (secção 22)
    status_response = client.get(f"/api/jobs/{job.id}/candidates", headers=recruiter_headers)
    application = next(a for a in status_response.json() if a["id"] == application_id)
    assert application["status"] == "interview_selected"


def test_update_interview_result_to_completed(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)
    schedule = client.post(
        f"/api/applications/{application_id}/interview",
        json={"scheduled_at": "2026-09-10T14:00:00"},
        headers=recruiter_headers,
    )
    interview_id = schedule.json()["id"]

    response = client.patch(
        f"/api/interviews/{interview_id}/result",
        json={"result": "completed", "result_notes": "Boa comunicação técnica"},
        headers=recruiter_headers,
    )
    assert response.status_code == 200
    assert response.json()["result"] == "completed"

    status_response = client.get(f"/api/jobs/{job.id}/candidates", headers=recruiter_headers)
    application = next(a for a in status_response.json() if a["id"] == application_id)
    assert application["status"] == "interviewed"


def test_schedule_requires_no_recruiter_feedback(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)
    feedback_url = f"/api/applications/{application_id}/feedback"
    assert client.get(feedback_url, headers=recruiter_headers).status_code == 404

    response = client.post(
        f"/api/applications/{application_id}/interview",
        json={"scheduled_at": "2026-09-15T14:00:00"},
        headers=recruiter_headers,
    )
    assert response.status_code == 201
    application = client.get(
        f"/api/applications/{application_id}", headers=recruiter_headers,
    ).json()
    assert application["status"] == "interview_selected"
    assert client.get(feedback_url, headers=recruiter_headers).status_code == 404


def test_list_interviews_for_application(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)
    client.post(
        f"/api/applications/{application_id}/interview",
        json={"scheduled_at": "2026-09-10T14:00:00"},
        headers=recruiter_headers,
    )

    response = client.get(f"/api/applications/{application_id}/interviews", headers=recruiter_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_submit_and_update_recruiter_feedback(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)

    response = client.put(
        f"/api/applications/{application_id}/feedback",
        json={
            "system_recommended": True, "selected_for_interview": True,
            "hired": False, "rating": "suitable", "comments": "Bom perfil técnico",
        },
        headers=recruiter_headers,
    )
    assert response.status_code == 200
    assert response.json()["rating"] == "suitable"

    # Atualizar o mesmo feedback (upsert) após a contratação
    response = client.put(
        f"/api/applications/{application_id}/feedback",
        json={
            "system_recommended": True, "selected_for_interview": True,
            "hired": True, "rating": "very_suitable", "comments": "Contratado!",
        },
        headers=recruiter_headers,
    )
    assert response.status_code == 200
    assert response.json()["hired"] is True

    status_response = client.get(f"/api/jobs/{job.id}/candidates", headers=recruiter_headers)
    application = next(a for a in status_response.json() if a["id"] == application_id)
    assert application["status"] == "hired"


def test_get_feedback_without_submission_returns_404(client, recruiter_headers, job):
    application_id = _create_application(client, recruiter_headers, job.id)
    response = client.get(f"/api/applications/{application_id}/feedback", headers=recruiter_headers)
    assert response.status_code == 404
