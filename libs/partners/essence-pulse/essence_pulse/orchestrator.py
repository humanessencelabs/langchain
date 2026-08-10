"""Essence Pulse orchestrator — wires the full pipeline.

The orchestrator is the single entry point for processing a
:class:`NormalizedEvent`.  It:

1. Resolves identity and context for the event actor.
2. Classifies the event using the :class:`ClassifierAgent`.
3. If the event is a scheduling request, invokes :class:`SchedulerAgent`.
4. Checks permissions via :class:`PolicyEngine` before any data access.
5. Routes consequential actions through :class:`ApprovalManager`.
6. Records every decision in :class:`AuditLog`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from essence_pulse.agents.classifier_agent import ClassifierAgent
from essence_pulse.agents.scheduler_agent import SchedulerAgent
from essence_pulse.approval.approval_manager import ApprovalManager, ApprovalOutcome
from essence_pulse.audit.audit_log import AuditLog
from essence_pulse.bus.event import NormalizedEvent
from essence_pulse.context.context_store import ContextStore
from essence_pulse.models.base import ModelProvider
from essence_pulse.models.stub_adapter import StubAdapter
from essence_pulse.policy.engine import PolicyEngine
from essence_pulse.policy.permissions import (
    CapabilityLevel,
    DEFAULT_DEMO_PERMISSIONS,
    Permission,
)


@dataclass
class PipelineResult:
    """Outcome of running the full pipeline for one event.

    Args:
        event_id: UUID of the processed event.
        classification: Classification data from the classifier agent.
        suggestion: Suggestion data from the specialist agent (if any).
        approval_outcome: Human approval decision (if required).
        audit_entry_count: Number of audit entries created.
        error: Error message if the pipeline failed.
    """

    event_id: str
    classification: dict[str, Any]
    suggestion: dict[str, Any]
    approval_outcome: ApprovalOutcome | None
    audit_entry_count: int
    error: str | None = None


class Orchestrator:
    """Coordinates the full Essence Pulse processing pipeline.

    Args:
        model: The :class:`ModelProvider` for all AI reasoning.
            Defaults to :class:`StubAdapter` (no API key required).
        context_store: The :class:`ContextStore` holding identity and
            memory data.  Defaults to a new store with demo data.
        policy_engine: The :class:`PolicyEngine` for permission checks.
            Defaults to a new engine with demo permissions.
        approval_manager: The :class:`ApprovalManager` for human-in-the-
            loop authorization.  Defaults to interactive mode.
        audit_log: The :class:`AuditLog`.  Defaults to in-memory only.
        interactive: If ``False``, disable interactive approval prompts
            (useful for automated tests).
    """

    def __init__(
        self,
        *,
        model: ModelProvider | None = None,
        context_store: ContextStore | None = None,
        policy_engine: PolicyEngine | None = None,
        approval_manager: ApprovalManager | None = None,
        audit_log: AuditLog | None = None,
        interactive: bool = True,
    ) -> None:
        self._model = model or StubAdapter()
        self._store = context_store or ContextStore(seed_demo_data=True)
        self._policy = policy_engine or PolicyEngine(list(DEFAULT_DEMO_PERMISSIONS))
        self._approval = approval_manager or ApprovalManager()
        self._audit = audit_log or AuditLog()
        self._interactive = interactive

        self._classifier = ClassifierAgent(self._model)

    def process(self, event: NormalizedEvent) -> PipelineResult:
        """Run the full pipeline for one event.

        Args:
            event: The :class:`NormalizedEvent` to process.

        Returns:
            A :class:`PipelineResult` summarising every pipeline step.
        """
        audit_start = self._audit.count()
        classification: dict[str, Any] = {}
        suggestion: dict[str, Any] = {}
        approval_outcome: ApprovalOutcome | None = None

        # ── Step 1: Resolve identity ───────────────────────────────────
        identity = self._store.resolve_identity(event.actor)
        identity_context: dict[str, Any] = (
            identity.to_agent_context() if identity else {"actor_id": event.actor}
        )
        self._audit.record(
            action="identity_resolved",
            agent_id="orchestrator",
            event_id=event.event_id,
            outcome="found" if identity else "unknown",
            metadata=identity_context,
        )

        # ── Step 2: Classify ───────────────────────────────────────────
        classify_policy = self._policy.check(
            self._classifier.agent_id, "messages", CapabilityLevel.READ, event.context
        )
        self._audit.record(
            action="policy_check",
            agent_id=self._classifier.agent_id,
            event_id=event.event_id,
            outcome="allowed" if classify_policy.allowed else "denied",
            metadata={"resource": "messages", "level": "read"},
        )

        if not classify_policy.allowed:
            self._audit.record(
                action="classify",
                agent_id=self._classifier.agent_id,
                event_id=event.event_id,
                outcome="policy_denied",
            )
            return PipelineResult(
                event_id=event.event_id,
                classification={},
                suggestion={},
                approval_outcome=None,
                audit_entry_count=self._audit.count() - audit_start,
                error="Policy denied classifier access to messages.",
            )

        classify_result = self._classifier.run(event, identity_context)
        classification = classify_result.data
        self._audit.record(
            action="classify",
            agent_id=self._classifier.agent_id,
            event_id=event.event_id,
            outcome="success",
            metadata=classification,
        )

        # ── Step 3: Route to specialist agent ─────────────────────────
        event_type = classification.get("event_type", "")
        requires_action = classification.get("requires_action", False)

        if event_type == "scheduling_request" and requires_action:
            # Check calendar permission before accessing availability
            cal_policy = self._policy.check(
                "scheduler_agent", "calendar", CapabilityLevel.READ, event.context
            )
            msg_policy = self._policy.check(
                "scheduler_agent", "messages", CapabilityLevel.PROPOSE, event.context
            )
            self._audit.record(
                action="policy_check",
                agent_id="scheduler_agent",
                event_id=event.event_id,
                outcome="allowed" if (cal_policy.allowed and msg_policy.allowed) else "denied",
                metadata={"resources": ["calendar:read", "messages:propose"]},
            )

            if cal_policy.allowed:
                calendar = self._store.get_calendar()
                free_slots = calendar.get("free_slots", [])
                scheduler = SchedulerAgent(self._model, free_slots)
                schedule_result = scheduler.run(event, identity_context)
                suggestion = schedule_result.data

                self._audit.record(
                    action="schedule_suggest",
                    agent_id="scheduler_agent",
                    event_id=event.event_id,
                    outcome="proposed",
                    metadata={
                        "suggested_slot": suggestion.get("suggested_slot"),
                        "has_reply": bool(suggestion.get("suggested_reply")),
                    },
                )

                # ── Step 4: Request human approval ─────────────────────
                if schedule_result.requires_approval:
                    approval_outcome = self._approval.request_approval(
                        schedule_result,
                        event.event_id,
                        interactive=self._interactive,
                    )
                    self._audit.record(
                        action="send_message",
                        agent_id="scheduler_agent",
                        event_id=event.event_id,
                        outcome=approval_outcome.value,
                        approved_by="user" if approval_outcome == ApprovalOutcome.APPROVED else None,
                        metadata={
                            "suggested_slot": suggestion.get("suggested_slot"),
                            "action_taken": approval_outcome == ApprovalOutcome.APPROVED,
                        },
                    )

        event.processed = True
        return PipelineResult(
            event_id=event.event_id,
            classification=classification,
            suggestion=suggestion,
            approval_outcome=approval_outcome,
            audit_entry_count=self._audit.count() - audit_start,
        )

    @property
    def audit_log(self) -> AuditLog:
        """Access the orchestrator's audit log."""
        return self._audit

    @property
    def context_store(self) -> ContextStore:
        """Access the orchestrator's context store."""
        return self._store

    @property
    def policy_engine(self) -> PolicyEngine:
        """Access the orchestrator's policy engine."""
        return self._policy

    @property
    def approval_manager(self) -> ApprovalManager:
        """Access the orchestrator's approval manager."""
        return self._approval
