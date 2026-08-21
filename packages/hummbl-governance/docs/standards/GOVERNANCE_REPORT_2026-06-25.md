# Governance Report | HUMMBL | 2026-06-25

**Period:** 2026-06-25 (single-day snapshot; first recurring report)
**Author:** devin (OWNER PROXY / primary Steward)
**Audience:** Board / Leadership + Technical
**Bus receipt:** Posted 2026-06-25T23:08Z
**Revision:** 2026-06-25T23:20Z — corrected control counts, added missing ISO 27001, fixed DOCTRINE.md risk inversion, fixed validation rate (per peer review)

---

## Executive Summary

HUMMBL's governance posture is **strong on framework coverage but weak on evidence validation**. Across 12 compliance frameworks, 237 controls are self-reported as implemented (✅), 198 have evidence rows in the validation system, and only 5 (2.5%) have automated evidence validation passing in CI — the ratchet baseline established today. Fleet-wide repo standard adoption jumped from 1 to 68 of 69 active non-fork repos having DOCTRINE.md in a single Phase 7 rollout. CI is green, 22 BLOCKED messages were all resolved same-day, and 20+ PRs merged. The critical gap is evidence validation: the ratchet is set at 2.5% and must ratchet upward each period.

**Methodology caveat — three-tier metric:** This report distinguishes three levels of control maturity:
1. **Self-reported implemented (✅)**: 237 controls — agent-authored marks in coverage matrices; not independently audited
2. **Fulfilled (evidence rows exist)**: 198 controls — the validation system recognizes these as having evidence rows
3. **Validated (evidence passes CI)**: 5 controls — automated row-identity validation passes in the ratchet gate

Board audience should weight the **validated** rate (2.5%), not the self-reported ✅ rate, when assessing compliance maturity. The gap between 237 ✅ and 198 fulfilled indicates 39 controls are marked implemented but lack evidence rows in the validation system.

---

## Compliance Scorecard

| Framework | ✅ Self-reported | Fulfilled (evidence rows) | Validated (CI ratchet) | Validation % | Trend | Status |
|-----------|-----------------|--------------------------|----------------------|-------------|-------|--------|
| NIST AI RMF | 36 | 35 | 0 | 0.0% | NEW | ON TRACK |
| NIST CSF 2.0 | 51 | 46 | 0 | 0.0% | NEW | ON TRACK |
| SOC 2 | 33 | 1 | 0 | 0.0% | NEW | NEEDS ATTENTION |
| ISO 27001 | 36 | 35 | 0 | 0.0% | NEW | ON TRACK |
| ISO 42001 | 23 | 2 | 0 | 0.0% | NEW | NEEDS ATTENTION |
| EU AI Act | 24 | 16 | 3 | 18.8% | NEW | NEEDS ATTENTION |
| GDPR | 21 | 20 | 2 | 10.0% | NEW | NEEDS ATTENTION |
| OWASP LLM Top 10 | 8 | 8 | 0 | 0.0% | NEW | ON TRACK |
| Colorado AI Act | 17 | 16 | 0 | 0.0% | NEW | NEEDS ATTENTION |
| NYC LL144 | 7 | 6 | 0 | 0.0% | NEW | ON TRACK |
| G7 AI Code | 6 | 6 | 0 | 0.0% | NEW | ON TRACK |
| IMDA Agentic | 8 | 7 | 0 | 0.0% | NEW | ON TRACK |
| **FLEET TOTAL** | **237** | **198** | **5** | **2.5%** | **NEW baseline** | **RATCHET SET** |

**Scoring methodology:**
- **✅ Self-reported** = control appears in coverage matrix with ✅ mark (agent-authored; not independently audited)
- **Fulfilled** = control has an evidence row in the validation system (EVIDENCE_VALIDATION.json `totals.fulfilled`)
- **Validated** = control's evidence row passes automated row-identity validation in CI ratchet gate (independently verified)
- **Validation %** = Validated / Fulfilled (the ratchet metric; monotonically increasing — can only go up)
- Note: SOC 2 (1 fulfilled vs 33 ✅) and ISO 42001 (2 fulfilled vs 23 ✅) show large gaps between self-reported and evidence-row counts, indicating the validation tool may parse these matrices differently or use stricter fulfillment criteria

