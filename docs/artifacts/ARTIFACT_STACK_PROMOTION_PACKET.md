# Artifact Stack Promotion Packet

**Status:** approved 2026-06-23 by Principal Agent (Operator). Artifacts 1-5 promoted to live per this packet's recommendations. Phase 1 funding approved. Day 6+ resumed per re-sequenced plan (section 8).
**Owner:** Operator (human Principal Agent)
**Prepared by:** Devin (delegated drafting system)
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (gating artifact)
**Session:** bmo-2026-06-23-artifact-stack-review
**Board review:** UNANIMOUS_ACCEPT with 3 conditions (bus REVIEW 2026-06-23)

**Reader:** Operator (human Principal Agent)
**Decision:** which of the 5 draft artifacts promote to live, which stay draft, which need revision, and whether to resume Day 6+ buildout

---

## 0. Authority-boundary statement (Board condition 3)

This packet, and every artifact it covers, operates under the following authority boundary:

- **Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent.
- **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals.
- **Promotion** from `draft` to `live` requires **human Principal Agent review** and a **KRINEIA receipt** recording the decision.
- **Public claims** in any promoted artifact must be added to `web/manifest/claims-provenance.json` with status and evidence before publication (CONSTITUTION §3.1).
- **The Board** is a deliberation surface that extends the Principal Agent's cognitive light cone; it does not own goals or binding authority. The Board ACCEPT recorded in bus REVIEW 2026-06-23 is not a promotion; it is a review outcome. Binding adoption requires Principal Agent decision via this packet.

This statement must appear in the header of every promoted artifact (condition 3 from governance-officer and stakeholder-proxy Directors).

---

## 1. Purpose

This packet is the gate between the 5 draft artifacts produced over Days 1-5 and any of the following:

- Promotion of any artifact from `draft` to `live`
- Publication of any artifact on `hummbl.io` or any external surface
- Resumption of Day 6+ artifact buildout
- PR of the 5 commits from `fix/claude/gitops-cleanup-from-april-audit` to `main`

Per Board condition 1 (risk-officer q0) and condition 2 (operator q3, risk-officer q2), no Day 6+ artifact expansion proceeds until this packet is reviewed and decided by the Principal Agent.

## 2. The 5 draft artifacts under review

