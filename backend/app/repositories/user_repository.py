"""Database access for the User table.

This file is the ONLY place that writes raw SQLAlchemy queries for users.
Services call these functions instead of touching the database directly.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email, or None if no such user exists."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Look up a user by their UUID, or None if no such user exists."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    full_name: str,
) -> User:
    """Insert a new user row and return it with id/timestamps populated."""
    user = User(email=email, password_hash=password_hash, full_name=full_name)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user