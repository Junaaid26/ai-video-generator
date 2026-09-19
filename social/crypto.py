"""
Encryption and credential security utilities.
Never store raw passwords or OAuth tokens in plain text.
Uses Fernet (AES-128-CBC + HMAC-SHA256 authenticated symmetric encryption).
"""

import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def _get_encryption_key() -> bytes:
    """
    Retrieves or derives a 32-byte URL-safe base64-encoded Fernet key.
    Reads from ENCRYPTION_KEY environment variable.
    If not found, derives a deterministic key from a salt/secret to ensure
    stability across restarts in development.
    """
    raw_key = os.getenv("ENCRYPTION_KEY")
    if raw_key:
        try:
            # Validate if it's already a valid Fernet key
            key_bytes = raw_key.strip().encode("utf-8")
            Fernet(key_bytes)
            return key_bytes
        except Exception:
            # If not a raw Fernet key, derive a valid 32-byte key via SHA-256
            derived = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode("utf-8")).digest())
            return derived

    # Default fallback for local zero-config development
    fallback_secret = "ai-video-generator-default-secret-salt-2026"
    derived = base64.urlsafe_b64encode(hashlib.sha256(fallback_secret.encode("utf-8")).digest())
    return derived


def encrypt_token(plain_text: Optional[str]) -> Optional[str]:
    """
    Encrypts a plain text token or secret.
    Returns URL-safe base64 encrypted string, or None if input is empty.
    """
    if not plain_text:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(cipher_text: Optional[str]) -> Optional[str]:
    """
    Decrypts an encrypted token string.
    Returns decrypted plain text, or None if input is empty.
    """
    if not cipher_text:
        return None
    key = _get_encryption_key()
    f = Fernet(key)
    try:
        decrypted = f.decrypt(cipher_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential: {str(e)}")
