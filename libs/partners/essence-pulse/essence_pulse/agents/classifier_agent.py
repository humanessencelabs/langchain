"""Classifier agent — identifies event type and priority."""

from __future__ import annotations

import json
from typing import Any

from essence_pulse.agents.base_agent import AgentResult, BaseAgent
from essence_pulse.bus.event import NormalizedEvent
from essence_pulse.models.base import ModelProvider


class ClassifierAgent(BaseAgent):
    """Classifies incoming events by type and priority.

    This agent reads the event payload (treated as untrusted input) and
    returns a structured classification without performing any write
    operations.

    Args:
        model: The :class:`ModelProvider` used for classification.
    """

    def __init__(self, model: ModelProvider) -> None:
        super().__init__(agent_id="classifier_agent", model=model)

    @property
    def description(self) -> str:
        return "Classifies events by type, priority, and whether action is required."

    @property
    def required_permissions(self) -> list[tuple[str, str]]:
        return [("messages", "read")]

    def run(self, event: NormalizedEvent, context: dict[str, Any]) -> AgentResult:
        """Classify the event.

        Args:
            event: The event to classify.
            context: Minimal identity metadata for the actor.

        Returns:
            An :class:`AgentResult` with classification data.
        """
        raw_content = str(event.payload.get("body", ""))
        instruction = (
            "Classify the following message. "
            "Return a JSON object with keys: "
            "event_type (string), confidence (float 0-1), "
            "priority (low|medium|high), requires_action (bool). "
            "Do not include any other text."
        )
        prompt = self._safe_prompt(instruction, raw_content)
        response = self._model.complete(prompt, context=context)

        classification = self._parse_classification(response)
        return AgentResult(
            agent_id=self.agent_id,
            success=True,
            action="classify",
            data=classification,
            reasoning=(
                f"Classified '{raw_content[:80]}' as "
                f"{classification.get('event_type')} "
                f"(confidence={classification.get('confidence')}, "
                f"priority={classification.get('priority')})"
            ),
            requires_approval=False,
        )

    def _parse_classification(self, response: str) -> dict[str, Any]:
        """Parse the model response into a classification dict.

        Falls back to safe defaults if parsing fails.

        Args:
            response: Raw model response string.
        """
        try:
            # Strip [STUB] prefix if present
            clean = response.replace("[STUB]", "").strip()
            # Find first JSON object in the response
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(clean[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return {
            "event_type": "unknown",
            "confidence": 0.5,
            "priority": "low",
            "requires_action": False,
        }
