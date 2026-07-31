from fastapi import APIRouter

from db.session import fetch_one

router = APIRouter()


@router.get("/health")
async def health():

    result = await fetch_one(
        "SELECT version();"
    )

    return {
        "status": "healthy",
        "database": result["version"],
    }