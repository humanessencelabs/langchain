"""Human-in-the-loop approval manager.

Consequential actions (anything above READ) require explicit human
authorization before execution.  The approval manager presents the
proposed action and waits for a response.

«Intelligence may be distributed.  Authority remains with the human.»
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from essence_pulse.agents.base_agent import AgentResult


class ApprovalOutcome(str, Enum):
    """Result of an approval request."""

    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    """A pending approval request awaiting human authorization.

    Args:
        request_id: Unique identifier for this request.
        agent_id: The agent proposing the action.
        action: The proposed action label.
        description: Human-readable description of what will happen.
        data: The structured data the action will use.
        event_id: The originating event UUID.
    """

    request_id: str
    agent_id: str
    action: str
    description: str
    data: dict[str, Any]
    event_id: str
    outcome: ApprovalOutcome | None = None
    approved_by: str | None = None


class ApprovalManager:
    """Manages human-in-the-loop approval for consequential actions.

    In the CLI demo, approval is requested interactively.  In the web UI,
    pending requests accumulate in :attr:`pending` until the user acts.

    Args:
        auto_approve: If ``True``, approve all actions without prompting.
            Only appropriate for automated testing.
    """

    def __init__(self, *, auto_approve: bool = False) -> None:
        self._auto_approve = auto_approve
        self._pending: list[ApprovalRequest] = []
        self._history: list[ApprovalRequest] = []

    def request_approval(
        self,
        result: AgentResult,
        event_id: str,
        *,
        interactive: bool = True,
    ) -> ApprovalOutcome:
        """Seek human approval for a proposed action.

        Args:
            result: The :class:`AgentResult` proposing the action.
            event_id: UUID of the originating event.
            interactive: If ``True``, prompt the user on stdin.

        Returns:
            The :class:`ApprovalOutcome` (approved or rejected).
        """
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            agent_id=result.agent_id,
            action=result.action,
            description=result.reasoning,
            data=result.data,
            event_id=event_id,
        )
        self._pending.append(req)

        if self._auto_approve:
            req.outcome = ApprovalOutcome.AUTO_APPROVED
            req.approved_by = "auto"
            self._pending.remove(req)
            self._history.append(req)
            return ApprovalOutcome.AUTO_APPROVED

        if interactive:
            outcome = self._prompt(req)
            req.outcome = outcome
            req.approved_by = "user"
            self._pending.remove(req)
            self._history.append(req)
            return outcome

        # Non-interactive, non-auto: leave pending
        return ApprovalOutcome.REJECTED

    def _prompt(self, req: ApprovalRequest) -> ApprovalOutcome:
        """Display the approval prompt and wait for user input.

        Args:
            req: The :class:`ApprovalRequest` to display.
        """
        print(f"\n{'─' * 60}")
        print(f"  ⚠️  ACTION REQUIRES YOUR APPROVAL")
        print(f"{'─' * 60}")
        print(f"  Agent   : {req.agent_id}")
        print(f"  Action  : {req.action}")
        print(f"  Reason  : {req.description}")
        if req.data.get("suggested_reply"):
            print(f"  Message : {req.data['suggested_reply']}")
        if req.data.get("suggested_slot"):
            print(f"  Slot    : {req.data['suggested_slot']}")
        print(f"{'─' * 60}")

        try:
            answer = input("  Approve this action? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer in ("y", "yes"):
            return ApprovalOutcome.APPROVED
        return ApprovalOutcome.REJECTED

    @property
    def pending(self) -> list[ApprovalRequest]:
        """Return all currently pending approval requests."""
        return list(self._pending)

    @property
    def history(self) -> list[ApprovalRequest]:
        """Return all resolved approval requests."""
        return list(self._history)
