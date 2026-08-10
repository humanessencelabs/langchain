"""In-memory context store — what the system currently remembers.

Memory is inspectable and deletable by the user at any time.
This satisfies the privacy principle: the system has no hidden state.
"""

from __future__ import annotations

import threading
from typing import Any

from essence_pulse.context.identity import Identity

# Demo seed data — uses synthetic personas, no real personal data.
_DEMO_IDENTITIES: list[Identity] = [
    Identity(
        actor_id="customer_123",
        display_name="Alex Chen",
        relationship="customer",
        contexts=["sales"],
        notes="",
        tags=["warm_lead"],
    ),
    Identity(
        actor_id="colleague_456",
        display_name="Jordan Rivera",
        relationship="colleague",
        contexts=["engineering"],
        notes="",
        tags=[],
    ),
]

# Demo calendar — synthetic free/busy data.
_DEMO_CALENDAR: dict[str, Any] = {
    "owner": "demo_user",
    "free_slots": [
        "2026-08-11T09:00:00Z",
        "2026-08-11T10:30:00Z",
        "2026-08-11T14:00:00Z",
        "2026-08-11T15:30:00Z",
    ],
    "busy_slots": [
        "2026-08-11T11:00:00Z",
        "2026-08-11T13:00:00Z",
    ],
}


class ContextStore:
    """Thread-safe in-memory context and memory store.

    Holds identity records, key-value facts, and the user's calendar
    (demo data only).  All data is stored in memory and lost on restart
    unless serialized explicitly.

    Args:
        seed_demo_data: If ``True`` (default), pre-populate with synthetic
            demo personas and calendar data.
    """

    def __init__(self, *, seed_demo_data: bool = True) -> None:
        self._lock = threading.Lock()
        self._identities: dict[str, Identity] = {}
        self._facts: dict[str, Any] = {}
        self._calendar: dict[str, Any] = {}

        if seed_demo_data:
            for identity in _DEMO_IDENTITIES:
                self._identities[identity.actor_id] = identity
            self._calendar = dict(_DEMO_CALENDAR)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def resolve_identity(self, actor_id: str) -> Identity | None:
        """Look up an :class:`Identity` by actor ID.

        Args:
            actor_id: Opaque actor identifier from the event.

        Returns:
            The :class:`Identity` if known, otherwise ``None``.
        """
        with self._lock:
            return self._identities.get(actor_id)

    def upsert_identity(self, identity: Identity) -> None:
        """Insert or update an identity record.

        Args:
            identity: The :class:`Identity` to store.
        """
        with self._lock:
            self._identities[identity.actor_id] = identity

    def delete_identity(self, actor_id: str) -> bool:
        """Remove an identity record (user-initiated deletion).

        Args:
            actor_id: The actor whose record should be deleted.

        Returns:
            ``True`` if the record existed and was removed.
        """
        with self._lock:
            return self._identities.pop(actor_id, None) is not None

    def list_identities(self) -> list[Identity]:
        """Return all stored identities."""
        with self._lock:
            return list(self._identities.values())

    # ------------------------------------------------------------------
    # Calendar (demo)
    # ------------------------------------------------------------------

    def get_calendar(self) -> dict[str, Any]:
        """Return the demo calendar data.

        Returns:
            Dictionary with ``free_slots`` and ``busy_slots`` lists.
        """
        with self._lock:
            return dict(self._calendar)

    # ------------------------------------------------------------------
    # Free-form facts (key-value memory)
    # ------------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Store a key-value fact.

        Args:
            key: Fact identifier.
            value: Fact value.
        """
        with self._lock:
            self._facts[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored fact.

        Args:
            key: Fact identifier.
            default: Value to return if the key is not found.
        """
        with self._lock:
            return self._facts.get(key, default)

    def forget(self, key: str) -> bool:
        """Delete a fact (user-initiated deletion).

        Args:
            key: Fact identifier.

        Returns:
            ``True`` if the fact existed.
        """
        with self._lock:
            return self._facts.pop(key, None) is not None

    def list_facts(self) -> dict[str, Any]:
        """Return all stored facts."""
        with self._lock:
            return dict(self._facts)
