"""Unit tests for the NormalizedEvent model."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from essence_pulse.bus.event import EventType, NormalizedEvent, Sensitivity


def make_event(**kwargs) -> NormalizedEvent:
    defaults = dict(
        source="test_source",
        event_type=EventType.MESSAGE_RECEIVED,
        actor="actor_1",
        context="test",
        sensitivity=Sensitivity.PRIVATE,
        required_permission="read",
        payload={"body": "hello"},
    )
    defaults.update(kwargs)
    return NormalizedEvent(**defaults)


def test_event_has_auto_id() -> None:
    e = make_event()
    assert e.event_id
    assert len(e.event_id) == 36  # UUID4


def test_event_has_utc_timestamp() -> None:
    e = make_event()
    assert e.timestamp.tzinfo is not None


def test_safe_summary_omits_payload() -> None:
    e = make_event(payload={"body": "secret content", "token": "abc123"})
    summary = e.safe_summary()
    assert "payload" not in summary
    assert summary["source"] == "test_source"
    assert summary["sensitivity"] == "private"


def test_safe_summary_includes_metadata() -> None:
    e = make_event()
    summary = e.safe_summary()
    assert "event_id" in summary
    assert "timestamp" in summary
    assert "processed" in summary


def test_processed_defaults_false() -> None:
    e = make_event()
    assert e.processed is False


def test_tags_default_empty() -> None:
    e = make_event()
    assert e.tags == []


def test_sensitivity_enum() -> None:
    e = make_event(sensitivity=Sensitivity.CONFIDENTIAL)
    assert e.sensitivity == Sensitivity.CONFIDENTIAL
    assert e.safe_summary()["sensitivity"] == "confidential"
