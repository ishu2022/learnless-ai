"""Dependency health checks used by GET /api/v1/health/ready."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations import storage
from app.integrations.redis_client import get_redis
from app.schemas.health import ComponentHealth

logger = logging.getLogger(__name__)
CHECK_TIMEOUT_SECONDS = 3


async def _run(check: Callable[[], Awaitable[str | None]]) -> ComponentHealth:
    start = time.perf_counter()
    try:
        detail = await asyncio.wait_for(check(), timeout=CHECK_TIMEOUT_SECONDS)
        status = "ok"
    except Exception as exc:
        logger.warning("Health check failed: %s: %s", type(exc).__name__, exc)
        # Only the exception type is exposed to clients, never connection strings/secrets
        detail = type(exc).__name__
        status = "error"
    latency = round((time.perf_counter() - start) * 1000, 1)
    return ComponentHealth(status=status, latency_ms=latency, detail=detail)


async def check_database(db: AsyncSession) -> ComponentHealth:
    async def _check() -> str:
        await db.execute(text("SELECT 1"))
        result = await db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise RuntimeError("pgvector extension is not installed")
        return f"pgvector {version}"

    return await _run(_check)


async def check_redis() -> ComponentHealth:
    async def _check() -> None:
        await get_redis().ping()

    return await _run(_check)


async def check_storage() -> ComponentHealth:
    async def _check() -> None:
        await storage.check_bucket()

    return await _run(_check)
