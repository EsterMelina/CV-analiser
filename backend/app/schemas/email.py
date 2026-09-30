from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from app.models.email_integration import EmailProviderType, EmailAccountStatus


class EmailAccountConnect(BaseModel):
    """
    Payload para ligar uma conta de e-mail corporativa (secção 10).
    - provider=imap: exige imap_host/imap_port/imap_password.
    - provider=gmail/outlook: exige oauth_access_token (obtido no ecrã de
      consentimento OAuth do respetivo provedor; ver app/integrations/email/oauth_providers.py
      para o que falta configurar antes disto funcionar de ponta a ponta).
    """
    email_address: EmailStr
    provider: EmailProviderType

    imap_host: str | None = None
    imap_port: int | None = 993
    imap_use_ssl: bool = True
    imap_password: str | None = None

    oauth_access_token: str | None = None
    oauth_refresh_token: str | None = None

    @model_validator(mode="after")
    def validate_provider_fields(self):
        if self.provider == EmailProviderType.IMAP:
            if not self.imap_host or not self.imap_password:
                raise ValueError("Contas IMAP exigem imap_host e imap_password")
        else:
            if not self.oauth_access_token:
                raise ValueError("Contas Gmail/Outlook exigem oauth_access_token")
        return self


class EmailAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email_address: str
    provider: EmailProviderType
    status: EmailAccountStatus
    sync_frequency_minutes: int
    last_sync_at: datetime | None = None
    last_sync_error: str | None = None
    messages_processed_count: int
    cvs_found_count: int
    cvs_analyzed_count: int
    errors_count: int
    created_at: datetime
