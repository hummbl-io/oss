# Strategic Plan: 12-Month (Q3 2026 → Q3 2027)

**Status:** live v1.0 internal (promoted 2026-06-23 per ARTIFACT_STACK_PROMOTION_PACKET.md; private — not for external publication)
**Owner:** Operator
**Steward:** HUMMBL Research Institute
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 2)
**Reader:** Operator + Board (Operator, Future Self, Governance Officer, Risk Officer, Stakeholder Proxy)
**Decision:** resource allocation across the next 12 months — what gets funded, what gets deferred, what gets skipped

---

## 1. The one sentence

Establish HUMMBL as the defining vendor for **governance infrastructure for AI-native teams** by closing the proof gap on our own fleet, making that proof publicly verifiable, and converting the first paid pilots — without premature hiring or platform build-out.

## 2. Where we are (Q3 2026)

| Dimension           | State          | Evidence                                                                                 |
| ------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| Internal governance | Complete       | Repo Standard v0.1 adopted across 67 active repos; fleet_verify.py shows 0 real failures |
| Public claims       | Verified       | 59 claims in claims-provenance.json, 0 pending, 12 fixed in 2026-06-23 audit             |
| Library             | Shipped        | hummbl-governance v1.2.0 on PyPI, 1,234 tests, zero third-party runtime deps             |
| Receipts            | Fleet-wide     | KRINEIA genesis receipts in every active + archived non-fork repo                        |
| Product surface     | Marketing only | hummbl.io is a marketing site; no public teaching or demo surface yet                    |
| Pipeline            | Zero           | No paid pilots, no enterprise discovery calls in flight                                  |
| Revenue             | Pre-revenue    | Solo founder, no employees, no outside investment                                        |
| Runway              | Finite         | Operator-funded; cost discipline is load-bearing                                         |

The internal layer is done. The next 12 months are about making it visible and converting visibility into pipeline.

## 3. The 12-month arc

### Q3 2026 (Jul–Sep) — Foundation

**Theme:** Build the strategic artifact stack and publish the category thesis.

| Goal                                      | Success metric                                        | Owner                   |
| ----------------------------------------- | ----------------------------------------------------- | ----------------------- |
| Artifact stack Wave 1 (20 artifacts)      | 20/20 in manifest, status `live`                      | Devin + operator        |
| White paper published                     | Live on hummbl.io, claims in manifest                 | Operator approval       |
| Strategic plan approved                   | This document approved by Board                       | Board review            |
| Risk register live                        | Top 10 risks scored, mitigation owners assigned       | Operator + Risk Officer |
| Competitive analysis                      | 5 vendors profiled, HUMMBL positioning differentiated | Operator                |
| Business cases for #410, #408             | Both approved or deferred with rationale              | Operator                |
| ADR-002 (IssueOps), ADR-003 (game engine) | Both merged                                           | Operator                |

**Exit gate:** Board approves Q4 plan at end of Q3. If Wave 1 is not complete, Q4 slips by the gap.

### Q4 2026 (Oct–Dec) — First public surface

**Theme:** Ship the first public teaching and demo surfaces. Prove the proof gap is closeable externally.

| Goal                                       | Success metric                                                        | Owner            |
| ------------------------------------------ | --------------------------------------------------------------------- | ---------------- |
| IssueOps teaching surface Phase 1 (static) | `/issueops.html` live with walkthrough, glossary, verification widget | Operator + Devin |
| Minecraft prototype Stage 1                | 8 primitives playable, 5 playtesters, 4/5 can explain receipts        | Operator + Devin |
| First case study published                 | Claims remediation 2026-06-23 → public case study with metrics        | Operator         |
| Artifact stack Wave 2 (20 artifacts)       | 20/20 in manifest, status `live`                                      | Devin + operator |
| First 3 discovery calls                    | 3 calls scheduled via inbound from white paper + IssueOps page        | Operator         |
| Claims added to manifest                   | All white paper + case study claims in claims-provenance.json         | Devin            |

**Exit gate:** 3 discovery calls. If 0, the thesis-to-pipeline conversion is broken and Q1 pivots to demand generation.

### Q1 2027 (Jan–Mar) — Live proof

**Theme:** Make the proof dynamic — live receipt feed, live bus feed. Convert discovery calls to paid pilots.

