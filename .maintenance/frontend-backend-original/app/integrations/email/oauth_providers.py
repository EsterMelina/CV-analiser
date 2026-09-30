"""
Adaptadores para Gmail (Google Workspace) e Microsoft 365/Outlook via OAuth 2.0.

IMPORTANTE — estado desta implementação:
Estes adaptadores ficam prontos ao nível de INTERFACE (implementam
EmailProvider, para que o resto do sistema já funcione com qualquer um
dos três provedores de forma transparente), mas a troca de tokens OAuth
real requer:

  - Gmail: um Client ID/Secret registado na Google Cloud Console com o
    scope "https://www.googleapis.com/auth/gmail.readonly" e o pacote
    google-api-python-client + google-auth-oauthlib.
  - Outlook: um App Registration no Azure AD com o scope
    "Mail.Read" via Microsoft Graph API e o pacote msal.

Como estas credenciais pertencem à empresa que usa o sistema (cada
empresa regista a sua própria app OAuth), não é possível pré-configurá-las
aqui. O fluxo de autorização (ecrã "Conectar conta" da secção 10) deve
redirecionar para o consent screen do respetivo provedor e guardar o
access_token/refresh_token devolvidos (cifrados — ver app/core/crypto.py)
em EmailAccount.oauth_*_token_encrypted.

Uma vez obtido um access_token válido, ambos os provedores expõem APIs
REST (Gmail API / Microsoft Graph) que podem substituir o corpo dos
métodos abaixo sem alterar mais nada no sistema, graças à abstração
EmailProvider.
"""
from app.integrations.email.base import EmailProvider, FetchedMessage, EmailProviderError


class GmailEmailProvider(EmailProvider):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def test_connection(self) -> bool:
        raise EmailProviderError(
            "Integração Gmail requer configuração OAuth 2.0 da Google Cloud Console "
            "(Client ID/Secret) por parte da empresa. Ver docstring deste módulo."
        )

    def fetch_new_messages(self, since_uid: str | None = None, limit: int = 50) -> list[FetchedMessage]:
        raise EmailProviderError(
            "Integração Gmail requer configuração OAuth 2.0 da Google Cloud Console "
            "(Client ID/Secret) por parte da empresa. Ver docstring deste módulo."
        )


class OutlookEmailProvider(EmailProvider):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def test_connection(self) -> bool:
        raise EmailProviderError(
            "Integração Outlook/Microsoft 365 requer um App Registration no Azure AD "
            "por parte da empresa. Ver docstring deste módulo."
        )

    def fetch_new_messages(self, since_uid: str | None = None, limit: int = 50) -> list[FetchedMessage]:
        raise EmailProviderError(
            "Integração Outlook/Microsoft 365 requer um App Registration no Azure AD "
            "por parte da empresa. Ver docstring deste módulo."
        )
