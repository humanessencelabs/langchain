#!/usr/bin/env python3
"""Essence Pulse — interactive end-to-end demo.

Demonstrates the full pipeline:

    Event → Context → Agent reasoning → Permission → Human approval → Action → Audit

Usage::

    python demo/run_demo.py [--scenario {scheduling_request,urgent_message,informational}]
    python demo/run_demo.py --auto-approve   # no interactive prompts

No API key required.  All data is synthetic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from the repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from essence_pulse.approval.approval_manager import ApprovalManager, ApprovalOutcome
from essence_pulse.audit.audit_log import AuditLog
from essence_pulse.bus.bus import EventBus
from essence_pulse.connectors.demo_connector import DemoConnector
from essence_pulse.context.context_store import ContextStore
from essence_pulse.models.stub_adapter import StubAdapter
from essence_pulse.orchestrator import Orchestrator
from essence_pulse.policy.engine import PolicyEngine
from essence_pulse.policy.permissions import DEFAULT_DEMO_PERMISSIONS
from essence_pulse.ui.cli import (
    show_audit,
    show_approvals,
    show_pulse,
    show_agents,
    show_memory,
)

console = Console()


def run_demo(scenario: str = "scheduling_request", *, auto_approve: bool = False) -> None:
    """Run the Essence Pulse demo pipeline.

    Args:
        scenario: The demo scenario to run.
        auto_approve: If ``True``, skip interactive approval prompts.
    """
    console.print()
    console.print(
        Panel(
            "[bold cyan]⬡ Essence Pulse[/bold cyan]  ·  Permission-controlled AI interoperability layer\n"
            "[dim]«Intelligence may be distributed.  Authority remains with the human.»[/dim]",
            expand=True,
            border_style="cyan",
        )
    )
    console.print()

    # ── 1. Build components ───────────────────────────────────────────
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
        interactive=not auto_approve,
    )

    # ── 2. Emit event ─────────────────────────────────────────────────
    console.rule("[bold]Step 1 — Event Ingestion[/bold]")
    connector = DemoConnector(scenario=scenario)
    event = connector.emit(bus.publish)

    console.print(f"  [cyan]Source[/cyan]     : {event.source}")
    console.print(f"  [cyan]Type[/cyan]       : {event.event_type}")
    console.print(f"  [cyan]Actor[/cyan]      : {event.actor}")
    console.print(f"  [cyan]Sensitivity[/cyan]: {event.sensitivity.value}")
    body = event.payload.get("body", "")
    console.print(f"  [cyan]Payload[/cyan]    : \"{body}\"")
    console.print()

    # ── 3. Resolve context ────────────────────────────────────────────
    console.rule("[bold]Step 2 — Context Resolution[/bold]")
    identity = store.resolve_identity(event.actor)
    if identity:
        console.print(
            f"  [green]✓[/green] Identity resolved: [bold]{identity.display_name}[/bold] "
            f"({identity.relationship}, contexts: {', '.join(identity.contexts)})"
        )
    else:
        console.print(f"  [yellow]?[/yellow] Unknown actor: {event.actor}")
    console.print()

    # ── 4. Run orchestrator (classify → schedule → approve → audit) ───
    console.rule("[bold]Steps 3–7 — Orchestration Pipeline[/bold]")
    console.print(
        "  Running: [dim]classify → policy check → schedule → approval → audit[/dim]"
    )
    console.print()

    result = orchestrator.process(event)

    # ── 5. Show classification ────────────────────────────────────────
    console.rule("[bold]Step 3 — Classification[/bold]")
    cls = result.classification
    if cls:
        console.print(f"  [cyan]Event type[/cyan]  : {cls.get('event_type')}")
        console.print(f"  [cyan]Confidence[/cyan]  : {cls.get('confidence')}")
        console.print(f"  [cyan]Priority[/cyan]    : {cls.get('priority')}")
        console.print(f"  [cyan]Needs action[/cyan]: {cls.get('requires_action')}")
    else:
        console.print("  [red]Classification failed.[/red]")
    console.print()

    # ── 6. Show suggestion ────────────────────────────────────────────
    if result.suggestion:
        console.rule("[bold]Step 5 — Suggested Action[/bold]")
        sug = result.suggestion
        console.print(f"  [cyan]Proposed slot[/cyan]: {sug.get('suggested_slot')}")
        console.print(f"  [cyan]Suggested reply[/cyan]:")
        console.print(f"    \"{sug.get('suggested_reply')}\"")
        console.print()

    # ── 7. Show approval outcome ──────────────────────────────────────
    if result.approval_outcome is not None:
        console.rule("[bold]Step 6 — Human Approval[/bold]")
        outcome = result.approval_outcome
        if outcome in (ApprovalOutcome.APPROVED, ApprovalOutcome.AUTO_APPROVED):
            console.print("  [green]✓ Action approved — response sent (simulated)[/green]")
        else:
            console.print("  [red]✗ Action rejected — no message sent[/red]")
        console.print()

    # ── 8. Show audit ─────────────────────────────────────────────────
    console.rule("[bold]Step 7 — Audit Log[/bold]")
    show_audit(audit)
    console.print()

    # ── 9. Summary screens ────────────────────────────────────────────
    console.rule("[dim]Additional Screens[/dim]")
    show_pulse(bus)
    console.print()
    show_agents(policy)
    console.print()
    show_memory(store)
    console.print()
    show_approvals(approval)
    console.print()

    # ── Done ──────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold green]Demo complete.[/bold green]  "
            f"{audit.count()} audit entries recorded.\n"
            "[dim]No real data was accessed.  "
            "No API keys were used.  "
            "All content is synthetic.[/dim]",
            border_style="green",
        )
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Essence Pulse — end-to-end AI interoperability demo"
    )
    parser.add_argument(
        "--scenario",
        choices=DemoConnector.available_scenarios(),
        default="scheduling_request",
        help="Demo scenario to run (default: scheduling_request)",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip interactive approval prompts (useful for CI)",
    )
    args = parser.parse_args()
    run_demo(scenario=args.scenario, auto_approve=args.auto_approve)


if __name__ == "__main__":
    main()
