import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken


@dataclass
class EncryptionResult:
    value: str
    algorithm: str


class CryptoService:
    """Encrypts sensitive values and supports a deterministic fallback for legacy environments."""

    def __init__(self, secret: str | None = None):
        self._secret = secret or os.environ.get("ENCRYPTION_SECRET") or os.environ.get("JWT_SECRET", "lifeos_default_secret")
        self._allow_legacy_fallback = os.environ.get("ALLOW_LEGACY_TOKEN_DECRYPT", "false").lower() == "true"
        key = base64.urlsafe_b64encode(hashlib.sha256(self._secret.encode("utf-8")).digest())
        self._fernet = Fernet(key)

    def encrypt(self, plain_text: str) -> EncryptionResult:
        token = self._fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")
        return EncryptionResult(value=f"v1:{token}", algorithm="fernet")

    def decrypt(self, encrypted_text: str) -> str:
        if encrypted_text.startswith("v1:"):
            token = encrypted_text.split("v1:", 1)[1]
            try:
                return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except InvalidToken as exc:
                raise ValueError("Invalid encrypted token") from exc

        # Legacy fallback is disabled by default for stronger security.
        if not self._allow_legacy_fallback:
            raise ValueError("Legacy token decryption is disabled")
        return base64.b64decode(encrypted_text.encode("utf-8")).decode("utf-8")


crypto_service = CryptoService()
