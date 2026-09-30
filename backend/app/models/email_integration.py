import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailProviderType(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    IMAP = "imap"


class EmailAccountStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class EmailAccount(Base):
    """
    Conta de e-mail corporativo ligada por uma empresa para receber
    candidaturas (secções 9-10). Credenciais nunca guardadas em texto
    simples — ver app/core/crypto.py.
    """
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)

    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[EmailProviderType] = mapped_column(Enum(EmailProviderType), nullable=False)
    status: Mapped[EmailAccountStatus] = mapped_column(Enum(EmailAccountStatus), default=EmailAccountStatus.PENDING)

    # OAuth 2.0 (Gmail / Outlook) — tokens cifrados em repouso
    oauth_access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # IMAP genérico — password cifrada em repouso
    imap_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imap_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imap_use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    imap_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    sync_frequency_minutes: Mapped[int] = mapped_column(Integer, default=15)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    messages_processed_count: Mapped[int] = mapped_column(Integer, default=0)
    cvs_found_count: Mapped[int] = mapped_column(Integer, default=0)
    cvs_analyzed_count: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), nullable=False)

    provider_message_id: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    matched_job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(nullable=True)  # 0-1

    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attachments: Mapped[list["EmailAttachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class AttachmentClassification(str, enum.Enum):
    CV = "cv"
    CERTIFICATE = "certificate"
    COVER_LETTER = "cover_letter"
    ADDITIONAL_DOCUMENT = "additional_document"
    UNKNOWN = "unknown"


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_message_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    classification: Mapped[AttachmentClassification] = mapped_column(
        Enum(AttachmentClassification), default=AttachmentClassification.UNKNOWN
    )
    # Preenchido quando classification == CV e o documento entra no pipeline de análise
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)

    message: Mapped["EmailMessage"] = relationship(back_populates="attachments")
