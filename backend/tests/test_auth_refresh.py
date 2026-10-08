from sqlalchemy import text

REGISTER_URL = "/api/v1/auth/register"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/auth/me"

USER = {
    "email": "refresh-test@example.com",
    "password": "TestPass123!",
    "full_name": "Refresh Test",
}


async def _register_tokens(db_client) -> dict:
    res = await db_client.post(REGISTER_URL, json=USER)
    assert res.status_code == 201
    return res.json()["tokens"]


async def _refresh(db_client, token: str):
    return await db_client.post(REFRESH_URL, json={"refresh_token": token})


async def test_refresh_success(db_client):
    tokens = await _register_tokens(db_client)

    res = await _refresh(db_client, tokens["refresh_token"])
    assert res.status_code == 200

    body = res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    # The new access token must really work.
    me = await db_client.get(
        ME_URL, headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == USER["email"]


async def test_refresh_does_not_rotate_the_refresh_token(db_client):
    tokens = await _register_tokens(db_client)

    first = await _refresh(db_client, tokens["refresh_token"])
    assert first.status_code == 200
    assert "refresh_token" not in first.json()

    # Current design: the same refresh token stays valid until expiry or logout.
    second = await _refresh(db_client, tokens["refresh_token"])
    assert second.status_code == 200


async def test_refresh_garbage_token_returns_401(db_client):
    res = await _refresh(db_client, "not-a-real-token")
    assert res.status_code == 401


async def test_refresh_revoked_token_returns_401(db_client, db_engine):
    tokens = await _register_tokens(db_client)

    async with db_engine.begin() as conn:
        await conn.execute(text("UPDATE refresh_tokens SET revoked_at = now()"))

    res = await _refresh(db_client, tokens["refresh_token"])
    assert res.status_code == 401


async def test_refresh_expired_token_returns_401(db_client, db_engine):
    tokens = await _register_tokens(db_client)

    async with db_engine.begin() as conn:
        await conn.execute(
            text("UPDATE refresh_tokens SET expires_at = now() - interval '1 hour'")
        )

    res = await _refresh(db_client, tokens["refresh_token"])
    assert res.status_code == 401


async def test_refresh_deactivated_user_returns_401(db_client, db_engine):
    tokens = await _register_tokens(db_client)

    async with db_engine.begin() as conn:
        await conn.execute(text("UPDATE users SET is_active = false"))

    res = await _refresh(db_client, tokens["refresh_token"])
    assert res.status_code == 401


async def test_refresh_rejects_access_token_in_place_of_refresh_token(db_client):
    tokens = await _register_tokens(db_client)

    res = await _refresh(db_client, tokens["access_token"])
    assert res.status_code == 401


async def test_refresh_missing_field_returns_422(db_client):
    res = await db_client.post(REFRESH_URL, json={})
    assert res.status_code == 422