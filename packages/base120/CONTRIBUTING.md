# Contributing to Base120

Thank you for your interest in Base120. This project follows a maintainer-approval model for contributions.

## Getting Started

```bash
git clone https://github.com/hummbl-io/oss.git
cd base120
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Submitting Changes

1. **Issues are welcome.** Open an issue to report bugs, suggest improvements, or ask questions.
2. **Pull requests require maintainer approval.** Please open an issue first to discuss your proposed change before submitting a PR.
3. **Commit format:** Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `fix:`, `feat:`, `docs:`, `test:`).
4. **Tests must pass.** All PRs must have a green CI check before review.

## Code Standards

- Python 3.11+
- Follow existing code style and patterns
- Add tests for new functionality
- Keep changes focused and minimal

## Test File Conventions

- Only `import pytest` if you are using pytest fixtures, marks (`@pytest.mark.*`), or `pytest.raises` / `pytest.warns`. Plain assertion-based tests need no pytest import.
- Only `import time` (or any stdlib module) if it is actually referenced in the test body.
- Run `make lint` before committing — unused imports are caught by ruff (F401) and will fail CI.

## Governance

Base120 v1.0.x is a **frozen specification**. Schema changes, registry modifications, and breaking changes are not accepted on the v1.0.x line.
