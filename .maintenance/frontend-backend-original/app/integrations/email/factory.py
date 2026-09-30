from app.core.crypto import decrypt_secret
from app.models.email_integration import EmailAccount, EmailProviderType
from app.integrations.email.base import EmailProvider, EmailProviderError
from app.integrations.email.imap_provider import ImapEmailProvider
from app.integrations.email.oauth_providers import GmailEmailProvider, OutlookEmailProvider


def get_provider_for_account(account: EmailAccount) -> EmailProvider:
    if account.provider == EmailProviderType.IMAP:
        if not account.imap_host or not account.imap_password_encrypted:
            raise EmailProviderError("Conta IMAP sem configuração completa (host/porta/password)")
        password = decrypt_secret(account.imap_password_encrypted)
        if password is None:
            raise EmailProviderError("Não foi possível decifrar a password IMAP guardada")
        return ImapEmailProvider(
            host=account.imap_host,
            port=account.imap_port or 993,
            username=account.email_address,
            password=password,
            use_ssl=account.imap_use_ssl,
        )

    if account.provider == EmailProviderType.GMAIL:
        token = decrypt_secret(account.oauth_access_token_encrypted or "")
        return GmailEmailProvider(access_token=token or "")

    if account.provider == EmailProviderType.OUTLOOK:
        token = decrypt_secret(account.oauth_access_token_encrypted or "")
        return OutlookEmailProvider(access_token=token or "")

    raise EmailProviderError(f"Provedor desconhecido: {account.provider}")