---

## Risk Posture

| Risk | Severity | Trend | Status |
|------|----------|-------|--------|
| Evidence validation gap (2.5% validated vs 198 fulfilled) | HIGH | Stable | Ratchet baseline set; upward-only from here |
| 1 of 69 active repos still missing DOCTRINE.md | MEDIUM | Improving | Phase 7 rollout nearly complete (68/69 done) |
| 39 controls marked ✅ but missing evidence rows | MEDIUM | Stable | Gap between self-reported and fulfilled; needs investigation |
| Codex usage quota exhausted | MEDIUM | Stable | Codex on offline fallback; devin covering |
| Disk pressure (92% → 91% after cleanup, 19GB free) | LOW | Improving | 3.6GB reclaimed in ops sweep |
| rules-index.md stale (12 days) | LOW | Stable | Metadata debt; empty Status/Owner columns |
| Roster divergence (two SoT files) | LOW | Stable | `~/.agents/ROSTER.md` vs `~/.agents/rules/agent-roster.md` |

---

## Key Metrics

| Metric | Value | Previous (2026-06-22) | Trend |
|--------|-------|----------------------|-------|
| Total repos | 104 | 91 | Improving (+13) |
| Active non-fork repos | 69 | ~69 | Stable |
| Repos with DOCTRINE.md | 68 | 1 | Improving (+67) |
| Repos with CODEOWNERS | 66 | ~15 | Improving (+51) |
| Repos with full governance stack | 14 | 0 | Improving (+14) |
| Canonical rules | 139 | ~130 | Improving |
| Candidate rules (T2 observe) | 53 | — | Stable |
| Skills | 572 | — | Growing |
| Memory pins | 175 | — | Growing |
| Bus messages (today) | 573 | 437 (2026-06-22) | High activity |
| BLOCKED messages (today) | 22 | — | All resolved |
| PRs merged (today) | 20+ | — | High throughput |
| CI status (hummbl-governance) | GREEN | — | Stable |
| Tests (hummbl-governance) | 1,329 | — | Stable |
| Controls self-reported (✅) | 237 | — | NEW |
| Controls with evidence rows (fulfilled) | 198 | — | NEW |
| Controls validated (CI ratchet) | 5 | 0 | Baseline set |
| Evidence validation rate | 2.5% | 0% (new ratchet) | Baseline set |

---

## Incidents Summary

| Date | Severity | Description | Status |
|------|----------|-------------|--------|
| 2026-06-25 | P1 | 13 ruff lint errors in coverage_ratchet + test files | RESOLVED — all fixed, CI green |
| 2026-06-25 | P1 | Flaky test `test_random_agent_ids` on Python 3.13 (agent ID collisions) | RESOLVED — min ID length increased to 8 |
| 2026-06-25 | P1 | Codex usage quota exhausted | MITIGATED — codex on offline fallback, devin covering |
| 2026-06-25 | P2 | hummbl-bibliography#72 CI failure (invalid model ref "P0") | RESOLVED — fixed + merged |
| 2026-06-25 | P2 | Disk pressure 92% on huxley | RESOLVED — 3.6GB reclaimed, down to 91% (19GB free) |
| 2026-06-25 | P2 | 8 stale worktree directories (PRs merged, dirs not cleaned) | RESOLVED — all removed |
| 2026-06-25 | P3 | Runaway `du` process eating 44% CPU | RESOLVED — killed |

---

## Recommendations

1. **Ratchet the evidence validation rate upward** — The 2.5% baseline (5/198) is set. Next period target: 15% (~30/198 controls). Prioritize NIST AI RMF (35 fulfilled) and ISO 27001 (35 fulfilled) — highest control counts with evidence rows already in place. Each ratchet step is irreversible per the ratchet gate design.

