from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RefreshToken(BaseModel):
    id: UUID
    user_id: UUID
    token_hash: str
    jti: UUID
    expire_at: datetime
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
