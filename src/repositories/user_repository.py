from fastapi import HTTPException, status

from db.session import fetch_all, fetch_one

ALLOWED_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "password_hash",
    "is_verified",
    "tokens_valid_after",
    "google_id",
}


async def get_user_by_email(email: str):

    query = """
        SELECT *
        FROM users
        WHERE email = $1;
    """

    return await fetch_one(query, email)


async def get_user_by_username(username: str):

    query = """
        SELECT *
        FROM users
        WHERE username = $1;
    """

    return await fetch_one(query, username)


async def get_user_by_id(user_id: str):

    query = """
        SELECT *
        FROM users
        WHERE id = $1;
    """

    return await fetch_one(query, user_id)


async def get_user_by_google_id(google_id: str):

    query = """
        SELECT *
        FROM users
        WHERE google_id = $1;
    """

    return await fetch_one(query, google_id)


async def create_oauth_user(
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    google_id: str,
):

    query = """
        INSERT INTO users (
            username,
            email,
            first_name,
            last_name,
            google_id,
            is_verified
        )
        VALUES ($1,$2,$3,$4,$5, TRUE)
        RETURNING *;
    """

    return await fetch_one(
        query,
        username,
        email,
        first_name,
        last_name,
        google_id,
    )


async def link_google_id(user_id: str, google_id: str):
    await update_user(user_id, google_id=google_id)
    return await get_user_by_id(user_id)


async def create_user(
    username: str,
    email: str,
    password_hash: str,
    first_name: str,
    last_name: str,
):

    query = """
        INSERT INTO users (
            username,
            email,
            password_hash,
            first_name,
            last_name
        )
        VALUES ($1,$2,$3,$4,$5)
        RETURNING
            id,
            username,
            email,
            is_verified;
    """

    return await fetch_one(
        query,
        username,
        email,
        password_hash,
        first_name,
        last_name,
    )


async def list_users():

    query = """
        SELECT id, username, email, first_name, last_name, role, is_active, is_verified
        FROM users
        ORDER BY created_at;
    """

    return await fetch_all(query)


async def update_user_role(user_id: str, role: str):

    query = """
        UPDATE users
        SET role = $2
        WHERE id = $1
        RETURNING
            id,
            username,
            email,
            first_name,
            last_name,
            role;
    """

    return await fetch_one(query, user_id, role)


async def update_user(user_id: str, **fields):

    updates = []
    values = []

    for index, (key, value) in enumerate(fields.items(), start=2):
        print(f"INDEX:{index} KEY:{key} VALUE:{value}")
        if key not in ALLOWED_FIELDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid key to update user data",
            )

        updates.append(f"{key} = ${index}")
        values.append(value)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="nothing to change"
        )

    query = f"""
        UPDATE users
        SET
            {", ".join(updates)}
        WHERE id = $1
        RETURNING
            id,
            username,
            email,
            first_name,
            last_name,
            role,
            is_verified;
    """

    return await fetch_one(query, user_id, *values)
