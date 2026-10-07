"""Database access for the RefreshToken table."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    """Insert a new refresh token row (one per login session)."""
    refresh_token = RefreshToken(
        user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    db.add(refresh_token)
    await db.flush()
    await db.refresh(refresh_token)
    return refresh_token


async def get_valid_refresh_token(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    """Find a refresh token by its hash, but ONLY if it's still usable
    (not expired, not revoked). Returns None otherwise — the caller
    doesn't need to know WHY it's invalid, just that it is."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()

    if token is None:
        return None
    if token.revoked_at is not None:
        return None
    if token.expires_at < datetime.now(timezone.utc):
        return None

    return token


async def revoke_refresh_token(db: AsyncSession, token: RefreshToken) -> None:
    """Mark a refresh token as revoked (used on logout)."""
    token.revoked_at = datetime.now(timezone.utc)
    await db.flush()