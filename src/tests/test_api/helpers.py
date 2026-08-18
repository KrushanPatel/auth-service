DEFAULT_USER = {
    "username": "krushan",
    "email": "krushan@example.com",
    "password": "Password@123",
    "first_name": "Krushan",
    "last_name": "Patel",
}


async def register_user(client, **overrides):
    payload = {**DEFAULT_USER, **overrides}
    return await client.post("/api/v1/auth/register", json=payload)


async def login_user(client, email=None, password=None):
    return await client.post(
        "/api/v1/auth/login",
        json={
            "email": email or DEFAULT_USER["email"],
            "password": password or DEFAULT_USER["password"],
        },
    )


async def register_and_login(client, **overrides):
    await register_user(client, **overrides)
    response = await login_user(
        client,
        email=overrides.get("email"),
        password=overrides.get("password"),
    )
    return response.json()
