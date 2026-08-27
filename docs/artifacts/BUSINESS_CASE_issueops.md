# Business Case: IssueOps Teaching Surface (#410)

**Status:** live v1.0 internal (promoted 2026-06-23 per ARTIFACT_STACK_PROMOTION_PACKET.md; private — not for external publication; Phase 1 funding approved)
**Owner:** Operator
**Steward:** HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 5)
**Reader:** Operator (operator)
**Decision:** fund Phase 1 of the IssueOps teaching surface, defer, or skip

---

## 1. The decision requested

Approve **$0 upfront capital** and **~40 engineering hours** to build Phase 1 of the IssueOps teaching surface at `hummbl.io/issueops.html` — a static page with an IssueOps walkthrough, glossary, and client-side receipt verification widget.

Phase 1 is the static teaching surface only. Live receipt feed (Phase 2), live bus feed (Phase 3), and interactive verification (Phase 4) are sequenced behind separate funding decisions.

## 2. The problem

HUMMBL sells governance infrastructure, but the public surface is invisible. A buyer who lands on `hummbl.io` sees marketing pages and a claims manifest — they cannot see _how an agent-governed fleet actually operates_. The thing we sell (deterministic agent governance with receipts) is the thing we don't show.

The competitive analysis (Day 4) confirmed the wedge: HUMMBL's unique position is the **proof gap** — buyers can verify our claims themselves rather than trusting a dashboard. But the proof gap is currently theoretical on the public surface. There is no public page where a visitor can:

- See what IssueOps (the entry point for agentic CI/CD) looks like
- Verify a KRINEIA receipt themselves
- Learn the vocabulary (KRINEIA, receipt, deterministic gate) that the white paper (Day 1) depends on

Without this surface, the white paper's call to action ("verify it yourself") lands on a buyer who has nowhere to verify anything.

## 3. The options

### Option A: Build Phase 1 (recommended)

**What:** Static `/issueops.html` with:

- IssueOps teaching walkthrough (7 steps, copyable templates)
- Glossary (KRINEIA, receipt, deterministic gate, IssueOps, agent contract, constitution, doctrine, steward, bus, dispatch manifest)
- Client-side verification widget (paste a receipt hash, verify against the published chain)

**Cost:**

- Capital: $0 (static page on existing Cloudflare Pages)
- Engineering hours: ~40 (1 week at 50% allocation)
- Ongoing maintenance: ~2 hours/month

**Benefits:**

- Closes the proof gap on the public surface
- Gives the white paper's call to action a destination
- Establishes the teaching surface that Phase 2-4 build on
- First public artifact that is _interactive proof_, not just _assertion_

**Risks:**

- Low traffic initially (mitigated: success metrics track this explicitly)
- Walkthrough becomes stale (mitigated: versioned, quarterly review per artifact manifest)

### Option B: Defer Phase 1, build Phase 2 (live receipt feed) first

**What:** Skip the static teaching surface, build the live receipt feed directly.

**Cost:**

- Capital: $0 (Cloudflare Worker on existing account)
- Engineering hours: ~80 (2 weeks — aggregator worker + feed UI + filtering)
- Ongoing maintenance: ~4 hours/month

**Benefits:**

- More impressive to a technical buyer (live data vs. static walkthrough)
- Shows the receipts are current, not just historical

**Risks:**

- A live feed without a teaching surface is incomprehensible to a non-expert buyer
- Higher complexity, higher maintenance, higher risk of bugs
- Skips the vocabulary establishment that the white paper depends on
- Violates the strategic plan's sequencing (Phase 1 before Phase 2)

**Why not:** A live feed without a teaching surface is a demo for experts, not a teaching surface for buyers. The white paper's audience is enterprise buyers and analysts, not (yet) engineers. Phase 1 first.

### Option C: Do nothing

**What:** Keep `hummbl.io` as a marketing site with claims manifest. No IssueOps surface.

**Cost:** $0, 0 hours

**Benefits:** None

**Risks:**

