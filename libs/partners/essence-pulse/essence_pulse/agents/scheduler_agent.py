"""Scheduler agent — proposes meeting responses using calendar availability."""

from __future__ import annotations

import json
from typing import Any

from essence_pulse.agents.base_agent import AgentResult, BaseAgent
from essence_pulse.bus.event import NormalizedEvent
from essence_pulse.models.base import ModelProvider


class SchedulerAgent(BaseAgent):
    """Generates a suggested meeting response based on calendar availability.

    The agent receives only the free/busy slots it has been granted
    permission to access — not the full calendar or personal details.

    Args:
        model: The :class:`ModelProvider` used for response generation.
        free_slots: List of ISO-8601 free-time slot strings from the
            context layer (already permission-checked by the orchestrator).
    """

    def __init__(self, model: ModelProvider, free_slots: list[str]) -> None:
        super().__init__(agent_id="scheduler_agent", model=model)
        self._free_slots = free_slots

    @property
    def description(self) -> str:
        return "Proposes a friendly reply for scheduling requests using calendar availability."

    @property
    def required_permissions(self) -> list[tuple[str, str]]:
        return [("calendar", "read"), ("messages", "propose")]

    def run(self, event: NormalizedEvent, context: dict[str, Any]) -> AgentResult:
        """Generate a suggested reply.

        Args:
            event: The scheduling-related event.
            context: Identity metadata for the actor.

        Returns:
            An :class:`AgentResult` with the suggested reply and the slot.
        """
        raw_content = str(event.payload.get("body", ""))
        sender = context.get("display_name", "the sender")

        # Build instruction with trusted calendar data in context
        instruction = (
            f"The user received a meeting request from {sender}. "
            f"Available time slots (trusted data): {self._free_slots}. "
            "Suggest the best slot and write a short, friendly reply "
            "in the first person. Return a JSON object with keys: "
            "suggested_slot (ISO-8601), suggested_reply (string)."
        )
        prompt = self._safe_prompt(instruction, raw_content)
        response = self._model.complete(prompt, context=context)

        # Try schedule parsing first, fall back to reply parsing
        suggestion = self._parse_suggestion(response)
        if not suggestion.get("suggested_reply"):
            suggestion["suggested_reply"] = self._model.complete(
                f"Suggest a short friendly reply to: {raw_content}",
                context=context,
            )

        return AgentResult(
            agent_id=self.agent_id,
            success=True,
            action="send_message",
            data=suggestion,
            reasoning=(
                f"Proposed slot {suggestion.get('suggested_slot')} "
                f"based on calendar availability for scheduling request from {sender}."
            ),
            requires_approval=True,  # Sending a message always requires approval
        )

    def _parse_suggestion(self, response: str) -> dict[str, Any]:
        """Parse model output into a suggestion dict.

        Args:
            response: Raw model response string.
        """
        try:
            clean = response.replace("[STUB]", "").strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(clean[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: treat the entire response as the reply
        return {
            "suggested_slot": self._free_slots[0] if self._free_slots else None,
            "suggested_reply": response.replace("[STUB]", "").strip(),
        }
