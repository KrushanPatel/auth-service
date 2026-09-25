import json
from datetime import datetime
from uuid import UUID

from db.session import fetch_all, fetch_one


def _decode_metadata(row: dict) -> dict:
    return {**row, "metadata": json.loads(row["metadata"])}


async def insert_audit_event(
    user_id: UUID | None,
    event_type: str,
    ip: str | None,
    user_agent: str | None,
    metadata: dict,
):
    query = """
        INSERT INTO audit_events (
            user_id,
            event_type,
            ip,
            user_agent,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5::jsonb)
        RETURNING *;
    """

    row = await fetch_one(query, user_id, event_type, ip, user_agent, json.dumps(metadata))
    return _decode_metadata(row) if row else None


async def list_audit_events(
    user_id: UUID | None,
    event_type: str | None,
    before: datetime | None,
    limit: int,
):
    query = """
        SELECT *
        FROM audit_events
        WHERE ($1::uuid IS NULL OR user_id = $1)
          AND ($2::text IS NULL OR event_type = $2)
          AND ($3::timestamptz IS NULL OR created_at < $3)
        ORDER BY created_at DESC
        LIMIT $4;
    """

    rows = await fetch_all(query, user_id, event_type, before, limit)
    return [_decode_metadata(row) for row in rows]
