"""In-memory normalized event bus.

The bus acts as the central message broker.  Connectors publish events;
the orchestrator (and any subscriber) consumes them in order.

This implementation is intentionally simple — a thread-safe deque — so
the prototype runs without external dependencies.  A production system
would swap this for a durable queue (Kafka, Pub/Sub, etc.).
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Callable

from essence_pulse.bus.event import NormalizedEvent


SubscriberFn = Callable[[NormalizedEvent], None]


class EventBus:
    """Thread-safe in-memory event bus.

    Args:
        max_history: Maximum number of events retained in the history
            deque.  Older entries are discarded.  Defaults to 1000.

    Example::

        bus = EventBus()
        bus.subscribe(lambda e: print(e.event_type))
        bus.publish(event)
    """

    def __init__(self, max_history: int = 1000) -> None:
        self._subscribers: list[SubscriberFn] = []
        self._history: deque[NormalizedEvent] = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def subscribe(self, fn: SubscriberFn) -> None:
        """Register a callback to receive every published event.

        Args:
            fn: Callable that accepts a single :class:`NormalizedEvent`.
        """
        with self._lock:
            self._subscribers.append(fn)

    def publish(self, event: NormalizedEvent) -> None:
        """Publish an event to all registered subscribers.

        The event is appended to the history *before* notifying
        subscribers so that subscribers can inspect history if needed.

        Args:
            event: The :class:`NormalizedEvent` to broadcast.
        """
        with self._lock:
            self._history.append(event)
            subscribers = list(self._subscribers)
        for fn in subscribers:
            fn(event)

    @property
    def history(self) -> list[NormalizedEvent]:
        """Return a snapshot of all retained events (oldest first)."""
        with self._lock:
            return list(self._history)

    def pending(self) -> list[NormalizedEvent]:
        """Return unprocessed events from the history."""
        with self._lock:
            return [e for e in self._history if not e.processed]
