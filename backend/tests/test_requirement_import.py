import json
import pytest
from fastapi import HTTPException
from app.models.criteria_version import CriteriaVersion
from app.services.requirement_import import parse_requirements


def send(client, headers, job, contents, filename="requisitos.txt"):
    return client.post(f"/api/jobs/{job.id}/requirements/import", headers=headers,
                       files={"file": (filename, contents, "text/plain")})


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16"])
def test_parser_accepts_lists_and_deduplicates(encoding):
    assert parse_requirements("- Python\n1. Inglês avançado\n• python\n\n".encode(encoding)) == ["Python", "Inglês avançado"]


@pytest.mark.parametrize("contents", [b"", b"\x00binary", b"\xffinvalid", ("a" * 4001).encode(),
                                     "\n".join(f"item {i}" for i in range(101)).encode()])
def test_parser_rejects_invalid_input(contents):
    with pytest.raises(HTTPException):
        parse_requirements(contents)


def test_import_appends_and_versions_once(client, recruiter_headers, job, db_session):
    initial, count = job.criteria_version, len(job.requirements)
    long_text = ("Conhecimentos especializados " * 10).strip()
    response = send(client, recruiter_headers, job, f"PHP\n- Python\n{long_text}".encode())
    assert response.status_code == 201
    assert response.json()["imported"] == 2
    assert response.json()["skipped"] == 1
    assert response.json()["requirements"][1]["description"] == long_text
    db_session.refresh(job)
    assert job.criteria_version == initial + 1
    assert len(job.requirements) == count + 2
    before = db_session.query(CriteriaVersion).filter_by(job_id=job.id, version=initial).one()
    assert len(json.loads(before.snapshot_json)["requirements"]) == count
    assert send(client, recruiter_headers, job, f"Python\n{long_text}".encode()).json()["imported"] == 0
    db_session.refresh(job)
    assert job.criteria_version == initial + 1


def test_empty_job_gets_equal_weights(client, recruiter_headers, job, db_session):
    job.requirements.clear()
    db_session.commit()
    response = send(client, recruiter_headers, job, b"Python\nPostgreSQL")
    assert response.status_code == 201
    assert [r["weight"] for r in response.json()["requirements"]] == [0.5, 0.5]


def test_import_checks_access_and_limits(client, recruiter_headers, other_recruiter_headers, job):
    assert send(client, other_recruiter_headers, job, b"Python").status_code == 403
    assert send(client, recruiter_headers, job, b"Python", "x.pdf").status_code == 400
    assert send(client, recruiter_headers, job, b"a" * (100 * 1024 + 1)).status_code == 413


def test_invalid_line_does_not_partially_import(client, recruiter_headers, job, db_session):
    count, version = len(job.requirements), job.criteria_version
    assert send(client, recruiter_headers, job, b"Python\n" + b"a" * 4001).status_code == 422
    db_session.refresh(job)
    assert len(job.requirements) == count
    assert job.criteria_version == version
