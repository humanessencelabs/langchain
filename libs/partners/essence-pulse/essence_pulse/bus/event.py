"""Normalized event model for the Essence Pulse event bus.

Every raw signal — notification, sensor reading, calendar update — is
transformed into a ``NormalizedEvent`` before entering the bus.  This
schema is the single source of truth for the pipeline.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Sensitivity(str, Enum):
    """Classification of how sensitive an event payload is."""

    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class EventType(str, Enum):
    """Canonical event types understood by the pipeline."""

    MESSAGE_RECEIVED = "message.received"
    CALENDAR_UPDATE = "calendar.update"
    NOTIFICATION = "notification.generic"
    SENSOR_READING = "sensor.reading"
    SYSTEM_ALERT = "system.alert"
    USER_ACTION = "user.action"
    AGENT_ACTION = "agent.action"


@dataclass
class NormalizedEvent:
    """A normalized, enriched event travelling through the Essence Pulse bus.

    Args:
        source: The connector that produced the event (e.g. ``"whatsapp"``).
        event_type: Canonical :class:`EventType` string.
        actor: Opaque identifier for whoever triggered the event.
        context: High-level domain label (e.g. ``"sales"``, ``"personal"``).
        sensitivity: Data sensitivity level.
        required_permission: Minimum permission needed to process the payload.
        payload: Raw, untrusted event data.  Always treat as untrusted input.
        event_id: Auto-generated UUID for deduplication.
        timestamp: UTC timestamp of event creation.
        processed: Whether the orchestrator has finished handling this event.
        tags: Optional free-form labels for filtering.
    """

    source: str
    event_type: str
    actor: str
    context: str
    sensitivity: Sensitivity
    required_permission: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    tags: list[str] = field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        """Return a minimal, non-sensitive summary safe for logging.

        The raw ``payload`` is omitted; only metadata is included.
        """
        return {
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type,
            "actor": self.actor,
            "context": self.context,
            "sensitivity": self.sensitivity.value
            if isinstance(self.sensitivity, Sensitivity)
            else self.sensitivity,
            "required_permission": self.required_permission,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "tags": self.tags,
        }
