from uuid import UUID

from db.session import execute, fetch_one


async def set_pending_mfa_secret(user_id: UUID, encrypted_secret: str):

    query = """
        UPDATE users
        SET mfa_secret = $2,
            mfa_enabled = FALSE
        WHERE id = $1
        RETURNING id, mfa_enabled, mfa_secret;
    """

    return await fetch_one(query, user_id, encrypted_secret)


async def activate_mfa(user_id: UUID):

    query = """
        UPDATE users
        SET mfa_enabled = TRUE
        WHERE id = $1
        RETURNING id, mfa_enabled, mfa_secret;
    """

    return await fetch_one(query, user_id)


async def deactivate_mfa(user_id: UUID):

    query = """
        UPDATE users
        SET mfa_enabled = FALSE,
            mfa_secret = NULL
        WHERE id = $1
        RETURNING id, mfa_enabled, mfa_secret;
    """

    return await fetch_one(query, user_id)


async def insert_recovery_codes(user_id: UUID, code_hashes: list[str]):

    query = """
        INSERT INTO mfa_recovery_codes (user_id, code_hash)
        VALUES ($1, $2)
        RETURNING *;
    """

    return [await fetch_one(query, user_id, code_hash) for code_hash in code_hashes]


async def get_recovery_code_by_hash(user_id: UUID, code_hash: str):

    query = """
        SELECT *
        FROM mfa_recovery_codes
        WHERE user_id = $1 AND code_hash = $2 AND used = FALSE;
    """

    return await fetch_one(query, user_id, code_hash)


async def mark_recovery_code_used(code_id: UUID):

    query = """
        UPDATE mfa_recovery_codes
        SET used = TRUE
        WHERE id = $1
        RETURNING *;
    """

    return await fetch_one(query, code_id)


async def delete_recovery_codes(user_id: UUID):

    query = """
        DELETE
        FROM mfa_recovery_codes
        WHERE user_id = $1;
    """

    await execute(query, user_id)
