# Security Policy

This document describes the security principles, threat model, and reporting policy for **Essence Pulse**.

---

## Non-negotiable principles

These rules are enforced in code and cannot be overridden by configuration:

1. **No secrets in source code.** API keys, tokens, OAuth credentials, and passwords must never be committed.  Use environment variables.  See [`.env.example`](.env.example).

2. **Least privilege.** Every agent declares its required permissions (`required_permissions` property).  The `PolicyEngine` verifies each access before data is read or written.

3. **Separate read, propose, and execute capabilities.** `CapabilityLevel` has four ordered levels: `read < propose < execute < admin`.  Agents are granted the minimum level required.

4. **Human approval for consequential actions.** Any action above `read` routes through `ApprovalManager`.  The system cannot take consequential action without an explicit human `[y/N]` decision.

5. **Immutable audit trail.** `AuditEntry` objects are frozen dataclasses.  The `AuditLog` never mutates or deletes entries.  Every agent action, data access, and approval decision is recorded.

6. **Agents receive only minimum context.** The orchestrator passes `identity.to_agent_context()` — a projection containing only `actor_id`, `display_name`, `relationship`, and `contexts` — never the full profile, notes, or raw facts.

7. **Untrusted input is never interpolated into system prompts.** All user/external content is wrapped in explicit delimiters in `BaseAgent._safe_prompt()` and placed in the user message role, not the system role.

8. **No `eval()`, `exec()`, or `pickle` on external input.** There are no such calls in the codebase.

9. **Synthetic/demo data by default.** The prototype never connects to real apps, devices, or services.  All demo data uses fictional personas.

10. **Memory is inspectable and deletable.** `ContextStore.delete_identity()` and `ContextStore.forget()` allow users to delete any stored record.

---

## Threat model

### Prompt injection

**Threat:** A malicious actor embeds instructions inside a message payload, attempting to override the AI agent's behavior.

**Mitigation:** `BaseAgent._safe_prompt()` wraps all untrusted content in explicit delimiters (`--- UNTRUSTED USER CONTENT START/END ---`) and places it in the user role, not the system role.  `OpenAIAdapter` further separates the system prompt from untrusted content.

### Confused-deputy attack

**Threat:** An agent is tricked into using its permissions to access data on behalf of a different, unauthorized request.

**Mitigation:** The `PolicyEngine` checks permissions at every data access point inside the orchestrator.  Permissions are scoped to `(agent_id, resource, level, context)`.  An agent cannot escalate its own access.

### Data over-sharing

**Threat:** An agent receives more personal data than needed and leaks it.

**Mitigation:** Agents receive only `to_agent_context()` (4 fields).  Calendar data is fetched only after a calendar permission check passes.  Raw payload content is passed as untrusted input, not trusted context.

### Log tampering

**Threat:** An attacker modifies audit log entries to cover actions.

**Mitigation:** `AuditEntry` is a frozen dataclass.  Entries are never modified after creation.  Optional file persistence is append-only.

### Secret leakage

**Threat:** API keys are committed to the repository.

**Mitigation:** All secrets are environment variables.  `.env.example` contains only placeholder strings (`your_key_here`).  The `.gitignore` excludes `.env` files.

---

## Vulnerability reporting

This is an independent research prototype, not a production system.

If you discover a security vulnerability:

1. **Do not open a public issue.**
2. Open a private security advisory via GitHub's Security tab, or contact the maintainer directly.
3. Provide a description, reproduction steps, and potential impact.
4. Allow reasonable time for a fix before public disclosure.

---

## Dependency security

- Pinned dependencies in `pyproject.toml`.
- Only two runtime dependencies: `rich` (display) and optionally `openai`.
- No network calls in the default (stub) configuration.