2. **Close the ✅-to-fulfilled gap** — 39 controls are marked ✅ but have no evidence rows in the validation system. SOC 2 (33 ✅ vs 1 fulfilled) and ISO 42001 (23 ✅ vs 2 fulfilled) are the largest gaps. Investigate whether the validation tool is parsing these matrices incorrectly or whether evidence rows need to be added.

3. **Complete Phase 7 DOCTRINE.md rollout** — 1 of 69 active non-fork repos still needs DOCTRINE.md. 8 Tier 7a repos (score 12/15) need only DOCTRINE.md to reach 13/15. This is the single highest-leverage governance improvement available.

4. **Promote 4 C1 candidate rules to canonical** — `cron-timezone-preflight`, `croncreate-durable-lock-preflight`, `fix-without-rca-stop`, and `guard-discipline-tests-and-state-machine` are all C1 (codify immediately — caused P0/P1 harm) but still in the candidate zone. Promote with retirement-pairing per `rule-lifecycle.md`.

---

## Next Period Focus

1. **Evidence validation ratchet**: Move from 2.5% → 15% by adding row-identity validation for NIST AI RMF (35 fulfilled) and ISO 27001 (35 fulfilled)
2. **✅-to-fulfilled gap investigation**: Determine why SOC 2 and ISO 42001 have 33 and 23 ✅ marks but only 1 and 2 fulfilled evidence rows
3. **Phase 7 completion**: Scaffold DOCTRINE.md for remaining 1 repo + 8 Tier 7a repos
4. **C1 candidate promotion**: Promote 4 C1 candidates to canonical with retirement-pairs
5. **Roster reconciliation**: Resolve divergence between `~/.agents/ROSTER.md` and `~/.agents/rules/agent-roster.md` — pick one SoT
6. **rules-index.md refresh**: Update stale index (last updated 2026-06-13), fill empty Status/Owner columns

---

## Control Implementation Status (Technical Detail)

| Framework | ✅ Self-reported | Fulfilled | Validated | Gap (fulfilled - validated) |
|-----------|-----------------|-----------|-----------|----------------------------|
| NIST AI RMF | 36 | 35 | 0 | 35 need evidence |
| NIST CSF 2.0 | 51 | 46 | 0 | 46 need evidence |
| SOC 2 | 33 | 1 | 0 | 1 needs evidence |
| ISO 27001 | 36 | 35 | 0 | 35 need evidence |
| ISO 42001 | 23 | 2 | 0 | 2 need evidence |
| EU AI Act | 24 | 16 | 3 | 13 need evidence |
| GDPR | 21 | 20 | 2 | 18 need evidence |
| OWASP LLM | 8 | 8 | 0 | 8 need evidence |
| Colorado AI Act | 17 | 16 | 0 | 16 need evidence |
| NYC LL144 | 7 | 6 | 0 | 6 need evidence |
| G7 AI Code | 6 | 6 | 0 | 6 need evidence |
| IMDA Agentic | 8 | 7 | 0 | 7 need evidence |
| **TOTAL** | **237** | **198** | **5** | **193 need evidence** |

---

## Gap Closure Progress

| Gap | Total | Closed | Remaining | Status |
|-----|-------|--------|-----------|--------|
| DOCTRINE.md adoption | 69 | 68 | 1 remaining | Phase 7 nearly complete |
| CODEOWNERS adoption | ~69 | ~15 | ~54 remaining | Phase 7 in progress |
| CHANGELOG.md adoption | ~69 | ~42 | ~27 remaining | Phase 7 in progress |
| Evidence validation | 198 | 5 | 193 remaining | Ratchet baseline set |
| ✅-to-fulfilled gap | 237 ✅ | 198 fulfilled | 39 gap | Needs investigation |
| C1 candidate promotion | 4 | 0 | 4 remaining | Awaiting promotion |
| Roster SoT divergence | 1 | 0 | 1 remaining | Awaiting reconciliation |
| rules-index staleness | 1 | 0 | 1 remaining | Awaiting refresh |

---

## Audit Findings

