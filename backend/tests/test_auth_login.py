import pytest
from sqlalchemy import text

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"

VALID = {
    "email": "login-test@example.com",
    "password": "TestPass123!",
    "full_name": "Login Test",
}
CREDENTIALS = {"email": VALID["email"], "password": VALID["password"]}


async def _register(db_client):
    res = await db_client.post(REGISTER_URL, json=VALID)
    assert res.status_code == 201


async def _count_refresh_tokens(db_engine) -> int:
    async with db_engine.connect() as conn:
        return (await conn.execute(text("SELECT count(*) FROM refresh_tokens"))).scalar_one()


async def test_login_success(db_client):
    await _register(db_client)

    res = await db_client.post(LOGIN_URL, json=CREDENTIALS)
    assert res.status_code == 200

    body = res.json()
    assert body["user"]["email"] == VALID["email"]
    assert body["user"]["full_name"] == VALID["full_name"]
    assert body["user"]["is_active"] is True
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"

    # Nothing secret may leak anywhere in the response.
    assert "password" not in res.text.lower()


async def test_login_creates_a_separate_session(db_client, db_engine):
    """Multi-device design: each login gets its own refresh token row."""
    await _register(db_client)
    assert await _count_refresh_tokens(db_engine) == 1  # created by register

    first = await db_client.post(LOGIN_URL, json=CREDENTIALS)
    second = await db_client.post(LOGIN_URL, json=CREDENTIALS)

    assert await _count_refresh_tokens(db_engine) == 3
    assert (
        first.json()["tokens"]["refresh_token"]
        != second.json()["tokens"]["refresh_token"]
    )


async def test_login_wrong_password_returns_401(db_client):
    await _register(db_client)

    res = await db_client.post(
        LOGIN_URL, json={"email": VALID["email"], "password": "WrongPass999!"}
    )
    assert res.status_code == 401
    assert res.json()["error"]["message"] == "Incorrect email or password"


async def test_login_unknown_email_gives_same_error_as_wrong_password(db_client):
    """The two failures must be indistinguishable, so attackers can't
    discover which emails have accounts."""
    await _register(db_client)

    wrong_password = await db_client.post(
        LOGIN_URL, json={"email": VALID["email"], "password": "WrongPass999!"}
    )
    unknown_email = await db_client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": "WrongPass999!"}
    )

    assert unknown_email.status_code == 401
    assert unknown_email.json() == wrong_password.json()


async def test_login_deactivated_account_returns_403(db_client, db_engine):
    await _register(db_client)

    async with db_engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET is_active = false WHERE email = :email"),
            {"email": VALID["email"]},
        )

    res = await db_client.post(LOGIN_URL, json=CREDENTIALS)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": VALID["password"]},
        {"email": VALID["email"]},  # password missing
    ],
    ids=["bad-email", "missing-password"],
)
async def test_login_rejects_invalid_input(db_client, payload):
    res = await db_client.post(LOGIN_URL, json=payload)
    assert res.status_code == 422


async def test_login_access_token_works_on_me(db_client):
    await _register(db_client)

    login = await db_client.post(LOGIN_URL, json=CREDENTIALS)
    token = login.json()["tokens"]["access_token"]

    me = await db_client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == VALID["email"]


async def test_failed_login_does_not_create_a_refresh_token(db_client, db_engine):
    await _register(db_client)
    assert await _count_refresh_tokens(db_engine) == 1

    await db_client.post(
        LOGIN_URL, json={"email": VALID["email"], "password": "WrongPass999!"}
    )

    assert await _count_refresh_tokens(db_engine) == 1