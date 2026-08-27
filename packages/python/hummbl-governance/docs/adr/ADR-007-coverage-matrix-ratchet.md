# ADR-007 — Coverage matrix ratchet gate

- **Status:** accepted
- **Date:** 2026-06-25
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Related:** [ADR-001](ADR-001-coverage-matrix-not-self-grade.md), `hummbl-io/hummbl-governance#128`

## Context

The `coverage-matrix-validate` CI job has been advisory since inception (`continue-on-error: true`). While the job runs evidence validation across all coverage matrices and generates `EVIDENCE_VALIDATION.{json,md}`, it exits successfully regardless of validation results. This means:

1. Unresolved evidence references can accumulate without any CI signal.
2. The aggregate `ci` job cannot distinguish a clean validation pass from a warning-only pass.
3. There is no mechanism to prevent regression — a PR that breaks a previously-validating evidence ref would not be caught.

As of 2026-06-25, 5 of 198 Fulfilled rows (2.5%) have validated evidence. The matrices remain DRAFT scaffolds per ADR-001, so blocking CI on full validation would be premature. However, preventing regression of the 5 validated rows is both feasible and valuable.

## Decision

Add a **ratchet gate** to the `coverage-matrix-validate` CI job. The ratchet:

1. **Baseline file**: `docs/coverage/ratchet-baseline.json` records the current validated row count (5 as of 2026-06-25).
2. **Regression check**: CI runs `scripts/coverage_ratchet.py` after evidence validation. If current validated count < baseline, the ratchet emits `::error::` and exits 1.
3. **Advisory state preserved**: The job remains `continue-on-error: true`, so ratchet failure does not block the aggregate `ci` job yet. The ratchet result is exposed as a job output (`ratchet-result`, `validated-count`, `validated-pct`, `clean-pass`).
4. **Baseline raising**: The baseline can only be raised by an explicit `--init-baseline` commit. It can never be lowered without operator approval.
5. **Promotion threshold**: When `validated_pct >= 50%`, the ratchet prints a promotion notice. At that point, `continue-on-error` should be flipped to `false`, making the ratchet a blocking gate.
6. **Row-identity ratchet** (added 2026-06-25, #136): The baseline includes a `validated_rows` array listing the specific row identities (matrix + control_id) that were validated at baseline freeze time. The ratchet checks that all baseline row identities still have `status=pass` in the current report. A baseline row that is missing or failing → FAIL even if the total count is stable or higher. This prevents row substitution from masking regression (e.g., one validated row disappears while another appears, count stays the same).
7. **Baseline-lowering protection** (added 2026-06-25, #135): `--init-baseline` refuses to lower the baseline below the existing frozen value without explicit `--force-lower --reason "..."` flags. This is a technical control, not just code review — a careless or malicious commit cannot silently lower the baseline. When `--force-lower` is used, the reason string is persisted in the baseline file as `lower_reason` for audit trail.

## Ratchet policy

| Condition | Ratchet exit | CI job result | Aggregate `ci` |
|-----------|-------------|---------------|-----------------|
| current >= baseline AND all baseline rows pass | 0 (pass) | success | success |
| current < baseline | 1 (fail) | success (advisory) | success (advisory) |
| baseline row identity lost (count stable or higher) | 1 (fail) | success (advisory) | success (advisory) |
| current >= baseline, pct >= 50% | 0 (pass) | success | success + promotion notice |
| Post-promotion: any ratchet failure | 1 (fail) | failure (blocking) | failure |

## Exit criteria for advisory state

The advisory state (`continue-on-error: true`) ends when ALL of:
1. `validated_pct >= 50%` (at least 99 of 198 rows validated)
2. A PR explicitly flips `continue-on-error` to `false`
3. The ratchet baseline has been raised to the current validated count
4. The PR references this ADR as the governing decision

## Consequences

- Regression of validated evidence rows is now visible in CI outputs even while advisory.
- The aggregate `ci` job prints ratchet status (result, count, pct, clean_pass) for every run.
- The baseline file is a committed artifact — changes to it are reviewable.
- No premature blocking of draft coverage work — the ratchet only prevents regression of already-validated rows.
- The promotion threshold (50%) provides a clear, measurable target for the team.

## Receipts

- Implementation: `scripts/coverage_ratchet.py`, `docs/coverage/ratchet-baseline.json`
- CI integration: `.github/workflows/ci.yml` — `coverage-matrix-validate` job, `Ratchet gate` step
- Tests: `tests/test_coverage_ratchet.py` — 15 tests covering count ratchet (pass, fail, init, missing baseline, promotion threshold), row-identity ratchet (preserved, lost, gained, init captures identities), and baseline-lowering protection (refuse without force, lower with force+reason, force without reason refused, raise without force)
- Acceptance: `hummbl-io/hummbl-governance#128` (count ratchet), `hummbl-io/hummbl-governance#136` (row-identity ratchet), `hummbl-io/hummbl-governance#135` (baseline-lowering protection)
- Baseline row identities (as of 2026-06-25): eu-ai-act.md/Art. 12, eu-ai-act.md/Art. 14, eu-ai-act.md/Art. 73, gdpr.md/Art. 5, gdpr.md/Art. 29
