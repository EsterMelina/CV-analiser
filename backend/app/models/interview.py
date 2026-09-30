import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewResult(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    scheduled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interviewers: Mapped[str | None] = mapped_column(String(500), nullable=True)  # nomes separados por vírgula
    location_or_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[InterviewResult] = mapped_column(Enum(InterviewResult), default=InterviewResult.SCHEDULED)
    result_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="interviews")


class RecruiterRating(str, enum.Enum):
    VERY_SUITABLE = "very_suitable"
    SUITABLE = "suitable"
    PARTIALLY_SUITABLE = "partially_suitable"
    NOT_SUITABLE = "not_suitable"


class RecruiterFeedback(Base):
    """
    Feedback estruturado do recrutador (secção 26), guardado para
    futura avaliação/treino de um modelo supervisionado (secção 24/36).
    """
    __tablename__ = "recruiter_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True, nullable=False)
    submitted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    system_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_for_interview: Mapped[bool] = mapped_column(Boolean, default=False)
    hired: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[RecruiterRating | None] = mapped_column(Enum(RecruiterRating), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application: Mapped["Application"] = relationship(back_populates="feedback")
