"""
Cifragem simétrica (Fernet) para credenciais sensíveis (password IMAP,
tokens OAuth) antes de serem guardadas na base de dados — secção 10 e 35
do prompt mestre ("nunca armazenar simplesmente a senha da conta de e-mail").

A chave é derivada de SECRET_KEY. Em produção, considerar um segredo
dedicado (ex: AWS KMS, Vault) em vez de reutilizar o SECRET_KEY da app.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plain_text: str) -> str:
    return _get_fernet().encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str | None:
    try:
        return _get_fernet().decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
