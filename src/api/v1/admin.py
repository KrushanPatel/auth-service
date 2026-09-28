from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from core.dependencies import require_role
from schemas.admin import AuditEventResponse, AuditEventType, RoleUpdate
from schemas.user import UserResponse
from services.audit_service import list_audit_events_service
from services.auth_service import list_users_service, update_user_role_service

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def list_users_api(current_user=Depends(require_role("admin"))):
    return await list_users_service()


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role_api(
    user_id: UUID,
    body: RoleUpdate,
    current_user=Depends(require_role("admin")),
):
    return await update_user_role_service(str(user_id), body.role, current_user["id"])


@router.get("/audit-events", response_model=list[AuditEventResponse])
async def list_audit_events_api(
    user_id: UUID | None = None,
    event_type: AuditEventType | None = None,
    before: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(require_role("admin")),
):
    return await list_audit_events_service(user_id, event_type, before, limit)
