"""Immutable-style append-only audit log.

Every agent action, data access, and approval decision is recorded here.
Entries are never mutated or deleted — the log can optionally be persisted
to a newline-delimited JSON file.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    """A single immutable audit log entry.

    Args:
        entry_id: Auto-generated UUID.
        timestamp: UTC timestamp of the record.
        action: Machine-readable action label (e.g. ``"send_message"``).
        agent_id: The agent that performed the action.
        event_id: The :class:`NormalizedEvent` this action relates to.
        outcome: Result label (e.g. ``"approved"``, ``"rejected"``,
            ``"denied_by_policy"``).
        approved_by: Who approved the action (``"user"``, ``"auto"``, or
            ``None`` for read-only operations).
        metadata: Optional additional context.  Must not contain PII.
    """

    entry_id: str
    timestamp: str
    action: str
    agent_id: str
    event_id: str
    outcome: str
    approved_by: str | None
    metadata: dict[str, Any]


class AuditLog:
    """Thread-safe, append-only audit log.

    Args:
        persist_path: Optional file path.  If provided, every entry is
            immediately appended as a JSON line.

    Example::

        log = AuditLog()
        log.record(action="classify", agent_id="classifier_agent", ...)
        entries = log.entries()
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._entries: list[AuditEntry] = []
        self._lock = threading.Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        action: str,
        agent_id: str,
        event_id: str,
        outcome: str,
        approved_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Append a new entry to the log.

        Args:
            action: Machine-readable action label.
            agent_id: The acting agent.
            event_id: Related event UUID.
            outcome: Result of the action.
            approved_by: Who authorized the action.
            metadata: Optional supplemental data (no PII).

        Returns:
            The newly created :class:`AuditEntry`.
        """
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            agent_id=agent_id,
            event_id=event_id,
            outcome=outcome,
            approved_by=approved_by,
            metadata=metadata or {},
        )
        with self._lock:
            self._entries.append(entry)
            if self._persist_path:
                with self._persist_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def entries(self, *, action: str | None = None) -> list[AuditEntry]:
        """Return all log entries, optionally filtered by action.

        Args:
            action: If provided, only return entries matching this action.
        """
        with self._lock:
            if action:
                return [e for e in self._entries if e.action == action]
            return list(self._entries)

    def count(self) -> int:
        """Return the total number of recorded entries."""
        with self._lock:
            return len(self._entries)
