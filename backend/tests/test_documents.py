import pytest
from pathlib import Path
from document_factory import pdf_bytes
from app.models.application import Application, Resume
from app.models.candidate import Candidate


def upload(client, headers, job_id, content, email="person@example.com"):
    return client.post(f"/api/jobs/{job_id}/cvs", headers=headers,
        data={"candidate_name": "Pessoa", "candidate_email": email},
        files={"file": ("cv.pdf", content, "application/pdf")})


@pytest.mark.parametrize("content,email", [(b"", "person@example.com"), (b"fake", "person@example.com"),
    (b"%PDF-1.4 broken", "person@example.com"), (pdf_bytes(), "not-email")])
def test_invalid_upload_has_no_partial_data(client, recruiter_headers, job, db_session, isolated_upload_dir, content, email):
    assert upload(client, recruiter_headers, job.id, content, email).status_code == 422
    assert db_session.query(Candidate).count() == 0
    assert db_session.query(Application).count() == 0
    assert not list(isolated_upload_dir.rglob("*.pdf"))


def test_versioned_upload_and_authorized_download(client, recruiter_headers, other_recruiter_headers, job):
    first = upload(client, recruiter_headers, job.id, pdf_bytes("Version one")).json()
    second = upload(client, recruiter_headers, job.id, pdf_bytes("Version two")).json()
    assert first["id"] == second["id"]
    assert [r["version"] for r in second["resumes"]] == [1, 2]
    assert len({r["sha256"] for r in second["resumes"]}) == 2
    url = f'/api/cvs/{first["resumes"][0]["id"]}/download'
    assert client.get(url, headers=recruiter_headers).content == pdf_bytes("Version one")
    assert client.get(url, headers=other_recruiter_headers).status_code == 403


def test_commit_failure_removes_file_and_rows(client, recruiter_headers, job, db_session, isolated_upload_dir, monkeypatch):
    def fail():
        raise RuntimeError("simulated commit failure")
    monkeypatch.setattr(db_session, "commit", fail)
    with pytest.raises(RuntimeError, match="simulated"):
        upload(client, recruiter_headers, job.id, pdf_bytes())
    assert db_session.query(Resume).count() == 0
    assert db_session.query(Candidate).count() == 0
    assert not list(isolated_upload_dir.rglob("*.pdf"))
