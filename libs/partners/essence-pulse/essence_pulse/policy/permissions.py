"""Permission model for the Essence Pulse policy engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CapabilityLevel(str, Enum):
    """Ordered capability levels (least to most privileged)."""

    READ = "read"
    PROPOSE = "propose"
    EXECUTE = "execute"
    ADMIN = "admin"

    @classmethod
    def ordered(cls) -> list["CapabilityLevel"]:
        """Return levels from least to most privileged."""
        return [cls.READ, cls.PROPOSE, cls.EXECUTE, cls.ADMIN]

    def satisfies(self, required: "CapabilityLevel") -> bool:
        """Return True if this level is at least as privileged as *required*.

        Args:
            required: The minimum :class:`CapabilityLevel` needed.
        """
        order = self.ordered()
        return order.index(self) >= order.index(required)


@dataclass
class Permission:
    """A scoped capability grant for an agent.

    Args:
        agent_id: Identifier of the agent holding this permission.
        resource: The resource being accessed (e.g. ``"calendar"``,
            ``"messages"``).
        level: The :class:`CapabilityLevel` granted.
        contexts: Optional list of context labels this permission is
            restricted to.  An empty list means all contexts.
        expires_at: Optional ISO-8601 expiry timestamp.
    """

    agent_id: str
    resource: str
    level: CapabilityLevel
    contexts: list[str] = field(default_factory=list)
    expires_at: str | None = None

    def allows(self, resource: str, level: CapabilityLevel, context: str = "") -> bool:
        """Check whether this permission covers a given access request.

        Args:
            resource: Resource being accessed.
            level: Required capability level.
            context: Optional context label (e.g. ``"sales"``).

        Returns:
            ``True`` if the permission covers the request.
        """
        if self.resource != resource and self.resource != "*":
            return False
        if not self.level.satisfies(level):
            return False
        if self.contexts and context and context not in self.contexts:
            return False
        return True


# Default permission grants used by the demo.  In production these would
# come from a persistent, user-managed policy store.
DEFAULT_DEMO_PERMISSIONS: list[Permission] = [
    Permission(
        agent_id="classifier_agent",
        resource="messages",
        level=CapabilityLevel.READ,
        contexts=[],
    ),
    Permission(
        agent_id="scheduler_agent",
        resource="calendar",
        level=CapabilityLevel.READ,
        contexts=[],
    ),
    Permission(
        agent_id="scheduler_agent",
        resource="messages",
        level=CapabilityLevel.PROPOSE,
        contexts=[],
    ),
]
