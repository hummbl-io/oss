# AGENTS.md — hummbl-io/oss monorepo

## Project

**hummbl-io/oss** — monorepo consolidating public-publishable HUMMBL packages.
Currently hosts 20 Python packages under `packages/python/<name>/`.

## Packages

| Package | Path | PyPI status | Description |
|---------|------|-------------|-------------|
| hummbl-governance | `packages/python/hummbl-governance/` | Published (1.4.2) | Governance primitives for AI agent orchestration |
| base120 | `packages/python/base120/` | Published (3.0.0) | 120 reasoning operators for structured thinking |
| hummbl-kernel | `packages/python/hummbl-kernel/` | Pre-release (0.1.0) | Orchestration kernel with security and compliance enforcement |
| hummbl | `packages/python/hummbl/` | Pre-release (0.1.0) | Structured reasoning framework for AI agents |
| hummbl-bif | `packages/python/hummbl-bif/` | Published (1.0.1) | Batch Ingestion Framework for technical knowledge acquisition |
| hummbl-tuples | `packages/python/hummbl-tuples/` | Published (0.2.0) | HUMMBL Typed Tuples governance model |
| hummbl-bus | `packages/python/hummbl-bus/` | Published (0.1.0) | Secure append-only TSV coordination bus for multi-agent systems |
| hummbl-cognition | `packages/python/hummbl-cognition/` | Published (0.1.0) | Cognitive Ledger Protocol (CLP) and Open Brain server |
| governed-compression | `packages/python/governed-compression/` | Published (0.1.0) | Governed compression experiments (numpy dependency exception) |
| hummbl-lattice | `packages/python/hummbl-lattice/` | Pre-release (0.1.0) | Domain-specific reasoning operator lattices for the Domain120 framework |
| hummbl-contracts | `packages/python/hummbl-contracts/` | Pre-release (0.1.0) | HUMMBL contract schemas and stdlib-only JSON Schema validator |
| hummbl-axis | `packages/python/hummbl-axis/` | Pre-release (0.1.0) | Ladder that selects which Atlas contradiction to act on |
| hummbl-intel | `packages/python/hummbl-intel/` | Pre-release (0.1.0) | INT taxonomy framework for agent intelligence collection |
| hummbl-lint-config | `packages/python/hummbl-lint-config/` | Pre-release (0.1.0) | Shared ruff lint configuration for the HUMMBL fleet |
| idp-spec | `packages/python/idp-spec/` | Pre-release (0.1.0) | Intelligent Delegation Profile — deterministic delegation for multi-agent systems |
| hummbl-compass | `packages/python/hummbl-compass/` | Pre-release (0.1.0) | HUMMBL Directional Navigation & Multi-Agent Routing Algorithms |
| hummbl-free-models | `packages/python/hummbl-free-models/` | Pre-release (0.1.0) | HUMMBL Open-Weights & Free-Tier Model Registry Generator |
| hummbl-rubric-templates | `packages/python/hummbl-rubric-templates/` | Pre-release (0.1.0) | HUMMBL Standard Evaluation Rubric Templates & Automated Validators |
| hummbl-taxonomy | `packages/python/hummbl-taxonomy/` | Pre-release (0.1.0) | HUMMBL Governed Intelligence Tier Taxonomy & Classifier |
| hummbl-validation | `packages/python/hummbl-validation/` | Pre-release (0.1.0) | HUMMBL Invariant & Schema Validation Primitives |
| hummbl-design-tokens | `packages/python/hummbl-design-tokens/` | Pre-release (0.1.0) | HUMMBL Design Token System — fleet visual identity source of truth |
| hummbl-heraldry | `packages/python/hummbl-heraldry/` | Pre-release (0.1.0) | HUMMBL Procedural Heraldic Identity System — SHA-256 agent arms generator |
| hummbl-garage | `packages/python/hummbl-garage/` | Pre-release (0.1.0) | HUMMBL Garage — Agent Performance Index, livery presets, watch faces, failure aesthetics |

## Setup

Each package has its own `pyproject.toml` and test suite. Install a package for development:

```bash
cd packages/python/<package-name>
pip install -e ".[test]"
```

## Testing

```bash
# Per-package
cd packages/python/hummbl-governance && python -m pytest tests/ -v
cd packages/python/hummbl-kernel && python -m pytest tests/ -v
cd packages/python/hummbl && python -m pytest tests/ -v
cd packages/python/base120 && python -m pytest tests/ -v
cd packages/python/hummbl-bif && python -m pytest tests/ -v
cd packages/python/hummbl-tuples && python -m pytest tests/ -v
cd packages/python/hummbl-bus && python -m pytest tests/ -v
cd packages/python/hummbl-cognition && python -m pytest tests/ -v
cd packages/python/governed-compression && python -m pytest tests/ -v
cd packages/python/hummbl-lattice && python -m pytest tests/ -v
cd packages/python/hummbl-contracts && python -m pytest tests/ -v
cd packages/python/hummbl-axis && python -m pytest tests/ -v
cd packages/python/hummbl-intel && python -m pytest tests/ -v
cd packages/python/idp-spec && python -m pytest tests/ -v
```

