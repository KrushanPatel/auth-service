from fastapi import APIRouter
from db.session import fetch_one
from schemas.health import HealthResponse
router = APIRouter()


@router.get("/health",response_model=HealthResponse)
async def health():

    result = await fetch_one(
        "SELECT version();"
    )
    
    return {
        "status": "healthy",
        "database": result["version"],
    }