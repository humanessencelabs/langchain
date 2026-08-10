"""Unit tests for the policy engine."""

from __future__ import annotations

import pytest

from essence_pulse.policy.engine import PolicyEngine
from essence_pulse.policy.permissions import CapabilityLevel, Permission


def _engine_with_defaults() -> PolicyEngine:
    return PolicyEngine(
        [
            Permission(
                agent_id="agent_a",
                resource="messages",
                level=CapabilityLevel.READ,
            ),
            Permission(
                agent_id="agent_b",
                resource="calendar",
                level=CapabilityLevel.PROPOSE,
                contexts=["sales"],
            ),
        ]
    )


def test_allowed_read() -> None:
    engine = _engine_with_defaults()
    decision = engine.check("agent_a", "messages", CapabilityLevel.READ)
    assert decision.allowed


def test_denied_no_permission() -> None:
    engine = _engine_with_defaults()
    decision = engine.check("agent_a", "calendar", CapabilityLevel.READ)
    assert not decision.allowed


def test_denied_insufficient_level() -> None:
    engine = _engine_with_defaults()
    decision = engine.check("agent_a", "messages", CapabilityLevel.EXECUTE)
    assert not decision.allowed


def test_context_scoped_permission_allowed() -> None:
    engine = _engine_with_defaults()
    decision = engine.check("agent_b", "calendar", CapabilityLevel.READ, context="sales")
    assert decision.allowed


def test_context_scoped_permission_denied_wrong_context() -> None:
    engine = _engine_with_defaults()
    decision = engine.check("agent_b", "calendar", CapabilityLevel.READ, context="personal")
    assert not decision.allowed


def test_grant_adds_permission() -> None:
    engine = PolicyEngine()
    decision_before = engine.check("agent_c", "messages", CapabilityLevel.READ)
    assert not decision_before.allowed

    engine.grant(Permission(agent_id="agent_c", resource="messages", level=CapabilityLevel.READ))
    decision_after = engine.check("agent_c", "messages", CapabilityLevel.READ)
    assert decision_after.allowed


def test_revoke_removes_permission() -> None:
    engine = _engine_with_defaults()
    removed = engine.revoke("agent_a", "messages")
    assert removed == 1
    assert not engine.check("agent_a", "messages", CapabilityLevel.READ).allowed


def test_list_permissions_filtered() -> None:
    engine = _engine_with_defaults()
    perms = engine.list_permissions("agent_a")
    assert all(p.agent_id == "agent_a" for p in perms)


def test_capability_level_satisfies() -> None:
    assert CapabilityLevel.EXECUTE.satisfies(CapabilityLevel.READ)
    assert CapabilityLevel.EXECUTE.satisfies(CapabilityLevel.PROPOSE)
    assert CapabilityLevel.EXECUTE.satisfies(CapabilityLevel.EXECUTE)
    assert not CapabilityLevel.READ.satisfies(CapabilityLevel.EXECUTE)
