# ADR-002 — IssueOps Teaching Surface Decision (#410)

- **Status:** accepted
- **Date:** 2026-06-23
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** hummbl-production#410
- **Business case:** `docs/artifacts/BUSINESS_CASE_issueops.md` (item 5)

## Context

HUMMBL sells governance infrastructure, but the public surface at `hummbl.io` does not show how an agent-governed fleet actually operates. A buyer who lands on the site sees marketing pages and a claims manifest — they cannot see IssueOps (the entry point for agentic CI/CD), verify a KRINEIA receipt themselves, or learn the vocabulary (KRINEIA, receipt, deterministic gate) that the white paper depends on.

The competitive analysis (Day 4, item 4) confirmed HUMMBL's wedge is the **proof gap** — buyers can verify HUMMBL's claims themselves rather than trusting a dashboard. But the proof gap is currently theoretical on the public surface. The white paper's call to action ("verify it yourself") lands on a buyer who has nowhere to verify anything.

The business case (item 5) evaluated 4 options (build Phase 1, defer to Phase 2, do nothing, buy) and recommended Option A: build Phase 1, the static teaching surface, at `hummbl.io/issueops.html`. Phase 1 is the static page only; live receipt feed (Phase 2), live bus feed (Phase 3), and interactive verification (Phase 4) are sequenced behind separate funding decisions.

This ADR records the decision to accept the business case's recommendation: build Phase 1.

## Decision

**Build Phase 1 of the IssueOps teaching surface at `hummbl.io/issueops.html`.**

### Scope

Phase 1 is the static teaching surface only:

| Component                       | Description                                                                                                             |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| IssueOps walkthrough            | 7-step teaching walkthrough with copyable templates                                                                     |
| Glossary                        | KRINEIA, receipt, deterministic gate, IssueOps, agent contract, constitution, doctrine, steward, bus, dispatch manifest |
| Client-side verification widget | Paste a receipt hash, verify against the published chain (pure client-side JS, no server)                               |

### Out of scope (deferred to later ADRs)

- Phase 2: live receipt feed (Cloudflare Worker aggregator + feed UI)
- Phase 3: live bus feed (real-time coordination bus stream)
- Phase 4: interactive verification (server-side verification with custom receipts)

### Cost

- **Capital:** $0 (static page on existing Cloudflare Pages)
- **Engineering hours:** ~40 (1 week at 50% allocation)
- **Ongoing maintenance:** ~2 hours/month

### Funding

Phase 1 funding approved 2026-06-23 per the business case (item 5) status line.

### Success metrics

Per the business case §6:

| Metric                                     | Target                  | Measurement                            |
| ------------------------------------------ | ----------------------- | -------------------------------------- |
| Page live                                  | by 2026-07-15           | Page exists at hummbl.io/issueops.html |
| Unique visitors                            | 100+ in first 90 days   | Cloudflare Pages analytics             |
| Receipt verification widget uses           | 25+ in first 90 days    | Client-side event tracking             |
| Discovery calls mentioning IssueOps        | 3+ by Q4 2026 exit gate | Sales call notes                       |
| White paper CTA click-through to /issueops | 10%+                    | Client-side event tracking             |

## Alternatives considered

### Option A: Build Phase 1 (ACCEPTED)

Static `/issueops.html` with walkthrough, glossary, and client-side verification widget. $0 capital, ~40 hours, ~2 hours/month maintenance.

**Why accepted:** Closes the proof gap on the public surface. Gives the white paper's call to action a destination. Establishes the teaching surface that Phase 2-4 build on. First public artifact that is interactive proof, not just assertion. Low cost, low risk, high strategic value.

### Option B: Defer Phase 1, build Phase 2 first (REJECTED)

Skip the static teaching surface, build the live receipt feed directly. $0 capital, ~80 hours, ~4 hours/month maintenance.

**Why rejected:** A live feed without a teaching surface is incomprehensible to a non-expert buyer. The white paper's audience is enterprise buyers and analysts, not (yet) engineers. Phase 1 first establishes the vocabulary that Phase 2's live feed depends on. Violates the strategic plan's sequencing (Phase 1 before Phase 2).

### Option C: Do nothing (REJECTED)

Keep `hummbl.io` as a marketing site with claims manifest. No IssueOps surface. $0, 0 hours.

**Why rejected:** The proof gap stays theoretical. The white paper's call to action has no destination. The strategic plan's Q4 2026 exit gate (3 discovery calls) becomes harder — inbound has nowhere to land. The category-creation bet loses its primary teaching surface. If the plan is wrong, revise the plan; do not silently skip its goals.

### Option D: Buy (NOT VIABLE)

