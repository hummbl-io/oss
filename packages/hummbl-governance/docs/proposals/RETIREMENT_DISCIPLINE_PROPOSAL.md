---
expires_for_review: 2026-11-16
last_reviewed: 2026-08-18
---

# PROPOSAL: Retirement Discipline for Procedural Artifacts

**Status:** DECIDED — operator ratified 2026-08-18 (see Decisions below)
**Author:** HUMMBL Research Institute (prepared by Devin, rec 5 of peer review synthesis)
**Date:** 2026-08-18
**Origin:** Weber P0-1, Luhmann P1-3, Foucault P0-1 — the fleet adds but never removes

## Decisions (operator-ratified 2026-08-18)

- **Q1 Review intervals:** TIERED — 90 days for proposals, 180 days for rules/evals, 365 days for ADRs
- **Q2 Who reviews:** AGENTS PROPOSE, OPERATOR RATIFIES — ACTIVE agents can flag artifacts for retirement; only the operator can execute (renew/retire/merge)
- **Q3 Backfill scope:** BACKFILL ALL — all 189 rules + 11 eval cases + existing proposals get `expires_for_review` set to 2027-02-18 (6 months from ratification)
- **Q4 Chain retirement:** YES, INCLUDE — KRINEIA chain-level retirement covered; repos can be marked "receipts dormant"

## Problem

The HUMMBL fleet has a `RETIRED` status for agents but no analogous mechanism for rules, eval cases, or receipt chains. The 15-action session added 7 direct fixes, 2 proposals, 3 eval categories, 6 golden fixtures, 60 chain activations, 3 SemVer normalizations, and 21 SHA pins. None removed any existing artifact. Weber's iron cage forms not because any single rule is oppressive but because rules accumulate without removal.

The fleet knows how to add. It does not yet know how to remove.

## Proposal

Every new procedural artifact (rule, eval case, receipt chain entry, governance document) carries an `expires_for_review` date. Artifacts not reviewed by their date are flagged for retirement.

### Scope

Applies to:
- `~/.agents/rules/*.md` — behavioral DNA files
- `apex-nexus/evals/cases/*.jsonl` — eval case definitions
- `_receipts/krineia/primary.jsonl` — receipt chain entries (the chain itself is append-only; this governs review of the chain's active relevance)
- `docs/proposals/*.md` — proposals (already have a DRAFT status; this adds aging)
- `docs/adr/*.md` — architecture decision records

Does NOT apply to:
- Agent definitions (`~/.agents/agents/*.md`) — already have DORMANT/PROBATIONARY/RETIRED status
- Skills (`~/.agents/skills/*/SKILL.md`) — skills are invocable; retirement is via the skill index `--check`
- Source code — governed by git history, not procedural review

### Mechanism

1. **`expires_for_review` field:** Every new rule/eval case/proposal includes an `expires_for_review` date in its frontmatter or metadata. Default: 180 days (6 months) from creation.

2. **Review trigger:** A scheduled job (monthly) scans all in-scope artifacts for `expires_for_review` dates that have passed. Expired artifacts are flagged in a bus `WARNING` and listed in a `docs/trackers/RETIREMENT_QUEUE.md`.

3. **Review outcomes:** For each expired artifact, the reviewer (operator or delegated agent) chooses:
   - **RENEW** — update the `expires_for_review` date to +180 days, add a `last_reviewed` field
   - **RETIRE** — move to `_archive/` subdirectory, add a `retired` field with date and reason
   - **MERGE** — combine with another artifact, retire the duplicate

4. **Retirement directory:** Each rules/evals/proposals directory gets an `_archive/` subdirectory. Retired artifacts move there, preserving history without polluting active surfaces.

5. **CI gate:** A `retirement-check` CI step fails if any artifact has an `expires_for_review` date more than 30 days past without a review decision. This prevents indefinite accumulation.

### Implementation Steps

1. Add `expires_for_review` and `last_reviewed` fields to the rule/eval case frontmatter schema
2. Create `scripts/retirement_check.py` — scans for expired artifacts, generates the retirement queue
3. Add `retirement-check` step to `apex-nexus/.github/workflows/ci.yml`
4. Create `docs/trackers/RETIREMENT_QUEUE.md` — the live queue
5. Backfill `expires_for_review` on existing artifacts (set to 2027-02-18 for all current rules/evals — 6 months from this proposal)

### Open Questions

1. **Default review interval:** 180 days (6 months) seems reasonable for rules and evals. Should proposals have a shorter interval (90 days) since they're decision-pending? Should ADRs have a longer interval (365 days) since they're architectural?

2. **Who reviews:** The operator is the default reviewer. Should ACTIVE agents be able to propose retirement (not execute it)? This connects to Ostrom's collective-choice deficit (P0-1 from the Ostrom review).

3. **Backfill scope:** Should we backfill `expires_for_review` on all 189 existing rules, or only on new rules going forward? Backfilling all 189 is a large task but ensures the fleet starts clean.

4. **Receipt chains:** KRINEIA chains are append-only — you can't retire a receipt. But you can retire the chain itself (mark the repo as no longer requiring active receipts). Should this proposal cover chain-level retirement, or is that a separate concern?

## Cost of Inaction

Per the Weber review: "The fleet adds but never removes. Every new rule, eval case, and receipt chain accumulates indefinitely. The iron cage forms not through oppression but through density." Without a retirement discipline, the fleet's procedural surface grows monotonically. Each new rule increases the cognitive load on agents, the eval suite's runtime, and the operator's review burden. The cost is not immediate — it compounds over months and years until the fleet becomes unmaintainable.
