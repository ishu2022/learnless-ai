"""Password hashing and JWT utilities.

Uses bcrypt directly (not passlib) — passlib is unmaintained and has a
known compatibility bug with modern bcrypt versions.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store the raw password."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    password_bytes = plain_password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a short-lived JWT identifying this user."""
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class InvalidTokenError(Exception):
    """Raised when a token is malformed, has a bad signature, or has expired."""


def decode_access_token(token: str) -> uuid.UUID:
    """Validate a JWT and return the user_id it identifies.

    Raises InvalidTokenError for ANY problem (bad signature, expired,
    malformed) — deliberately one error type, so the caller doesn't need
    to know JWT-library-specific exception names.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token is missing its subject")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise InvalidTokenError("Token subject is not a valid user id") from exc


def generate_refresh_token() -> str:
    """Create a new random refresh token (the raw value given to the client)."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token for storage (SHA-256 — fast hash is correct here,
    since the token is already high-entropy random data, not a human-chosen
    secret like a password)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()