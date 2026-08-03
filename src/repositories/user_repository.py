from db.session import execute, fetch_one

ALLOWED_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "password_hash",
    "is_verified",
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
    
async def update_user(user_id:str,**fields):
    
    updates = []
    values = []
    
    for index, (key,value) in enumerate(fields.items(),start=2):
        if key not in ALLOWED_FIELDS:
            continue
        
        updates.append(f"{key} = ${index}")
        values.append(value)
        
    if not updates:
        return None
    
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
            is_verified;
    """
    
    return await fetch_one(query,user_id,*values)
    