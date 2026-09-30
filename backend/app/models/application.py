import enum
from datetime import datetime

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApplicationSource(str, enum.Enum):
    UPLOAD = "upload"
    EMAIL = "email"


class ApplicationStatus(str, enum.Enum):
    RECEIVED = "received"
    IN_ANALYSIS = "in_analysis"
    ANALYZED = "analyzed"
    RECOMMENDED = "recommended"
    IN_EVALUATION = "in_evaluation"
    INTERVIEW_SELECTED = "interview_selected"
    INTERVIEWED = "interviewed"
    REJECTED = "rejected"
    HIRED = "hired"


class Application(Base):
    """
    Representa a candidatura de um Candidate a um Job específico.
    O score/matching (fase de IA) será calculado sobre esta entidade numa fase posterior.
    """
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)

    source: Mapped[ApplicationSource] = mapped_column(Enum(ApplicationSource), default=ApplicationSource.UPLOAD)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.RECEIVED)
    analysis_status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending")

    # Preenchido pelo motor de scoring (app/services/analysis_service.py). O
    # detalhe completo (breakdown por requisito, etiqueta de recomendação,
    # requisitos obrigatórios em falta) fica em CandidateMatch — este campo
    # existe apenas para ordenar/filtrar rapidamente sem juntar tabelas.
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="applications")
    job: Mapped["Job"] = relationship(back_populates="applications")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    feedback: Mapped["RecruiterFeedback"] = relationship(
        back_populates="application", cascade="all, delete-orphan", uselist=False
    )
    match_result: Mapped["CandidateMatch"] = relationship(
        back_populates="application", cascade="all, delete-orphan", uselist=False
    )


class Resume(Base):
    """
    Ficheiro de CV associado a uma candidatura.
    A extração de texto/NLP será implementada na fase de IA (secções 14-19 do prompt mestre).
    """
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(default=1, server_default="1")

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # preenchido na extração (fase IA)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="resumes")
