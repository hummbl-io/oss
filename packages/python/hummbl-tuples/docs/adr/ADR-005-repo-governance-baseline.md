# ADR-005 — hummbl-tuples repo governance baseline

- **Status:** accepted
- **Date:** 2026-06-22
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none

## Context

hummbl-tuples was initialized with governance artifacts (CONSTITUTION.md,
KRINEIA.md, hummbl.repo.yaml, CODEOWNERS, _receipts/) but the ADR
documenting the governance baseline adoption was missing from docs/adr/.
Existing ADRs are in adrs/ directory (pre-standard).

## Decision

Adopt the HUMMBL Repo Standard v0.1 artifact stack. Document the
governance baseline in docs/adr/ per the Init Standard.

## Alternatives considered

- Move existing adrs/ to docs/adr/ — deferred to avoid breaking references.

## Consequences

- **Positive:** Governance baseline is now documented in the standard location.
- **Negative:** Two ADR directories exist temporarily (adrs/ and docs/adr/).

## Receipts

Genesis receipt in _receipts/krineia/primary.jsonl.
