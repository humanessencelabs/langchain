"""Policy engine — checks agent permissions before data access."""

from __future__ import annotations

from dataclasses import dataclass

from essence_pulse.policy.permissions import CapabilityLevel, Permission


@dataclass
class PolicyDecision:
    """Result of a policy check.

    Args:
        allowed: Whether the request is permitted.
        agent_id: The requesting agent.
        resource: The resource being accessed.
        level: The required capability level.
        reason: Human-readable explanation.
    """

    allowed: bool
    agent_id: str
    resource: str
    level: CapabilityLevel
    reason: str


class PolicyEngine:
    """Evaluates permission requests against a set of :class:`Permission` grants.

    Args:
        permissions: Initial list of permission grants.  More can be added
            via :meth:`grant`.

    Example::

        engine = PolicyEngine(DEFAULT_DEMO_PERMISSIONS)
        decision = engine.check("scheduler_agent", "calendar", CapabilityLevel.READ)
        assert decision.allowed
    """

    def __init__(self, permissions: list[Permission] | None = None) -> None:
        self._permissions: list[Permission] = list(permissions or [])

    def grant(self, permission: Permission) -> None:
        """Add a new permission grant at runtime.

        Args:
            permission: The :class:`Permission` to add.
        """
        self._permissions.append(permission)

    def revoke(self, agent_id: str, resource: str) -> int:
        """Remove all grants for *agent_id* on *resource*.

        Args:
            agent_id: The agent whose permission is being revoked.
            resource: The resource to revoke access to.

        Returns:
            Number of grants removed.
        """
        before = len(self._permissions)
        self._permissions = [
            p
            for p in self._permissions
            if not (p.agent_id == agent_id and p.resource == resource)
        ]
        return before - len(self._permissions)

    def check(
        self,
        agent_id: str,
        resource: str,
        level: CapabilityLevel,
        context: str = "",
    ) -> PolicyDecision:
        """Evaluate whether *agent_id* may access *resource* at *level*.

        Args:
            agent_id: Identifier of the requesting agent.
            resource: Resource being accessed.
            level: Minimum capability level required.
            context: Optional context label for context-scoped permissions.

        Returns:
            A :class:`PolicyDecision` describing the outcome.
        """
        for perm in self._permissions:
            if perm.agent_id == agent_id and perm.allows(resource, level, context):
                return PolicyDecision(
                    allowed=True,
                    agent_id=agent_id,
                    resource=resource,
                    level=level,
                    reason=f"Granted by permission: {perm.resource}@{perm.level.value}",
                )
        return PolicyDecision(
            allowed=False,
            agent_id=agent_id,
            resource=resource,
            level=level,
            reason=f"No permission for {agent_id} to {level.value} {resource}",
        )

    def list_permissions(self, agent_id: str | None = None) -> list[Permission]:
        """Return all current permission grants, optionally filtered.

        Args:
            agent_id: If provided, only return grants for this agent.
        """
        if agent_id:
            return [p for p in self._permissions if p.agent_id == agent_id]
        return list(self._permissions)
