from datetime import datetime, timedelta, timezone
import copy
import json
import pytest
from pydantic import ValidationError
from app.schemas.ai import GeneratedQuestionnaire, QuestionnaireContent
from app.services.executions import process_one, claim
from app.models.ai_execution import AIExecution


def config(job, count=2):
    return {"requirement_ids": [job.requirements[0].id], "count": count, "format": "open", "language": "pt"}


def test_generated_questions_require_answers_but_manual_drafts_can_be_incomplete():
    content = {"language": "pt", "questions": [{"key": "q1", "requirement_id": 1,
        "category": "technology", "format": "open", "prompt": "Como aplicaria Python?"}]}
    assert QuestionnaireContent.model_validate(content).questions[0].expected_answer == ""
    with pytest.raises(ValidationError):
        GeneratedQuestionnaire.model_validate(content)
    content["questions"][0].update(expected_answer="Descrever um exemplo concreto.", rubric="Avaliar clareza e adequação.")
    assert len(GeneratedQuestionnaire.model_validate(content).questions) == 1


def test_generate_by_area_and_reject_mismatched_requirements(client, recruiter_headers, job, db_session):
    requirement = job.requirements[0]
    value = config(job)
    value["category"] = requirement.category.value
    response = client.post(f"/api/jobs/{job.id}/questionnaires/generate",
        headers={**recruiter_headers, "Idempotency-Key": "area-valid"}, json={"config": value})
    assert response.status_code == 202
    process_one(db_session)
    execution = client.get(f'/api/executions/{response.json()["id"]}', headers=recruiter_headers).json()
    assert execution["status"] == "succeeded"
    assert all(q["category"] == value["category"] and q["expected_answer"] and q["rubric"]
               for q in execution["result"]["content"]["questions"])
    value["category"] = "language" if value["category"] != "language" else "technology"
    response = client.post(f"/api/jobs/{job.id}/questionnaires/generate",
        headers={**recruiter_headers, "Idempotency-Key": "area-invalid"}, json={"config": value})
    assert response.status_code == 422


def generate(client, headers, job, key="test-key", **extra):
    return client.post(f"/api/jobs/{job.id}/questionnaires/generate",
        headers={**headers, "Idempotency-Key": key}, json={"config": config(job), **extra})


def test_generate_without_candidates_edit_reopen_approve_and_print(client, recruiter_headers, job, db_session, other_recruiter_headers):
    job.title = "Gestor de Armazém"
    db_session.commit()
    response = generate(client, recruiter_headers, job)
    assert response.status_code == 202
    execution_id = response.json()["id"]
    assert generate(client, recruiter_headers, job).json()["id"] == execution_id
    assert process_one(db_session)
    execution = client.get(f"/api/executions/{execution_id}", headers=recruiter_headers).json()
    assert execution["status"] == "succeeded", execution
    assert execution["result"]["simulated"] is True
    version_id = execution["result"]["version_id"]
    url = f"/api/questionnaire-versions/{version_id}"
    version = client.get(url, headers=recruiter_headers).json()
    assert version["status"] == "draft"
    content = copy.deepcopy(version["content"])
    content["questions"].reverse()
    content["questions"][0]["prompt"] = "Explique a reconciliação do inventário físico."
    saved = client.put(url, headers=recruiter_headers, json={"expected_revision": 1, "content": content})
    assert saved.status_code == 200
    assert client.put(url, headers=recruiter_headers, json={"expected_revision": 1, "content": content}).status_code == 409
    reopened = client.get(url, headers=recruiter_headers).json()
    assert reopened["content"]["questions"][0]["prompt"] == content["questions"][0]["prompt"]
    assert reopened["content"]["questions"][0]["provenance"] == "edited"
    approved = client.post(url + "/approve", headers=recruiter_headers, json={"expected_revision": 2})
    assert approved.status_code == 200
    assert approved.json()["approved_by_id"]
    assert client.put(url, headers=recruiter_headers, json={"expected_revision": 3, "content": content}).status_code == 409
    fork = client.post(url + "/fork", headers=recruiter_headers)
    assert fork.status_code == 201
    assert fork.json()["status"] == "draft"
    assert client.get(url, headers=recruiter_headers).json()["status"] == "approved"
    sheet = client.get(url + "/print", headers=recruiter_headers).json()
    assert all(set(q) == {"prompt", "format", "options"} for q in sheet["questions"])
    guide = client.get(url + "/print?mode=guide", headers=recruiter_headers).json()
    assert all(q["rubric"] for q in guide["questions"])
    for path in (url, url + "/print", f"/api/executions/{execution_id}"):
        assert client.get(path, headers=other_recruiter_headers).status_code == 403


def test_regeneration_preserves_original_until_explicit_apply(client, recruiter_headers, job, db_session):
    generate(client, recruiter_headers, job)
    process_one(db_session)
    original = client.get(f"/api/jobs/{job.id}/questionnaires", headers=recruiter_headers).json()[0]
    target = original["content"]["questions"][1]
    request = {"version_id": original["id"], "target_key": target["key"], "config": config(job, 1)}
    execution = client.post(f"/api/jobs/{job.id}/questionnaires/generate", headers={**recruiter_headers, "Idempotency-Key": "regen"}, json=request).json()
    process_one(db_session)
    url = f'/api/questionnaire-versions/{original["id"]}'
    assert client.get(url, headers=recruiter_headers).json()["content"] == original["content"]
    applied = client.post(url + "/apply-generation", headers=recruiter_headers,
        json={"expected_revision": original["revision"], "execution_id": execution["id"]})
    assert applied.status_code == 200
    updated = applied.json()["content"]["questions"]
    assert updated[0] == original["content"]["questions"][0]
    assert updated[1]["key"] == target["key"]
    assert updated[1]["prompt"] != target["prompt"]


def test_expired_worker_reservation_is_recovered_and_failure_can_retry(client, recruiter_headers, job, db_session):
    execution_id = generate(client, recruiter_headers, job).json()["id"]
    claim(db_session)
    execution = db_session.get(AIExecution, execution_id)
    execution.lease_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    class Unavailable:
        name = "fake"
        def complete(self, *args):
            raise RuntimeError("SECRET-must-not-leak")
    process_one(db_session, Unavailable())
    failure = client.get(f"/api/executions/{execution_id}", headers=recruiter_headers).json()
    assert failure["status"] == "failed"
    assert "SECRET" not in json.dumps(failure)
    assert client.post(f"/api/executions/{execution_id}/retry", headers=recruiter_headers).status_code == 200
    process_one(db_session)
    assert client.get(f"/api/executions/{execution_id}", headers=recruiter_headers).json()["status"] == "succeeded"