- The proof gap stays theoretical
- The white paper's call to action has no destination
- The strategic plan's Q4 2026 exit gate (3 discovery calls) becomes harder — inbound has nowhere to land
- The category-creation bet (strategic plan Bet 1) loses its primary teaching surface

**Why not:** The strategic plan (Day 2) makes IssueOps Phase 1 a Q4 2026 goal. Deferring it to "do nothing" breaks the plan. If the plan is wrong, revise the plan; do not silently skip its goals.

### Option D: Buy (no viable vendor)

There is no vendor that sells an "IssueOps teaching surface with KRINEIA receipt verification." This is not a buy-vs-build decision; it is a build-vs-skip decision.

## 4. Cost analysis

### 4.1 Capital cost

| Item                        | Cost                               |
| --------------------------- | ---------------------------------- |
| Cloudflare Pages (existing) | $0 (within current $20/month plan) |
| Domain (existing hummbl.io) | $0                                 |
| SSL, CDN                    | $0 (Cloudflare included)           |
| **Total capital**           | **$0**                             |

### 4.2 Engineering hours

| Task                                                                    | Hours        |
| ----------------------------------------------------------------------- | ------------ |
| Draft walkthrough content (7 steps, copyable templates)                 | 8            |
| Draft glossary (15-20 terms)                                            | 4            |
| Build verification widget (client-side JS, fetch chain from GitHub raw) | 12           |
| Build static page (HTML/CSS, brand guidelines)                          | 8            |
| Claims addition to claims-provenance.json                               | 4            |
| Testing (cross-browser, mobile, receipt verification)                   | 4            |
| **Total**                                                               | **40 hours** |

At 50% allocation (20 hours/week per strategic plan), this is 2 weeks of calendar time. At 100% allocation, 1 week.

### 4.3 Ongoing maintenance

| Task                                                    | Hours/month        |
| ------------------------------------------------------- | ------------------ |
| Walkthrough review (quarterly, ~1 hour amortized)       | 0.33               |
| Glossary review (quarterly)                             | 0.17               |
| Widget maintenance (browser compat, GitHub API changes) | 1                  |
| Claims audit (quarterly, amortized)                     | 0.5                |
| **Total**                                               | **~2 hours/month** |

### 4.4 Opportunity cost

The 40 hours spent on Phase 1 are 40 hours not spent on:

- Game engine roadmap Stage 0 (doctrine formalization) — but Stage 0 is Q3 2026, IssueOps is Q4 2026, no conflict
- hummbl-governance library improvements — but the library is at v1.2.0 and stable
- Sales outreach — but the strategic plan is inbound-first, and IssueOps Phase 1 _is_ the inbound surface

The opportunity cost is low because Phase 1 is the inbound surface that the strategic plan's Q4 exit gate (3 discovery calls) depends on.

## 5. Benefit analysis

### 5.1 Quantitative benefits

| Metric                                               | Baseline (now) | Target (Q4 2026, 3 months post-launch) | Target (Q1 2027, 6 months) |
| ---------------------------------------------------- | -------------- | -------------------------------------- | -------------------------- |
| Unique visitors to /issueops.html/month              | 0              | 100                                    | 300                        |
| Verification widget uses/month                       | 0              | 10                                     | 50                         |
| Inbound discovery calls mentioning IssueOps          | 0              | 1                                      | 3                          |
| Time-to-first-receipt-verification for a new visitor | n/a            | < 2 minutes                            | < 2 minutes                |

These are conservative targets. The strategic plan's Q4 exit gate is 3 discovery calls total (not all from IssueOps); IssueOps is one of three inbound sources (white paper, IssueOps, case study).

### 5.2 Qualitative benefits

