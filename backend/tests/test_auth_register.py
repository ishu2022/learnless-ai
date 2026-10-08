import pytest
from sqlalchemy import text

REGISTER_URL = "/api/v1/auth/register"
ME_URL = "/api/v1/auth/me"

VALID = {
    "email": "register-test@example.com",
    "password": "TestPass123!",
    "full_name": "Register Test",
}


async def test_register_success(db_client):
    res = await db_client.post(REGISTER_URL, json=VALID)
    assert res.status_code == 201

    body = res.json()
    assert body["user"]["email"] == VALID["email"]
    assert body["user"]["full_name"] == VALID["full_name"]
    assert body["user"]["is_active"] is True
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"

    # Nothing secret may leak anywhere in the response.
    assert "password" not in res.text.lower()


async def test_register_stores_only_hashes(db_client, db_engine):
    res = await db_client.post(REGISTER_URL, json=VALID)
    raw_refresh_token = res.json()["tokens"]["refresh_token"]

    async with db_engine.connect() as conn:
        stored_password = (
            await conn.execute(text("SELECT password_hash FROM users"))
        ).scalar_one()
        stored_token = (
            await conn.execute(text("SELECT token_hash FROM refresh_tokens"))
        ).scalar_one()

    assert stored_password != VALID["password"]
    assert stored_password.startswith("$2")  # bcrypt hash prefix
    assert stored_token != raw_refresh_token
    assert len(stored_token) == 64  # SHA-256 hex digest


async def test_register_duplicate_email_returns_409(db_client, db_engine):
    first = await db_client.post(REGISTER_URL, json=VALID)
    assert first.status_code == 201

    second = await db_client.post(REGISTER_URL, json=VALID)
    assert second.status_code == 409

    async with db_engine.connect() as conn:
        count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
    assert count == 1


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "email": "not-an-email"},
        {**VALID, "password": "short7!"},  # 7 characters, minimum is 8
        {**VALID, "password": "a" * 73},  # maximum is 72
        {**VALID, "full_name": ""},
        {"email": VALID["email"]},  # password and full_name missing
    ],
    ids=["bad-email", "password-too-short", "password-too-long", "empty-name", "missing-fields"],
)
async def test_register_rejects_invalid_input(db_client, db_engine, payload):
    res = await db_client.post(REGISTER_URL, json=payload)
    assert res.status_code == 422

    async with db_engine.connect() as conn:
        count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
    assert count == 0


async def test_register_access_token_works_on_me(db_client):
    res = await db_client.post(REGISTER_URL, json=VALID)
    token = res.json()["tokens"]["access_token"]

    me = await db_client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == VALID["email"]