from app.schemas.health import ComponentHealth
from app.services import health_service

OK = ComponentHealth(status="ok", latency_ms=1.0, detail=None)
DOWN = ComponentHealth(status="error", latency_ms=3000.0, detail="ConnectionError")


def _patch(monkeypatch, db=OK, redis=OK, storage=OK):
    async def _db(_session):
        return db

    async def _redis():
        return redis

    async def _storage():
        return storage

    monkeypatch.setattr(health_service, "check_database", _db)
    monkeypatch.setattr(health_service, "check_redis", _redis)
    monkeypatch.setattr(health_service, "check_storage", _storage)


async def test_liveness(client):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["service"] == "LearnLess AI"


async def test_readiness_all_ok(client, monkeypatch):
    _patch(monkeypatch)
    res = await client.get("/api/v1/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert set(body["components"]) == {"database", "redis", "storage"}


async def test_readiness_degraded_returns_503(client, monkeypatch):
    _patch(monkeypatch, redis=DOWN)
    res = await client.get("/api/v1/health/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "degraded"
    assert body["components"]["redis"]["status"] == "error"
    assert body["components"]["database"]["status"] == "ok"


async def test_unknown_route_uses_consistent_error_shape(client):
    res = await client.get("/api/v1/does-not-exist")
    assert res.status_code == 404
    error = res.json()["error"]
    assert error["code"] == "http_404"
    assert "message" in error
