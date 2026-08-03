from fastapi import APIRouter, Depends,HTTPException
from fastapi import Security
from core.dependencies import get_current_user
from services.auth_service import update_user_service
from schemas.user import UserResponse, UserUpdate
router = APIRouter()


@router.get("/me",response_model=UserResponse)
async def me(
    current_user=Depends(get_current_user),
):
    return dict(current_user)
    
@router.patch("/update/{user_id}")
async def update_user_api(user: UserUpdate,user_id:str,):

    
    updated_user = await update_user_service(user_id, user)

    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found or nothing to update"
        )

    return updated_user