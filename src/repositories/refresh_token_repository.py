from datetime import datetime, timezone
from uuid import UUID

from db.session import execute, fetch_one


async def create_refresh_token_record(
    user_id: UUID,
    token_hash: str,
    jti: UUID,
    expires_at: datetime,
):
    query = """
        INSERT INTO refresh_tokens (
            user_id,
            token_hash,
            jti,
            expires_at
        )
        VALUES ($1, $2, $3, $4)
        RETURNING *;
    """

    return await fetch_one(
        query,
        user_id,
        token_hash,
        jti,
        expires_at,
    )


async def get_refresh_token_by_jti(jti: UUID):

    query = """
        SELECT *
        FROM refresh_tokens
        WHERE jti = $1;
    """

    return await fetch_one(query, jti)


async def revoke_refresh_token_by_jti(jti: UUID):

    query = """
        UPDATE refresh_tokens
        SET revoked = TRUE
        WHERE jti = $1
        RETURNING *;
    """

    return await fetch_one(query, jti)


async def update_refresh_token_last_used(jti: UUID):

    query = """
        UPDATE refresh_tokens
        SET last_used_at = $2
        WHERE jti = $1
        RETURNING *;
    """

    return await fetch_one(
        query,
        jti,
        datetime.now(timezone.utc),
    )


async def delete_expired_refresh_tokens():

    query = """
        DELETE
        FROM refresh_tokens
        WHERE expires_at < NOW();
    """

    await execute(query)