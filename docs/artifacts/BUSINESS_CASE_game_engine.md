# Business Case: Game Engine Roadmap — Minecraft to Unreal (#408)

**Status:** live v1.0 (private)
**Author:** Operator, HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md (item 6); GitHub issue hummbl-io/hummbl-production#408
**Reader:** Operator (Principal Agent) — funding decision for Stage 0
**Decision:** whether to fund Stage 0 (Doctrine & schemas, Q3 2026) of the simulation-ready game engine roadmap

**TL;DR:** HUMMBL's governance primitives are currently abstract Python code. The product vision is to embody them as playable in-world mechanics — first in Minecraft (Q4 2026), then in 2+ other engines (Q1-Q2 2027), then in Unreal (Q3-Q4 2027). This makes governance legible to non-engineers: a compliance buyer can _play_ a kill switch, _read_ a receipt chain, _watch_ a delegation token get checked. Stage 0 (the funding ask) is the doctrine + schema formalization that makes all later stages possible. The cost is ~$15-25K and 4-6 weeks of engineering time. The return is a product demo that no competitor can match and a path to a category HUMMBL would own: playable governance.

---

## 1. The opportunity

### The product vision

HUMMBL's governance primitives (KillSwitch, CircuitBreaker, DelegationToken, GovernanceBus, Receipts, AgentRegistry, CostGovernor, CapabilityFence) are currently pure Python. They work. They have 1,234 tests. They produce deterministic evidence. But they are invisible to non-engineers.

A compliance buyer who reads the white paper understands the primitives intellectually. A compliance buyer who _plays_ a kill switch in Minecraft understands them viscerally. The product vision is to make governance **legible to non-engineers by making it playable**.

This is not a game. It is a product demo category. No AI governance vendor has a playable embodiment of their primitives. Credo AI, Holistic AI, Arthur AI, Fiddler AI, IBM watsonx.governance — all have dashboards. None have a world you can walk into and watch governance happen.

### The category

If HUMMBL executes this roadmap, it creates a new category: **playable governance**. The category is small today (zero vendors) but has three properties that make it valuable:

1. **Differentiation** — no competitor can match it without doing the same work. A dashboard is faster to build; a playable world is harder.
2. **Memorability** — a compliance buyer who plays a kill switch remembers it. A compliance buyer who sees a dashboard forgets it.
3. **Demo-ability** — a playable world is a conference talk, a sales call, a YouTube video. A dashboard is a screenshot.

### The strategic fit

The game engine roadmap is not a distraction from HUMMBL's governance mission. It is the embodiment of it. The primitives are the doctrine; the playable world is the embodiment. The same primitives that produce deterministic evidence for EU AI Act conformity assessment produce a playable kill switch in Minecraft. The library and the world are the same thing, expressed in two media.

This is the same pattern as the claims remediation case study: HUMMBL uses its own primitives to govern its own claims. Here, HUMMBL uses its own primitives to embody its own product vision. The primitives are the product; the world is the demo.

---

## 2. The roadmap (4 stages)

