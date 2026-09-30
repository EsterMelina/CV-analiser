from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Questionnaire(Base):
    __tablename__ = "questionnaires"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"
    __table_args__ = (UniqueConstraint("questionnaire_id", "number", name="uq_questionnaire_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    questionnaire_id: Mapped[int] = mapped_column(ForeignKey("questionnaires.id"))
    number: Mapped[int] = mapped_column()
    revision: Mapped[int] = mapped_column(default=1)
    criteria_version: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="draft")
    language: Mapped[str] = mapped_column(String(5), default="pt")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_version_id: Mapped[int | None] = mapped_column(ForeignKey("questionnaire_versions.id"), nullable=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("ai_executions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    questions: Mapped[list["Question"]] = relationship(cascade="all, delete-orphan", order_by="Question.position")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("version_id", "position", name="uq_question_position"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_versions.id"))
    position: Mapped[int] = mapped_column()
    content_json: Mapped[str] = mapped_column(Text)