- **Repo Standard Audit 2026-06-25**: 104 repos audited (up from 91). 35 archived, 23 forks (all with HUMMBL_FORK.md), 69 active non-fork. Score distribution: 8 repos at 12/15, 18 at 11/15, 27 at 10/15, 8 empty repos at 0/15.
- **Phase 7 rollout**: Phases 1-6 and 8 complete. Phase 7 (remaining 69 active non-fork repos) nearly complete. DOCTRINE.md now in 68/69 repos. Remaining gaps: CODEOWNERS (~50), CHANGELOG.md (~27).
- **nosec suppression audit**: Quarterly workflow configured (`.github/workflows/nosec-audit.yml`). Next scheduled run: Q3 (Jul 1). Issue #137 tracks manual review.
- **ADR count**: 7 ADRs in hummbl-governance. ADR-007 (coverage matrix ratchet) is the most recent.

---

## Technical Recommendations

1. **Automate evidence collection** — The 193-control evidence gap is not solvable manually. Build automated evidence collectors for each framework that produce row-identity JSON matching the ratchet schema. Prioritize NIST AI RMF (35 fulfilled, 0 validated) and ISO 27001 (35 fulfilled, 0 validated) — highest fulfilled counts with zero validation.

2. **Investigate ✅-to-fulfilled parsing discrepancy** — SOC 2 has 33 ✅ marks but only 1 fulfilled evidence row. ISO 42001 has 23 ✅ but only 2 fulfilled. Either the validation tool is parsing these matrices incorrectly, or the fulfillment criteria are stricter than the ✅ marks suggest. This discrepancy undermines the self-reported implementation rate's credibility.

3. **Ratchet gate enforcement** — The CI ratchet gate (`docs/coverage/ratchet-baseline.json`) is live. Ensure every PR that adds a control also adds its evidence row. The ratchet only moves up.

4. **Fleet-wide DOCTRINE.md template** — Create a reusable DOCTRINE.md template with repo-specific thesis section. The 8 Tier 7a repos need only this file to reach 13/15. Batch-create via script.

5. **Candidate rule triage** — 53 candidates in T2 observe-zone. 4 are C1 (overdue for promotion). Run `/skill-evolve` or manual triage to promote C1s and discard expired T2s.

6. **Roster SoT consolidation** — Two files claim to be the agent roster SoT. Pick `~/.agents/ROSTER.md` (more recent, has 2026-06-24 reconciliation note) and mark `~/.agents/rules/agent-roster.md` as a mirror with SoT header.

---

## Data Sources

- `docs/coverage/EVIDENCE_VALIDATION.json` — 12 matrices, 198 fulfilled, 5 validated, 2.5%
- `docs/coverage/ratchet-baseline.json` — baseline: 5 validated, 198 fulfilled, 2.5%
- `docs/coverage/*.md` — 12 framework coverage matrices, 237 ✅ marks total
- `docs/standards/AUDIT_2026-06-25.md` — 104 repos, Phase 7 tracking
- `docs/standards/AUDIT_2026-06-22.md` — previous audit (91 repos) for trend
- `docs/compliance-calendar.md` — quarterly review schedule
- `_state/coordination/messages.tsv` — bus activity (573 messages today)
- `gh run list` / `gh search prs` — CI and PR activity
- `~/.agents/rules/` — 139 canonical rules, 53 candidates, 4 archived
- `~/.agents/ROSTER.md` — 16 agent identities
- `~/.agents/skills/` — 572 skills
- `~/.claude/projects/-Users-others/memory/` — 175 memory pins

---

## Revision History

| Revision | Time | Changes | Reason |
|----------|------|---------|--------|
| v1 | 2026-06-25T23:08Z | Initial report | First recurring governance report |
| v2 | 2026-06-25T23:20Z | Corrected control counts (231→237✅/198 fulfilled), added ISO 27001, fixed validation rate (2.2%→2.5%), fixed DOCTRINE.md risk inversion, fixed bus count (566→573), added three-tier metric | Peer review found 4 P1 factual errors |
