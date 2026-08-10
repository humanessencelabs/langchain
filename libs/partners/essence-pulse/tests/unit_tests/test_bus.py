"""Unit tests for the EventBus."""

from __future__ import annotations

import threading

from essence_pulse.bus.bus import EventBus
from essence_pulse.bus.event import EventType, NormalizedEvent, Sensitivity


def _make_event(actor: str = "actor_1") -> NormalizedEvent:
    return NormalizedEvent(
        source="test",
        event_type=EventType.MESSAGE_RECEIVED,
        actor=actor,
        context="test",
        sensitivity=Sensitivity.PUBLIC,
        required_permission="read",
        payload={},
    )


def test_publish_and_history() -> None:
    bus = EventBus()
    e = _make_event()
    bus.publish(e)
    assert len(bus.history) == 1
    assert bus.history[0] is e


def test_subscriber_called() -> None:
    bus = EventBus()
    received: list[NormalizedEvent] = []
    bus.subscribe(received.append)
    e = _make_event()
    bus.publish(e)
    assert received == [e]


def test_multiple_subscribers() -> None:
    bus = EventBus()
    counts: list[int] = [0, 0]
    bus.subscribe(lambda _: counts.__setitem__(0, counts[0] + 1))
    bus.subscribe(lambda _: counts.__setitem__(1, counts[1] + 1))
    bus.publish(_make_event())
    assert counts == [1, 1]


def test_pending_returns_unprocessed() -> None:
    bus = EventBus()
    e1 = _make_event("a")
    e2 = _make_event("b")
    bus.publish(e1)
    bus.publish(e2)
    e1.processed = True
    assert bus.pending() == [e2]


def test_thread_safe_publish() -> None:
    bus = EventBus()
    errors: list[Exception] = []

    def publisher() -> None:
        try:
            for _ in range(50):
                bus.publish(_make_event())
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=publisher) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(bus.history) == 200
