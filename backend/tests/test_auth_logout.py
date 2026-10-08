from sqlalchemy import text

from app.core.security import hash_refresh_token

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"

USER = {
    "email": "logout-test@example.com",
    "password": "TestPass123!",
    "full_name": "Logout Test",
}
OTHER_USER = {
    "email": "logout-other@example.com",
    "password": "TestPass123!",
    "full_name": "Other User",
}


async def _register_tokens(db_client, user=USER) -> dict:
    res = await db_client.post(REGISTER_URL, json=user)
    assert res.status_code == 201
    return res.json()["tokens"]


async def _logout(db_client, token: str):
    return await db_client.post(LOGOUT_URL, json={"refresh_token": token})


async def _refresh(db_client, token: str):
    return await db_client.post(REFRESH_URL, json={"refresh_token": token})


async def _revoked_at(db_engine, raw_token: str):
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT revoked_at FROM refresh_tokens WHERE token_hash = :h"),
            {"h": hash_refresh_token(raw_token)},
        )
        return result.scalar_one()


async def _revoked_count(db_engine) -> int:
    async with db_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM refresh_tokens WHERE revoked_at IS NOT NULL")
        )
        return result.scalar_one()


async def test_logout_then_refresh_returns_401(db_client):
    tokens = await _register_tokens(db_client)

    res = await _logout(db_client, tokens["refresh_token"])
    assert res.status_code == 204

    after = await _refresh(db_client, tokens["refresh_token"])
    assert after.status_code == 401


async def test_logout_sets_revoked_at_in_database(db_client, db_engine):
    tokens = await _register_tokens(db_client)
    assert await _revoked_at(db_engine, tokens["refresh_token"]) is None

    await _logout(db_client, tokens["refresh_token"])
    assert await _revoked_at(db_engine, tokens["refresh_token"]) is not None


async def test_logout_only_revokes_that_session(db_client, db_engine):
    session_a = await _register_tokens(db_client)
    login = await db_client.post(
        LOGIN_URL, json={"email": USER["email"], "password": USER["password"]}
    )
    assert login.status_code == 200
    session_b = login.json()["tokens"]

    await _logout(db_client, session_a["refresh_token"])

    assert await _revoked_count(db_engine) == 1
    assert (await _refresh(db_client, session_a["refresh_token"])).status_code == 401
    assert (await _refresh(db_client, session_b["refresh_token"])).status_code == 200


async def test_logout_does_not_affect_other_users(db_client):
    user_tokens = await _register_tokens(db_client)
    other_tokens = await _register_tokens(db_client, OTHER_USER)

    await _logout(db_client, user_tokens["refresh_token"])

    res = await _refresh(db_client, other_tokens["refresh_token"])
    assert res.status_code == 200


async def test_logout_twice_is_idempotent_and_keeps_original_revoked_at(
    db_client, db_engine
):
    tokens = await _register_tokens(db_client)

    first = await _logout(db_client, tokens["refresh_token"])
    assert first.status_code == 204
    revoked_first = await _revoked_at(db_engine, tokens["refresh_token"])

    second = await _logout(db_client, tokens["refresh_token"])
    assert second.status_code == 204
    revoked_second = await _revoked_at(db_engine, tokens["refresh_token"])

    assert revoked_first == revoked_second


async def test_logout_garbage_token_returns_204_and_revokes_nothing(
    db_client, db_engine
):
    await _register_tokens(db_client)

    res = await _logout(db_client, "not-a-real-token")
    assert res.status_code == 204
    assert await _revoked_count(db_engine) == 0


async def test_logout_expired_token_returns_204_and_revokes_nothing(
    db_client, db_engine
):
    tokens = await _register_tokens(db_client)

    async with db_engine.begin() as conn:
        await conn.execute(
            text("UPDATE refresh_tokens SET expires_at = now() - interval '1 hour'")
        )

    res = await _logout(db_client, tokens["refresh_token"])
    assert res.status_code == 204
    assert await _revoked_at(db_engine, tokens["refresh_token"]) is None


async def test_access_token_still_works_after_logout(db_client):
    # Documents a known tradeoff: access tokens are stateless JWTs, so logout
    # cannot cancel one early. It stays valid until it expires.
    tokens = await _register_tokens(db_client)

    await _logout(db_client, tokens["refresh_token"])

    me = await db_client.get(
        ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200


async def test_logout_missing_field_returns_422(db_client):
    res = await db_client.post(LOGOUT_URL, json={})
    assert res.status_code == 422