There is no vendor that sells an "IssueOps teaching surface with KRINEIA receipt verification." This is not a buy-vs-build decision; it is a build-vs-skip decision.

## Consequences

### Positive

- **Closes the proof gap on the public surface.** The white paper's "verify it yourself" call to action has a destination.
- **Establishes the teaching surface** that Phase 2-4 build on. Phase 2 (live feed) will be incomprehensible without Phase 1's glossary.
- **First public interactive proof artifact.** All prior public artifacts (white paper, position papers, case study) are assertions. Phase 1 is interactive — a visitor can verify a receipt themselves.
- **Supports the strategic plan's Q4 2026 exit gate** (3 discovery calls). Inbound has a landing page that teaches the vocabulary.
- **Low cost, low risk.** $0 capital, ~40 hours, static page on existing infrastructure.

### Negative

- **40 engineering hours** spent on Phase 1 are 40 hours not spent on other work. The opportunity cost is low because Phase 1 is the inbound surface that the strategic plan's Q4 exit gate depends on.
- **~2 hours/month maintenance** ongoing. The walkthrough must be reviewed quarterly per the artifact manifest.
- **Low traffic initially.** The success metrics track this explicitly; if traffic is below target after 90 days, escalate to the Board.

### Risks

- **Walkthrough becomes stale.** Mitigated: versioned, quarterly review per artifact manifest.
- **Low traffic.** Mitigated: success metrics track unique visitors; if below target, escalate.
- **Widget breaks.** Mitigated: client-side only, no server dependency; test in CI.

## Receipts

- **Business case promotion receipt:** in `_receipts/krineia/primary.jsonl` (governance.artifact_promoted for item 5)
- **This ADR's promotion receipt:** emitted on commit (governance.artifact_promoted for item 16)

## Implementation plan

1. **Week 1 (2026-07-01 to 2026-07-07):** Draft the IssueOps walkthrough (7 steps), glossary, and widget spec. Review with the Principal Agent.
2. **Week 2 (2026-07-08 to 2026-07-14):** Build the static page at `web/issueops.html`. Build the client-side verification widget (pure JS, no server). Test in CI.
3. **Week 3 (2026-07-15):** Deploy to Cloudflare Pages. Verify the page is live at `hummbl.io/issueops.html`. Emit a KRINEIA receipt: `governance.issueops_phase1_live`.
4. **Ongoing:** Quarterly review of the walkthrough per the artifact manifest. Monitor success metrics. Escalate to the Board if metrics are below target after 90 days.

## Boundary disclaimer

This ADR records a decision to build a static teaching surface. It is not a commitment to a specific implementation, vendor, or timeline beyond the implementation plan in §"Implementation plan". The implementation may change if the Principal Agent or the Board determines that the plan is no longer appropriate.

This ADR does not make HUMMBL a certification body, a Notified Body, or a NIST-recognized assessor. The IssueOps teaching surface teaches the vocabulary; it does not certify the visitor.

## How to verify this ADR

A reader can re-verify this ADR's claims by:

1. **The business case exists** — `ls docs/artifacts/BUSINESS_CASE_issueops.md`
2. **The business case recommends Option A** — `grep "Option A: Build Phase 1 (recommended)" docs/artifacts/BUSINESS_CASE_issueops.md`
3. **The strategic plan exists** — `ls docs/artifacts/STRATEGIC_PLAN_12mo.md`
4. **The competitive analysis exists** — `ls docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
5. **The white paper exists** — `ls docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
6. **The tracking issue exists** — `gh issue view 410 --repo hummbl-io/hummbl-production`
7. **This ADR is in the manifest** — `grep "ADR-002" docs/artifacts/ARTIFACT_MANIFEST.md`

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

## References

- Business case: `docs/artifacts/BUSINESS_CASE_issueops.md` (item 5)
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md` (item 1)
- Strategic plan: `docs/artifacts/STRATEGIC_PLAN_12mo.md` (item 2)
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md` (item 4)
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (item 11)
- Charter: `docs/artifacts/CHARTER_hri.md` (item 12)
- ADR-001: `docs/adr/ADR-001-repo-governance-baseline.md`
- Tracking issue: hummbl-production#410
- CONSTITUTION: `CONSTITUTION.md` (§3.3 Cloudflare boundary discipline)
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents) are delegated drafting, research, and execution systems. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This ADR was drafted by Devin at the direction of the Principal Agent, based on the business case (item 5), the strategic plan (item 2), the competitive analysis (item 4), and the white paper (item 1), and was promoted to live (public) by Principal Agent decision on 2026-06-23. The decision recorded in this ADR is the Principal Agent's; the implementation plan is a proposal for the Principal Agent to approve or revise. This document is **public** — ADRs are public by default per the HUMMBL Repo Standard.
