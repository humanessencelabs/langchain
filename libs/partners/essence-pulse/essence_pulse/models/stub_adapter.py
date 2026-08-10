"""Deterministic stub model adapter for local/offline demos.

This adapter uses hard-coded heuristics to simulate AI reasoning.  It
requires no API key and produces deterministic outputs, making it ideal
for unit tests and live demos.

Do not use this adapter in production.
"""

from __future__ import annotations

from typing import Any

from essence_pulse.models.base import ModelProvider


class StubAdapter(ModelProvider):
    """Offline, deterministic model adapter.

    Responses are keyword-based heuristics.  Useful for demos and tests.

    Args:
        verbose: If ``True``, prefix every response with ``[STUB]``.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        self._verbose = verbose

    @property
    def provider_name(self) -> str:
        return "stub"

    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        """Return a deterministic response based on prompt keywords.

        Args:
            prompt: The instruction to respond to.
            context: Ignored by the stub; present for interface compatibility.

        Returns:
            A hard-coded response string.
        """
        lowered = prompt.lower()

        if "classify" in lowered or "event type" in lowered:
            response = self._classify(prompt)
        elif "schedule" in lowered or "calendar" in lowered or "meeting" in lowered:
            response = self._schedule(prompt)
        elif "respond" in lowered or "reply" in lowered or "suggest" in lowered:
            response = self._suggest_reply(prompt)
        elif "summarize" in lowered or "summary" in lowered:
            response = "Summary: a scheduling request was received and a response proposed."
        else:
            response = "Understood. No action required at this time."

        return f"[STUB] {response}" if self._verbose else response

    # ------------------------------------------------------------------
    # Internal heuristics
    # ------------------------------------------------------------------

    def _classify(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "meet" in lowered or "tomorrow" in lowered or "schedule" in lowered:
            return (
                '{"event_type": "scheduling_request", "confidence": 0.94, '
                '"priority": "medium", "requires_action": true}'
            )
        if "urgent" in lowered or "asap" in lowered or "emergency" in lowered:
            return (
                '{"event_type": "urgent_message", "confidence": 0.91, '
                '"priority": "high", "requires_action": true}'
            )
        return (
            '{"event_type": "informational", "confidence": 0.80, '
            '"priority": "low", "requires_action": false}'
        )

    def _schedule(self, prompt: str) -> str:
        return (
            '{"available_slots": ["2026-08-11T14:00:00Z", "2026-08-11T15:30:00Z"], '
            '"suggested_slot": "2026-08-11T14:00:00Z", '
            '"reason": "First available afternoon slot tomorrow"}'
        )

    def _suggest_reply(self, prompt: str) -> str:
        return (
            "Hi! Tomorrow afternoon works great. "
            "How about 2 PM? Looking forward to it."
        )
