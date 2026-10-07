"""Shared, reusable column mixins for SQLAlchemy models.

These are NOT tables themselves — they are small building blocks that
get combined with Base to form actual tables, so every model doesn't
have to redefine id/created_at/updated_at from scratch.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Gives a model a UUID primary key, generated in Python before insert."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Gives a model created_at/updated_at columns, set by the database itself."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )