"""
Sincroniza uma conta de e-mail: procura mensagens novas, identifica a
vaga, classifica anexos e injeta os CVs encontrados no MESMO pipeline
usado pelo upload manual (secção 32 — "pipeline unificado").
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application, Resume, ApplicationSource
from app.models.email_integration import (
    EmailAccount, EmailAccountStatus, EmailMessage, EmailAttachment, AttachmentClassification,
)
from app.models.processing_log import ProcessingLog, ProcessingSource, ProcessingStatus
from app.integrations.email.factory import get_provider_for_account
from app.integrations.email.base import EmailProviderError, FetchedMessage, FetchedAttachment

_JOB_CODE_RE = re.compile(r"[A-Z]{2,6}-\d{4}-\d+")
_CV_KEYWORDS = ["cv", "curriculo", "currículo", "resume"]
_CERTIFICATE_KEYWORDS = ["certificado", "certificate", "diploma"]
_COVER_LETTER_KEYWORDS = ["carta", "motivacao", "motivação", "cover letter", "apresentacao", "apresentação"]

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}


def _classify_attachment(filename: str) -> AttachmentClassification:
    lower = filename.lower()
    extension = Path(lower).suffix

    if extension not in ALLOWED_CV_EXTENSIONS:
        return AttachmentClassification.UNKNOWN
    if any(keyword in lower for keyword in _CV_KEYWORDS):
        return AttachmentClassification.CV
    if any(keyword in lower for keyword in _CERTIFICATE_KEYWORDS):
        return AttachmentClassification.CERTIFICATE
    if any(keyword in lower for keyword in _COVER_LETTER_KEYWORDS):
        return AttachmentClassification.COVER_LETTER
    return AttachmentClassification.UNKNOWN


def _identify_job(db: Session, company_id: int, subject: str | None, body: str | None) -> tuple[Job | None, float]:
    text = f"{subject or ''} {body or ''}"

    code_match = _JOB_CODE_RE.search(text)
    if code_match:
        job = db.query(Job).filter(Job.code == code_match.group(), Job.company_id == company_id).first()
        if job:
            return job, 1.0

    jobs = db.query(Job).filter(Job.company_id == company_id).all()
    lower_text = text.lower()
    for job in jobs:
        if job.title.lower() in lower_text:
            return job, 0.7

    return None, 0.0


def _extract_sender_email(sender_header: str | None) -> str:
    if not sender_header:
        return f"desconhecido-{uuid.uuid4().hex[:8]}@sem-email.local"
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", sender_header)
    return match.group() if match else sender_header.strip()


def _extract_sender_name(sender_header: str | None, fallback_email: str) -> str:
    if not sender_header:
        return fallback_email.split("@")[0]
    name_part = sender_header.split("<")[0].strip().strip('"')
    return name_part or fallback_email.split("@")[0]


def _find_or_create_candidate(db: Session, name: str, email_addr: str, company_id: int) -> Candidate:
    email_addr = email_addr.strip().lower()
    candidate = db.query(Candidate).filter(Candidate.email == email_addr, Candidate.company_id == company_id).first()
    if candidate:
        return candidate
    candidate = Candidate(name=name, email=email_addr, company_id=company_id)
    db.add(candidate)
    db.flush()
    return candidate


def _store_attachment_file(job_id: int, content: bytes, extension: str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR) / str(job_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid.uuid4().hex}{extension}"
    stored_path.write_bytes(content)
    return str(stored_path)


def _process_message(db: Session, account: EmailAccount, message: FetchedMessage) -> None:
    job, confidence = _identify_job(db, account.company_id, message.subject, message.body_text)

    email_message = EmailMessage(
        email_account_id=account.id,
        provider_message_id=message.provider_message_id,
        subject=message.subject,
        sender=message.sender,
        received_at=datetime.fromisoformat(message.received_at) if message.received_at else None,
        matched_job_id=job.id if job else None,
        match_confidence=confidence if job else None,
    )
    db.add(email_message)
    db.flush()

    account.messages_processed_count += 1

    classifications = [_classify_attachment(att.filename) for att in message.attachments]
    unknown_pdf_docx = [
        i for i, (att, c) in enumerate(zip(message.attachments, classifications))
        if c == AttachmentClassification.UNKNOWN and Path(att.filename.lower()).suffix in ALLOWED_CV_EXTENSIONS
    ]
    if len(unknown_pdf_docx) == 1 and not any(c == AttachmentClassification.CV for c in classifications):
        classifications[unknown_pdf_docx[0]] = AttachmentClassification.CV

    sender_email = _extract_sender_email(message.sender)
    sender_name = _extract_sender_name(message.sender, sender_email)

    if job is None:
        db.add(ProcessingLog(
            source=ProcessingSource.EMAIL, candidate_email=sender_email,
            document_name=message.subject, email_message_id=email_message.id,
            status=ProcessingStatus.SKIPPED,
            error_message="Candidatura não associada: não foi possível identificar a vaga com confiança suficiente.",
        ))
        db.commit()
        return

    for attachment, classification in zip(message.attachments, classifications):
        db_attachment = EmailAttachment(
            email_message_id=email_message.id, filename=attachment.filename, classification=classification,
        )
        db.add(db_attachment)
        db.flush()

        if classification != AttachmentClassification.CV:
            continue

        extension = Path(attachment.filename.lower()).suffix
        if extension not in ALLOWED_CV_EXTENSIONS:
            continue

        try:
            candidate = _find_or_create_candidate(db, sender_name, sender_email, account.company_id)
            application = Application(candidate_id=candidate.id, job_id=job.id, source=ApplicationSource.EMAIL)
            db.add(application)
            db.flush()

            stored_path = _store_attachment_file(job.id, attachment.content, extension)
            resume = Resume(
                application_id=application.id, original_filename=attachment.filename,
                stored_path=stored_path, content_type=attachment.content_type,
                file_size_bytes=len(attachment.content),
            )
            db.add(resume)
            db.flush()

            db_attachment.resume_id = resume.id
            account.cvs_found_count += 1

            db.add(ProcessingLog(
                source=ProcessingSource.EMAIL, candidate_email=sender_email,
                document_name=attachment.filename, application_id=application.id,
                email_message_id=email_message.id, status=ProcessingStatus.PROCESSED,
            ))
        except Exception as exc:  # nunca deixar um anexo com erro parar a sincronização toda
            account.errors_count += 1
            db.add(ProcessingLog(
                source=ProcessingSource.EMAIL, candidate_email=sender_email,
                document_name=attachment.filename, email_message_id=email_message.id,
                status=ProcessingStatus.ERROR, error_message=str(exc),
            ))

    email_message.processed = True
    db.commit()


def sync_account(db: Session, account: EmailAccount) -> EmailAccount:
    try:
        provider = get_provider_for_account(account)
        messages = provider.fetch_new_messages()

        for message in messages:
            _process_message(db, account, message)

        account.status = EmailAccountStatus.CONNECTED
        account.last_sync_at = datetime.now(timezone.utc)
        account.last_sync_error = None
        db.commit()
        db.refresh(account)
        return account

    except EmailProviderError as exc:
        account.status = EmailAccountStatus.ERROR
        account.last_sync_error = str(exc)
        account.last_sync_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(account)
        raise
