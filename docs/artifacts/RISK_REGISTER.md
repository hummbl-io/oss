# Risk Register

**Status:** live v1.0 internal (promoted 2026-06-23 per ARTIFACT_STACK_PROMOTION_PACKET.md; private — not for external publication)
**Owner:** Operator
**Risk Officer:** (Board seat — currently operator-occupied)
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 3)
**Reader:** Operator + Board Risk Officer
**Decision:** mitigation prioritization — which risks get active investment this quarter, which get monitored, which get accepted

---

## 1. Purpose

This register tracks risks that could materially affect HUMMBL's ability to execute the 12-month strategic plan. Each risk is scored, owned, and reviewed on a quarterly cadence. The register is not exhaustive — it captures risks that meet the materiality threshold (likelihood × impact ≥ 8 on the 1-25 scale below).

## 2. Scoring

| Dimension      | Scale | Definition                                                                         |
| -------------- | ----- | ---------------------------------------------------------------------------------- |
| **Likelihood** | 1-5   | 1=rare, 2=unlikely, 3=possible, 4=likely, 5=almost certain                         |
| **Impact**     | 1-5   | 1=minor, 2=moderate, 3=significant, 4=major, 5=critical                            |
| **Score**      | 1-25  | Likelihood × Impact                                                                |
| **Priority**   |       | ≥16=critical (active mitigation), 9-15=high (monitored + contingency), ≤8=accepted |

## 3. Risk register

### R-01: Operator burnout (solo founder, 12-month plan)

| Field              | Value                                                                                                                                                                                                                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 4 (likely — 12 months solo is the historical failure mode)                                                                                                                                                                                                                               |
| **Impact**         | 5 (critical — operator is the entire execution surface)                                                                                                                                                                                                                                  |
| **Score**          | 20 — **CRITICAL**                                                                                                                                                                                                                                                                        |
| **Owner**          | Operator                                                                                                                                                                                                                                                                                 |
| **Mitigation**     | Agent fleet absorbs engineering (50% of operator time per strategic plan); operator focuses on pipeline + judgment; weekly bus STATUS surfaces overload early; quarterly Board review checks for drift; if 2 paid pilots signed by Q2 2027, first hire is engineering to absorb further. |
| **Contingency**    | If burnout signals appear (missed weekly reviews, bus silence > 3 days), contract scope to pipeline-only and pause artifact buildout.                                                                                                                                                    |
| **Review cadence** | Monthly                                                                                                                                                                                                                                                                                  |

### R-02: 0 paid pilots by end of Q1 2027

| Field              | Value                                                                                                                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — category is forming, not formed)                                                                                                                                                          |
| **Impact**         | 5 (critical — invalidates the strategic plan's commercial thesis)                                                                                                                                       |
| **Score**          | 15 — **HIGH**                                                                                                                                                                                           |
| **Owner**          | Operator                                                                                                                                                                                                |
| **Mitigation**     | Q4 2026 exit gate requires 3 discovery calls; if 0, pivot to demand generation before Q1; Q1 exit gate requires 1 pilot; if 0, pivot to vertical (healthcare AI governance) or contract to runway mode. |
| **Contingency**    | Vertical pivot (healthcare) or runway contraction to $300/month until pipeline recovers.                                                                                                                |
| **Review cadence** | Quarterly (at exit gates)                                                                                                                                                                               |

### R-03: Category does not form (buyers don't recognize "governance infrastructure" as a category)

| Field              | Value                                                                                                                                                                                                                                                                                                       |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — category-creation is hard)                                                                                                                                                                                                                                                                    |
| **Impact**         | 4 (major — forces vertical focus or repositioning)                                                                                                                                                                                                                                                          |
| **Score**          | 12 — **HIGH**                                                                                                                                                                                                                                                                                               |
| **Owner**          | Operator                                                                                                                                                                                                                                                                                                    |
| **Mitigation**     | White paper establishes the category thesis explicitly; IssueOps teaching surface educates the market; analyst placement (Forrester Q3 2027) reinforces category. If category fails to form by Q2 2027, pivot to vertical where regulatory pressure creates buyer urgency regardless of category awareness. |
| **Contingency**    | Vertical pivot (healthcare AI governance — ONC HTI-1, FDA PCCP, HIPAA create urgency).                                                                                                                                                                                                                      |
| **Review cadence** | Quarterly                                                                                                                                                                                                                                                                                                   |

### R-04: GRC platform adds AI module and out-markets HUMMBL

