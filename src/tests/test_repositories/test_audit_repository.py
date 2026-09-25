from datetime import datetime, timedelta, timezone

import pytest
from asyncpg.exceptions import CheckViolationError

from db.session import execute
from repositories.audit_repository import insert_audit_event, list_audit_events
from repositories.user_repository import create_user


async def _create_test_user(username="krushan", email="krushan@example.com"):
    return await create_user(
        username=username,
        email=email,
        password_hash="hashed-password",
        first_name="Krushan",
        last_name="Patel",
    )


async def _insert(user_id=None, event_type="login_success", **overrides):
    data = {
        "user_id": user_id,
        "event_type": event_type,
        "ip": "203.0.113.7",
        "user_agent": "pytest",
        "metadata": {},
    }
    data.update(overrides)
    return await insert_audit_event(**data)


async def test_insert_audit_event_round_trips_metadata():
    user = await _create_test_user()

    event = await _insert(user["id"], metadata={"method": "password"})

    assert event["user_id"] == user["id"]
    assert event["event_type"] == "login_success"
    assert event["ip"] == "203.0.113.7"
    assert event["metadata"] == {"method": "password"}
    assert event["created_at"] is not None


async def test_insert_audit_event_allows_null_user():
    event = await _insert(None, "login_failure", metadata={"reason": "unknown_account"})

    assert event["user_id"] is None


async def test_insert_audit_event_rejects_unknown_event_type():
    with pytest.raises(CheckViolationError):
        await _insert(None, "not_a_real_event")


async def test_list_audit_events_newest_first_with_filters():
    user = await _create_test_user()
    other = await _create_test_user("other", "other@example.com")
    first = await _insert(user["id"], "login_success")
    second = await _insert(user["id"], "logout")
    await _insert(other["id"], "login_success")

    by_user = await list_audit_events(user["id"], None, None, 50)
    assert [e["id"] for e in by_user] == [second["id"], first["id"]]

    by_type = await list_audit_events(None, "login_success", None, 50)
    assert {e["user_id"] for e in by_type} == {user["id"], other["id"]}

    assert len(await list_audit_events(None, None, None, 2)) == 2


async def test_list_audit_events_before_cursor():
    user = await _create_test_user()
    older = await _insert(user["id"])
    await execute(
        "UPDATE audit_events SET created_at = $2 WHERE id = $1",
        older["id"],
        datetime.now(timezone.utc) - timedelta(hours=1),
    )
    await _insert(user["id"])

    events = await list_audit_events(
        None, None, datetime.now(timezone.utc) - timedelta(minutes=30), 50
    )

    assert [e["id"] for e in events] == [older["id"]]


async def test_audit_events_survive_user_deletion():
    user = await _create_test_user()
    event = await _insert(user["id"])

    await execute("DELETE FROM users WHERE id = $1", user["id"])

    events = await list_audit_events(None, None, None, 50)
    assert [(e["id"], e["user_id"]) for e in events] == [(event["id"], None)]
