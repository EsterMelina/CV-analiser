"""
Camada de abstração para provedores de e-mail (secção 9 do prompt mestre:
"criar uma camada de abstração para que a aplicação não fique dependente
de um único fornecedor").

Qualquer provedor (Gmail, Outlook, IMAP genérico) implementa a mesma
interface EmailProvider, para que o resto da aplicação (email_sync_service)
seja completamente agnóstico da origem.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FetchedAttachment:
    filename: str
    content: bytes
    content_type: str | None = None


@dataclass
class FetchedMessage:
    provider_message_id: str
    subject: str | None
    sender: str | None
    received_at: str | None  # ISO 8601
    body_text: str
    attachments: list[FetchedAttachment] = field(default_factory=list)


class EmailProvider(ABC):
    """Interface comum que qualquer adaptador de e-mail deve implementar."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Verifica se as credenciais/tokens são válidos."""
        raise NotImplementedError

    @abstractmethod
    def fetch_new_messages(self, since_uid: str | None = None, limit: int = 50) -> list[FetchedMessage]:
        """Devolve mensagens novas (não processadas ainda) da caixa de entrada."""
        raise NotImplementedError


class EmailProviderError(Exception):
    pass
