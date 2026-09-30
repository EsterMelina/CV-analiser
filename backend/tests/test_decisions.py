import pytest
from test_analysis_integration import _upload_docx


@pytest.mark.parametrize("decision", ["hired", "rejected", "interview_selected", "interviewed", "in_evaluation"])
def test_reanalysis_preserves_decision(client, recruiter_headers, job, decision):
    upload = _upload_docx(client, recruiter_headers, job.id, ["PHP Laravel PostgreSQL Git, 4 anos de experiência."], "person@example.com").json()
    assert client.patch(f'/api/applications/{upload["id"]}/status', json={"status": decision}, headers=recruiter_headers).status_code == 200
    assert client.post(f'/api/cvs/{upload["resumes"][0]["id"]}/analyze', headers=recruiter_headers).status_code == 200
    application = client.get(f'/api/jobs/{job.id}/candidates', headers=recruiter_headers).json()[0]
    assert application["status"] == decision
    assert application["analysis_status"] == "completed"


def test_feedback_uses_facts_and_requires_explicit_reopening(client, recruiter_headers, job):
    application = _upload_docx(client, recruiter_headers, job.id, ["Perfil fictício."], "person@example.com").json()
    url = f'/api/applications/{application["id"]}'
    result = client.put(url + "/feedback", json={"system_recommended": True, "selected_for_interview": True}, headers=recruiter_headers)
    assert result.json()["system_recommended"] is False
    assert result.json()["selected_for_interview"] is False
    assert client.put(url + "/feedback", json={"hired": True, "rating": "not_suitable"}, headers=recruiter_headers).status_code == 409
    assert client.put(url + "/feedback", json={"hired": True, "comments": "Decisão humana"}, headers=recruiter_headers).status_code == 200
    assert client.patch(url + "/status", json={"status": "rejected"}, headers=recruiter_headers).status_code == 409
    assert client.post(url + "/interview", json={"scheduled_at": "2026-10-01T10:00:00Z"}, headers=recruiter_headers).status_code == 409
    assert client.get(url + "/feedback", headers=recruiter_headers).json()["comments"] == "Decisão humana"
    assert client.patch(url + "/status", json={"status": "in_evaluation"}, headers=recruiter_headers).status_code == 200
    assert client.get(url + "/feedback", headers=recruiter_headers).json()["hired"] is False