| Goal                                 | Success metric                                                            | Owner                         |
| ------------------------------------ | ------------------------------------------------------------------------- | ----------------------------- |
| IssueOps Phase 2 (live receipt feed) | Aggregator worker deployed, 60s cache, read-only                          | Devin                         |
| IssueOps Phase 3 (live bus feed)     | Public-safe bus messages streaming                                        | Devin                         |
| Minecraft playtest complete          | Pilot experiment receipt chain published, success metrics met or redesign | Operator                      |
| First paid pilot signed              | 1 pilot, $25k-$75k, 90-day engagement                                     | Operator                      |
| Artifact stack Wave 3 (20 artifacts) | 20/20 in manifest, status `live`                                          | Devin + operator              |
| Compliance matrix: NIST AI RMF       | Drafted, gaps identified                                                  | Operator + Governance Officer |
| 5 more discovery calls               | 5 calls, 2 from compliance matrix outreach                                | Operator                      |

**Exit gate:** 1 paid pilot signed. If 0, the pricing/packaging thesis is wrong and Q2 pivots to packaging.

### Q2 2027 (Apr–Jun) — Scale the proof

**Theme:** Multi-engine embodiment, first pilot delivered, second pilot signed.

| Goal                                      | Success metric                                                 | Owner                         |
| ----------------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| Game engine Stage 2 (multi-game adapters) | GameEngineAdapter interface stable, 2 engines beyond Minecraft | Devin                         |
| First pilot delivered                     | Pilot complete, receipt chain, case study drafted              | Operator                      |
| Second paid pilot signed                  | 1 pilot, $50k-$150k, 90-day engagement                         | Operator                      |
| Compliance matrix: ISO 42001, EU AI Act   | Both drafted, gaps identified                                  | Operator + Governance Officer |
| Artifact stack Wave 4 begins              | Triggers firing, new artifacts created as needed               | Devin + operator              |
| 10 discovery calls cumulative             | 10 calls, 5 from compliance outreach                           | Operator                      |

**Exit gate:** 2 paid pilots cumulative. If < 2, the category thesis is not landing and Q3 pivots to category redefinition or niche focus.

### Q3 2027 (Jul–Sep) — Public demo and category claim

**Theme:** High-fidelity public demo, first industry recognition, third pilot.

| Goal                                        | Success metric                                              | Owner            |
| ------------------------------------------- | ----------------------------------------------------------- | ---------------- |
| Game engine Stage 3 (Unreal embodiment)     | Public demo live, 20 playtest sessions                      | Devin + operator |
| IssueOps Phase 4 (interactive verification) | Verification widget verifies any pasted receipt             | Devin            |
| Second pilot delivered                      | Case study published                                        | Operator         |
| Third paid pilot signed                     | 1 pilot, $75k-$250k                                         | Operator         |
| Analyst placement                           | 1 Gartner or Forrester briefing, named in a category report | Operator         |
| Press coverage                              | 2 pieces mentioning HUMMBL in AI governance context         | Operator         |
| Annual report published                     | First annual report covering Q3 2026 → Q3 2027              | Operator         |

**Exit gate:** 3 paid pilots cumulative, 1 analyst placement. If < 3 pilots, the category is not yet forming and we extend runway rather than scale.

## 4. Resource allocation

### 4.1 Time allocation (solo founder, no hires this plan)

| Activity                                                     | % of time | Hours/week |
| ------------------------------------------------------------ | --------- | ---------- |
| Product engineering (IssueOps, game engine, library)         | 50%       | 20         |
| Pipeline (discovery calls, sales, follow-up)                 | 20%       | 8          |
| Strategic artifacts (white papers, case studies, compliance) | 15%       | 6          |
| Fleet operations (governance, audits, receipts)              | 10%       | 4          |
| Board + governance overhead                                  | 5%        | 2          |

**Hiring policy:** no hires in this plan. The 12-month plan is designed to be executable by 1 human + agent fleet. First hire (engineering) considered in Q2 2027 only if 2 paid pilots are signed and pipeline supports the cost. First hire is not a goal; it is a contingent response to demand.

### 4.2 Budget allocation

