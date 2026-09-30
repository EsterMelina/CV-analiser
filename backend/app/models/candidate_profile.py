"""
Entidades que guardam a informação estruturada extraída do CV
(secção 14/27 do prompt mestre). Preenchidas pelo pipeline de
extração/NLP em app/services/nlp_extraction.py.
"""
from datetime import date, datetime

from sqlalchemy import String, Text, Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # null = emprego atual
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # normalizado (ex: "python")
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # technical_skill/technology/tool/...
    # Excerto do CV que evidencia a competência (para explicabilidade, secção 25)
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 0-1: confiança da extração (regex/keyword=1.0, semântico/fuzzy < 1.0)
    confidence: Mapped[float] = mapped_column(default=1.0)


class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class CandidateLanguage(Base):
    __tablename__ = "candidate_languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)  # básico/intermédio/avançado/nativo


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class CandidateMatch(Base):
    """
    Resultado do matching entre uma Application e a respetiva Job:
    guarda o breakdown explicável (secção 25) usado para gerar o score.
    """
    __tablename__ = "candidate_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    criteria_version: Mapped[int] = mapped_column(default=1, server_default="1")
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True, nullable=False)

    overall_score: Mapped[float] = mapped_column(nullable=False)  # 0-100
    recommendation_label: Mapped[str] = mapped_column(String(50), nullable=False)
    # JSON serializado: lista de {requirement, met, mandatory, contribution, evidence}
    breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    mandatory_missing_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="match_result")
