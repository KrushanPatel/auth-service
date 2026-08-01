from fastapi import APIRouter, Depends
from fastapi import Security
from core.dependencies import get_current_user
from schemas.user import UserResponse
router = APIRouter()


@router.get("/me",response_model=UserResponse)
async def me(
    current_user=Depends(get_current_user),
):
    return dict(current_user)
    