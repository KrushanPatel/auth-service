from unittest.mock import AsyncMock

import pytest

import services.audit_service as audit_service


@pytest.fixture(autouse=True)
def audit_events(monkeypatch):
    insert_audit_event = AsyncMock()
    monkeypatch.setattr(audit_service, "insert_audit_event", insert_audit_event)
    return insert_audit_event
