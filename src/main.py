from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.v1.health import router
from api.v1.auth import router as auth_router
from db.connection import create_pool
from db.connection import close_pool
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_pool()
    print("Database connected")

    yield

    await close_pool()
    print("Database disconnected")


app = FastAPI(
    title="Auth Service",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0', port=8000,reload=True)