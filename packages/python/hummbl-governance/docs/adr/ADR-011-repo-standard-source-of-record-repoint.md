# ADR-011 — Repo Standard Source of Record Repoint and §13 Amendment Route

- **Status:** proposed (pending human approval)
- **Date:** 2026-10-29
- **Decision owner:** Human Principal Agent
- **Steward:** HUMMBL, LLC
- **Supersedes:** ADR-003 (in part, canonical home and amendment route)
- **Superseded by:** none
- **Related:** hummbl-io/oss PR #360, hummbl-io/hummbl-doctrine PR #57

## Context

The standalone repository `hummbl-io/hummbl-governance` is archived and read-only.
The canonical package and active codebase for `hummbl-governance` are maintained in
`hummbl-io/oss` at `packages/python/hummbl-governance`.

In `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`:
1. The **Source of record** header pointed to the archived `hummbl-io/hummbl-governance` repository.
2. **Section 13 (Amendment)** routed changes as PRs to `hummbl-io/hummbl-governance`.

Per §13:
> "Changes to this standard require: a PR to `hummbl-io/oss` against `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`, an ADR under `docs/adr/`, a KRINEIA receipt, and human approval (Human Principal Agent)."

This ADR satisfies the ADR requirement for the §13 amendment.

## Decision

1. **Repoint Source of Record:** The header in `HUMMBL_REPO_STANDARD.md` is updated to point to `packages/python/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md` in `hummbl-io/oss` as canonical. The historical copy in the archived `hummbl-io/hummbl-governance` repository is marked read-only.
2. **Repoint Amendment Route:** §13 is amended to direct future PRs to `hummbl-io/oss` against this file.
3. **Retain Public Redaction:** In accordance with the public-repository redaction policy (PRs #166, #209), personal names remain redacted in `hummbl-io/oss`. All approving human and exception authority fields retain the canonical title `Human Principal Agent`.
4. **Stage §13 KRINEIA Receipt:** An amendment admission receipt is staged in `_receipts/krineia/pending/2026-10-29-repo-standard-s13-amendment.json` (and `docs/adr/receipts/ADR-011-receipt-staged.json`) with an explicit placeholder for Human Principal Agent signature.

## Alternatives Considered

- **Unarchive hummbl-governance repo:** Rejected. Fleet topology archives the standalone repo in favor of the unified monorepo `hummbl-io/oss`.
- **Expose approver personal name in public repository:** Rejected. Reversing the redaction policy in a public repo violates HUMMBL privacy and redaction boundaries. The Human Principal Agent designation clearly establishes human-only authority without leaking individual personal data.

## Consequences

- Authority over `HUMMBL_REPO_STANDARD.md` is canonically anchored in `hummbl-io/oss`.
- Fleet tooling and downstream documentation citing the Standard are directed to the active tree.
- The amendment is fully documented under §13 with companion ADR and staged receipt.
