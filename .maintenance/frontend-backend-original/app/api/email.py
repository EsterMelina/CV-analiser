from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.crypto import encrypt_secret
from app.models.email_integration import EmailAccount, EmailAccountStatus, EmailProviderType
from app.models.user import User
from app.schemas.email import EmailAccountConnect, EmailAccountRead
from app.api.deps import get_current_user, require_recruiter
from app.integrations.email.factory import get_provider_for_account
from app.integrations.email.base import EmailProviderError
from app.services.email_sync_service import sync_account

router = APIRouter(prefix="/api/email", tags=["Integração de E-mail"])


def _get_company_account(db: Session, company_id: int) -> EmailAccount | None:
    return db.query(EmailAccount).filter(EmailAccount.company_id == company_id).first()


@router.post("/connect", response_model=EmailAccountRead, dependencies=[Depends(require_recruiter)])
def connect_email_account(
    payload: EmailAccountConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liga (ou reconfigura) a conta de e-mail corporativo da empresa do
    recrutador autenticado. Nunca guarda credenciais em texto simples
    (secção 10) — tudo passa por app.core.crypto antes de chegar à BD.
    """
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilizador sem empresa associada")

    account = _get_company_account(db, current_user.company_id)
    if account is None:
        account = EmailAccount(company_id=current_user.company_id, email_address=payload.email_address, provider=payload.provider)
        db.add(account)
    else:
        account.email_address = payload.email_address
        account.provider = payload.provider

    if payload.provider == EmailProviderType.IMAP:
        account.imap_host = payload.imap_host
        account.imap_port = payload.imap_port
        account.imap_use_ssl = payload.imap_use_ssl
        account.imap_password_encrypted = encrypt_secret(payload.imap_password)
    else:
        account.oauth_access_token_encrypted = encrypt_secret(payload.oauth_access_token)
        if payload.oauth_refresh_token:
            account.oauth_refresh_token_encrypted = encrypt_secret(payload.oauth_refresh_token)

    db.flush()

    # Testa a ligação imediatamente para dar feedback claro no ecrã de configuração.
    try:
        provider = get_provider_for_account(account)
        if provider.test_connection():
            account.status = EmailAccountStatus.CONNECTED
            account.last_sync_error = None
        else:
            account.status = EmailAccountStatus.ERROR
            account.last_sync_error = "Falha ao autenticar com as credenciais fornecidas"
    except EmailProviderError as exc:
        account.status = EmailAccountStatus.ERROR
        account.last_sync_error = str(exc)

    db.commit()
    db.refresh(account)
    return account


@router.get("/status", response_model=EmailAccountRead)
def get_email_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilizador sem empresa associada")

    account = _get_company_account(db, current_user.company_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma conta de e-mail ligada")
    return account


@router.post("/sync", response_model=EmailAccountRead, dependencies=[Depends(require_recruiter)])
def trigger_sync(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Sincronização manual (secção 30). Numa fase de escalabilidade (secção 40),
    isto deve passar a ser acionado periodicamente por uma fila de tarefas
    (ex: Celery/RQ) em vez de um pedido HTTP síncrono.
    """
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilizador sem empresa associada")

    account = _get_company_account(db, current_user.company_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma conta de e-mail ligada")

    try:
        return sync_account(db, account)
    except EmailProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_recruiter)])
def disconnect_email_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = _get_company_account(db, current_user.company_id)
    if account:
        account.status = EmailAccountStatus.DISCONNECTED
        db.commit()
