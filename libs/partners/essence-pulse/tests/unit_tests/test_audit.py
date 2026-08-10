"""Unit tests for the audit log."""

from __future__ import annotations

import pytest

from essence_pulse.audit.audit_log import AuditLog


def test_record_and_count() -> None:
    log = AuditLog()
    assert log.count() == 0
    log.record(
        action="classify",
        agent_id="classifier_agent",
        event_id="evt_001",
        outcome="success",
    )
    assert log.count() == 1


def test_entries_returns_all() -> None:
    log = AuditLog()
    log.record(action="a", agent_id="ag1", event_id="e1", outcome="ok")
    log.record(action="b", agent_id="ag2", event_id="e2", outcome="ok")
    entries = log.entries()
    assert len(entries) == 2


def test_entries_filtered_by_action() -> None:
    log = AuditLog()
    log.record(action="classify", agent_id="ag1", event_id="e1", outcome="ok")
    log.record(action="send_message", agent_id="ag2", event_id="e1", outcome="approved")
    filtered = log.entries(action="classify")
    assert len(filtered) == 1
    assert filtered[0].action == "classify"


def test_entry_is_frozen() -> None:
    log = AuditLog()
    entry = log.record(action="test", agent_id="ag1", event_id="e1", outcome="ok")
    with pytest.raises((AttributeError, TypeError)):
        entry.action = "mutated"  # type: ignore[misc]


def test_approved_by_recorded() -> None:
    log = AuditLog()
    entry = log.record(
        action="send_message",
        agent_id="scheduler_agent",
        event_id="e1",
        outcome="approved",
        approved_by="user",
    )
    assert entry.approved_by == "user"


def test_metadata_stored() -> None:
    log = AuditLog()
    entry = log.record(
        action="classify",
        agent_id="ag",
        event_id="e1",
        outcome="ok",
        metadata={"event_type": "scheduling_request"},
    )
    assert entry.metadata["event_type"] == "scheduling_request"


def test_entry_has_unique_ids() -> None:
    log = AuditLog()
    e1 = log.record(action="a", agent_id="ag", event_id="e1", outcome="ok")
    e2 = log.record(action="b", agent_id="ag", event_id="e1", outcome="ok")
    assert e1.entry_id != e2.entry_id