| Field              | Value                                                                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 2 (unlikely — GRC platforms move slowly, are policy-not-runtime)                                                                                                                      |
| **Impact**         | 4 (major — would crowd out the category if timed well)                                                                                                                                |
| **Score**          | 8 — **ACCEPTED** (with monitoring)                                                                                                                                                    |
| **Owner**          | Operator                                                                                                                                                                              |
| **Mitigation**     | Library-first advantage: we are in the runtime, they are in the dashboard. Receipt chain proves provenance in a way a GRC add-on cannot match. Monitor competitor releases quarterly. |
| **Contingency**    | If a GRC platform ships a credible runtime-enforcement layer, narrow to a vertical where our library is already installed and theirs is not.                                          |
| **Review cadence** | Quarterly                                                                                                                                                                             |

### R-05: Runway exhaustion

| Field              | Value                                                                                                                                                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Likelihood**     | 2 (unlikely — operator-funded, low burn)                                                                                                                                                                                                   |
| **Impact**         | 5 (critical — ends the company)                                                                                                                                                                                                            |
| **Score**          | 10 — **HIGH**                                                                                                                                                                                                                              |
| **Owner**          | Operator                                                                                                                                                                                                                                   |
| **Mitigation**     | Budget scales with revenue triggers, not on a fixed ramp; contingency mode ($300/month) is the default if Q1 2027 closes with 0 pilots; no hires until 2 pilots signed; no SaaS platform build (the largest potential spend) in this plan. |
| **Contingency**    | Contract to $300/month contingency mode; pause artifact buildout; focus on pipeline only.                                                                                                                                                  |
| **Review cadence** | Monthly (budget actuals)                                                                                                                                                                                                                   |

### R-06: Public proof gets copied without attribution

| Field              | Value                                                                                                                                                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 5 (almost certain — open-source + public claims)                                                                                                                                                                                          |
| **Impact**         | 2 (moderate — copying without attribution is detectable and damaging to the copier)                                                                                                                                                       |
| **Score**          | 10 — **HIGH** (monitored, not actively mitigated)                                                                                                                                                                                         |
| **Owner**          | Operator                                                                                                                                                                                                                                  |
| **Mitigation**     | KRINEIA receipt chain proves provenance; claims-provenance.json dates every claim; CONSTITUTION §3.1 makes claim honesty a constitutional invariant. Copying without attribution is detectable and reputationally damaging to the copier. |
| **Contingency**    | If a competitor copies substantively, publish a receipt-backed comparison showing provenance.                                                                                                                                             |
| **Review cadence** | Quarterly                                                                                                                                                                                                                                 |

### R-07: Agent fleet produces a public-facing error (wrong claim, broken demo, bad receipt)

| Field              | Value                                                                                                                                                                                                                                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 4 (likely — agents are doing the work, errors will happen)                                                                                                                                                                                                                                                       |
| **Impact**         | 3 (significant — damages credibility if uncorrected)                                                                                                                                                                                                                                                             |
| **Score**          | 12 — **HIGH**                                                                                                                                                                                                                                                                                                    |
| **Owner**          | Operator + agent fleet                                                                                                                                                                                                                                                                                           |
| **Mitigation**     | Claims remediation protocol (just executed 2026-06-23) catches stale/wrong claims quarterly; deterministic gates (schema validation, receipt verification) catch structural errors; CONSTITUTION §3.1 requires every public claim to have provenance; ADRs record decisions so errors in judgment are traceable. |
| **Contingency**    | If a public error ships, publish a correction with a KRINEIA receipt within 48 hours. The correction itself becomes proof that governance works.                                                                                                                                                                 |
| **Review cadence** | Monthly (with claims audit)                                                                                                                                                                                                                                                                                      |

### R-08: Compliance matrix work absorbs too much time

| Field              | Value                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — compliance work expands to fill available time)                                                                         |
| **Impact**         | 2 (moderate — delays product work, does not stop it)                                                                                  |
| **Score**          | 6 — **ACCEPTED**                                                                                                                      |
| **Owner**          | Operator                                                                                                                              |
| **Mitigation**     | Time-boxed to 15% of weekly hours per strategic plan; defer if over; matrices are drafted, not certified (certification is Q4 2027+). |
| **Contingency**    | If compliance work exceeds 15% for 2 consecutive weeks, pause and reprioritize.                                                       |
| **Review cadence** | Monthly                                                                                                                               |

### R-09: Minecraft / Unreal demo misses the mark (users don't understand receipts after playing)

| Field              | Value                                                                                                                                                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — comprehension is hard to design for)                                                                                                                                                                      |
| **Impact**         | 2 (moderate — demo is one channel, not the only one)                                                                                                                                                                    |
| **Score**          | 6 — **ACCEPTED**                                                                                                                                                                                                        |
| **Owner**          | Operator + Devin                                                                                                                                                                                                        |
| **Mitigation**     | Pilot experiment tests comprehension explicitly (4/5 must explain receipts); failure response is redesign, not abandonment; IssueOps teaching surface is the primary comprehension channel, the game demo is secondary. |
| **Contingency**    | If pilot fails comprehension target, redesign the in-world receipt visualization before Stage 2.                                                                                                                        |
| **Review cadence** | At pilot completion (Q4 2026)                                                                                                                                                                                           |

