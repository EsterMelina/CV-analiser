import enum

from sqlalchemy import String, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RequirementCategory(str, enum.Enum):
    EDUCATION = "education"
    EXPERIENCE = "experience"
    TECHNICAL_SKILL = "technical_skill"
    TECHNOLOGY = "technology"
    TOOL = "tool"
    LANGUAGE = "language"
    CERTIFICATION = "certification"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class RequirementLevel(str, enum.Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[RequirementCategory] = mapped_column(
        Enum(RequirementCategory), default=RequirementCategory.OTHER
    )
    # Peso relativo do requisito no cálculo do score final (0.0 - 1.0).
    # A soma dos pesos de uma vaga deve ser validada a somar ~1.0 na camada de serviço.
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    expected_level: Mapped[RequirementLevel] = mapped_column(
        Enum(RequirementLevel), default=RequirementLevel.INTERMEDIATE
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    job: Mapped["Job"] = relationship(back_populates="requirements")
