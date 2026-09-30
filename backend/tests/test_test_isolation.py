"""Garantias da infraestrutura de testes, sem recursos operacionais."""
import socket
from pathlib import Path

import pytest
import sqlalchemy

from app.core.config import get_settings, settings
from app.core.database import SessionLocal, engine
from app.services import embeddings


def test_settings_ignore_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DB_HOST=operational.invalid\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DB_HOST", raising=False)
    isolated = get_settings.__wrapped__()
    assert isolated.DB_HOST == "127.0.0.1"
    assert isolated.sqlalchemy_database_url == "sqlite:///:memory:"


def test_startup_uses_test_engine(client, isolated_upload_dir):
    assert client.get("/api/health").json()["environment"] == "test"
    assert str(engine.url) == "sqlite:///:memory:"
    assert SessionLocal.kw["bind"] is engine
    assert Path(settings.UPLOAD_DIR) == isolated_upload_dir
    assert isolated_upload_dir != Path(__file__).resolve().parents[1] / "uploads"


@pytest.mark.parametrize("url", ["sqlite:///operational.db", "postgresql://localhost/operational"])
def test_external_database_engine_is_blocked(url):
    with pytest.raises(AssertionError, match="SQLite em memória"):
        sqlalchemy.create_engine(url)


def test_network_is_blocked():
    with pytest.raises(AssertionError, match="Rede externa"):
        socket.getaddrinfo("example.com", 443)
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match="Rede externa"):
            connection.connect(("127.0.0.1", 143))


def test_models_are_offline():
    assert isinstance(embeddings._get_backend(), embeddings._TfidfBackend)
    with pytest.raises(AssertionError):
        embeddings._SentenceTransformerBackend()
    assert embeddings.semantic_similarity("python", "python") == pytest.approx(1.0)


def test_two_company_fixtures(client, job, other_job, recruiter_headers, other_recruiter_headers):
    for headers, own, foreign in (
        (recruiter_headers, job, other_job),
        (other_recruiter_headers, other_job, job),
    ):
        response = client.get("/api/jobs", headers=headers)
        assert response.status_code == 200
        assert [entry["id"] for entry in response.json()] == [own.id]
        assert client.get(f"/api/jobs/{foreign.id}", headers=headers).status_code == 403
