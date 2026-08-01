from db.session import execute, fetch_one


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