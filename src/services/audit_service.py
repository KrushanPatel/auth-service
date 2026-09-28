from datetime import datetime
from uuid import UUID

from core.request_context import client_ip, user_agent
from repositories.audit_repository import insert_audit_event, list_audit_events
from schemas.admin import AuditEventType


async def record_event(event_type: AuditEventType, user_id: UUID | str | None = None, **metadata):
    await insert_audit_event(
        user_id=UUID(str(user_id)) if user_id else None,
        event_type=event_type,
        ip=client_ip.get(),
        user_agent=user_agent.get(),
        metadata=metadata,
    )


async def list_audit_events_service(
    user_id: UUID | None,
    event_type: AuditEventType | None,
    before: datetime | None,
    limit: int,
):
    return await list_audit_events(user_id, event_type, before, limit)
