from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    criteria_version: Mapped[int] = mapped_column()
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("ai_executions.id"), unique=True, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[str] = mapped_column(String(100))
    policy_version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    score: Mapped[float | None] = mapped_column(nullable=True)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    evidence: Mapped[list["AnalysisEvidence"]] = relationship(cascade="all, delete-orphan", order_by="AnalysisEvidence.id")


class AnalysisEvidence(Base):
    __tablename__ = "analysis_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"))
    requirement_id: Mapped[int] = mapped_column()  # identifier in the frozen criteria, may later be removed
    state: Mapped[str] = mapped_column(String(30))
    content_json: Mapped[str] = mapped_column(Text)
