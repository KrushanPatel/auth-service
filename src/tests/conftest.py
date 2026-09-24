import os

import asyncpg
import pytest
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient

import db.connection as db_connection
import db.redis_connection as db_redis_connection
from main import app

TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = int(os.getenv("TEST_DB_PORT", "5433"))
TEST_DB_USER = os.getenv("TEST_DB_USER", "test")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "test")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "auth_test")

TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/0")

SCHEMA_SQL = """
DROP TABLE IF EXISTS email_verifications;
DROP TABLE IF EXISTS password_resets;
DROP TABLE IF EXISTS mfa_recovery_codes;
DROP TABLE IF EXISTS refresh_tokens;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    tokens_valid_after TIMESTAMPTZ,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    google_id TEXT UNIQUE
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    jti UUID UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mfa_recovery_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


@pytest.fixture(scope="session")
async def test_pool():
    """
    Session-wide asyncpg pool against the docker-compose.test.yml Postgres,
    wired in as db.connection's module-level pool so repositories/services
    under test hit a real database without going through create_pool()
    (which requires AWS-style DB_* secrets and defaults to ssl="require").
    """
    pool = await asyncpg.create_pool(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        database=TEST_DB_NAME,
        min_size=1,
        max_size=5,
    )

    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)

    db_connection._pool = pool

    yield pool

    db_connection._pool = None
    await pool.close()


@pytest.fixture
async def clean_db(test_pool):
    async with test_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE email_verifications, password_resets,"
            " mfa_recovery_codes, refresh_tokens, users RESTART IDENTITY CASCADE;"
        )
    yield


@pytest.fixture(scope="session")
async def test_redis():
    """
    Session-wide Redis client against docker-compose.test.yml's disposable
    redis-test service, wired in as db.redis_connection's module-level client
    so the rate limit repository under test hits real Redis — mirrors
    test_pool's approach for asyncpg above.
    """
    client = redis.from_url(TEST_REDIS_URL)

    db_redis_connection._redis_client = client

    yield client

    db_redis_connection._redis_client = None
    await client.aclose()


@pytest.fixture
async def clean_redis(test_redis):
    await test_redis.flushdb()
    yield


@pytest.fixture
async def client(test_pool, test_redis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
