from uuid import UUID

from fastapi import APIRouter, Depends

from core.dependencies import require_role
from schemas.admin import RoleUpdate
from schemas.user import UserResponse
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
    return await update_user_role_service(str(user_id), body.role)
