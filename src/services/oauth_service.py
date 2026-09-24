import secrets
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from core.jwt import (
    create_access_token,
    create_mfa_token,
    create_oauth_state_token,
    create_refresh_token,
    verify_oauth_state_token,
)
from core.security import hash_reset_token
from repositories.user_repository import (
    create_oauth_user,
    get_user_by_email,
    get_user_by_google_id,
    get_user_by_username,
    link_google_id,
)
from services.refresh_token_service import store_refresh_token

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

USERNAME_SUFFIX_ATTEMPTS = 5


def get_google_authorize_url() -> tuple[str, str]:
    """
    Returns (authorize_url, state_cookie_nonce). The nonce must be set by the
    caller as an HttpOnly cookie and echoed back on the callback: the signed
    `state` JWT alone doesn't bind the callback to the browser that started
    the flow (a signed-but-unbound state is replayable as a login-CSRF), so
    the cookie is the actual CSRF defense.
    """
    nonce = secrets.token_urlsafe(32)
    state = create_oauth_state_token(hash_reset_token(nonce))

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
    }

    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}", nonce


async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    response.raise_for_status()
    return response.json()


async def fetch_google_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    response.raise_for_status()
    return response.json()


async def _unique_username(email: str) -> str:
    local_part = email.split("@", 1)[0][:50] or "user"
    if len(local_part) < 3:
        local_part = (local_part + "user")[:3]

    if not await get_user_by_username(local_part):
        return local_part

    for _ in range(USERNAME_SUFFIX_ATTEMPTS):
        candidate = f"{local_part[:42]}-{secrets.token_hex(3)}"[:50]
        if not await get_user_by_username(candidate):
            return candidate

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique username",
    )


async def handle_google_callback(code: str, state: str, cookie_nonce: str | None):
    if not cookie_nonce:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing OAuth state cookie"
        )

    try:
        payload = verify_oauth_state_token(state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    if payload["nonce_hash"] != hash_reset_token(cookie_nonce):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth state")

    tokens = await exchange_code_for_token(code)
    userinfo = await fetch_google_userinfo(tokens["access_token"])

    if not userinfo.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google account email is not verified",
        )

    google_id = userinfo["sub"]
    email = userinfo["email"]

    user = await get_user_by_google_id(google_id)

    if not user:
        user = await get_user_by_email(email)

        if user:
            user = await link_google_id(str(user["id"]), google_id)
        else:
            username = await _unique_username(email)
            user = await create_oauth_user(
                username=username,
                email=email,
                first_name=userinfo.get("given_name") or "Google",
                last_name=userinfo.get("family_name") or "User",
                google_id=google_id,
            )

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    if user["mfa_enabled"]:
        return {
            "mfa_required": True,
            "mfa_token": create_mfa_token(str(user["id"])),
        }

    access_token = create_access_token(str(user["id"]))

    refresh_token, jti = create_refresh_token(str(user["id"]))

    await store_refresh_token(
        user_id=user["id"],
        refresh_token=refresh_token,
        jti=jti,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
