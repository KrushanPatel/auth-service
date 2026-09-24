import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.v1.admin import router as admin_router
from api.v1.auth import router as auth_router
from api.v1.health import router as health_router
from api.v1.mfa import router as mfa_router
from api.v1.users import router as users_router
from core.email import validate_email_config
from core.google_oauth import validate_google_oauth_config
from core.mfa_crypto import validate_mfa_config
from db.connection import close_pool, create_pool
from services.refresh_token_service import cleanup_task


@asynccontextmanager
async def lifespan(app: FastAPI):

    validate_email_config()
    validate_mfa_config()
    await create_pool()
    validate_google_oauth_config()
    validate_redis_config()
    print("Database connected")
    task = asyncio.create_task(cleanup_task())
    yield

    task.cancel()
    await close_pool()
    print("Database disconnected")


app = FastAPI(
    title="Auth Service",
    lifespan=lifespan,
)

app.include_router(
    health_router,
    prefix="",
    tags=["Health"],
)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["Users"],
)

app.include_router(
    mfa_router,
    prefix="/api/v1/mfa",
    tags=["MFA"],
)

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
