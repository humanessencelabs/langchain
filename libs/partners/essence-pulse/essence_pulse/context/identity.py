"""Identity model for the context layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Identity:
    """A resolved person associated with an event actor identifier.

    Identities are stored in the :class:`ContextStore` and enriched
    over time as more events arrive.  Only the minimum data needed to
    assist the user is stored — this is not a surveillance profile.

    Args:
        actor_id: The opaque actor identifier from the event.
        display_name: Human-readable name.
        relationship: Relationship label (e.g. ``"colleague"``, ``"customer"``).
        contexts: Domain contexts this person appears in.
        notes: Optional free-form notes visible to the user.
        tags: Optional labels.
    """

    actor_id: str
    display_name: str
    relationship: str = "unknown"
    contexts: list[str] = field(default_factory=list)
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_agent_context(self) -> dict[str, str]:
        """Return a minimal context dict safe to pass to an agent.

        Returns only the non-sensitive identity metadata required for
        reasoning — not raw notes or full profile.
        """
        return {
            "actor_id": self.actor_id,
            "display_name": self.display_name,
            "relationship": self.relationship,
            "contexts": ", ".join(self.contexts),
        }
