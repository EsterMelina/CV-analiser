import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcessingSource(str, enum.Enum):
    UPLOAD = "upload"
    EMAIL = "email"


class ProcessingStatus(str, enum.Enum):
    PROCESSED = "processed"
    ERROR = "error"
    SKIPPED = "skipped"


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[ProcessingSource] = mapped_column(Enum(ProcessingSource), nullable=False)

    candidate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    email_message_id: Mapped[int | None] = mapped_column(ForeignKey("email_messages.id"), nullable=True)

    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
