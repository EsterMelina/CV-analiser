import json
from test_analysis_integration import _upload_docx
from app.models.criteria_version import CriteriaVersion


def test_edit_preserves_snapshot_and_marks_analysis_stale(client, recruiter_headers, job, db_session):
    uploaded = _upload_docx(client, recruiter_headers, job.id, ["PHP e Laravel."], "person@example.com").json()
    resume_id = uploaded["resumes"][0]["id"]
    assert client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers).status_code == 200
    original = client.get(f"/api/cvs/{resume_id}/analysis", headers=recruiter_headers).json()
    old_name = job.requirements[0].name
    assert client.put(f"/api/requirements/{job.requirements[0].id}", json={"name": "Novo requisito", "description": "Descrição", "expected_level": "advanced"}, headers=recruiter_headers).status_code == 200
    versions = db_session.query(CriteriaVersion).filter_by(job_id=job.id).order_by(CriteriaVersion.version).all()
    assert len(versions) == 2
    assert json.loads(versions[0].snapshot_json)["requirements"][0]["name"] == old_name
    updated = client.get(f"/api/cvs/{resume_id}/analysis", headers=recruiter_headers).json()
    assert updated["stale"] is True
    assert updated["overall_score"] == original["overall_score"]
    assert updated["breakdown"] == original["breakdown"]


def test_zero_weights_reject_analysis(client, recruiter_headers, job, db_session):
    for requirement in job.requirements:
        requirement.weight = 0
    db_session.commit()
    uploaded = _upload_docx(client, recruiter_headers, job.id, ["PHP."], "person@example.com").json()
    assert client.post(f'/api/cvs/{uploaded["resumes"][0]["id"]}/analyze', headers=recruiter_headers).status_code == 400
