from fastapi import APIRouter, Depends
from fastapi import Security
from core.dependencies import get_current_user

router = APIRouter()


@router.get("/me")
async def me(
    current_user=Depends(get_current_user),
):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
    }