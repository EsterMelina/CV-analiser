from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.processing_log import ProcessingLog, ProcessingSource, ProcessingStatus
from app.models.application import Application
from app.models.job import Job
from app.models.email_integration import EmailMessage, EmailAccount
from app.models.user import User, UserRole
from app.schemas.processing_log import ProcessingLogRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/processing-logs", tags=["Histórico de Processamento"])


@router.get("", response_model=list[ProcessingLogRead])
def list_processing_logs(
    status_filter: ProcessingStatus | None = Query(default=None, alias="status"),
    source: ProcessingSource | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcessingLog)

    if current_user.role != UserRole.ADMIN:
        # Restringe aos logs relacionados com candidaturas ou contas de e-mail
        # da empresa do recrutador autenticado.
        company_application_ids = (
            db.query(Application.id)
            .join(Job, Application.job_id == Job.id)
            .filter(Job.company_id == current_user.company_id)
            .scalar_subquery()
        )
        company_message_ids = (
            db.query(EmailMessage.id)
            .join(EmailAccount, EmailMessage.email_account_id == EmailAccount.id)
            .filter(EmailAccount.company_id == current_user.company_id)
            .scalar_subquery()
        )
        query = query.filter(
            or_(
                ProcessingLog.application_id.in_(company_application_ids),
                ProcessingLog.email_message_id.in_(company_message_ids),
            )
        )

    if status_filter:
        query = query.filter(ProcessingLog.status == status_filter)
    if source:
        query = query.filter(ProcessingLog.source == source)

    return query.order_by(ProcessingLog.created_at.desc()).limit(limit).all()
