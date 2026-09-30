from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Candidate(Base):
    """
    Representa uma PESSOA candidata, independentemente da vaga.
    Um mesmo candidato pode ter várias Applications (candidaturas) a vagas diferentes.
    A deduplicação (secção 13 do prompt mestre) usa email/telefone como chave principal.
    """
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    applications: Mapped[list["Application"]] = relationship(back_populates="candidate")

    # Perfil estruturado extraído do(s) CV(s) (secção 14). Um candidato pode
    # ter submetido vários CVs ao longo do tempo; estas entidades guardam a
    # versão mais recentemente extraída para reutilização entre candidaturas.
    education: Mapped[list["CandidateEducation"]] = relationship(cascade="all, delete-orphan")
    experience: Mapped[list["CandidateExperience"]] = relationship(cascade="all, delete-orphan")
    skills: Mapped[list["CandidateSkill"]] = relationship(cascade="all, delete-orphan")
    certifications: Mapped[list["CandidateCertification"]] = relationship(cascade="all, delete-orphan")
    languages: Mapped[list["CandidateLanguage"]] = relationship(cascade="all, delete-orphan")
    projects: Mapped[list["CandidateProject"]] = relationship(cascade="all, delete-orphan")
