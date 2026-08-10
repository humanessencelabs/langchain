# Roadmap

> Essence Pulse is an independent experimental prototype.  This roadmap describes potential future development directions, not commitments.

---

## Phase 0 — Working prototype (current)

- [x] Normalized event schema
- [x] In-memory event bus
- [x] Demo connector (synthetic events)
- [x] Identity and context store
- [x] Stub model adapter (offline, no API key)
- [x] OpenAI adapter
- [x] Classifier agent
- [x] Scheduler agent
- [x] Policy engine (least-privilege permissions)
- [x] Human approval manager (CLI)
- [x] Immutable audit log
- [x] CLI interface (7 screens via Rich)
- [x] Unit and integration tests (34 tests)
- [x] Security, privacy, architecture documentation

---

## Phase 1 — Real model integration

- [ ] Anthropic Claude adapter
- [ ] Google Gemini adapter
- [ ] Local model adapter (llama.cpp / GGUF via `llama-cpp-python`)
- [ ] Streaming support in `ModelProvider`
- [ ] Model-agnostic prompt templates
- [ ] Configurable system prompt per agent

---

## Phase 2 — Persistent memory and real connectors

- [ ] SQLite-backed `ContextStore` with encryption at rest
- [ ] Audit log with configurable retention and file rotation
- [ ] Email connector (IMAP with OAuth, read-only)
- [ ] Calendar connector (CalDAV, read-only)
- [ ] Android notification listener connector (concept / POC)
- [ ] Webhook connector (generic HTTP ingest)

---

## Phase 3 — Web UI and multi-agent coordination

- [ ] FastAPI web server with the 7 Essence Pulse screens
- [ ] React or HTMX frontend
- [ ] Real-time event stream (Server-Sent Events or WebSocket)
- [ ] Approval UI with rich context display
- [ ] Multiple specialist agents running in parallel
- [ ] Agent-to-agent messaging via the event bus

---

## Phase 4 — Permission UX and user control

- [ ] Visual permission manager (grant / revoke / inspect)
- [ ] Time-limited permission grants
- [ ] Context-scoped permissions (e.g. "only during work hours")
- [ ] Permission templates (e.g. "scheduling assistant" preset)
- [ ] Export / import permission policy as JSON

---

## Phase 5 — Privacy and compliance

- [ ] GDPR-ready data deletion (right to erasure)
- [ ] Data retention limits with automated expiry
- [ ] Differential privacy for analytics
- [ ] Privacy audit report generator
- [ ] Consent management for third-party AI providers

---

## Speculative research directions

These are exploratory ideas, not product commitments:

- **Device mesh**: phones, watches, earbuds, glasses, and vehicles as interfaces to the same intelligence layer.
- **Agent marketplace**: installable specialist agents with declared permission scopes.
- **Cross-device context sync**: encrypted, user-controlled context sync.
- **Federated AI**: personal model running on-device, with cloud fallback.
- **OS-level event API**: a standardized Android/iOS API that exposes safe event streams to authorized agents.

---

## Not in scope

- Building a full operating system.
- Replicating proprietary visual identities.
- Real-time production integrations with third-party services (prototype only).
