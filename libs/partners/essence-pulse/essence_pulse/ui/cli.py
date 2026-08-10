"""Essence Pulse CLI — 7-screen terminal interface.

Uses the Rich library for a clean, calm display.  Runs without any
web server or external dependency beyond ``rich``.

Screens:
    pulse      - Chronological event stream
    now        - High-priority pending events
    agents     - Active agents and their permissions
    memory     - Inspectable context store
    approvals  - Pending approval requests
    connections - Registered connectors
    audit      - Full immutable audit log
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from essence_pulse.audit.audit_log import AuditLog, AuditEntry
from essence_pulse.approval.approval_manager import ApprovalManager
from essence_pulse.bus.bus import EventBus
from essence_pulse.bus.event import NormalizedEvent
from essence_pulse.context.context_store import ContextStore
from essence_pulse.policy.engine import PolicyEngine

console = Console()

_BRAND = "[bold cyan]⬡ Essence Pulse[/bold cyan]"


def _header(screen: str) -> None:
    console.print(Panel(f"{_BRAND}  ·  [dim]{screen}[/dim]", expand=True))


def show_pulse(bus: EventBus) -> None:
    """Render the Pulse screen — chronological event stream.

    Args:
        bus: The :class:`EventBus` to read history from.
    """
    _header("Pulse — Event Stream")
    events = bus.history
    if not events:
        console.print("[dim]  No events yet.[/dim]")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Time", style="dim", width=22)
    table.add_column("Source", width=16)
    table.add_column("Type", width=22)
    table.add_column("Actor", width=18)
    table.add_column("Context", width=12)
    table.add_column("Status", width=10)

    for e in reversed(events):
        status = "[green]✓[/green]" if e.processed else "[yellow]●[/yellow]"
        table.add_row(
            e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            e.source,
            e.event_type,
            e.actor,
            e.context,
            status,
        )
    console.print(table)


def show_now(bus: EventBus) -> None:
    """Render the Now screen — unprocessed / high-priority events.

    Args:
        bus: The :class:`EventBus` to read from.
    """
    _header("Now — Requires Attention")
    pending = bus.pending()
    if not pending:
        console.print("[green]  Nothing requires your attention right now.[/green]")
        return

    for e in pending:
        console.print(
            Panel(
                f"[bold]{e.event_type}[/bold] from [cyan]{e.actor}[/cyan]\n"
                f"Source: {e.source}  |  Context: {e.context}  |  "
                f"Sensitivity: {e.sensitivity.value if hasattr(e.sensitivity, 'value') else e.sensitivity}",
                title=f"[yellow]⚑ Pending[/yellow] · {e.event_id[:8]}",
                border_style="yellow",
            )
        )


def show_agents(policy: PolicyEngine) -> None:
    """Render the Agents screen — active agents and their permissions.

    Args:
        policy: The :class:`PolicyEngine` to query permissions from.
    """
    _header("Agents — Active Agents & Permissions")
    agents = {
        "classifier_agent": "Classifies events by type, priority, and required action.",
        "scheduler_agent": "Generates scheduling replies using calendar availability.",
        "orchestrator": "Coordinates the full pipeline.",
    }
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Agent", width=22)
    table.add_column("Description", width=46)
    table.add_column("Permissions", width=30)

    for agent_id, desc in agents.items():
        perms = policy.list_permissions(agent_id)
        perm_str = ", ".join(
            f"{p.resource}:{p.level.value}" for p in perms
        ) or "[dim]none[/dim]"
        table.add_row(agent_id, desc, perm_str)
    console.print(table)


def show_memory(store: ContextStore) -> None:
    """Render the Memory screen — inspectable context store.

    Args:
        store: The :class:`ContextStore` to display.
    """
    _header("Memory — What the System Remembers")
    identities = store.list_identities()
    facts = store.list_facts()

    console.print("[bold]Known Identities[/bold]")
    if identities:
        id_table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
        id_table.add_column("Actor ID", width=18)
        id_table.add_column("Name", width=20)
        id_table.add_column("Relationship", width=14)
        id_table.add_column("Contexts", width=20)
        for ident in identities:
            id_table.add_row(
                ident.actor_id,
                ident.display_name,
                ident.relationship,
                ", ".join(ident.contexts),
            )
        console.print(id_table)
    else:
        console.print("[dim]  No identities stored.[/dim]")

    console.print("\n[bold]Stored Facts[/bold]")
    if facts:
        for k, v in facts.items():
            console.print(f"  [cyan]{k}[/cyan] = {v}")
    else:
        console.print("[dim]  No facts stored.[/dim]")

    console.print(
        "\n[dim]All memory is inspectable and deletable by the user.[/dim]"
    )


def show_approvals(manager: ApprovalManager) -> None:
    """Render the Approvals screen — pending human authorizations.

    Args:
        manager: The :class:`ApprovalManager` to query.
    """
    _header("Approvals — Awaiting Authorization")
    pending = manager.pending
    if not pending:
        console.print("[green]  No pending approvals.[/green]")
    else:
        for req in pending:
            console.print(
                Panel(
                    f"Action: [bold]{req.action}[/bold]\n"
                    f"Agent: {req.agent_id}\n"
                    f"Reason: {req.description}",
                    title=f"[red]⚡ Pending Approval[/red] · {req.request_id[:8]}",
                    border_style="red",
                )
            )

    console.print("\n[bold]Resolved Approvals[/bold]")
    resolved = manager.history
    if resolved:
        for req in resolved:
            icon = "[green]✓[/green]" if req.outcome and "approved" in req.outcome.value else "[red]✗[/red]"
            console.print(
                f"  {icon} {req.action} · {req.agent_id} · {req.outcome.value if req.outcome else 'unknown'}"
            )
    else:
        console.print("[dim]  No resolved approvals yet.[/dim]")


def show_connections() -> None:
    """Render the Connections screen — registered connectors."""
    _header("Connections — Connected Apps & Devices")
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("Connector", width=22)
    table.add_column("Status", width=12)
    table.add_column("Type", width=18)
    table.add_column("Note", width=36)
    table.add_row(
        "whatsapp_demo",
        "[green]active[/green]",
        "messaging",
        "Synthetic demo data only",
    )
    table.add_row(
        "email_demo",
        "[green]active[/green]",
        "messaging",
        "Synthetic demo data only",
    )
    table.add_row(
        "calendar_demo",
        "[green]active[/green]",
        "productivity",
        "Synthetic free/busy slots",
    )
    table.add_row(
        "android_notifications",
        "[dim]not connected[/dim]",
        "os_events",
        "Future: Android Notification Listener",
    )
    console.print(table)


def show_audit(audit_log: AuditLog) -> None:
    """Render the Audit screen — full immutable action log.

    Args:
        audit_log: The :class:`AuditLog` to display.
    """
    _header("Audit — Immutable Action Log")
    entries = audit_log.entries()
    if not entries:
        console.print("[dim]  No audit entries yet.[/dim]")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("#", width=4)
    table.add_column("Timestamp", width=26, style="dim")
    table.add_column("Action", width=22)
    table.add_column("Agent", width=20)
    table.add_column("Outcome", width=16)
    table.add_column("Approved by", width=12)

    for i, entry in enumerate(entries, 1):
        outcome_style = (
            "[green]" if "success" in entry.outcome or "approved" in entry.outcome or entry.outcome == "allowed"
            else "[red]" if "denied" in entry.outcome or "rejected" in entry.outcome
            else "[yellow]"
        )
        table.add_row(
            str(i),
            entry.timestamp,
            entry.action,
            entry.agent_id,
            f"{outcome_style}{entry.outcome}[/]",
            entry.approved_by or "—",
        )
    console.print(table)
