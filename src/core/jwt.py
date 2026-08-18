import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from core.config import ACCESS_TOKEN_EXPIRE, JWT_ALGORITHM, JWT_SECRET_KEY, REFRESH_TOKEN_EXPIRE


def _decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")


def create_access_token(user_id: str) -> str:

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def verify_access_token(token: str) -> dict:

    payload = _decode_token(token)

    if payload.get("type") != "access":
        raise ValueError("Invalid access token")

    if "sub" not in payload:
        raise ValueError("Invalid token payload")

    return payload


def create_refresh_token(user_id: str) -> tuple[str, UUID]:

    now = datetime.now(timezone.utc)
    jti = uuid.uuid4()
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(jti),
        "iat": now,
        "exp": now + REFRESH_TOKEN_EXPIRE,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return token, jti


def verify_refresh_token(token: str) -> dict:
    payload = _decode_token(token)

    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    if "sub" not in payload or "jti" not in payload:
        raise ValueError("Invalid refresh token payload")

    return payload