### R-10: Single-point-of-failure on operator judgment

| Field              | Value                                                                                                                                                                                                                                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — solo founder means one judgment center)                                                                                                                                                                                          |
| **Impact**         | 4 (major — bad judgment compounds without a check)                                                                                                                                                                                             |
| **Score**          | 12 — **HIGH**                                                                                                                                                                                                                                  |
| **Owner**          | Operator + Board                                                                                                                                                                                                                               |
| **Mitigation**     | Board review at quarterly exit gates; resident agents (Apex, Nexus, Auditor) provide pre-decision assessment; ADRs record decisions so judgment is traceable and reviewable; open-questions-steward surfaces decisions pending operator input. |
| **Contingency**    | If a judgment call goes wrong (post-mortem trigger), add a Board review gate for that class of decision.                                                                                                                                       |
| **Review cadence** | Quarterly                                                                                                                                                                                                                                      |

### R-11: Library supply-chain risk (a dependency goes malicious or unmaintained)

| Field              | Value                                                                                                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 1 (rare — zero third-party runtime deps, CI-enforced)                                                                                                                               |
| **Impact**         | 4 (major — would undermine the "infrastructure you can inspect" thesis)                                                                                                             |
| **Score**          | 4 — **ACCEPTED**                                                                                                                                                                    |
| **Owner**          | Operator + Devin                                                                                                                                                                    |
| **Mitigation**     | Zero third-party runtime deps is CI-enforced; `/dep-check` skill scans for conditional imports; SBOM generation available; the library is stdlib-only by constitutional constraint. |
| **Contingency**    | If a dev dependency goes malicious, remove and replace; runtime is unaffected.                                                                                                      |
| **Review cadence** | Quarterly                                                                                                                                                                           |

### R-12: Public claim honesty invariant is violated (a claim ships without provenance)

| Field              | Value                                                                                                                                                                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 2 (unlikely — protocol just verified 2026-06-23)                                                                                                                                                                                   |
| **Impact**         | 4 (major — undermines the core differentiator)                                                                                                                                                                                     |
| **Score**          | 8 — **ACCEPTED** (with monitoring)                                                                                                                                                                                                 |
| **Owner**          | Operator + Devin                                                                                                                                                                                                                   |
| **Mitigation**     | CONSTITUTION §3.1 makes it a constitutional invariant; claims-provenance.json is the source of truth; quarterly claims audit (just executed); every white paper and case study must add claims to the manifest before publication. |
| **Contingency**    | If a claim ships without provenance, add it retroactively within 48 hours and publish a correction receipt.                                                                                                                        |
| **Review cadence** | Quarterly (with claims audit)                                                                                                                                                                                                      |

### R-13: Tailscale / mesh / fleet connectivity loss

| Field              | Value                                                                                                                                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 2 (unlikely — Tailscale is reliable)                                                                                                                                |
| **Impact**         | 3 (significant — fleet coordination pauses, not stops)                                                                                                              |
| **Score**          | 6 — **ACCEPTED**                                                                                                                                                    |
| **Owner**          | Operator                                                                                                                                                            |
| **Mitigation**     | Tailscale is the mesh layer; coordination bus is local-first (file-based); agents can operate offline for short periods; heartbeat skill detects connectivity loss. |
| **Contingency**    | If Tailscale is down, switch to direct SSH or wait; bus messages queue locally.                                                                                     |
| **Review cadence** | Quarterly                                                                                                                                                           |

### R-14: GitHub outage or account compromise

| Field              | Value                                                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 2 (unlikely — GitHub is reliable; account compromise is the real risk)                                                                                               |
| **Impact**         | 4 (major — 92 repos, single org)                                                                                                                                     |
| **Score**          | 8 — **ACCEPTED** (with monitoring)                                                                                                                                   |
| **Owner**          | Operator                                                                                                                                                             |
| **Mitigation**     | 2FA on GitHub account; GPG signing on all commits (key [REDACTED-GPG-KEY]); local mirrors via Gitea self-hosted; receipts are in git history (durable across outages). |
| **Contingency**    | If GitHub is down, work locally and sync when restored. If account compromised, rotate credentials and audit recent commits via Gitea mirror.                        |
| **Review cadence** | Quarterly                                                                                                                                                            |

### R-15: AI API provider deprecation or price spike