| Category                              | Q3 2026  | Q4 2026  | Q1 2027  | Q2 2027  | Q3 2027    |
| ------------------------------------- | -------- | -------- | -------- | -------- | ---------- |
| Cloudflare (Pages, Workers, R2)       | $20      | $20      | $50      | $50      | $100       |
| GitHub (Pro, Actions)                 | $10      | $10      | $10      | $10      | $10        |
| AI API spend (Claude, OpenAI, Gemini) | $200     | $300     | $400     | $500     | $600       |
| Minecraft / Unreal assets             | $0       | $50      | $0       | $100     | $300       |
| Marketing (domain, email, analytics)  | $20      | $20      | $20      | $20      | $20        |
| Compliance tools (if needed)          | $0       | $0       | $0       | $200     | $200       |
| Contingency                           | $50      | $50      | $100     | $100     | $200       |
| **Total/month**                       | **$300** | **$450** | **$580** | **$980** | **$1,430** |

**Runway assumption:** operator-funded. If Q1 2027 closes with 0 paid pilots, budget contracts to $300/month contingency mode until pipeline recovers.

### 4.3 Agent fleet allocation

| Agent                                  | Role in this plan                                             | Time allocation |
| -------------------------------------- | ------------------------------------------------------------- | --------------- |
| Devin                                  | Product engineering, artifact drafting, fleet ops             | Primary lane    |
| Codex                                  | Engineering review, implementation                            | Secondary lane  |
| Claude Code                            | Peer review, synthesis, Kai scheduled sessions                | Tertiary lane   |
| Gemini                                 | Research, long-context synthesis                              | On-demand       |
| OpenCode                               | Interactive multi-model                                       | On-demand       |
| Resident agents (Apex, Nexus, Auditor) | Pre-decision assessment, pre-deploy scans, pre-publish audits | On-demand       |

## 5. The 3 strategic bets

This plan makes 3 explicit bets. If any of them is wrong, the plan adjusts.

### Bet 1: Category definition beats feature competition

We are not trying to out-feature established GRC platforms. We are trying to define a new category — "governance infrastructure for AI-native teams" — that those platforms do not occupy. The white paper, the IssueOps teaching surface, and the public demos are all category-definition spend, not feature spend.

**If wrong:** we get out-flanked by a GRC platform that adds an "AI agents" module. Pivot: narrow to a vertical (e.g., healthcare AI governance) where the GRC platforms are slow.

### Bet 2: Public proof beats private demos

We are publishing our receipt chain, our claims manifest, our fleet audit, and our case studies rather than gating them behind a sales conversation. The thesis is that buyers who can verify our claims themselves convert at higher rates than buyers who have to trust a sales deck.

**If wrong:** public proof gets ignored or copied without attribution. Pivot: gate the deepest proof (live receipt feed) behind a free registration, keep the teaching surface public.

### Bet 3: Installable library beats SaaS platform

We are building hummbl-governance as an installable Python library, not a SaaS platform. The thesis is that runtime proximity, provider neutrality, and verifiability matter more to AI-native teams than a managed dashboard.

**If wrong:** buyers prefer a managed platform and won't install a library. Pivot: wrap the library in a thin control-plane service (still library-first, but with an optional hosted aggregation layer). Do not abandon the library — it remains the enforcement layer even if the aggregation layer is hosted.

## 6. The 3 anti-goals

Explicit non-goals for this 12-month period:

1. **No SaaS platform build.** The library is the product. A hosted aggregation layer is a Q4 2027+ consideration, not this plan.
2. **No enterprise sales motion.** No field sales, no RFP responses to Fortune 500 RFPs. Inbound + product-led + analyst-influenced only. Enterprise sales is a Q4 2027+ consideration.
3. **No hiring until demand is proven.** First hire is contingent on 2 paid pilots signed, not on a headcount plan. Premature hiring is the most common solo-founder failure mode.

## 7. Risks and mitigations

