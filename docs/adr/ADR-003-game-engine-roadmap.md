# ADR-003 — Game Engine Roadmap Decision (#408)

- **Status:** accepted
- **Date:** 2026-06-23
- **Decision owner:** Operator
- **Steward:** HUMMBL, LLC
- **Supersedes:** none
- **Superseded by:** none
- **Tracking issue:** hummbl-production#408
- **Business case:** `docs/artifacts/BUSINESS_CASE_game_engine.md` (item 6)
- **Status ledger:** `docs/reports/game-engine-roadmap-status-ledger.md`

## Context

HUMMBL's governance primitives (KillSwitch, CircuitBreaker, DelegationToken, GovernanceBus, Receipts, AgentRegistry, CostGovernor, CapabilityFence) are currently pure Python. They work — 1,234 tests, deterministic evidence, framework-agnostic. But they are invisible to non-engineers. A compliance buyer who reads the white paper understands the primitives intellectually; a compliance buyer who _plays_ a kill switch in Minecraft understands them viscerally.

The business case (item 6) proposed a 4-stage roadmap to embody HUMMBL's governance primitives as playable in-world mechanics — first in Minecraft (Q4 2026), then in 2+ other engines (Q1-Q2 2027), then in Unreal (Q3-Q4 2027). This creates a new category: **playable governance**. No AI governance vendor has a playable embodiment of their primitives. Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance — all have dashboards. None have a world you can walk into and watch governance happen.

The business case asked for **Stage 0 funding only** ($15-25K, 4-6 weeks engineering). Stage 0 is the doctrine + JSON Schema + Simulation Affordance layer for all 8 primitives — the engine-agnostic contract that makes Stages 1-3 possible. Stages 1-3 are separate funding decisions, each gated on the prior stage's exit criteria.

This ADR records the decision to accept the business case's recommendation: fund Stage 0.

2026-07-03 status reconciliation: the repository now contains
Stage 1-shaped headless validation and runtime/prototype evidence in
`minecraft-governance/` and `hummbl-governed-quest-sim/`. That evidence does
not supersede this ADR's authority boundary. Stage 1+ public positioning,
engine binding, pilot operation, and funding/canon promotion remain separately
gated unless a later ADR or operator decision says otherwise.

## Decision

**Fund Stage 0 of the game engine roadmap: doctrine + JSON Schema + Simulation Affordance for all 8 primitives.**

### Scope

Stage 0 delivers:

| Component                     | Description                                                                                                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Doctrine                      | For each of 8 primitives: what it means, its invariants, its receipt contract (engine-agnostic, lives in `hummbl-governance` + `hummbl-doctrine`) |
| JSON Schema                   | The machine-readable shape of each primitive's state (engine-agnostic, JSON Schema in `hummbl-governance/schemas/`)                               |
| Simulation Affordance section | For each primitive: how it manifests in a playable world (what the player sees, does, verifies)                                                   |

### Out of scope (deferred to later ADRs)

- Stage 1: Minecraft prototype (Q4 2026, ~$30-50K, 6-8 weeks)
- Stage 2: Multi-game adapters — Roblox, Unity, Godot (Q1-Q2 2027, ~$60-100K, 12-16 weeks)
- Stage 3: Unreal embodiment + public demo (Q3-Q4 2027, ~$150-300K, 16-24 weeks)

### Cost