## CI

- **GitHub Actions** (primary): `.github/workflows/ci.yml`, self-hosted runner, Python 3.11/3.12/3.13 matrix
- **Workflow validator**: `.github/workflows/validate-workflows.yml` — enforces SHA-pinning
- SHA-pinning is required (`sha_pinning_required: true`). Tag refs (`@v4`, `@main`) cause `startup_failure`.

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only in production code)
  - **Exception**: `governed-compression` requires `numpy>=1.26` for array operations (documented in its `pyproject.toml`)
- Test dependencies in `[test]` extras only
- Apache 2.0 license (packages); MIT OR Apache-2.0 (repo level)
- **pyproject.toml template**: `.github/PYPROJECT_TEMPLATE.toml` — copy this when creating a new package to get correct license/author/classifiers/URLs
- Commit format: Conventional Commits
- AI agents may assist with research, review, patch preparation, and operational coordination, but must not be credited in Git commit authorship metadata or commit-message trailers. Do not add `Co-authored-by`, `Generated-by`, `Authored-with`, or equivalent AI/vendor/agent attribution to commits.

## Lock files

Packages with runtime dependencies have a `requirements.lock` file generated by
`uv pip compile pyproject.toml --output-file requirements.lock`. Stdlib-only
packages (zero runtime deps) do not need a lock file. When updating a package's
runtime dependencies, regenerate its lock file.

## Pre-PR checklist

1. `git fetch origin` — ensure local refs are current
2. `git rebase origin/main` — PR branch starts from latest
3. Run tests for the affected package(s)
4. If runtime dependencies changed, regenerate `requirements.lock` for the affected package(s)
5. Verify no internal docs (handoffs, AARs, receipts, trackers) are in the public repo

## Public/private boundary

This is a **public** repository. Do not commit:
- Internal handoffs or session transcripts
- AARs (After Action Reviews)
- Internal receipts or audit files
- Operator names, machine hostnames, or internal infrastructure details
- Fleet inventory or audit matrices

Internal artifacts belong in the private `hummbl-io/hummbl-dev` repo.

## Encoding-safe file extraction (Windows)

When extracting files from git (e.g., `git show <ref>:<path>`) on Windows with PowerShell, **never pipe through PowerShell stdout** — it transcodes non-ASCII bytes through the system codepage (CP1252), corrupting UTF-8 content (em-dashes, arrows, math symbols become mojibake).

**Correct method** — use Python `subprocess` with binary capture:
```python
import subprocess, pathlib
result = subprocess.run(['git', 'show', f'{ref}:{path}'], cwd=repo, capture_output=True)
pathlib.Path(dest).write_bytes(result.stdout)  # raw bytes, no transcoding
```

**Verify after extraction** — compare bytes against the git blob:
```python
verify = subprocess.run(['git', 'cat-file', 'blob', f'{ref}:{path}'], cwd=repo, capture_output=True)
assert pathlib.Path(dest).read_bytes() == verify.stdout, "Byte mismatch"
```

**Never use** `Out-File -Encoding utf8` (adds BOM, transcodes through CP1252) or `git show ... > file` in PowerShell (same transcoding issue). If you must use the shell, use `cmd /c "git show ... > file"` which doesn't transcode.

Origin: 2026-08-27 session — mojibake introduced by `Out-File -Encoding utf8` was not caught by a flawed verification check (`chr(0xe7) in text` tested for the wrong codepoint). The correct check is byte-for-byte comparison against the git blob.

## Shell patterns to avoid (Tailscale CLI interception)

On hosts with Tailscale installed, the `tailscale` CLI binary intercepts certain shell patterns that match its subcommand syntax, causing unexpected output or failed commands:

- **`;;` in case statements**: Tailscale's CLI parser can interpret `;;` as a subcommand boundary. Use Python for multi-branch logic instead of shell `case` statements.
- **`tail -N` in piped commands**: The `tail` binary is shadowed or intercepted. Use the `read` tool (with `offset`/`limit`) instead of piping through `tail -3`, `tail -5`, etc.
- **`head -N` in piped commands**: Same issue — use `read` tool or Python `subprocess` with line slicing instead.

When a shell command returns Tailscale help text instead of expected output, this is the likely cause. Switch to the `read` tool or Python-based alternatives.

Origin: 2026-08-28 session — repeated Tailscale CLI output appeared in 3+ shell calls during the oss Phase 3 migration, including one failed command loop.
