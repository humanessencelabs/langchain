"""Integration tests — full pipeline end-to-end with stub adapter."""

from __future__ import annotations

from essence_pulse.approval.approval_manager import ApprovalManager, ApprovalOutcome
from essence_pulse.audit.audit_log import AuditLog
from essence_pulse.bus.bus import EventBus
from essence_pulse.connectors.demo_connector import DemoConnector
from essence_pulse.context.context_store import ContextStore
from essence_pulse.models.stub_adapter import StubAdapter
from essence_pulse.orchestrator import Orchestrator
from essence_pulse.policy.engine import PolicyEngine
from essence_pulse.policy.permissions import DEFAULT_DEMO_PERMISSIONS


def _build_orchestrator(auto_approve: bool = True) -> tuple[Orchestrator, EventBus, AuditLog]:
    bus = EventBus()
    store = ContextStore(seed_demo_data=True)
    policy = PolicyEngine(list(DEFAULT_DEMO_PERMISSIONS))
    audit = AuditLog()
    approval = ApprovalManager(auto_approve=auto_approve)
    model = StubAdapter()
    orchestrator = Orchestrator(
        model=model,
        context_store=store,
        policy_engine=policy,
        approval_manager=approval,
        audit_log=audit,
        interactive=False,
    )
    return orchestrator, bus, audit


def test_scheduling_pipeline_auto_approve() -> None:
    orchestrator, bus, audit = _build_orchestrator(auto_approve=True)
    connector = DemoConnector(scenario="scheduling_request")
    event = connector.emit(bus.publish)

    result = orchestrator.process(event)

    assert result.classification.get("event_type") == "scheduling_request"
    assert result.classification.get("requires_action") is True
    assert result.suggestion.get("suggested_slot") is not None
    assert result.approval_outcome == ApprovalOutcome.AUTO_APPROVED
    assert audit.count() > 0
    assert event.processed is True


def test_informational_pipeline_no_approval() -> None:
    orchestrator, bus, audit = _build_orchestrator(auto_approve=True)
    connector = DemoConnector(scenario="informational")
    event = connector.emit(bus.publish)

    result = orchestrator.process(event)

    # Informational events should not trigger approval
    assert result.approval_outcome is None
    assert event.processed is True


def test_audit_records_all_steps() -> None:
    orchestrator, bus, audit = _build_orchestrator(auto_approve=True)
    connector = DemoConnector(scenario="scheduling_request")
    event = connector.emit(bus.publish)
    orchestrator.process(event)

    actions = {e.action for e in audit.entries()}
    assert "identity_resolved" in actions
    assert "policy_check" in actions
    assert "classify" in actions


def test_stub_adapter_classify() -> None:
    model = StubAdapter()
    response = model.complete("classify this message: Can we meet tomorrow?")
    assert "scheduling_request" in response


def test_context_store_resolves_demo_identity() -> None:
    store = ContextStore(seed_demo_data=True)
    identity = store.resolve_identity("customer_123")
    assert identity is not None
    assert identity.display_name == "Alex Chen"


def test_context_store_delete_identity() -> None:
    store = ContextStore(seed_demo_data=True)
    assert store.delete_identity("customer_123") is True
    assert store.resolve_identity("customer_123") is None
