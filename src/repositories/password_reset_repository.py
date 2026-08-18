from datetime import datetime
from uuid import UUID

from db.session import execute, fetch_one


async def create_password_reset_token_record(
    user_id: UUID,
    token_hash: str,
    jti: UUID,
    expires_at: datetime,
):
    query = """
        INSERT INTO password_reset_tokens (
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


async def get_password_reset_token_by_jti(jti: UUID):

    query = """
        SELECT *
        FROM password_reset_tokens
        WHERE jti = $1;
    """

    return await fetch_one(query, jti)


async def mark_password_reset_token_used(jti: UUID):

    query = """
        UPDATE password_reset_tokens
        SET used = TRUE
        WHERE jti = $1
        RETURNING *;
    """

    return await fetch_one(query, jti)


async def delete_expired_password_reset_tokens():

    query = """
        DELETE
        FROM password_reset_tokens
        WHERE expires_at < NOW();
    """

    await execute(query)