The full roadmap is in `docs/product/GAME_ENGINE_ROADMAP.md` (commit 7fdf172, drafted per issue #408). Summary:

| Stage       | Quarter                     | Goal                                                                        | Cost estimate                                        | Exit criteria                                                          |
| ----------- | --------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| **Stage 0** | Q3 2026 (current → 6 weeks) | Doctrine + JSON Schema + Simulation Affordance section for all 8 primitives | $15-25K + 4-6 weeks engineering                      | 8 primitives have doctrine + schema + simulation affordance            |
| **Stage 1** | Q4 2026 (6-8 weeks)         | Minecraft prototype: 8 playable primitives, Python bridge, 5 playtesters    | $30-50K + 6-8 weeks engineering                      | 5 external playtesters, 4/5 can explain receipts, 3/5 can verify chain |
| **Stage 2** | Q1-Q2 2027 (12-16 weeks)    | Multi-game adapters: Roblox, Unity, Godot via GameEngineAdapter interface   | $60-100K + 12-16 weeks engineering                   | 3 engines, cross-engine receipt compatibility                          |
| **Stage 3** | Q3-Q4 2027 (16-24 weeks)    | Unreal embodiment + public demo deployed                                    | $150-300K + 16-24 weeks engineering + asset pipeline | Public demo deployed, downloadable, conference talks                   |

**Total roadmap cost estimate: $255-475K over 12-18 months.**

This business case asks for **Stage 0 funding only** ($15-25K). Stages 1-3 are separate funding decisions, each gated on the prior stage's exit criteria.

### Core principle: engine-agnostic doctrine, engine-specific embodiment

The roadmap separates:

- **Doctrine** — what the primitive means, its invariants, its receipt contract (engine-agnostic, lives in `hummbl-governance` + `hummbl-doctrine`)
- **Schema** — the machine-readable shape of the primitive's state (engine-agnostic, JSON Schema in `hummbl-governance/schemas/`)
- **Adapter** — the engine-specific embodiment (engine-specific, lives in the game repo)
- **Demo** — a public, playable surface (engine-specific, deployed)

This separation ensures a primitive defined once can be embodied in Minecraft, then Unreal, then any future engine, without redefining the doctrine. Stage 0 funds the doctrine + schema layer. The adapter and demo layers are funded in Stages 1-3.

---

## 3. Stage 0 scope (the funding ask)

### What Stage 0 delivers

For each of 8 primitives (KillSwitch, CircuitBreaker, DelegationToken, GovernanceBus, Receipt, AgentRegistry, CostGovernor, CapabilityFence):

1. **Doctrine document** — `docs/doctrine/<PRIMITIVE>.md` in `hummbl-governance`, specifying:
   - What the primitive means (semantics)
   - Its invariants (what must always be true)
   - Its receipt contract (what evidence it emits)
   - Its lifecycle (creation, use, decommission)

2. **JSON Schema** — `hummbl-governance/schemas/<PRIMITIVE>.json`, the machine-readable shape of the primitive's state. This is the contract between the doctrine and any adapter.

3. **Simulation Affordance section** — a section in each doctrine doc specifying:
   - How the primitive appears in-world (the in-world name and form)
   - What a player can do with it (the player affordances)
   - What a player can observe (the observability)
   - What a player can verify (the verifiability)

### The 8 primitives and their in-world forms

| Primitive         | In-world name   | In-world form              | Player affordance                 |
| ----------------- | --------------- | -------------------------- | --------------------------------- |
| KillSwitch        | The Kill Switch | Redstone lever             | Pull to halt all agents           |
| CircuitBreaker    | The Breaker     | Redstone repeater          | Watch it trip on repeated failure |
| DelegationToken   | The Token       | Writable book              | Carry, present, inspect           |
| GovernanceBus     | The Bus         | Lectern + book             | Read agent messages               |
| Receipt (KRINEIA) | The Receipt     | Signed book in chest chain | Read, verify hash chain           |
| AgentRegistry     | Agent Census    | Armor stand + name tag     | See registered agents             |
| CostGovernor      | The Vault       | Chest + hopper             | Watch resources deplete           |
| CapabilityFence   | The Fence       | Gated area                 | Watch token check at gate         |

### Stage 0 exit criteria

- [ ] All 8 primitives have a doctrine document in `hummbl-governance/docs/doctrine/`
- [ ] All 8 primitives have a JSON Schema in `hummbl-governance/schemas/`
- [ ] All 8 doctrine docs have a Simulation Affordance section
- [ ] The doctrine docs are reviewed by the Board (or PA delegate)
- [ ] A KRINEIA receipt is emitted for the Stage 0 completion

### What Stage 0 does NOT deliver

- No Minecraft code (that is Stage 1)
- No adapter interface (that is Stage 1-2)
- No public demo (that is Stage 3)
- No playtesters (that is Stage 1)

Stage 0 is the doctrine + schema layer. It is the contract that makes Stages 1-3 possible.

---

## 4. Cost and timeline

### Cost breakdown (Stage 0)

| Item                         | Estimate    | Notes                                                |
| ---------------------------- | ----------- | ---------------------------------------------------- |
| Engineering time (4-6 weeks) | $10-20K     | At HUMMBL's internal cost rate; 1 engineer part-time |
| Doctrine review (Board + PA) | $2-3K       | 2 Board meetings, 1 PA review                        |
| Schema validation tooling    | $1-2K       | JSON Schema validator, CI integration                |
| Documentation polish         | $2K         | Technical writer for public-facing doctrine docs     |
| **Total**                    | **$15-27K** |                                                      |

### Timeline (Stage 0)

| Week | Deliverable                                                               |
| ---- | ------------------------------------------------------------------------- |
| 1    | KillSwitch + CircuitBreaker doctrine + schema + simulation affordance     |
| 2    | DelegationToken + GovernanceBus doctrine + schema + simulation affordance |
| 3    | Receipt + AgentRegistry doctrine + schema + simulation affordance         |
| 4    | CostGovernor + CapabilityFence doctrine + schema + simulation affordance  |
| 5    | Schema validation tooling + CI integration                                |
| 6    | Board review + PA review + KRINEIA receipt                                |

### Funding source

Stage 0 is funded from HUMMBL's existing operating budget (no new capital required). The cost is within the Q3 2026 engineering allocation. The PA approved Phase 1 funding on 2026-06-23; Stage 0 is within that envelope.

---

## 5. Return on investment

### Direct return (Stage 0 alone)

Stage 0 produces no direct revenue. It is the doctrine + schema layer that makes Stages 1-3 possible. The direct return is:

1. **A formal doctrine for all 8 primitives** — this is a deliverable that benefits HUMMBL regardless of whether Stages 1-3 happen. The doctrine docs are the canonical reference for what each primitive means. They are useful for the white paper, the position papers, the compliance mapper, and any future product surface.
2. **JSON Schemas for all 8 primitives** — this is a deliverable that benefits the compliance mapper (which can now validate primitive state against the schema) and any future adapter (which can now rely on the schema as the contract).
3. **Simulation Affordance sections** — this is a deliverable that makes the primitives legible to non-engineers even before the playable embodiment exists. The sections can be excerpted into the white paper and position papers.

### Indirect return (Stages 1-3, if funded)

If Stages 1-3 are funded and executed, the indirect return is:

1. **A product demo that no competitor can match** — playable governance is a new category. HUMMBL would own it.
2. **A conference talk that writes itself** — "Come play a kill switch in Minecraft" is a talk title that gets accepted.
3. **A sales call that closes itself** — a compliance buyer who plays a kill switch remembers it.
4. **A YouTube video that markets itself** — a playable world is shareable; a dashboard is not.
5. **A category HUMMBL would own** — "playable governance" is a category with zero competitors today.

### Strategic option value

Even if Stages 1-3 are never funded, Stage 0 has strategic value:

1. **The doctrine docs are the canonical reference** — they improve every other artifact (white paper, position papers, compliance mapper).
2. **The schemas are the contract** — they make the primitives more rigorous and more interoperable.
3. **The simulation affordance sections are a future option** — if HUMMBL decides to pursue playable governance in 2027 or 2028, the doctrine + schema layer is already done.

### The downside risk

The downside risk of Stage 0 is low:

1. **Cost is small** ($15-27K) — within Q3 2026 operating budget.
2. **Time is short** (4-6 weeks) — does not block other work.
3. **Deliverables are useful regardless** — doctrine + schema + simulation affordance benefit HUMMBL even if Stages 1-3 never happen.
4. **No irreversible commitment** — Stage 0 does not commit to Minecraft, Unreal, or any engine. It commits only to formalizing the doctrine.

The downside risk of NOT funding Stage 0:

1. **The roadmap stalls** — without Stage 0, Stages 1-3 cannot start (no doctrine to embody).
2. **The category remains unclaimed** — if a competitor moves first on playable governance, HUMMBL loses the category.
3. **The doctrine remains informal** — the primitives are currently documented in code comments and the white paper, not in formal doctrine docs. This is a governance gap.

---

## 6. Risks and mitigations

| Risk                                                    | Likelihood    | Impact        | Mitigation                                                                                                                        |
| ------------------------------------------------------- | ------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Stage 0 doctrine is wrong and must be reworked**      | Low           | Medium        | Board review at week 6; doctrine is versioned and can be revised in Stage 1                                                       |
| **Stage 0 schema does not match Stage 1 adapter needs** | Medium        | Medium        | Schema is versioned; Stage 1 can request schema changes via ADR                                                                   |
| **Stage 0 takes longer than 6 weeks**                   | Medium        | Low           | Stage 0 is not on the critical path for any revenue; slippage is acceptable                                                       |
| **Stages 1-3 are never funded**                         | Medium        | Low           | Stage 0 deliverables are useful regardless (doctrine, schemas, simulation affordance sections)                                    |
| **A competitor ships playable governance first**        | Low           | High          | Stage 0 is 6 weeks; no competitor is known to be working on this; HUMMBL's primitive library is the hard part, not the embodiment |
| **Minecraft/Unreal licensing or platform risk**         | Low (Stage 0) | N/A (Stage 0) | Stage 0 does not commit to any engine; platform risk is a Stage 1-3 concern                                                       |

---

## 7. Alternatives considered

### Alternative A: Skip Stage 0, go straight to Minecraft prototype

**Rejected.** Without formal doctrine, the Minecraft prototype would be ad hoc. The in-world forms would be designed on the fly, and the doctrine would be reverse-engineered from the prototype. This is faster in week 1 but slower in month 3, because every later stage (Unity, Godot, Unreal) would have to reverse-engineer the doctrine from the Minecraft implementation. Stage 0 is the contract that prevents this.

### Alternative B: Skip Stage 0 and Stage 1, go straight to Unreal

**Rejected.** Unreal is the highest-fidelity option but also the highest-cost (engine expertise, asset pipeline, compute). Going straight to Unreal without a prototype in a cheaper engine (Minecraft) means the doctrine is untested. If the doctrine is wrong, the Unreal embodiment is wrong, and the rework cost is 10x. The staged roadmap (Minecraft → multi-game → Unreal) tests the doctrine cheaply before committing to the expensive embodiment.

### Alternative C: Do not pursue playable governance at all

**Rejected.** The playable governance category is empty. A competitor who moves first will own it. HUMMBL's primitive library is the hard part; the embodiment is the easy part. If HUMMBL does not embody its own primitives, a competitor with a worse library and a better embodiment will take the category. Stage 0 is the cheapest way to keep the option open.

### Alternative D: Outsource Stage 0 to a consulting firm

**Rejected.** The doctrine is the product. Outsourcing the doctrine means outsourcing the product. HUMMBL's primitives are the differentiator; the doctrine must be authored by HUMMBL.

---

## 8. Recommendation

**Fund Stage 0 at $15-27K, 4-6 weeks, Q3 2026.**

Stage 0 is:

- **Low cost** ($15-27K, within Q3 2026 operating budget)
- **Low risk** (no irreversible commitment, deliverables useful regardless)
- **High option value** (keeps the playable governance category open for HUMMBL)
- **Strategically aligned** (doctrine + schema + simulation affordance benefit all other artifacts)

Stages 1-3 are separate funding decisions, each gated on the prior stage's exit criteria. This business case asks only for Stage 0.

### Approval request

The Principal Agent is asked to approve:

1. **Stage 0 funding**: $15-27K from Q3 2026 operating budget
2. **Stage 0 scope**: doctrine + JSON Schema + Simulation Affordance section for all 8 primitives
3. **Stage 0 timeline**: 4-6 weeks, starting within 2 weeks of approval
4. **Stage 0 owner**: Operator (PA) with engineering delegation to Devin/Codex
5. **Stage 0 exit criteria**: all 8 primitives have doctrine + schema + simulation affordance; Board review; KRINEIA receipt

On approval, the next step is ADR-003 (Game Engine Doctrine Architecture) per the roadmap.

---

## 9. How to verify this business case

A reader can re-verify every claim in this case independently:

1. **Issue #408 exists** — `gh issue view 408` in `hummbl-io/hummbl-production`.
2. **The roadmap exists** — inspect `docs/product/GAME_ENGINE_ROADMAP.md` (commit 7fdf172).
3. **The 8 primitives exist** — `pip install hummbl-governance` and inspect the package; or read `hummbl-io/hummbl-governance/hummbl_governance/`.
4. **The 1,234 tests exist** — clone `hummbl-io/hummbl-governance` and run `pytest --collect-only`.
5. **No competitor has a playable embodiment** — check the competitive analysis (`docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`); none of the 19 vendors surveyed have a playable world.
6. **The PA approved Phase 1 funding on 2026-06-23** — inspect the promotion packet review log in `docs/artifacts/ARTIFACT_MANIFEST.md`.

If any claim in this case cannot be re-verified, open an issue at `hummbl-io/hummbl-production/issues` and the claim will be corrected or removed per CONSTITUTION §3.1.

---

## References

- Issue #408: `hummbl-io/hummbl-production#408` — product: define simulation-ready game engine roadmap from Minecraft to Unreal
- Roadmap: `docs/product/GAME_ENGINE_ROADMAP.md` (commit 7fdf172)
- White paper: `docs/artifacts/WHITE_PAPER_governance_infrastructure.md`
- Competitive analysis: `docs/artifacts/COMPETITIVE_ANALYSIS_ai_governance.md`
- Market analysis: `docs/artifacts/MARKET_ANALYSIS_ai_governance.md`
- Case study: `docs/artifacts/CASE_STUDY_claims_remediation.md`
- Strategic plan: `docs/artifacts/STRATEGIC_PLAN_12mo.md`
- Claims manifest: `web/manifest/claims-provenance.json`
- CONSTITUTION: `CONSTITUTION.md` (§3.1 public claim honesty invariant)

---

## Authority boundary

**Operator** is the human **Principal Agent** for HUMMBL — the goal-owning, value-bearing, accountable agent. **Devin** (and other software agents: Codex, Claude Code, Gemini, OpenCode, Kai, Apex, Nexus, Auditor, Hermes) are **delegated drafting, research, and execution systems**. They can draft, collect, compare, format, inspect, and surface — they cannot confer strategic authority on themselves, promote drafts to live, publish external claims, or redefine strategic goals. This business case was drafted by Devin at the direction of the Principal Agent, based on issue #408 and the game engine roadmap (commit 7fdf172), and was promoted to live (private) by Principal Agent decision on 2026-06-23. The funding decision is the Principal Agent's. This document is **private** — it is intended for internal readers (Operator, Board) and is not for external publication.
