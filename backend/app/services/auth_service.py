"""Business logic for authentication: registration, login, refresh."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import (
    create_refresh_token,
    get_valid_refresh_token,
)
from app.repositories.user_repository import create_user, get_user_by_email, get_user_by_id
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest


async def _issue_refresh_token(db: AsyncSession, user_id) -> str:
    """Create a new refresh token row and return the RAW token for the client.
    Only the hash is ever stored (see core/security.py)."""
    settings = get_settings()
    raw_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    await create_refresh_token(
        db,
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=expires_at,
    )
    return raw_token


async def register_user(db: AsyncSession, data: RegisterRequest) -> tuple[User, str, str]:
    """Create a new user account. Raises 409 if the email is already taken."""
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    password_hash = hash_password(data.password)
    user = await create_user(
        db,
        email=data.email,
        password_hash=password_hash,
        full_name=data.full_name,
    )

    access_token = create_access_token(user.id)
    refresh_token = await _issue_refresh_token(db, user.id)
    await db.commit()

    return user, access_token, refresh_token


async def login_user(db: AsyncSession, data: LoginRequest) -> tuple[User, str, str]:
    """Verify credentials and return the user + a fresh access + refresh token.

    Raises 401 for either a missing user OR a wrong password - deliberately
    the same error/message for both, so an attacker can't use this endpoint
    to figure out which emails are registered.
    """
    user = await get_user_by_email(db, data.email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    access_token = create_access_token(user.id)
    refresh_token = await _issue_refresh_token(db, user.id)
    await db.commit()

    return user, access_token, refresh_token


async def refresh_access_token(db: AsyncSession, data: RefreshRequest) -> str:
    """Validate a refresh token and issue a NEW access token.

    The refresh token itself is not rotated/replaced here — it stays
    valid until it naturally expires or is revoked via logout.
    """
    token_hash = hash_refresh_token(data.refresh_token)
    stored_token = await get_valid_refresh_token(db, token_hash)

    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, expired, or has been revoked",
        )

    user = await get_user_by_id(db, stored_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid, expired, or has been revoked",
        )

    return create_access_token(user.id)