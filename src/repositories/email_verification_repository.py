from datetime import datetime
from uuid import UUID

from db.session import execute, fetch_one


async def create_email_verification_token_record(
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
):
    query = """
        INSERT INTO email_verifications (
            user_id,
            token_hash,
            expires_at
        )
        VALUES ($1, $2, $3)
        RETURNING *;
    """

    return await fetch_one(
        query,
        user_id,
        token_hash,
        expires_at,
    )


async def get_email_verification_token_by_hash(token_hash: str):

    query = """
        SELECT *
        FROM email_verifications
        WHERE token_hash = $1;
    """

    return await fetch_one(query, token_hash)


async def mark_email_verification_token_used(token_id: UUID):

    query = """
        UPDATE email_verifications
        SET used = TRUE
        WHERE id = $1
        RETURNING *;
    """

    return await fetch_one(query, token_id)


async def delete_expired_email_verification_tokens():

    query = """
        DELETE
        FROM email_verifications
        WHERE expires_at < NOW();
    """

    await execute(query)
