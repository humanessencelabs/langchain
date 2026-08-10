"""Notification connector interface.

A production notification connector would subscribe to a real push
notification service (e.g. FCM, APNs, a webhook endpoint) and normalize
incoming signals into :class:`NormalizedEvent` objects.

This module defines the connector interface; see ``demo_connector.py``
for a synthetic implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from essence_pulse.bus.event import NormalizedEvent


class NotificationConnector(ABC):
    """Abstract interface for notification/event source connectors.

    Implement this class to connect a real data source to the Essence
    Pulse event bus.
    """

    @property
    @abstractmethod
    def connector_id(self) -> str:
        """Unique identifier for this connector."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable connector name."""

    @abstractmethod
    def emit(self, publish: Callable[[NormalizedEvent], None]) -> NormalizedEvent:
        """Normalize and emit one event via *publish*.

        Args:
            publish: Callable that accepts a :class:`NormalizedEvent`.

        Returns:
            The emitted event.
        """