1. **Closes the proof gap on the public surface.** The white paper (Day 1) argues "verify it yourself"; Phase 1 makes that possible.
2. **Establishes the vocabulary.** The glossary gives every later artifact (case studies, position papers, analyst briefing) a shared terminology.
3. **Creates the Phase 2-4 foundation.** The static page is the host for the live feed (Phase 2), bus feed (Phase 3), and interactive verification (Phase 4). Without Phase 1, Phases 2-4 have nowhere to live.
4. **Differentiates from competitors.** No competitor (per Day 4 analysis) offers a public "verify our receipts yourself" surface. This is a category-creation move.
5. **Builds the teaching surface that the game engine roadmap (#408) Stage 1 playtest depends on.** The playtest measures whether users can verify a receipt chain; the IssueOps widget is the reference implementation of that verification.

### 5.3 Strategic alignment

| Strategic plan element                   | How Phase 1 supports it                       |
| ---------------------------------------- | --------------------------------------------- |
| Bet 2: Public proof beats private demos  | Phase 1 is the public proof surface           |
| Q4 2026 goal: 3 discovery calls          | Phase 1 is the inbound destination            |
| Q4 2026 goal: First case study published | Case study links to IssueOps for verification |
| Category-creation bet                    | Phase 1 teaches the category vocabulary       |
| White paper call to action               | Phase 1 is where the call to action lands     |

## 6. ROI analysis

### 6.1 Direct ROI (conservative)

- **Cost:** 40 engineering hours + $0 capital + 2 hours/month maintenance
- **Revenue trigger:** 1 inbound discovery call mentioning IssueOps by Q4 2026
- **Conversion assumption:** 1 in 3 discovery calls becomes a paid pilot (strategic plan assumption)
- **Pilot value:** $25k-$75k (strategic plan Q1 2027 pilot range)
- **Expected revenue from Phase 1:** (1 call × 33% conversion × $50k midpoint) = ~$16.5k expected value
- **ROI:** $16.5k / (40 hours × $100/hour opportunity cost) = $16.5k / $4k = **4.1x** on the first pilot

This is conservative because:

- It counts only the first pilot, not downstream pilots
- It uses the midpoint pilot value, not the upper bound
- It assumes only 1 call (the target), not the 3-call Q4 goal

### 6.2 Indirect ROI

- **White paper effectiveness:** the white paper's CTA lands on a real destination, increasing white paper conversion rate (unmeasured but non-zero)
- **Case study credibility:** the case study can link to IssueOps for receipt verification, increasing case study credibility
- **Analyst placement:** Forrester submission (Q3 2027) can reference the public verification surface as evidence of "verify-it-yourself" positioning
- **Differentiation defensibility:** once the surface is live, competitors cannot claim "first public receipt verification surface" — HUMMBL has it

### 6.3 Payback period

- Cost: 40 hours (~$4k opportunity cost) + $0 capital
- First revenue: Q1 2027 pilot ($25k-$75k)
- **Payback: < 1 pilot**

Phase 1 pays for itself with the first paid pilot it helps generate. Even at 10% attribution (the pilot would have happened anyway), the payback is < 1 pilot.

## 7. Risks

| Risk                                | Likelihood | Impact | Mitigation                                                                                                           |
| ----------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| Low traffic (no one visits)         | Medium     | Medium | White paper + case study link to it; SEO for "IssueOps" and "agent governance"; success metric tracks visits monthly |
| Widget breaks (GitHub API change)   | Low        | Low    | Widget fetches from GitHub raw URLs (stable); fallback to cached chain; monthly maintenance checks                   |
| Walkthrough becomes stale           | Medium     | Low    | Versioned (v0.1, v0.2...); quarterly review per artifact manifest; ADR required for protocol changes                 |
| Buyer doesn't understand the widget | Medium     | Medium | Glossary + walkthrough teach the vocabulary; pilot experiment (#408 Stage 1) tests comprehension explicitly          |
| Claims on the page are wrong        | Low        | Medium | Per CONSTITUTION §3.1, every claim goes in claims-provenance.json before publication; quarterly claims audit         |
| Phase 1 slips into Phase 2 scope    | Medium     | Medium | Strict scope: static only; live feed is a separate funding decision                                                  |

## 8. Success metrics

| Metric                                   | How measured                 | Target (Q4 2026)    | Target (Q1 2027)  |
| ---------------------------------------- | ---------------------------- | ------------------- | ----------------- |
| Page live                                | Visual check                 | Yes by Oct 15, 2026 | —                 |
| Unique visitors/month                    | Cloudflare Analytics         | 100                 | 300               |
| Verification widget uses/month           | Widget telemetry (anonymous) | 10                  | 50                |
| Inbound calls mentioning IssueOps        | Sales CRM tag                | 1                   | 3                 |
| Time-to-first-verification               | Widget telemetry             | < 2 min             | < 2 min           |
| Claims on page in claims-provenance.json | Manifest check               | 100%                | 100%              |
| Walkthrough version current              | Review log                   | v0.1                | v0.2 (if revised) |

## 9. Phasing (recap from product brief #410)

| Phase       | Scope                                                    | Cost       | When       | Funding decision       |
| ----------- | -------------------------------------------------------- | ---------- | ---------- | ---------------------- |
| **Phase 1** | Static teaching surface + glossary + verification widget | 40 hrs, $0 | Q4 2026    | **This business case** |
| Phase 2     | Live receipt feed (aggregator worker)                    | 80 hrs, $0 | Q1 2027    | Separate business case |
| Phase 3     | Live bus feed (filtered public-safe messages)            | 60 hrs, $0 | Q1-Q2 2027 | Separate business case |
| Phase 4     | Interactive verification (any pasted receipt)            | 40 hrs, $0 | Q2-Q3 2027 | Separate business case |

This business case funds Phase 1 only. Phases 2-4 are sequenced behind their own gates — Phase 1 success metrics inform whether to fund Phase 2.

## 10. Recommendation

**Fund Phase 1.** The cost is low ($0 capital, 40 hours), the ROI is positive on the first pilot it helps generate, the strategic alignment is high (it is the inbound surface the Q4 2026 exit gate depends on), and the risk is low (static page, no live data, no security surface).

The alternative (defer or skip) breaks the strategic plan's Q4 2026 sequencing and leaves the white paper's call to action without a destination.

## 11. Open questions

1. **Timing:** build Phase 1 in Q3 2026 (ahead of the Q4 2026 target) or on schedule in Q4? (Recommendation: Q3 — the white paper is already drafted and needs a destination; building Phase 1 early gives Q4 room for the case study and Minecraft prototype.)
2. **Scope: glossary depth:** 15 terms or 25 terms? (Recommendation: 15 for v0.1 — the glossary is a reference, not a textbook; expand on demand.)
3. **Widget: fetch from GitHub raw or from a Cloudflare-cached copy?** (Recommendation: GitHub raw for v0.1 — simpler, no caching infra; add Cloudflare cache in Phase 2 if latency matters.)
4. **Claims: how many new claims does Phase 1 add to claims-provenance.json?** (Recommendation: estimate 5-8 claims — "live receipt verification widget", "IssueOps walkthrough", "glossary", etc. — exact count determined at implementation.)
5. **Analytics: Cloudflare Analytics (privacy-preserving, no cookies) or Plausible/Umami?** (Recommendation: Cloudflare Analytics for v0.1 — already included in the existing plan, no new dependency.)

## 12. Next steps

1. **This business case:** operator decision (no Board review needed — within operator authority per strategic plan).
2. **On approval:** emit ADR-002 recording the decision to build Phase 1.
3. **Implementation:** 40 hours, target completion Oct 15, 2026 (or earlier if Q3 timing is chosen).
4. **Claims:** add Phase 1 claims to claims-provenance.json before page goes live.
5. **Receipt:** emit KRINEIA receipt when the page ships.

## References

- Product brief: `docs/product/ISSUEOPS_TEACHING_SURFACE_BRIEF.md`
- Issue: `hummbl-io/hummbl-production#410`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Strategic plan: `docs/artifacts/STRATEGIC_PLAN_12mo.md`
- Risk register: `docs/artifacts/RISK_REGISTER.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This business case was drafted by Devin at the direction of the Principal Agent and was promoted to live (internal) by Principal Agent decision on 2026-06-23 (KRINEIA receipt recorded; bus REVIEW 2026-06-23). Phase 1 funding was approved per the packet's section 4.5 recommendation. This document is **private** — internal funding decision, not for external publication.
