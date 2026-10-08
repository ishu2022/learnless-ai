import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text

from app.core.config import get_settings

REGISTER_URL = "/api/v1/auth/register"
ME_URL = "/api/v1/auth/me"

USER = {
    "email": "me-test@example.com",
    "password": "TestPass123!",
    "full_name": "Me Test",
}


def _make_token(claims: dict, secret: str | None = None) -> str:
    """Build a JWT by hand so we can create tokens the app would never issue."""
    settings = get_settings()
    return jwt.encode(
        claims,
        secret or settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _in_minutes(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


async def _register(db_client) -> dict:
    res = await db_client.post(REGISTER_URL, json=USER)
    assert res.status_code == 201
    return res.json()


async def _me(db_client, token: str):
    return await db_client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})


async def test_me_success(db_client):
    body = await _register(db_client)
    token = body["tokens"]["access_token"]

    res = await _me(db_client, token)
    assert res.status_code == 200

    data = res.json()
    assert data["id"] == body["user"]["id"]
    assert data["email"] == USER["email"]
    assert data["full_name"] == USER["full_name"]
    assert data["is_active"] is True
    assert "password" not in res.text.lower()


async def test_me_handmade_valid_token_is_accepted(db_client):
    # Control: proves the hand-made tokens below are built correctly, so a 401
    # in the other tests is caused by the one thing we broke on purpose.
    body = await _register(db_client)
    user_id = body["user"]["id"]

    token = _make_token({"sub": user_id, "exp": _in_minutes(5)})
    res = await _me(db_client, token)
    assert res.status_code == 200
    assert res.json()["id"] == user_id


async def test_me_missing_header_returns_401(db_client):
    res = await db_client.get(ME_URL)
    assert res.status_code == 401


async def test_me_garbage_token_returns_401(db_client):
    res = await _me(db_client, "not-a-real-token")
    assert res.status_code == 401


async def test_me_expired_token_returns_401(db_client):
    body = await _register(db_client)
    token = _make_token({"sub": body["user"]["id"], "exp": _in_minutes(-60)})

    res = await _me(db_client, token)
    assert res.status_code == 401


async def test_me_wrong_signature_returns_401(db_client):
    body = await _register(db_client)
    token = _make_token(
        {"sub": body["user"]["id"], "exp": _in_minutes(5)},
        secret="wrong-secret-xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    )

    res = await _me(db_client, token)
    assert res.status_code == 401


async def test_me_deactivated_user_returns_401(db_client, db_engine):
    body = await _register(db_client)
    token = body["tokens"]["access_token"]
    assert (await _me(db_client, token)).status_code == 200

    async with db_engine.begin() as conn:
        await conn.execute(text("UPDATE users SET is_active = false"))

    # Same token, still unexpired. Only the active-user check can reject it.
    res = await _me(db_client, token)
    assert res.status_code == 401


async def test_me_token_for_nonexistent_user_returns_401(db_client):
    token = _make_token({"sub": str(uuid.uuid4()), "exp": _in_minutes(5)})

    res = await _me(db_client, token)
    assert res.status_code == 401


async def test_me_rejects_refresh_token_used_as_bearer(db_client):
    body = await _register(db_client)

    res = await _me(db_client, body["tokens"]["refresh_token"])
    assert res.status_code == 401


async def test_me_token_without_subject_returns_401(db_client):
    token = _make_token({"exp": _in_minutes(5)})

    res = await _me(db_client, token)
    assert res.status_code == 401


async def test_me_token_with_non_uuid_subject_returns_401(db_client):
    token = _make_token({"sub": "not-a-uuid", "exp": _in_minutes(5)})

    res = await _me(db_client, token)
    assert res.status_code == 401