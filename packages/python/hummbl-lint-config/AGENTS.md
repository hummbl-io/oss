# AGENTS.md — hummbl-lint-config

## Project

**hummbl-lint-config** — Shared ruff lint configuration for the HUMMBL fleet. Configures PLW1514, B904, SIM, I, UP rule sets.

## Scope

- In scope: Shared ruff.toml configuration, Python package wrapper for PyPI distribution
- Out of scope: Other linters (mypy, pylint), formatter configuration, CI workflow definitions

## Setup

```bash
cd packages/python/hummbl-lint-config
pip install -e .
```

## Usage

Reference the ruff.toml from your project:

```toml
[tool.ruff]
extend = "path/to/hummbl_lint_config/ruff.toml"
```

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (config only)
- MIT OR Apache-2.0 license
