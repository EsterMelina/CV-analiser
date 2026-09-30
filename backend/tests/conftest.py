"""Testes offline: configuração controlada antes de importar a aplicação.

O mesmo engine SQLite em memória serve o arranque, SessionLocal e os pedidos.
A suite bloqueia rede e carregamento de modelos; IMAP deve ser simulado.
"""
import os
import socket
import tempfile
import threading
from pathlib import Path

import pytest
import sqlalchemy

# Executado durante a recolha, antes de importar app e antes das fixtures.
# Nunca herdar DATABASE_URL, segredos, uploads ou .env do ambiente operacional.
_bootstrap = pytest.MonkeyPatch()
_test_directory = tempfile.TemporaryDirectory(prefix="recruiter-tests-")
for key, value in {
    "ENVIRONMENT": "test",
    "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "isolated-test-secret-not-for-deployment",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "MAX_UPLOAD_SIZE_MB": "10",
    "CORS_ORIGINS": "http://testserver",
    "UPLOAD_DIR": _test_directory.name,
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HOME": str(Path(_test_directory.name) / "models"),
    "AI_PROVIDER": "mock",
    "AI_REAL_ENABLED": "false",
    "AI_DATA_APPROVED": "false",
    "AI_API_KEY": "",
    "AI_ENDPOINT": "",
    "LEGACY_ANALYSIS_ENABLED": "true",
}.items():
    _bootstrap.setenv(key, value)


class ExternalAccessBlocked(AssertionError):
    """Uma dependência real foi usada num teste que deveria ser offline."""


def _blocked(*args, **kwargs):
    raise ExternalAccessBlocked("Rede externa bloqueada nos testes; use um fake.")


_original_connect = socket.socket.connect
_original_socketpair = socket.socketpair
_socketpair_context = threading.local()


def _guarded_connect(sock, address):
    # Windows implementa socketpair via TCP loopback para o wakeup do asyncio.
    # Autorizar apenas dentro de socketpair, nesta thread; nunca localhost geral.
    if (
        getattr(_socketpair_context, "active", False)
        and isinstance(address, tuple)
        and address[0] in {"127.0.0.1", "::1"}
    ):
        return _original_connect(sock, address)
    return _blocked()


def _local_socketpair(*args, **kwargs):
    previous = getattr(_socketpair_context, "active", False)
    _socketpair_context.active = True
    try:
        return _original_socketpair(*args, **kwargs)
    finally:
        _socketpair_context.active = previous


_bootstrap.setattr(socket, "socketpair", _local_socketpair)
_bootstrap.setattr(socket.socket, "connect", _guarded_connect)
_bootstrap.setattr(socket.socket, "connect_ex", _blocked)
_bootstrap.setattr(socket.socket, "sendto", _blocked)
_bootstrap.setattr(socket, "create_connection", _blocked)
_bootstrap.setattr(socket, "getaddrinfo", _blocked)
_bootstrap.setattr(socket, "gethostbyname", _blocked)
_bootstrap.setattr(socket, "gethostbyname_ex", _blocked)

_original_create_engine = sqlalchemy.create_engine


def _test_only_engine(url, *args, **kwargs):
    parsed = sqlalchemy.engine.make_url(url)
    if parsed.drivername != "sqlite" or parsed.database != ":memory:":
        raise ExternalAccessBlocked("A suite só permite SQLite em memória.")
    return _original_create_engine(url, *args, **kwargs)


_bootstrap.setattr(sqlalchemy, "create_engine", _test_only_engine)

# Imports intencionalmente depois da configuração e dos bloqueios.
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.core.security import hash_password
from app.main import app
from app.models.company import Company
from app.models.user import User, UserRole
from app.services import embeddings
from fastapi.testclient import TestClient

_offline_backend = embeddings._TfidfBackend()


def _offline_embeddings():
    return _offline_backend


# Fixar o motor, inclusive durante a recolha: nunca tentar carregar o transformer.
_bootstrap.setattr(embeddings, "_get_backend", _offline_embeddings)
_bootstrap.setattr(embeddings, "_SentenceTransformerBackend", _blocked)


def pytest_unconfigure(config):
    app.dependency_overrides.clear()
    engine.dispose()
    _bootstrap.undo()
    _test_directory.cleanup()


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def company(db_session):
    company = Company(name="TechMoz Solutions", email_domain="techmoz.co.mz")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def other_company(db_session):
    company = Company(name="Empresa Fictícia B", email_domain="empresa-b.example.com")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def other_recruiter_user(db_session, other_company):
    user = User(
        name="Recrutador Fictício B", email="recruiter@empresa-b.example.com",
        password_hash=hash_password("TesteB@123"), role=UserRole.RECRUITER,
        company_id=other_company.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_recruiter_headers(client, other_recruiter_user):
    return auth_headers(client, other_recruiter_user.email, "TesteB@123")


@pytest.fixture
def other_job(db_session, other_company, other_recruiter_user):
    from app.models.job import Job, JobStatus, JobType, JobModality

    job = Job(
        company_id=other_company.id, created_by_id=other_recruiter_user.id,
        title="Gestor de Armazém", code="FICTICIA-B-001",
        description="Gestão de inventário e equipa de armazém.",
        job_type=JobType.FULL_TIME, modality=JobModality.ON_SITE,
        status=JobStatus.DRAFT,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def admin_user(db_session):
    user = User(
        name="Administrador",
        email="admin@sistema.co.mz",
        password_hash=hash_password("Admin@123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def recruiter_user(db_session, company):
    user = User(
        name="Recrutadora TechMoz",
        email="recrutamento@techmoz.co.mz",
        password_hash=hash_password("Recruta@123"),
        role=UserRole.RECRUITER,
        company_id=company.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recruiter_headers(client, recruiter_user):
    return auth_headers(client, "recrutamento@techmoz.co.mz", "Recruta@123")


@pytest.fixture
def admin_headers(client, admin_user):
    return auth_headers(client, "admin@sistema.co.mz", "Admin@123")


@pytest.fixture
def job(db_session, company, recruiter_user):
    """Vaga de exemplo (baseada na secção 2 do prompt mestre), já com requisitos."""
    from app.models.job import Job, JobStatus, JobType, JobModality
    from app.models.job_requirement import JobRequirement, RequirementCategory

    job = Job(
        company_id=company.id,
        created_by_id=recruiter_user.id,
        title="Desenvolvedor Backend",
        code="VAG-2026-014",
        description="Desenvolvimento e manutenção de APIs REST em PHP/Laravel.",
        department="Tecnologia",
        location="Maputo, Moçambique",
        job_type=JobType.FULL_TIME,
        modality=JobModality.HYBRID,
        min_experience_years=2,
        education_level="Licenciatura em Informática",
        status=JobStatus.DRAFT,
    )
    db_session.add(job)
    db_session.flush()

    requirements = [
        ("PHP", RequirementCategory.TECHNICAL_SKILL, 0.25, True),
        ("Laravel", RequirementCategory.TECHNOLOGY, 0.25, True),
        ("PostgreSQL", RequirementCategory.TECHNOLOGY, 0.20, True),
        ("Git", RequirementCategory.TOOL, 0.10, False),
        ("Experiência mínima de 2 anos", RequirementCategory.EXPERIENCE, 0.20, True),
    ]
    for name, category, weight, mandatory in requirements:
        db_session.add(JobRequirement(
            job_id=job.id, name=name, category=category, weight=weight, is_mandatory=mandatory,
        ))
    db_session.commit()
    db_session.refresh(job)
    return job