| Risk                                                         | Likelihood | Impact   | Mitigation                                                                             |
| ------------------------------------------------------------ | ---------- | -------- | -------------------------------------------------------------------------------------- |
| 0 paid pilots by Q1 2027                                     | Medium     | High     | Pivot to demand generation; contract budget to runway mode                             |
| Category does not form (buyers don't recognize the category) | Medium     | High     | Vertical focus (healthcare or finance AI governance)                                   |
| GRC platform adds AI module and out-markets us               | Low        | High     | Library-first advantage: we are in the runtime, they are in the dashboard              |
| Operator burnout (solo founder, 12 months)                   | Medium     | Critical | Agent fleet absorbs engineering; operator focuses on pipeline + judgment               |
| Runway exhaustion                                            | Low        | Critical | Budget contracts to $300/month contingency mode if Q1 fails                            |
| Public proof gets copied without attribution                 | High       | Low      | Receipt chain proves provenance; copying without attribution is detectable             |
| Minecraft / Unreal demo misses the mark                      | Medium     | Medium   | Pilot experiment tests comprehension explicitly; redesign if failure response triggers |
| Compliance matrix work absorbs too much time                 | Medium     | Medium   | Time-box compliance to 15% of weekly hours; defer if over                              |

## 8. Success metrics — 12-month summary

| Metric                                               | Q3 2026 baseline | Q3 2027 target              |
| ---------------------------------------------------- | ---------------- | --------------------------- |
| Paid pilots signed                                   | 0                | 3                           |
| Discovery calls                                      | 0                | 15 cumulative               |
| Public artifacts (white papers, case studies, demos) | 0                | 5+                          |
| hummbl-governance PyPI downloads                     | low              | 1,000/month                 |
| GitHub stars across hummbl-io repos                  | current          | 2x current                  |
| Analyst placements                                   | 0                | 1                           |
| Press mentions                                       | 0                | 2                           |
| Compliance matrices drafted                          | 0                | 3 (NIST, ISO, EU AI Act)    |
| Monthly spend                                        | $300             | $1,430                      |
| Runway remaining                                     | operator-funded  | 12+ months at Q3 2027 spend |

## 9. Quarterly review cadence

| Review    | When                  | Attendees                | Output                                         |
| --------- | --------------------- | ------------------------ | ---------------------------------------------- |
| Weekly    | Every Monday          | Operator + agent fleet   | Status update, blocker surfacing               |
| Monthly   | First Monday of month | Operator + Board (async) | Monthly metric check, budget actuals           |
| Quarterly | End of each quarter   | Operator + Board (sync)  | Exit gate decision: proceed / pivot / contract |
| Annual    | End of Q3 2027        | Operator + Board         | Annual report, next-year plan                  |

## 10. Open questions for Board

1. **Runway:** what is the operator's actual runway at $300/month contingency vs $1,430/month full spend? (Needs operator input — not in this plan.)
2. **Vertical focus:** if Q1 2027 closes with 0 pilots, do we pivot to a vertical (healthcare, finance, legal) or double down on horizontal? (Recommendation: vertical — healthcare AI governance — because regulatory pressure creates buyer urgency.)
3. **Analyst strategy:** is Gartner or Forrester the right first analyst target? (Recommendation: Forrester — more receptive to category-creation narratives; Gartner is more checklist-driven.)
4. **Open-source strategy for hummbl-governance:** do we keep the library fully open-source, or add a commercial license for enterprise features? (Recommendation: fully open-source through Q1 2027; revisit at first pilot.)
5. **First hire profile:** if 2 pilots are signed by Q2 2027, is the first hire engineering or sales? (Recommendation: engineering — the operator can sell; the operator cannot scale engineering alone.)

## 11. Next steps

1. **This plan:** Board review at the next sync. Decision: approve, modify, or defer.
2. **On approval:** emit ADR-004 recording the strategic plan decision.
3. **Q3 2026 execution:** continue artifact stack Wave 1 (Day 3: risk register).
4. **Q3 2026 exit gate:** Board reviews Wave 1 completion + Q4 plan at end of Q3.

## References

- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Artifact stack proposal: `docs/proposals/PROPOSAL_artifact_stack_buildout.md`
- IssueOps brief: `docs/product/ISSUEOPS_TEACHING_SURFACE_BRIEF.md`
- Game engine roadmap: `docs/product/GAME_ENGINE_ROADMAP.md`
- Fleet audit: `hummbl-io/hummbl-governance/docs/standards/AUDIT_2026-06-22.md`
- Claims manifest: `web/manifest/claims-provenance.json`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This strategic plan was drafted by Devin at the direction of the Principal Agent and was promoted to live (internal) by Principal Agent decision on 2026-06-23 (KRINEIA receipt recorded; bus REVIEW 2026-06-23). This document is **private** — internal resource allocation, not for external publication.
