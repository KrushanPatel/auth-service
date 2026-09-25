from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleUpdate(BaseModel):
    role: Literal["user", "admin"]


AuditEventType = Literal[
    "login_success",
    "login_failure",
    "logout",
    "refresh_token_reuse_detected",
    "password_reset_completed",
    "mfa_enabled",
    "mfa_disabled",
    "role_changed",
    "oauth_account_linked",
]


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    event_type: AuditEventType
    ip: str | None
    user_agent: str | None
    metadata: dict[str, Any]
    created_at: datetime
