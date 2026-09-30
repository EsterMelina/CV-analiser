"""
Adaptador IMAP genérico. Funciona com qualquer servidor IMAP (incluindo
Gmail/Outlook configurados com "acesso de app menos seguro"/app password),
usando apenas imaplib e email da biblioteca padrão — não requer nenhuma
dependência externa nem acesso à internet para "instalar" nada.

Nota de segurança: a password nunca é guardada em texto simples (ver
app/core/crypto.py); aqui só é usada em memória para autenticar.
"""
import email
import imaplib
from email.header import decode_header
from email.utils import parsedate_to_datetime

from app.integrations.email.base import EmailProvider, FetchedMessage, FetchedAttachment, EmailProviderError


def _decode(value: str | None) -> str | None:
    if not value:
        return None
    parts = decode_header(value)
    decoded = ""
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded += text.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


class ImapEmailProvider(EmailProvider):
    def __init__(self, host: str, port: int, username: str, password: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    def _connect(self) -> imaplib.IMAP4:
        try:
            conn = imaplib.IMAP4_SSL(self.host, self.port) if self.use_ssl else imaplib.IMAP4(self.host, self.port)
            conn.login(self.username, self.password)
            return conn
        except (imaplib.IMAP4.error, OSError) as exc:
            raise EmailProviderError(f"Falha ao ligar ao servidor IMAP: {exc}") from exc

    def test_connection(self) -> bool:
        try:
            conn = self._connect()
            conn.logout()
            return True
        except EmailProviderError:
            return False

    def fetch_new_messages(self, since_uid: str | None = None, limit: int = 50) -> list[FetchedMessage]:
        conn = self._connect()
        try:
            conn.select("INBOX")
            # UNSEEN = apenas mensagens ainda não lidas. Numa evolução futura,
            # usar UID SEARCH com since_uid para evitar reprocessar mensagens.
            status, data = conn.search(None, "UNSEEN")
            if status != "OK":
                raise EmailProviderError("Falha ao pesquisar mensagens no IMAP")

            message_ids = data[0].split()[-limit:]
            results: list[FetchedMessage] = []

            for msg_id in message_ids:
                status, msg_data = conn.fetch(msg_id, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                parsed = email.message_from_bytes(raw_email)

                subject = _decode(parsed.get("Subject"))
                sender = _decode(parsed.get("From"))
                date_header = parsed.get("Date")
                received_at = None
                if date_header:
                    try:
                        received_at = parsedate_to_datetime(date_header).isoformat()
                    except (TypeError, ValueError):
                        received_at = None

                body_text = ""
                attachments: list[FetchedAttachment] = []

                if parsed.is_multipart():
                    for part in parsed.walk():
                        content_disposition = str(part.get("Content-Disposition") or "")
                        content_type = part.get_content_type()

                        if "attachment" in content_disposition or part.get_filename():
                            filename = _decode(part.get_filename())
                            payload = part.get_payload(decode=True)
                            if filename and payload:
                                attachments.append(FetchedAttachment(
                                    filename=filename, content=payload, content_type=content_type,
                                ))
                        elif content_type == "text/plain" and not body_text:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or "utf-8"
                                body_text = payload.decode(charset, errors="ignore")
                else:
                    payload = parsed.get_payload(decode=True)
                    if payload:
                        charset = parsed.get_content_charset() or "utf-8"
                        body_text = payload.decode(charset, errors="ignore")

                results.append(FetchedMessage(
                    provider_message_id=msg_id.decode(),
                    subject=subject,
                    sender=sender,
                    received_at=received_at,
                    body_text=body_text,
                    attachments=attachments,
                ))

            return results
        finally:
            try:
                conn.logout()
            except Exception:
                pass
