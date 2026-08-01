import jwt
from jwt import ExpiredSignatureError,InvalidTokenError
from core.config import (JWT_ALGORITHM,JWT_SECRET_KEY,
                    ACCESS_TOKEN_EXPIRE,REFRESH_TOKEN_EXPIRE)
from datetime import datetime, timezone

def create_access_token(user_id:str)->str:
    
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    
def verify_access_token(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        return payload

    except ExpiredSignatureError:
        raise ValueError("Token has expired")

    except InvalidTokenError:
        raise ValueError("Invalid token")