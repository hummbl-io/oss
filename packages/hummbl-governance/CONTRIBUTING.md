# Contributing to hummbl-governance

Thank you for considering contributing to hummbl-governance. This project is intentionally small, focused, and stdlib-only. Every line of code is load-bearing.

---

## Before You Start

1. **Read the design philosophy:** Every module must be independently importable, thread-safe, and stdlib-only. If your contribution introduces a third-party dependency, it will be rejected unless there is an extraordinary justification.
2. **Open an issue first:** For new primitives, breaking changes, or architectural questions. Bug fixes and documentation improvements do not require an issue.
3. **Check existing issues:** Someone may already be working on the same thing.

---

## Development Setup

```bash
# Clone
git clone https://github.com/hummbl-io/hummbl-governance.git
cd hummbl-governance

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate     # Windows

# Install with test dependencies
pip install -e ".[test]"

# Run tests
python -m pytest tests/ -v --cov=hummbl_governance --cov-report=term --cov-fail-under=80
```

---

## What We're Looking For

### High Priority

- **Bug fixes** in existing primitives
- **Documentation** improvements (docstrings, examples, README clarity)
- **Test coverage** for edge cases not currently covered
- **Compliance mappings** for new frameworks (e.g., add ISO 27001 controls to `compliance_mapper.py`)
- **MCP server tool definitions** for primitives not yet exposed

### Medium Priority

- **New primitives** that fit the existing categories (safety, cost, identity, audit, reasoning, coordination)
- **Performance optimizations** with benchmarks showing improvement
- **Error message clarity** improvements

### Low Priority / Likely Rejected

- **New dependencies** — almost certainly rejected. The stdlib-only constraint is non-negotiable.
- **Dashboards or UIs** — out of scope. This is a library, not an application.
- **Framework-specific integrations** (e.g., LangChain adapter, CrewAI plugin) — these belong in separate repos.
- **Style-only changes** (reformatting, renaming) — unless part of a larger PR.

---

## Pull Request Process

1. **Branch naming:** `type/description` — e.g., `fix/circuit-breaker-recovery-timeout`, `docs/kill-switch-examples`
2. **Commit format:** Conventional Commits — `fix:`, `feat:`, `docs:`, `test:`, `refactor:`
3. **PR description:** Include:
   - What changed and why
   - Test plan (commands you ran)
   - Any breaking changes
4. **CI must pass:** All tests + coverage threshold (80%)
5. **One concern per PR:** Do not bundle unrelated changes.

---

## Code Standards

### Python

- Python 3.11+ syntax only
- Type hints required for public functions
- Docstrings: Google style
- No `print()` statements in production code — use the governance bus or logging

### Testing

- Every new primitive needs tests in `tests/unit/`
- Every bug fix needs a regression test
- Thread-safety tests for shared state (e.g., kill switch, circuit breaker)

### Documentation

- Every public function needs a docstring with:
  - What it does (one sentence)
  - Args and types
  - Returns and types
  - Raises (if applicable)
  - One code example

---

## Governance Primitive Design Checklist

If you're proposing a new primitive, verify it meets these criteria:

- [ ] Solves a problem that existing primitives do not solve
- [ ] Can be used independently (no required imports from other HUMMBL modules)
- [ ] Does not require third-party packages at runtime
- [ ] Has clear production evidence or a realistic scenario where it would be needed
- [ ] Integrates with the governance bus (logs its actions)
- [ ] Has a clear state machine or decision boundary
- [ ] Is thread-safe or documents when it is not
- [ ] Has tests covering: normal operation, failure modes, edge cases, concurrency

---

## Questions?

- **Technical:** Open an issue with the `question` label
- **Security:** Email security@hummbl.io (do not open public issues for security concerns)
- **General:** Reach out on the HUMMBL governance bus or in GitHub discussions

---

**License:** Apache 2.0. By contributing, you agree that your contributions will be licensed under the same license.
