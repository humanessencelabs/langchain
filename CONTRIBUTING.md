# Contributing to Essence Pulse

Thank you for your interest in contributing to Essence Pulse — an independent open-source prototype for permission-controlled AI interoperability.

---

## Before you start

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design.
2. Read [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).
3. Check the [ROADMAP.md](ROADMAP.md) to see what is planned.
4. Search existing issues before opening a new one.

---

## Development setup

```bash
git clone https://github.com/humanessencelabs/langchain
cd langchain/libs/partners/essence-pulse

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run the demo
python demo/run_demo.py --auto-approve
```

---

## Code standards

- All Python code must have type hints and return types.
- Use Google-style docstrings with `Args` and `Returns` sections.
- Follow the existing module structure.
- No `eval()`, `exec()`, or `pickle` on external input.
- Never commit secrets, API keys, or real personal data.
- All external content must pass through `BaseAgent._safe_prompt()` to prevent prompt injection.

---

## Adding a new model adapter

1. Subclass `ModelProvider` in `essence_pulse/models/`.
2. Implement `provider_name` and `complete()`.
3. Follow the prompt injection mitigation pattern in `OpenAIAdapter`.
4. Add the adapter to `essence_pulse/models/__init__.py`.
5. Write unit tests.

---

## Adding a new specialist agent

1. Subclass `BaseAgent` in `essence_pulse/agents/`.
2. Declare `description` and `required_permissions`.
3. Implement `run()` — use `self._safe_prompt()` for untrusted content.
4. Add the agent to `essence_pulse/agents/__init__.py`.
5. Register it in `Orchestrator.process()` or create a routing rule.
6. Write unit tests.

---

## Adding a new connector

1. Implement the `NotificationConnector` interface in `essence_pulse/connectors/`.
2. All output must be a `NormalizedEvent`.
3. Never store or log raw payload content beyond what is necessary.
4. Write tests using synthetic data only.

---

## Pull request guidelines

- Keep PRs focused: one feature or fix per PR.
- Include tests for new behavior.
- Update documentation if you change a public interface.
- Ensure `pytest tests/` passes before submitting.
- Describe **why** the change is needed, not just what it does.
- Run `ruff check .` and `ruff format .` before submitting.

---

## Security vulnerabilities

Do not open a public issue for security vulnerabilities.  
See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Disclaimer

Essence Pulse is an independent experimental project, not affiliated with any company.  
All contributors agree that contributions are made under the MIT license.
