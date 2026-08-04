from fastapi import APIRouter, Depends,HTTPException
from fastapi import Security
from core.dependencies import get_current_user
from services.auth_service import update_user_service
from schemas.user import UserResponse, UserUpdate
router = APIRouter()


@router.get("/profile",response_model=UserResponse)
async def profile(
    current_user=Depends(get_current_user),
):
    return dict(current_user)
    
@router.patch("", response_model=UserResponse)
async def update_user_api(user: UserUpdate,current_user=Depends(get_current_user)):
    
    user_id = dict(current_user)["id"]
    updated_user = await update_user_service(user_id, user)

    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found or nothing to update"
        )

    return updated_user