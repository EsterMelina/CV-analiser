"""
Configuração partilhada dos testes.

Usa SQLite em memória (via StaticPool, para que todas as ligações da mesma
sessão de testes partilhem o mesmo estado) em vez do PostgreSQL de produção.
Isto permite correr a suite de testes sem precisar de um servidor de BD.

Nota: alguns tipos específicos do PostgreSQL não são usados nos modelos
(ver app/models/*), pelo que a compatibilidade com SQLite é garantida.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.company import Company
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Cria todas as tabelas antes de cada teste e limpa tudo no final (isolamento total)."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def company(db_session):
    company = Company(name="TechMoz Solutions", email_domain="techmoz.co.mz")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


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


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    """Evita que os testes escrevam ficheiros na pasta uploads/ real do projeto."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    yield tmp_path


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