| # | Artifact | Commit | Public/private | Makes public claims? |
|---|----------|--------|----------------|----------------------|
| 1 | White paper: Why Governance Infrastructure for AI-Native Teams | `9fdd8e` | **Public** (intended for hummbl.io) | Yes — about HUMMBL and about competitors |
| 2 | Strategic plan: 12-month | `161f3b3` | **Private** (Operator + Board) | No — internal resource allocation |
| 3 | Risk register | `6ea416f` | **Private** (Operator + Risk Officer) | No — internal risk management |
| 4 | Competitive analysis: AI governance vendors | `8304e2e` | **Public with caveats** (vendor capabilities change) | Yes — about 19 vendors |
| 5 | Business case: IssueOps teaching surface (#410) | `b386a4a` | **Private** (Operator) | No — internal funding decision |

Plus the gating documents:

| Artifact | Commit | Public/private |
|----------|--------|----------------|
| Proposal: gradual artifact stack buildout | `dc4e64f` | **Public** (methodology doc, defensible) |
| Artifact manifest | (in commit `9fdd8e` + subsequent edits) | **Public** (tracking surface) |
| This promotion packet | (this commit) | **Private** until decided, then **Public** (receipt of governance) |

## 3. Promotion criteria

Every artifact must meet these criteria to promote from `draft` to `live`:

### 3.1 Universal criteria (apply to all artifacts)

| Criterion | How verified |
|-----------|--------------|
| Authority-boundary statement in header | Visual check — section 0 text present |
| Reader and decision named in header | Visual check — already present in all 5 |
| Status marked `live` in manifest | Manifest edit |
| KRINEIA receipt for the promotion | `_receipts/krineia/primary.jsonl` entry |
| Board review recorded | bus REVIEW 2026-06-23 (already posted) |
| Principal Agent written approval | Operator signature on this packet |
| No unsupported status labels | governance-officer check |
| No protected-surface change without review | protected-surfaces.md check |

### 3.2 Public artifacts — additional criteria

Public artifacts (white paper, competitive analysis, proposal, manifest) must also meet:

| Criterion | How verified |
|-----------|--------------|
| Every public claim in `claims-provenance.json` with status + evidence | Manifest check |
| No claim about a competitor that cannot be re-verified quarterly | Vendor claim audit |
| No claim about HUMMBL that cannot be verified by inspecting an artifact | Self-claim audit |
| Authority-boundary statement visible to a reader who skims | Header placement |
| Published on `hummbl.io` or referenced from a public page | Deploy check |

### 3.3 Private artifacts — additional criteria

Private artifacts (strategic plan, risk register, IssueOps business case) must also meet:

| Criterion | How verified |
|-----------|--------------|
| Not deployed to `hummbl.io` or any public surface | Deploy check |
| Access limited to Operator + Board (or named officers) | Repo visibility / file path |
| No claim that could embarrass if leaked | Stakeholder-proxy q2 test |

## 4. Per-artifact recommendation

### 4.1 White paper (commit `9fdd8e`) — RECOMMEND: promote to live with revisions

**Strengths:**
- Establishes the category thesis clearly
- Names the 8 primitives, the proof gap, the 3 buyer questions
- Self-reference customer section is verifiable
- Call to action is concrete

**Revisions required before promotion:**

1. **Add authority-boundary statement** (section 0 of this packet) to the white paper header.
2. **Add claims to `claims-provenance.json`** — the white paper makes ~12 public claims about HUMMBL (92 repos, 67 active stacks, 1,234 tests, 59 verified claims, fleet-wide KRINEIA chain, hummbl-governance on PyPI v1.2.0, zero third-party runtime deps). Each needs a status and evidence entry. **Estimate: 12 new claims.**
3. **Soften competitor references** — the white paper mentions "GRC platforms" generically and does not name specific competitors. This is correct for the white paper (the competitive analysis names them). No change needed, but confirm no specific vendor is named.
4. **Verify the 1,234 tests claim** — the white paper says 1,234; the strategic plan and other artifacts say 1,234. The actual count should be verified against the current `hummbl-governance` test suite before publication. **Action: run `pytest --collect-only` and confirm.**
5. **Verify the 59 claims, 0 pending claim** — this was true on 2026-06-23 per the claims remediation. Confirm still true at promotion time.

**Redlines (would block promotion):**
- Any HUMMBL claim that cannot be verified by inspecting an artifact
- Any claim about a competitor (none currently — confirm)
- Missing authority-boundary statement

**Public/private:** Public — this is the primary external-facing category thesis.

### 4.2 Strategic plan (commit `161f3b3`) — RECOMMEND: keep private, promote to live internally

**Strengths:**
- Clear quarterly arc with exit gates
- 3 strategic bets with explicit "if wrong" pivots
- 3 anti-goals (no SaaS, no enterprise sales, no hires)
- Resource discipline (solo founder + agent fleet, no hires until 2 pilots)
- Success metrics with Q3 2027 targets

**Revisions required before promotion:**

1. **Add authority-boundary statement** to header.
2. **Confirm runway numbers** — the plan references operator-funded runway but the actual runway is "needs operator input — not in this plan" (open question 1). The plan should either include the runway number or explicitly defer it. **Action: operator inputs runway number or confirms deferral.**
3. **Confirm the budget ramp** ($300 → $1,430/month) is consistent with actual runway. **Action: operator confirms.**
4. **Resolve open question 2** (vertical pivot if Q1 2027 closes with 0 pilots) — the plan recommends healthcare; confirm or adjust.
5. **Resolve open question 5** (first hire profile if 2 pilots signed) — the plan recommends engineering; confirm or adjust.

**Redlines:**
- Promotion without operator confirming runway would publish an internal plan with a gap
- Missing authority-boundary statement

**Public/private:** **Private** — internal resource allocation, pivot contingencies, and runway details are not for external audiences. A public summary (the white paper covers this) is sufficient for external readers.

### 4.3 Risk register (commit `6ea416f`) — RECOMMEND: keep private, promote to live internally

**Strengths:**
- 15 risks scored on a clear rubric
- 1 critical (burnout), 6 high, 8 accepted — honest prioritization
- Each risk has mitigation, contingency, review cadence
- Append-only archival policy (consistent with KRINEIA discipline)

**Revisions required before promotion:**

1. **Add authority-boundary statement** to header.
2. **Resolve open question 1** (Risk Officer seat — formally fill with operator-as-Risk-Officer until first hire?) — confirm.
3. **Resolve open question 3** (burnout mitigation — add soft cap of 45 hours/week averaged over a month?) — confirm. The Board's operator-q2 answer ("next 16 hours must produce a conversion-oriented artifact") suggests the operator is already monitoring this; a soft cap makes it explicit.
4. **Resolve open question 4** (insurance before first paid pilot?) — confirm.

**Redlines:**
- Missing authority-boundary statement
- Publishing risk register externally would expose mitigation gaps to competitors

**Public/private:** **Private** — risk registers name mitigation gaps and contingency plans that are strategically sensitive. A public summary (top 3 risks, anonymized) is possible later but not required.

### 4.4 Competitive analysis (commit `8304e2e`) — RECOMMEND: promote to live with revisions, public with quarterly refresh commitment

**Strengths:**
- 19 vendors profiled via web research
- 2x2 positioning matrix shows HUMMBL's unique quadrant
- 3 buyer questions are sharp and defensible
- "Complementary not competitive" positioning is honest
- Go-to-market implications are actionable

**Revisions required before promotion:**

1. **Add authority-boundary statement** to header.
2. **Add vendor-capability disclaimer** — vendor capabilities change; this analysis is current as of June 2026 and should be refreshed quarterly. Add to header: "Vendor capabilities described are based on public materials as of June 2026. This analysis is refreshed quarterly. Verify vendor claims directly before procurement."
3. **Add claims to `claims-provenance.json`** — the analysis makes claims about 19 vendors (funding amounts, product capabilities, certifications). These are public-source claims but should be tracked. **Estimate: ~30 vendor claims (funding, certifications, MQ positions).** Each needs a source URL.
4. **Verify the 2 vendors marked "deterministic"** (Modulos, Airia) — this is the load-bearing claim for HUMMBL's positioning. Re-verify via web research before publication. **Action: re-verify Modulos and Airia deterministic-enforcement claims.**
5. **Soften any claim that could be disputed** — e.g., "Arthur AI uses LLM-as-judge" should be "Arthur AI's documentation describes LLM-influenced evals" (precise, defensible).
6. **Add a "how to verify this analysis" section** — tell the reader how to re-verify the 2x2 matrix themselves. This is the proof-gap principle applied to our own competitive analysis.

**Redlines:**
- Any vendor claim that cannot be re-verified quarterly
- Any claim that Modulos or Airia is NOT deterministic (would weaken HUMMBL's positioning — but if true, must be corrected)
- Missing authority-boundary statement
- Missing quarterly-refresh commitment

**Public/private:** **Public with quarterly refresh commitment** — this is external-facing evidence that HUMMBL understands the market. The quarterly refresh is the integrity mechanism.

### 4.5 IssueOps business case (commit `b386a4a`) — RECOMMEND: keep private, promote to live internally, then fund Phase 1

**Strengths:**
- 4 options analyzed (build, defer, do nothing, buy)
- $0 capital, 40 hours, 4.1x ROI on first pilot
- Strategic alignment explicit (Bet 2, Q4 exit gate, white paper CTA)
- Success metrics with Q4 2026 and Q1 2027 targets
- Phasing discipline (Phase 1 only; Phases 2-4 separate gates)

**Revisions required before promotion:**

1. **Add authority-boundary statement** to header.
2. **Resolve open question 1** (timing: Q3 2026 ahead of target, or Q4 on schedule?) — the Board's operator-q2 answer ("next 16 hours must produce a conversion-oriented artifact") suggests Q3 timing is correct. Confirm.
3. **Resolve open question 2-5** (glossary depth, widget fetch source, claims count, analytics) — these are implementation decisions, not promotion-gating. Confirm or defer to implementation.
4. **Decision requested:** fund Phase 1 (yes/no/defer). This is the Principal Agent's call.

**Redlines:**
- Funding Phase 1 without operator confirming the 40-hour time investment fits within Q3 2026 capacity
- Missing authority-boundary statement

**Public/private:** **Private** — internal funding decision. The IssueOps teaching surface itself (when built) is public; the business case for it is not.

## 5. Claims to add to claims-provenance.json

Before any public artifact is published, the following claims must be added to `web/manifest/claims-provenance.json` with status and evidence:

### 5.1 White paper claims (~12)

| Claim | Evidence |
|-------|----------|
| 92-repo fleet with 67 active governance stacks | `hummbl-governance/docs/standards/AUDIT_2026-06-22.md` + `tools/fleet_verify.py` output 2026-06-23 |
| 1,234 governance tests | `hummbl-governance` test suite (CI-verified) — **re-verify count at promotion time** |
| 59 verified public claims, 0 pending | `web/manifest/claims-provenance.json` (2026-06-23) — **re-verify at promotion time** |
| Fleet-wide KRINEIA receipt chain | `_receipts/krineia/primary.jsonl` in every active repo |
| hummbl-governance on PyPI | `pypi.org/project/hummbl-governance/` (v1.2.0) |
| Zero third-party runtime dependencies | `pyproject.toml` in hummbl-governance (CI-enforced) |
| 8 governance primitives | `hummbl-governance` library + `PRIMITIVES.md` |
| KRINEIA invariants (observed_agent_may_write_receipts: false, etc.) | `krineia/RECEIPT_SCHEMA.md` |
| HUMMBL Repo Standard v0.1 adopted fleet-wide | `hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md` + fleet_verify.py |
| Sub-millisecond enforcement | **needs benchmark — defer or remove claim if not benchmarked** |
| Apache 2.0 license | `hummbl-governance/LICENSE` |
| Self-reference customer (HUMMBL runs on HUMMBL) | This is a composite claim — evidence is the fleet audit + claims manifest |

### 5.2 Competitive analysis claims (~30)

Each vendor claim (funding amount, certification, MQ position, capability characterization) needs a source URL. The research subagent provided sources; they need to be formalized in the claims manifest.

### 5.3 Total new claims: ~42

This is a meaningful addition to the claims manifest (currently 59 claims). After addition, the manifest will have ~101 claims. The quarterly claims audit (per CONSTITUTION §3.1) will need to cover all of them.

## 6. Redlines (would block the entire promotion)

1. **Any HUMMBL claim that cannot be verified by inspecting an artifact.** The "sub-millisecond enforcement" claim in the white paper needs a benchmark or removal.
2. **Any vendor claim in the competitive analysis that cannot be re-verified.** The Modulos and Airia "deterministic" claims are load-bearing — re-verify before publication.
3. **Missing authority-boundary statement in any promoted artifact.** This is Board condition 3.
4. **Promotion without operator confirming runway.** The strategic plan's open question 1 must be resolved before the plan is promoted.
5. **No KRINEIA receipt for the promotion.** Every promotion is a governance event; it gets a receipt.

## 7. PR plan

The 5 commits are currently on `fix/claude/gitops-cleanup-from-april-audit`. This branch name is misleading (it predates the artifact stack work). Recommended PR approach:

### 7.1 Branch strategy

| Option | Description | Recommendation |
|--------|-------------|----------------|
| A: PR the current branch | `fix/claude/gitops-cleanup-from-april-audit` → `main` | **No** — branch name is misleading and may include unrelated commits |
| B: Cherry-pick to a new branch | Create `feat/devin/artifact-stack-wave-1`, cherry-pick the 5 commits, PR to main | **Yes** — clean branch, clean PR |
| C: Squash to a single commit | Create `feat/devin/artifact-stack-wave-1`, squash 5 commits into 1, PR to main | **Acceptable** — but loses the per-day commit history |

**Recommendation: Option B.** Cherry-pick preserves the per-day commit history (which is the receipt chain for the buildout) and gives a clean branch name.

### 7.2 PR scope

The PR should include:
- `docs/proposals/PROPOSAL_artifact_stack_buildout.md` (commit `dc4e64f`)
- `docs/artifacts/ARTIFACT_MANIFEST.md` (with all 5 items marked per this packet's decisions)
- `docs/artifacts/WHITE_PAPER_governance_infrastructure.md` (with revisions)
- `docs/artifacts/STRATEGIC_PLAN_12mo.md` (with revisions)
- `docs/artifacts/RISK_REGISTER.md` (with revisions)
- `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md` (with revisions)
- `docs/artifacts/BUSINESS_CASE_issueops.md` (with revisions)
- `docs/artifacts/ARTIFACT_STACK_PROMOTION_PACKET.md` (this file)
- `web/manifest/claims-provenance.json` (with ~42 new claims)
- KRINEIA receipt for the promotion

### 7.3 PR review

- Code review: minimal (markdown + JSON)
- Claims review: every new claim in `claims-provenance.json` verified against evidence
- Board review: already recorded (bus REVIEW 2026-06-23)
- Principal Agent approval: signature on this packet

## 8. Day 6+ resumption gate

Per Board condition 1 (risk-officer) and condition 2 (operator + risk-officer), Day 6+ artifact expansion is paused until:

1. **This packet is reviewed and decided by the Principal Agent.** (Signature below.)
2. **The 5 artifacts are revised per section 4 recommendations.** (Or explicitly accepted as-is.)
3. **The PR is opened to main.** (Or explicitly deferred.)
4. **The authority-boundary statement is added to every promoted artifact.** (Board condition 3.)
5. **Claims are added to `claims-provenance.json` for public artifacts.** (CONSTITUTION §3.1.)

Once these are done, the Principal Agent may authorize resumption of Day 6+ buildout. The original Day 6 was the **Business case: Game engine roadmap (#408)**. The operator's operator-q2 answer ("next 16 hours must produce a conversion-oriented artifact") suggests Day 6+ should prioritize conversion-oriented artifacts (case study, position papers that can drive inbound) over more internal planning artifacts.

**Recommendation for Day 6+ sequencing (post-promotion):**
- Day 6: Case study: Claims remediation 2026-06-23 (item 7 — conversion-oriented, public, proves HUMMBL does what it says)
- Day 7: Position paper: EU AI Act readiness (item 9 — conversion-oriented, regulatory tailwind, Aug 2 2026 deadline)
- Day 8: Position paper: NIST AI RMF alignment (item 10 — conversion-oriented, compliance buyer)
- Day 9: Market analysis: AI governance market size (item 8 — supports analyst placement)
- Day 10: Business case: Game engine roadmap (#408) (item 6 — internal, but supports the public demo roadmap)

This re-sequencing puts public, conversion-oriented artifacts first, consistent with the operator's operator-q2 answer.

## 9. Decision requested from Principal Agent

Operator — please decide each of the following:

### 9.1 Per-artifact promotion decisions

| # | Artifact | Promote to live? | Public? | Revisions required (section 4) |
|---|----------|------------------|---------|-------------------------------|
| 1 | White paper | ☐ Yes ☐ Yes with revisions ☐ No | ☐ Public ☐ Private | Authority-boundary, ~12 claims, verify 1,234 tests, verify 59 claims |
| 2 | Strategic plan | ☐ Yes ☐ Yes with revisions ☐ No | ☐ Public ☐ Private | Authority-boundary, confirm runway, resolve OQ 2 + 5 |
| 3 | Risk register | ☐ Yes ☐ Yes with revisions ☐ No | ☐ Public ☐ Private | Authority-boundary, resolve OQ 1 + 3 + 4 |
| 4 | Competitive analysis | ☐ Yes ☐ Yes with revisions ☐ No | ☐ Public ☐ Private | Authority-boundary, vendor disclaimer, ~30 claims, re-verify Modulos + Airia, "how to verify" section |
| 5 | IssueOps business case | ☐ Yes ☐ Yes with revisions ☐ No | ☐ Public ☐ Private | Authority-boundary, resolve OQ 1 (timing), fund Phase 1? |

### 9.2 Cross-cutting decisions

1. **Authority-boundary statement** (section 0 of this packet): approve as written, or revise?
2. **PR strategy** (section 7): Option B (cherry-pick to `feat/devin/artifact-stack-wave-1`)?
3. **Claims manifest expansion** (~42 new claims): approve, or defer some?
4. **Day 6+ resumption** (section 8): authorize the re-sequenced Day 6-10, or different sequence?
5. **IssueOps Phase 1 funding** (section 4.5): fund, defer, or skip?
6. **Runway input** (strategic plan open question 1): what is the actual runway at $300/month contingency vs $1,430/month full spend?

### 9.3 Signature

```
PRINCIPAL AGENT DECISION
═══════════════════════════════════════════════════════════════
Principal Agent: Operator
Date: ___________
Decision: ☐ Approve packet as written
          ☐ Approve with modifications (specify below)
          ☐ Defer (specify what is needed)
          ☐ Reject (specify rationale)

Modifications / deferral / rejection rationale:
_______________________________________________
_______________________________________________
_______________________________________________

Promotion decisions (from 9.1):
  Artifact 1 (white paper): ___________
  Artifact 2 (strategic plan): ___________
  Artifact 3 (risk register): ___________
  Artifact 4 (competitive analysis): ___________
  Artifact 5 (IssueOps business case): ___________

Cross-cutting decisions (from 9.2):
  Authority-boundary statement: ___________
  PR strategy: ___________
  Claims manifest expansion: ___________
  Day 6+ resumption: ___________
  IssueOps Phase 1 funding: ___________
  Runway input: ___________

KRINEIA receipt ID for this decision: ___________
═══════════════════════════════════════════════════════════════
```

## 10. What happens after the Principal Agent decides

| Decision | Next action |
|----------|-------------|
| Approve | Apply revisions per section 4, add claims to manifest, add authority-boundary to each artifact, open PR, emit KRINEIA receipt, mark artifacts `live` in manifest, resume Day 6+ per section 8 sequence |
| Approve with modifications | Apply the modifications plus section 4 revisions, then same as Approve |
| Defer | Pause all promotion; address the deferral items; re-present packet |
| Reject | Mark the 5 artifacts `rejected` in manifest with rationale; preserve commits as receipts of an abandoned option; return to last operator-approved baseline |

In all cases, the decision is recorded as a KRINEIA receipt and posted to the bus as a DECISION message from the Principal Agent (not from Devin — agents do not post binding DECISIONs).

## 11. Open questions for Principal Agent

These are the questions the packet cannot answer without operator input:

1. **Runway** (strategic plan OQ 1): what is the actual runway at $300/month vs $1,430/month?
2. **Vertical pivot** (strategic plan OQ 2): if Q1 2027 closes with 0 pilots, pivot to healthcare AI governance?
3. **First hire profile** (strategic plan OQ 5): if 2 pilots signed by Q2 2027, is first hire engineering or sales?
4. **Risk Officer seat** (risk register OQ 1): formally fill with operator-as-Risk-Officer until first hire?
5. **Burnout soft cap** (risk register OQ 3): add 45 hours/week averaged over a month?
6. **Insurance** (risk register OQ 4): carry E&O/cyber before first paid pilot?
7. **IssueOps timing** (business case OQ 1): Q3 2026 ahead of target, or Q4 on schedule?
8. **IssueOps Phase 1 funding**: fund, defer, or skip?
9. **Open-source license** (competitive analysis OQ 1): Apache 2.0 or AGPL?
10. **Analyst strategy** (competitive analysis OQ 3): Forrester Wave submission Q3 2027?

These do not all need to be answered to promote the artifacts. The packet can be approved with some OQs deferred. But the cross-cutting decisions in section 9.2 should be answered.

## References

- Board meeting minutes: bus REVIEW 2026-06-23 (session bmo-2026-06-23-artifact-stack-review)
- Board registry: `governance/board/registry.yaml`
- Director constitutions: `governance/board/constitutions/*.yaml`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)
- HUMMBL Repo Standard v0.1: `hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md`
- Artifact manifest: `docs/artifacts/ARTIFACT_MANIFEST.md`
- 5 draft artifacts: commits `9fdd8e`, `161f3b3`, `6ea416f`, `8304e2e`, `b386a4a`
- Proposal: `docs/proposals/PROPOSAL_artifact_stack_buildout.md` (commit `dc4e64f`)
- Protected surfaces: `.agents/rules/protected-surfaces.md`
- Claims manifest: `web/manifest/claims-provenance.json`
