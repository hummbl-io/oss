# ADR-004 — hummbl-governance repo governance baseline

- **Status:** accepted
- **Date:** 2026-06-22
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none

## Context

`hummbl-io/hummbl-governance` is the canonical host of the HUMMBL Repo Standard v0.1 and its JSON Schema. It has a strong `AGENTS.md` and `CLAUDE.md` but was missing its own governance artifact stack: `CONSTITUTION.md`, `KRINEIA.md`, `hummbl.repo.yaml`, `CODEOWNERS`, `_receipts/`.

## Decision

Adopt the HUMMBL Repo Standard v0.1 artifact stack for `hummbl-io/hummbl-governance` itself. The canonical standard host should lead by example.

### Files added

| File | Purpose |
|------|---------|
| `CONSTITUTION.md` | 8 protected invariants: zero runtime deps, coverage floor, thread safety, MCP tool contract, Apache-2.0, receipt integrity, schema stability, canonical standard host |
| `KRINEIA.md` | repo-local receipt manifest |
| `hummbl.repo.yaml` | machine-readable manifest |
| `CODEOWNERS` | normative files require steward approval |
| `docs/adr/ADR-004` | this decision record |
| `_receipts/krineia/primary.jsonl` | genesis receipt |

## Consequences

- **Positive:** The canonical standard host is now self-compliant.
- **Positive:** 8 protected invariants are constitutionally protected.
- **Note:** ADR numbering continues from ADR-003 (the standard adoption).

## Receipts

- Genesis receipt: `_receipts/krineia/primary.jsonl` line 1.
