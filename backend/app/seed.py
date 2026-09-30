"""
Popula a base de dados com dados de exemplo para desenvolvimento/demonstração.

Uso:
    python -m app.seed
"""
from app.core.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.job import Job, JobStatus, JobType, JobModality
from app.models.job_requirement import JobRequirement, RequirementCategory, RequirementLevel


def run():
    from app.core.config import settings
    from app.migrate import assert_current
    if settings.ENVIRONMENT != "development":
        raise RuntimeError("Dados de demonstração só são permitidos em desenvolvimento.")
    with engine.connect() as connection:
        assert_current(connection)
    db = SessionLocal()
    try:
        # --- Administrador global ---
        admin = db.query(User).filter(User.email == "admin@sistema.co.mz").first()
        if not admin:
            admin = User(
                name="Administrador do Sistema",
                email="admin@sistema.co.mz",
                password_hash=hash_password("Admin@123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)

        # --- Empresa de exemplo ---
        company = db.query(Company).filter(Company.name == "TechMoz Solutions").first()
        if not company:
            company = Company(name="TechMoz Solutions", email_domain="techmoz.co.mz")
            db.add(company)
            db.flush()

        # --- Recrutador de exemplo ---
        recruiter = db.query(User).filter(User.email == "recrutamento@techmoz.co.mz").first()
        if not recruiter:
            recruiter = User(
                name="Recrutadora TechMoz",
                email="recrutamento@techmoz.co.mz",
                password_hash=hash_password("Recruta@123"),
                role=UserRole.RECRUITER,
                company_id=company.id,
            )
            db.add(recruiter)
            db.flush()

        # --- Vaga de exemplo (baseada na secção 2 do prompt mestre) ---
        job = db.query(Job).filter(Job.code == "VAG-2026-014").first()
        if not job:
            job = Job(
                company_id=company.id,
                created_by_id=recruiter.id,
                title="Desenvolvedor Backend",
                code="VAG-2026-014",
                description="Desenvolvimento e manutenção de APIs REST em PHP/Laravel.",
                department="Tecnologia",
                location="Maputo, Moçambique",
                job_type=JobType.FULL_TIME,
                modality=JobModality.HYBRID,
                min_experience_years=2,
                education_level="Licenciatura em Informática ou área relacionada",
                status=JobStatus.PUBLISHED,
            )
            db.add(job)
            db.flush()

            requirements = [
                ("PHP", RequirementCategory.TECHNICAL_SKILL, 0.20, True),
                ("Laravel", RequirementCategory.TECHNOLOGY, 0.20, True),
                ("PostgreSQL", RequirementCategory.TECHNOLOGY, 0.15, True),
                ("REST API", RequirementCategory.TECHNICAL_SKILL, 0.15, True),
                ("Git", RequirementCategory.TOOL, 0.10, True),
                ("Docker", RequirementCategory.TOOL, 0.10, False),
                ("Experiência mínima de 2 anos", RequirementCategory.EXPERIENCE, 0.10, True),
            ]
            for name, category, weight, mandatory in requirements:
                db.add(JobRequirement(
                    job_id=job.id,
                    name=name,
                    category=category,
                    weight=weight,
                    expected_level=RequirementLevel.INTERMEDIATE,
                    is_mandatory=mandatory,
                ))

        db.commit()
        print("Seed concluído com sucesso.")
        print("Admin:      admin@sistema.co.mz / Admin@123")
        print("Recrutador: recrutamento@techmoz.co.mz / Recruta@123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
