# Privacy Policy

This document describes how Essence Pulse handles personal data in the prototype.

> **How should personal AI memory work?**  
> Memory should belong to the user, be inspectable, and be deletable on demand.

---

## Data minimization principles

**How can multiple AI models share context safely?**

The answer is strict data minimization:

- Each agent receives only the fields it needs for its specific task.
- The `ContextStore` never shares the full user profile with any agent.
- Agents request data through the `PolicyEngine`; access is logged.
- The `to_agent_context()` projection strips notes, tags, and sensitive fields.

---

## What Essence Pulse stores (prototype)

All data is held **in memory only** and is lost when the process exits, unless you explicitly configure file persistence.

| Data type | Contents | Storage | Deletable? |
|-----------|----------|---------|------------|
| Identity records | `actor_id`, `display_name`, `relationship`, `contexts` | In-memory | Yes |
| Calendar data | Synthetic free/busy slots | In-memory | — (demo only) |
| Facts | Key-value pairs | In-memory | Yes |
| Audit log | Action, agent, outcome, approver, timestamp | In-memory (optional file) | No (audit logs are immutable) |
| Event history | Event metadata (no payload PII) | In-memory | — |

**What is NOT stored:**
- Raw message bodies or email content.
- Payload contents in the audit log.
- Biometric or location data.
- Any real personal data (the demo uses synthetic personas only).

---

## User rights

### Inspect memory

```python
store = orchestrator.context_store
identities = store.list_identities()
facts = store.list_facts()
```

Or run the demo and view the **Memory** screen.

### Delete an identity

```python
store.delete_identity("actor_id_here")
```

### Delete a fact

```python
store.forget("fact_key_here")
```

### View the audit log

```python
entries = orchestrator.audit_log.entries()
```

Or run the demo and view the **Audit** screen.

---

## Production considerations (not yet implemented)

If you build a production system on top of this prototype:

- Apply GDPR / CCPA / applicable data protection regulations.
- Implement persistent storage with encryption at rest.
- Add record-level deletion (right to erasure) in the persistent store.
- Do not send personal data to third-party AI providers without user consent and a lawful basis.
- Implement data retention limits.
- Audit logs should be append-only but accessible to the user for review.
- Never use real personal data to train or fine-tune models without explicit consent.

---

## No telemetry

The Essence Pulse prototype collects no telemetry, usage data, or analytics.  
It makes no network requests in default (stub adapter) configuration.

---

## Third-party AI providers

If you configure a real model adapter (e.g. `OpenAIAdapter`):

- Data sent to the provider is governed by that provider's terms of service and privacy policy.
- Never send sensitive personal data without reviewing those policies.
- Use the minimum prompt content required for the task.
- The stub adapter (default) makes no external calls.
