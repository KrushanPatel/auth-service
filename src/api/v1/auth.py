from fastapi import APIRouter
from schemas.auth import RegisterRequest

router = APIRouter()

@router.post("/register")
async def register(request: RegisterRequest):
    return {
        "message": "Registration endpoint created",
        "user": request.model_dump(),
    }