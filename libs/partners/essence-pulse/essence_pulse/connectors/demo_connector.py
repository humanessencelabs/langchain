"""Demo connector — emits synthetic events for local development.

This connector generates realistic but entirely fictional events.
It never connects to any real app, service, or device.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Callable

from essence_pulse.bus.event import EventType, NormalizedEvent, Sensitivity

# Synthetic WhatsApp-style messages — no real personal data.
DEMO_SCENARIOS: list[dict] = [
    {
        "label": "scheduling_request",
        "event": NormalizedEvent(
            source="whatsapp_demo",
            event_type=EventType.MESSAGE_RECEIVED,
            actor="customer_123",
            context="sales",
            sensitivity=Sensitivity.PRIVATE,
            required_permission="read",
            payload={
                "body": "Can we meet tomorrow afternoon?",
                "thread_id": "thread_001",
                "platform": "whatsapp",
            },
            tags=["demo"],
        ),
    },
    {
        "label": "urgent_message",
        "event": NormalizedEvent(
            source="email_demo",
            event_type=EventType.MESSAGE_RECEIVED,
            actor="colleague_456",
            context="engineering",
            sensitivity=Sensitivity.INTERNAL,
            required_permission="read",
            payload={
                "body": "The staging deploy is failing — need your sign-off ASAP.",
                "thread_id": "thread_002",
                "platform": "email",
            },
            tags=["demo", "urgent"],
        ),
    },
    {
        "label": "informational",
        "event": NormalizedEvent(
            source="newsletter_demo",
            event_type=EventType.NOTIFICATION,
            actor="newsletter_system",
            context="personal",
            sensitivity=Sensitivity.PUBLIC,
            required_permission="read",
            payload={
                "body": "Your weekly digest is ready.",
                "thread_id": "thread_003",
                "platform": "email",
            },
            tags=["demo"],
        ),
    },
]


class DemoConnector:
    """Emits pre-defined synthetic events for the demo pipeline.

    Args:
        scenario: Which demo scenario to emit.  One of ``"scheduling_request"``,
            ``"urgent_message"``, or ``"informational"``.  Defaults to
            ``"scheduling_request"``.
    """

    def __init__(self, scenario: str = "scheduling_request") -> None:
        self._scenario = scenario

    def emit(self, publish: Callable[[NormalizedEvent], None]) -> NormalizedEvent:
        """Emit the configured demo event via *publish*.

        Args:
            publish: A callable that accepts a :class:`NormalizedEvent`
                (typically :meth:`EventBus.publish`).

        Returns:
            The emitted event.
        """
        scenario_map = {s["label"]: s["event"] for s in DEMO_SCENARIOS}
        event = scenario_map.get(self._scenario, DEMO_SCENARIOS[0]["event"])

        # Stamp a fresh timestamp so every run looks current
        event = dataclasses.replace(event, timestamp=datetime.now(timezone.utc))
        publish(event)
        return event

    @staticmethod
    def available_scenarios() -> list[str]:
        """Return the list of available demo scenario labels."""
        return [s["label"] for s in DEMO_SCENARIOS]
