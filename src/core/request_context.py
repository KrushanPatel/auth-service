from contextvars import ContextVar

from fastapi import Request

client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)
user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)


async def capture_request_context(request: Request, call_next):
    client_ip.set(request.client.host if request.client else None)
    user_agent.set(request.headers.get("user-agent"))
    return await call_next(request)
