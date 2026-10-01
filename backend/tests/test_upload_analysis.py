import json

import pytest

from app.core.config import settings
from app.models.ai_execution import AIExecution
from app.models.application import Resume
from app.models.candidate import Candidate
from app.services.executions import process_one
from document_factory import pdf_bytes
from test_documents import upload


@pytest.fixture
def configured_ai(monkeypatch):
    for key, value in {
        "AI_PROVIDER": "openai-compatible", "AI_ENDPOINT": "https://example.test/chat/completions",
        "AI_MODEL": "fixture", "AI_API_KEY": "fixture", "AI_REAL_ENABLED": True,
        "AI_DATA_APPROVED": True,
    }.items():
        monkeypatch.setattr(settings, key, value)


def test_upload_queues_and_worker_publishes_analysis(client, recruiter_headers, job, db_session, configured_ai):
    response = upload(client, recruiter_headers, job.id, pdf_bytes())
    assert response.status_code == 201
    application = response.json()
    assert application["analysis_status"] == "queued"
    execution = db_session.get(AIExecution, application["analysis_execution_id"])
    payload = json.loads(execution.payload_json)
    assert execution.attempts == 0
    assert execution.created_by_id == job.created_by_id
    assert payload["resume_id"] == application["resumes"][0]["id"]
    assert payload["document_hash"] == application["resumes"][0]["sha256"]
    assert payload["criteria_version"] == job.criteria_version

    class ProviderFixture:
        name = "fixture-real-contract"
        assessment_only = True

        def complete(self, operation, payload):
            return {"evidence": [{"requirement_id": r["id"], "state": "not_evidenced",
                "explanation": "Sem evidência suficiente.", "citations": []}
                for r in payload["criteria"]["requirements"]]}

    assert process_one(db_session, ProviderFixture())
    detail = client.get(f'/api/applications/{application["id"]}', headers=recruiter_headers).json()
    assert detail["analysis_status"] == "completed"
    assert detail["analysis_id"] is not None
    # Manual reanalysis remains available after the automatic run.
    manual = client.post(f'/api/cvs/{payload["resume_id"]}/analysis-executions',
        headers={**recruiter_headers, "Idempotency-Key": "manual-after-upload"})
    assert manual.status_code == 202


def test_duplicate_upload_does_not_queue_again_but_new_version_does(
        client, recruiter_headers, job, db_session, configured_ai):
    contents = pdf_bytes()
    first = upload(client, recruiter_headers, job.id, contents).json()
    duplicate = upload(client, recruiter_headers, job.id, contents).json()
    assert duplicate["analysis_execution_id"] == first["analysis_execution_id"]
    assert db_session.query(AIExecution).count() == 1
    updated = upload(client, recruiter_headers, job.id, pdf_bytes("Novo CV: PHP e Laravel.")).json()
    assert updated["id"] == first["id"]
    assert updated["analysis_execution_id"] != first["analysis_execution_id"]
    assert updated["analysis_status"] == "queued"
    assert db_session.query(AIExecution).count() == 2


@pytest.mark.parametrize("missing", ["provider", "requirements", "weights"])
def test_upload_is_preserved_when_analysis_not_ready(
        client, recruiter_headers, job, db_session, configured_ai, monkeypatch, missing):
    if missing == "provider":
        monkeypatch.setattr(settings, "AI_REAL_ENABLED", False)
    elif missing == "requirements":
        job.requirements.clear()
    else:
        for requirement in job.requirements:
            requirement.weight = 0
    db_session.commit()
    response = upload(client, recruiter_headers, job.id, pdf_bytes())
    assert response.status_code == 201
    assert response.json()["analysis_status"] == "pending"
    assert db_session.query(Resume).count() == 1
    assert db_session.query(AIExecution).count() == 0


def test_failed_upload_rolls_back_queued_analysis(
        client, recruiter_headers, job, db_session, configured_ai, isolated_upload_dir, monkeypatch):
    def fail():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db_session, "commit", fail)
    with pytest.raises(RuntimeError, match="commit failed"):
        upload(client, recruiter_headers, job.id, pdf_bytes())
    assert db_session.query(AIExecution).count() == 0
    assert db_session.query(Resume).count() == 0
    assert db_session.query(Candidate).count() == 0
    assert not list(isolated_upload_dir.rglob("*.pdf"))
