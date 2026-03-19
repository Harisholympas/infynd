"""Simple credential vault - encrypts credentials at rest using Fernet."""
import json, base64, os, logging
from core.config import settings

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    def _make_key(secret: str) -> bytes:
        import hashlib
        raw = hashlib.sha256(secret.encode()).digest()
        return base64.urlsafe_b64encode(raw)
    _fernet = Fernet(_make_key(settings.SECRET_KEY))
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("cryptography not installed - credentials stored as plain JSON")


def encrypt_credentials(creds: dict) -> str:
    raw = json.dumps(creds)
    if HAS_CRYPTO:
        return _fernet.encrypt(raw.encode()).decode()
    return raw  # fallback: plain JSON (warn user)


def decrypt_credentials(stored: str) -> dict:
    if not stored:
        return {}
    if HAS_CRYPTO:
        try:
            return json.loads(_fernet.decrypt(stored.encode()).decode())
        except Exception:
            pass  # might be unencrypted from before crypto was available
    try:
        return json.loads(stored)
    except:
        return {}
