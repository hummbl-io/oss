# AGENTS.md — hummbl-io/oss monorepo

## Project

**hummbl-io/oss** — monorepo consolidating public-publishable HUMMBL packages.
Currently hosts 4 Python packages: `base120`, `hummbl`, `hummbl-governance`, `hummbl-kernel`.

## Packages

| Package | Path | PyPI status | Description |
|---------|------|-------------|-------------|
| hummbl-governance | `packages/hummbl-governance/` | Published (1.4.1) | Governance primitives for AI agent orchestration |
| base120 | `packages/base120/` | Published (2.0.0) | 120 reasoning operators for structured thinking |
| hummbl-kernel | `packages/hummbl-kernel/` | Pre-release (0.1.0) | Orchestration kernel with security and compliance enforcement |
| hummbl | `packages/hummbl/` | Pre-release (0.1.0) | Structured reasoning framework for AI agents |

## Setup

Each package has its own `pyproject.toml` and test suite. Install a package for development:

```bash
cd packages/<package-name>
pip install -e ".[test]"
```

## Testing

```bash
# Per-package
cd packages/hummbl-governance && python -m pytest tests/ -v
cd packages/hummbl-kernel && python -m pytest tests/ -v
cd packages/hummbl && python -m pytest tests/ -v
```

## CI

- **GitHub Actions** (primary): `.github/workflows/ci.yml`, self-hosted runner, Python 3.11/3.12/3.13 matrix
- **Workflow validator**: `.github/workflows/validate-workflows.yml` — enforces SHA-pinning
- SHA-pinning is required (`sha_pinning_required: true`). Tag refs (`@v4`, `@main`) cause `startup_failure`.

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only in production code)
- Test dependencies in `[test]` extras only
- Apache 2.0 license (packages); MIT OR Apache-2.0 (repo level)
- Commit format: Conventional Commits
- AI agents may assist with research, review, patch preparation, and operational coordination, but must not be credited in Git commit authorship metadata or commit-message trailers. Do not add `Co-authored-by`, `Generated-by`, `Authored-with`, or equivalent AI/vendor/agent attribution to commits.

## Pre-PR checklist

1. `git fetch origin` — ensure local refs are current
2. `git rebase origin/main` — PR branch starts from latest
3. Run tests for the affected package(s)
4. Verify no internal docs (handoffs, AARs, receipts, trackers) are in the public repo

## Public/private boundary

This is a **public** repository. Do not commit:
- Internal handoffs or session transcripts
- AARs (After Action Reviews)
- Internal receipts or audit files
- Operator names, machine hostnames, or internal infrastructure details
- Fleet inventory or audit matrices

Internal artifacts belong in the private `hummbl-io/hummbl-governance` repo.