| Field              | Value                                                                                                                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likelihood**     | 3 (possible — providers change pricing regularly)                                                                                                                                             |
| **Impact**         | 2 (moderate — agent fleet is multi-provider)                                                                                                                                                  |
| **Score**          | 6 — **ACCEPTED**                                                                                                                                                                              |
| **Owner**          | Operator                                                                                                                                                                                      |
| **Mitigation**     | Multi-provider fleet (Claude, OpenAI, Gemini, local models); model-tier policy routes by data sensitivity; cost governor halts at ceiling; provider neutrality is a constitutional invariant. |
| **Contingency**    | If a provider spikes prices, route more traffic to alternatives; if a provider deprecates a model, the model-tier policy already has fallbacks.                                               |
| **Review cadence** | Quarterly                                                                                                                                                                                     |

## 4. Priority summary

| Priority           | Risks                                                                                                                                                             | Action                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Critical (≥16)** | R-01 (burnout)                                                                                                                                                    | Active mitigation, monthly review               |
| **High (9-15)**    | R-02 (0 pilots), R-03 (no category), R-05 (runway), R-06 (copying), R-07 (agent error), R-10 (judgment SPOF)                                                      | Monitored + contingency ready, quarterly review |
| **Accepted (≤8)**  | R-04 (GRC competition), R-08 (compliance time), R-09 (demo miss), R-11 (supply chain), R-12 (claim honesty), R-13 (mesh loss), R-14 (GitHub), R-15 (API provider) | Accepted with monitoring, quarterly review      |

## 5. Top 3 risks to actively manage this quarter (Q3 2026)

1. **R-01: Operator burnout** — the only critical risk. Agent fleet absorbs engineering; operator focuses on pipeline + judgment; monthly review for drift signals.
2. **R-10: Single-point-of-failure on operator judgment** — Board review at quarterly exit gates; resident agents for pre-decision assessment; ADRs for traceability.
3. **R-07: Agent fleet produces a public-facing error** — claims remediation protocol (just executed), deterministic gates, CONSTITUTION §3.1, quarterly claims audit.

## 6. Review cadence

| Review    | When                  | Output                                                                                      |
| --------- | --------------------- | ------------------------------------------------------------------------------------------- |
| Monthly   | First Monday of month | R-01, R-05, R-07, R-08 reviewed; new risks added if materiality threshold met               |
| Quarterly | End of each quarter   | All risks reviewed; scores updated; mitigations adjusted; contingency triggers checked      |
| Annual    | End of Q3 2027        | Full register refresh; archived risks moved to history; lessons learned feed next-year plan |

## 7. Risk archiving policy

A risk is archived (not deleted) when:

- Likelihood drops to 1 AND impact drops to 1 for 2 consecutive quarterly reviews, OR
- The risk is no longer relevant (e.g., company pivots away from the affected surface)

Archived risks stay in git history with a receipt. No deletion — the register is append-only.

## 8. Open questions for Board

1. **Risk Officer seat:** the Board has a Risk Officer seat that is currently operator-occupied. Should this be formally filled (even if by the operator with a documented hat-change), or left informal until first hire? (Recommendation: formally fill with operator-as-Risk-Officer until first hire, document the hat-change in the charter.)
2. **Materiality threshold:** is 8 the right threshold for inclusion, or should we be more conservative (≥6) or more permissive (≥12)? (Recommendation: keep at 8 for now, revisit after first quarterly review.)
3. **R-01 (burnout) mitigation:** is the agent-fleet-absorbs-engineering mitigation sufficient, or should we add an explicit operator-workload cap? (Recommendation: add a soft cap of 45 hours/week averaged over a month; if exceeded for 2 consecutive months, contract scope.)
4. **Insurance:** should HUMMBL carry any insurance (E&O, cyber, general liability) before first paid pilot? (Recommendation: defer until first pilot — pre-revenue, the cost is not justified; revisit at pilot signing.)

## 9. Next steps

1. **This register:** Board review at the next sync. Decision: approve, modify, or defer.
2. **On approval:** emit ADR-005 recording the risk register decision.
3. **Monthly review:** first Monday of August 2026 reviews R-01, R-05, R-07, R-08.
4. **Quarterly review:** end of Q3 2026 reviews all 15 risks + adds any new materiality-threshold risks.

## References

- Strategic plan: `docs/artifacts/STRATEGIC_PLAN_12mo.md`
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Artifact stack proposal: `docs/proposals/PROPOSAL_artifact_stack_buildout.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)
- Fleet audit: `hummbl-io/hummbl-governance/docs/standards/AUDIT_2026-06-22.md`

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This risk register was drafted by Devin at the direction of the Principal Agent and was promoted to live (internal) by Principal Agent decision on 2026-06-23 (KRINEIA receipt recorded; bus REVIEW 2026-06-23). This document is **private** — internal risk management, not for external publication.
