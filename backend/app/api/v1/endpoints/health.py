from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.health import LivenessResponse, ReadinessResponse
from app.services import health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Is the API process up? Does not touch any dependency."""
    s = get_settings()
    return LivenessResponse(
        status="ok", service=s.app_name, version=s.app_version, environment=s.app_env
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse, "description": "A dependency is down"}},
)
async def readiness(response: Response, db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """Are PostgreSQL (+pgvector), Redis and MinIO reachable? Returns 503 if any is down."""
    s = get_settings()
    components = {
        "database": await health_service.check_database(db),
        "redis": await health_service.check_redis(),
        "storage": await health_service.check_storage(),
    }
    healthy = all(c.status == "ok" for c in components.values())
    if not healthy:
        response.status_code = 503
    return ReadinessResponse(
        status="ok" if healthy else "degraded",
        service=s.app_name,
        version=s.app_version,
        environment=s.app_env,
        components=components,
    )