- **Capital:** $15-25K (from HUMMBL's existing Q3 2026 operating budget; no new capital required)
- **Engineering hours:** 4-6 weeks
- **Ongoing maintenance:** minimal (doctrine + schema are stable; updates are versioned)

### Funding

Stage 0 funding approved 2026-06-23 per the business case (item 6). The cost is within the Q3 2026 engineering allocation; the PA approved Phase 1 funding on 2026-06-23, and Stage 0 is within that envelope.

### Success metrics (Stage 0 exit criteria)

Per the business case §3:

| Metric                                         | Target    | Measurement                                                            |
| ---------------------------------------------- | --------- | ---------------------------------------------------------------------- |
| 8 primitives have doctrine                     | 8/8       | Each primitive has a doctrine doc with invariants and receipt contract |
| 8 primitives have JSON Schema                  | 8/8       | Each primitive has a JSON Schema in `hummbl-governance/schemas/`       |
| 8 primitives have Simulation Affordance        | 8/8       | Each primitive has a Simulation Affordance section                     |
| Schemas validate against test fixtures         | 100%      | `pytest hummbl_governance/tests/test_schemas.py` passes                |
| Doctrine reviewed by PA                        | 1 review  | PA reviews and approves the 8 doctrine docs                            |
| KRINEIA receipt emitted for Stage 0 completion | 1 receipt | `governance.game_engine.stage_0_complete` in the chain                 |

## Alternatives considered

### Option A: Fund Stage 0 (ACCEPTED)

Doctrine + JSON Schema + Simulation Affordance for all 8 primitives. $15-25K from existing budget, 4-6 weeks engineering.

**Why accepted:** Stage 0 is the engine-agnostic contract that makes Stages 1-3 possible. Without it, the Minecraft prototype (Stage 1) would have to define doctrine on the fly, leading to engine-coupled doctrine that cannot be re-used for Unreal (Stage 3). Stage 0 is the cheapest stage ($15-25K vs $255-475K total) and the highest-leverage (it gates all later stages). Funding Stage 0 does not commit HUMMBL to Stages 1-3; each later stage is a separate decision gated on the prior stage's exit criteria.

### Option B: Skip Stage 0, build Stage 1 (Minecraft) directly (REJECTED)

Skip the doctrine + schema layer, build the Minecraft prototype directly. ~$30-50K, 6-8 weeks.

**Why rejected:** Building Minecraft directly without doctrine leads to engine-coupled doctrine. The Minecraft kill switch would be defined in Minecraft terms (redstone, command blocks), not in engine-agnostic terms. When Stage 3 (Unreal) comes, the doctrine would need to be re-defined, re-tested, and re-receipted. This violates the engine-agnostic doctrine principle (business case §2) and doubles the long-term cost. Stage 0 first; Stage 1 second.

### Option C: Defer the entire roadmap (REJECTED)

Do not fund Stage 0. Keep HUMMBL's primitives as pure Python. Focus on the dashboard and the IssueOps teaching surface (ADR-002).

**Why rejected:** The dashboard and IssueOps are necessary but not sufficient. They teach the vocabulary; they do not embody the primitives. A compliance buyer who reads the IssueOps glossary understands "kill switch" intellectually; a compliance buyer who plays a kill switch in Minecraft understands it viscerally. The playable governance category is empty (zero vendors); deferring it cedes the category to a future competitor. The cost of Stage 0 ($15-25K) is low; the cost of ceding the category is high.

### Option D: Buy a game engine integration (NOT VIABLE)

There is no vendor that sells a "game engine integration for AI governance primitives." This is not a buy-vs-build decision; it is a build-vs-skip decision.

## Consequences

### Positive

- **Creates a new category: playable governance.** No competitor has this. The category is empty; HUMMBL would own it.
- **Makes governance legible to non-engineers.** A compliance buyer who plays a kill switch understands it viscerally, not just intellectually.
- **Engine-agnostic doctrine.** Stage 0's doctrine + schema layer is re-usable across Minecraft, Roblox, Unity, Godot, Unreal. Define once, embody many times.
- **Gates Stages 1-3 cleanly.** Each later stage is a separate funding decision. Stage 0 does not commit HUMMBL to the full $255-475K roadmap.
- **Low cost, high leverage.** $15-25K for the contract that gates $240-450K of later work.

### Negative

- **$15-25K and 4-6 weeks** spent on Stage 0 are not spent on other work. The opportunity cost is low because Stage 0 is the contract that makes the playable governance category possible.
- **Stage 0 does not produce a public artifact.** The doctrine + schema are internal (open-source, but not a marketing surface). The public artifact comes in Stage 1 (Minecraft prototype). This is acceptable — Stage 0 is the foundation, not the demo.

### Risks

- **Stage 0 doctrine is wrong.** Mitigated: PA reviews and approves the 8 doctrine docs; schemas validate against test fixtures; KRINEIA receipt for completion.
- **Stage 1 funding is not approved.** Mitigated: Stage 0 is still useful even if Stage 1 is deferred — the doctrine + schema are re-usable for any future engine embodiment.
- **The playable governance category does not materialize.** Mitigated: the cost of Stage 0 is low ($15-25K); the cost of ceding the category is high. Even if the category is small, HUMMBL owns it.

## Receipts

- **Business case promotion receipt:** in `_receipts/krineia/primary.jsonl` (governance.artifact_promoted for item 6)
- **This ADR's promotion receipt:** emitted on commit (governance.artifact_promoted for item 17)
- **Stage 0 completion receipt (future):** `governance.game_engine.stage_0_complete` — to be emitted when Stage 0 exit criteria are met

## Implementation plan

1. **Week 1-2 (2026-07-01 to 2026-07-14):** Draft doctrine for 4 primitives (KillSwitch, CircuitBreaker, DelegationToken, GovernanceBus). Review with PA.
2. **Week 3-4 (2026-07-15 to 2026-07-28):** Draft doctrine for 4 more primitives (Receipts, AgentRegistry, CostGovernor, CapabilityFence). Draft JSON Schemas for all 8. Review with PA.
3. **Week 5-6 (2026-07-29 to 2026-08-11):** Draft Simulation Affordance sections for all 8. Validate schemas against test fixtures. PA review and approval. Emit `governance.game_engine.stage_0_complete` KRINEIA receipt.
4. **Ongoing:** Versioned updates to doctrine + schema. Each update emits a receipt. Stage 1 funding decision is a separate ADR, gated on Stage 0 exit criteria.

## Boundary disclaimer

This ADR records a decision to fund Stage 0 of a 4-stage roadmap. It is not a commitment to fund Stages 1-3. Each later stage is a separate funding decision, gated on the prior stage's exit criteria. The PA may decline to fund Stage 1 even if Stage 0 succeeds.

This ADR does not make HUMMBL a game studio. The game engine roadmap is a product demo category, not a game production. The playable world is a demo of the primitives, not a commercial game.

## How to verify this ADR

A reader can re-verify this ADR's claims by:

1. **The business case exists** — `ls docs/artifacts/BUSINESS_CASE_game_engine.md`
2. **The business case asks for Stage 0 funding** — `grep "Stage 0 funding" docs/artifacts/BUSINESS_CASE_game_engine.md`
3. **The roadmap exists** — `ls docs/product/GAME_ENGINE_ROADMAP.md` (commit 7fdf172)
4. **The tracking issue exists** — `gh issue view 408 --repo hummbl-io/hummbl-production`
5. **The white paper exists** — `ls docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
6. **This ADR is in the manifest** — `grep "ADR-003" docs/artifacts/ARTIFACT_MANIFEST.md`
7. **The hummbl-governance library exists** — `pip install hummbl-governance && python -c "import hummbl_governance; print(hummbl_governance.__version__)"`

If any verification fails, open an issue at `hummbl-io/hummbl-production/issues`.

## References

- Business case: `docs/artifacts/BUSINESS_CASE_game_engine.md` (item 6)
- Roadmap: `docs/product/GAME_ENGINE_ROADMAP.md` (commit 7fdf172)
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md` (item 1)
- Strategic plan: `docs/artifacts/STRATEGIC_PLAN_12mo.md` (item 2)
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md` (item 4)
- Doctrine: `docs/artifacts/DOCTRINE_ai_governance.md` (item 11)
- Charter: `docs/artifacts/CHARTER_hri.md` (item 12)
- ADR-001: `docs/adr/ADR-001-repo-governance-baseline.md`
- ADR-002: `docs/adr/ADR-002-issueops-teaching-surface.md`
- Tracking issue: hummbl-production#408
- hummbl-governance: https://github.com/hummbl-io/hummbl-governance (Apache 2.0)
- KRINEIA receipt chain: `_receipts/krineia/primary.jsonl`

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents) are delegated drafting, research, and execution systems. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This ADR was drafted by Devin at the direction of the Principal Agent, based on the business case (item 6), the game engine roadmap (commit 7fdf172), the white paper (item 1), and the strategic plan (item 2), and was promoted to live (public) by Principal Agent decision on 2026-06-23. The decision recorded in this ADR is the Principal Agent's; the implementation plan is a proposal for the Principal Agent to approve or revise. This document is **public** — ADRs are public by default per the HUMMBL Repo Standard.
