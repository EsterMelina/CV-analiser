from datetime import datetime, timedelta, timezone
from app.models.ai_execution import AIExecution
from app.services.executions import process_one, claim
from test_analysis_integration import _upload_docx


def views(client, headers, job_id):
    candidate = client.get(f"/api/jobs/{job_id}/candidates", headers=headers).json()[0]
    ranked = client.get(f"/api/jobs/{job_id}/ranking", headers=headers).json()[0]
    for field in ("analysis_status", "analysis_method", "score", "stale", "analysis_execution_id"):
        assert candidate[field] == ranked[field], field
    return candidate


def test_queue_running_and_completed_without_score_agree_in_both_views(client, recruiter_headers, job, db_session):
    uploaded = _upload_docx(client, recruiter_headers, job.id, ["PHP Laravel."], "person@example.com").json()
    resume_id = uploaded["resumes"][0]["id"]
    assert views(client, recruiter_headers, job.id)["analysis_status"] == "pending"
    started = client.post(f"/api/cvs/{resume_id}/analysis-executions",
        headers={**recruiter_headers, "Idempotency-Key": "overview"}).json()
    queued = views(client, recruiter_headers, job.id)
    assert queued["analysis_status"] == "queued"
    assert queued["analysis_execution_id"] == started["id"]
    claim(db_session)
    assert views(client, recruiter_headers, job.id)["analysis_status"] == "running"
    execution = db_session.get(AIExecution, started["id"])
    execution.lease_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    process_one(db_session)
    complete = views(client, recruiter_headers, job.id)
    assert complete["analysis_status"] == "review_required"
    assert complete["analysis_method"] == "mock-v1"
    assert complete["score"] is None
    assert complete["analysis_id"] is not None
    assert complete["analysis_execution_id"] is None
    history = client.get(f'/api/applications/{uploaded["id"]}/analysis-runs', headers=recruiter_headers).json()
    reviewed = client.post(f'/api/analysis-runs/{complete["analysis_id"]}/review', headers=recruiter_headers,
        json={"reason": "Revisão humana dos trechos do CV", "evidence": history[0]["evidence"]})
    assert reviewed.status_code == 201
    final = views(client, recruiter_headers, job.id)
    assert final["analysis_status"] == "reviewed"
    assert final["analysis_method"] == "human-review"
    assert final["score"] == 0  # A valid zero is distinct from no assessment.


def test_new_document_requires_its_own_analysis(client, recruiter_headers, job, db_session):
    first = _upload_docx(client, recruiter_headers, job.id, ["First CV"], "person@example.com").json()
    client.post(f'/api/cvs/{first["resumes"][0]["id"]}/analysis-executions',
        headers={**recruiter_headers, "Idempotency-Key": "first"})
    process_one(db_session)
    second = _upload_docx(client, recruiter_headers, job.id, ["Second CV"], "person@example.com").json()
    overview = views(client, recruiter_headers, job.id)
    assert overview["latest_resume_id"] == max(r["id"] for r in second["resumes"])
    assert overview["latest_resume_id"] != first["resumes"][0]["id"]
    assert overview["analysis_status"] == "stale"
    assert overview["score"] is None


def test_failed_execution_is_not_stuck_pending(client, recruiter_headers, job, db_session):
    uploaded = _upload_docx(client, recruiter_headers, job.id, ["CV"], "person@example.com").json()
    client.post(f'/api/cvs/{uploaded["resumes"][0]["id"]}/analysis-executions',
        headers={**recruiter_headers, "Idempotency-Key": "failure"})
    class FailedProvider:
        name = "failed"
        def complete(self, *args): raise RuntimeError("offline")
    process_one(db_session, FailedProvider())
    failed = views(client, recruiter_headers, job.id)
    assert failed["analysis_status"] == "error"
    assert failed["analysis_error"]
