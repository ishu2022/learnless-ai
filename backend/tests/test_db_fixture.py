from sqlalchemy import text


async def _count_users(db_engine) -> int:
    async with db_engine.connect() as conn:
        result = await conn.execute(text("SELECT count(*) FROM users"))
        return result.scalar_one()


async def test_connected_to_test_database(db_engine):
    async with db_engine.connect() as conn:
        result = await conn.execute(text("SELECT current_database()"))
        assert result.scalar_one() == "learnless_test"


async def test_register_writes_to_test_database(db_client, db_engine):
    res = await db_client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture-smoke@example.com",
            "password": "TestPass123!",
            "full_name": "Fixture Smoke",
        },
    )
    assert res.status_code == 201
    assert await _count_users(db_engine) == 1


async def test_tables_start_empty_in_each_test(db_engine):
    # The previous test created a user. The fixture must have cleaned it up.
    assert await _count_users(db_engine) == 0