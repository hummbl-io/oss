# Simulation-Ready Game Engine Roadmap — Minecraft to Unreal

**Status:** draft v0.1
**Owner:** Operator
**Steward:** HUMMBL, LLC
**Date:** 2026-06-23
**Tracking:** hummbl-io/hummbl-production#408

## 1. Problem

HUMMBL's governance and memory architecture is constrained by eventual implementation in Minecraft, other games, and Unreal Engine. The product surface needs a roadmap that translates governance primitives into playable/simulatable systems without prematurely committing to high-fidelity Unreal implementation.

Without a staged roadmap, the team may either overbuild engine-specific prototypes too early or fail to preserve the simulation affordances needed for later productization.

## 2. Core principle: engine-agnostic doctrine, engine-specific embodiment

The governance primitives (KillSwitch, CircuitBreaker, DelegationToken, Bus, Receipts, etc.) are defined in `hummbl-governance` as pure Python with zero runtime dependencies. They are **engine-agnostic by construction**. The roadmap separates:

- **Doctrine** — what the primitive means, its invariants, its receipt contract (engine-agnostic, lives in `hummbl-governance` + `hummbl-doctrine`)
- **Schema** — the machine-readable shape of the primitive's state (engine-agnostic, JSON Schema in `hummbl-governance/schemas/`)
- **Adapter** — the engine-specific embodiment that makes the primitive playable/simulable in a given game engine (engine-specific, lives in the game repo)
- **Demo** — a public, playable surface that shows the primitive in action (engine-specific, deployed)

This separation ensures that a primitive defined once can be embodied in Minecraft, then in Unreal, then in any future engine, without redefining the doctrine.

## 3. Staged roadmap

### Stage 0 — Doctrine & schemas (current → Q3 2026)

**Goal:** every governance primitive that will appear in-world has a written doctrine and a JSON Schema.

**Primitives to formalize:**

| Primitive         | Doctrine location | Schema location            | In-world name                         |
| ----------------- | ----------------- | -------------------------- | ------------------------------------- |
| KillSwitch        | hummbl-governance | hummbl-governance/schemas/ | The Kill Switch (redstone lever)      |
| CircuitBreaker    | hummbl-governance | hummbl-governance/schemas/ | The Breaker (redstone repeater)       |
| DelegationToken   | hummbl-governance | hummbl-governance/schemas/ | The Token (writable book)             |
| GovernanceBus     | hummbl-governance | hummbl-governance/schemas/ | The Bus (lectern + book)              |
| Receipt (KRINEIA) | krineia repo      | krineia/RECEIPT_SCHEMA.md  | The Receipt (signed book)             |
| AgentRegistry     | hummbl-governance | hummbl-governance/schemas/ | Agent Census (armor stand + name tag) |
| CostGovernor      | hummbl-governance | hummbl-governance/schemas/ | The Vault (chest + hopper)            |
| CapabilityFence   | hummbl-governance | hummbl-governance/schemas/ | The Fence (gated area)                |

**Deliverables:**

- [ ] Each primitive has a `docs/doctrine/<PRIMITIVE>.md` in hummbl-governance
- [ ] Each primitive has a JSON Schema in `hummbl-governance/schemas/`
- [ ] A `Simulation Affordance` section is added to each doctrine doc (see §6 template)

**Exit criteria:** all 8 primitives have doctrine + schema + simulation affordance section.

### Stage 1 — Minecraft prototype (Q4 2026)

**Goal:** a playable Minecraft world that embodies the 8 primitives as in-world mechanics. Proves the doctrine is simulatable.

**Architecture:**

- Minecraft Java Edition (modded) or Bedrock Edition (behavior pack)
- A Python-side bridge that connects `hummbl-governance` primitives to Minecraft via a simple protocol (RCON or WebSocket)
- The bridge is the adapter; the primitives stay pure Python

**Minimum viable playable primitives:**

1. **The Kill Switch** — a redstone lever that, when pulled, halts all agent activity in the world. Visible, audible, unambiguous.
2. **The Bus** — a lectern where agents post messages (written books). Players can read the bus by opening the lectern.
3. **The Receipt** — every agent action writes a signed book to a chest chain. The chain is hash-linked; players can verify by comparing hashes.
4. **The Token** — agents carry writable books (delegation tokens) that define what they're allowed to do. A fence gate checks the token before letting the agent through.
5. **The Vault** — a chest + hopper system that represents the cost governor. When the vault is empty, agents stop working.
6. **The Breaker** — a redstone repeater that trips when an agent fails repeatedly, cutting power to that agent's area.
7. **Agent Census** — armor stands with name tags representing registered agents. Unregistered agents (no armor stand) are refused service.
8. **The Fence** — a gated area that agents cannot leave without a capability token. Visualizes the capability fence.

**Success metrics:**

| Metric                                             | Target                     |
| -------------------------------------------------- | -------------------------- |
| Primitives playable in-world                       | 8/8                        |
| Receipt chain verifiable by a player               | Yes (book hash comparison) |
| Kill switch halts all agents in < 5 seconds        | Yes                        |
| Bridge latency (Python → Minecraft)                | < 500ms                    |
| Playtest sessions with external users              | 5                          |
| User can explain what a "receipt" is after playing | 4/5 users                  |
| User can verify a receipt chain manually           | 3/5 users                  |

**Deliverables:**

- [ ] Minecraft world file with the 8 primitives built
- [ ] Python bridge (`hummbl-minecraft-adapter` repo, new)
- [ ] Playtest report with success metrics
- [ ] KRINEIA receipts for each playtest session

**Exit criteria:** 5 external playtesters, 4/5 can explain receipts after playing.

### Stage 2 — Multi-game adapters (Q1-Q2 2027)

**Goal:** abstract the Minecraft adapter into a reusable protocol and implement it for 2+ additional game engines.

**Engines to evaluate:**

- **Roblox** (Lua, large audience, easy multiplayer)
- **Unity** (C#, industry standard, good for 3D)
- **Godot** (open source, growing, lightweight)

**Architecture:**

- Define a `GameEngineAdapter` interface in `hummbl-governance` (or a new `hummbl-game-adapter` package)
- Each engine implements the interface: `spawn_primitive`, `read_state`, `write_state`, `emit_receipt`
- The doctrine and schemas stay unchanged; only the embodiment changes

**Success metrics:**

| Metric                             | Target                                                  |
| ---------------------------------- | ------------------------------------------------------- |
| Engines supported                  | 3 (Minecraft + 2 new)                                   |
| Adapter interface stable           | Yes (no breaking changes after v0.1)                    |
| Cross-engine receipt compatibility | A receipt written in Minecraft reads correctly in Unity |
| Playtests per engine               | 3                                                       |

**Exit criteria:** 3 engines, cross-engine receipt compatibility verified.

### Stage 3 — Unreal embodiment & public demo (Q3-Q4 2027)

**Goal:** a high-fidelity Unreal Engine embodiment of the governance primitives, deployed as a public demo.

**Why Unreal is last:**

- Unreal is the highest-fidelity option but also the highest-cost (engine expertise, asset pipeline, compute)
- By Stage 3, the doctrine and schemas are battle-tested in Minecraft + 2 other engines
- The Unreal embodiment is then a pure adapter implementation, not a design exercise
- This avoids overbuilding Unreal-specific prototypes before the doctrine is stable

**Architecture:**

- Unreal Engine 5 (latest at time of implementation)
- C++ adapter implementing the `GameEngineAdapter` interface
- High-fidelity 3D embodiments of the 8 primitives (e.g., The Kill Switch is a physical lever in a governance chamber, not a redstone lever)
- Multiplayer support for playtests
- Deployed as a downloadable demo or cloud-streamed demo

**Success metrics:**

| Metric                                                  | Target                               |
| ------------------------------------------------------- | ------------------------------------ |
| Primitives embodied in Unreal                           | 8/8                                  |
| Public demo available                                   | Yes (downloadable or cloud-streamed) |
| Demo playtest sessions                                  | 20                                   |
| Press / analyst coverage                                | 2 pieces                             |
| Inbound discovery calls mentioning the demo             | 5                                    |
| Cross-engine receipt compatibility (Minecraft ↔ Unreal) | Verified                             |

**Exit criteria:** public demo live, 20 playtest sessions, 5 inbound calls.

## 4. What must remain engine-agnostic

These must not depend on any specific game engine:

1. **Doctrine** — primitive definitions, invariants, receipt contracts
2. **Schemas** — JSON Schema for primitive state
3. **Receipts** — KRINEIA receipt format and chain validation
4. **Bus protocol** — coordination bus message format
5. **Agent registry** — agent identity and capability definitions
6. **Validation** — deterministic gates (schema validation, receipt verification)

These may be engine-specific:

1. **Visual embodiment** — how a primitive looks in-world (redstone lever vs. 3D lever)
2. **Interaction model** — how a player interacts (right-click vs. E key vs. VR gesture)
3. **Audio** — sounds associated with primitive events
4. **Multiplayer transport** — how state syncs between players
5. **Asset pipeline** — models, textures, animations

## 5. Prior-art corpus and novelty rubric

This roadmap references:

- **Simulation-governance prior-art corpus:** hummbl-io/hummbl-governance#1018 — a curated corpus of prior art on governance in simulation/game environments
- **Governance registry:** hummbl-io/hummbl-governance#79 — the registry of governance primitives that will be embodied
- **Arbiter novelty rubric:** the `arbiter` tool's novelty scoring, used to evaluate whether a primitive embodiment is novel or derivative

Before each stage, the prior-art corpus is reviewed to ensure the embodiment is grounded. After each stage, the novelty rubric is applied to the embodiment to document what is novel.

## 6. Simulation Affordance section template

Every product spec and governance doc that defines a primitive must include a `Simulation Affordance` section:

```markdown
## Simulation Affordance

**In-world name:** <the name players see>
**Visual embodiment:** <how it appears in-world>
**Interaction model:** <how players interact>
**State visibility:** <how players can observe the primitive's state>
**Receipt contract:** <what receipt is emitted when the primitive fires>
**Engine-agnostic invariants:** <what must not change across engines>
**Engine-specific affordances:** <what may differ across engines>
**Playtest notes:** <observations from playtests, if any>
```

This section is required for all 8 primitives by end of Stage 0.

## 7. Research vs. demo vs. production separation

| Surface                 | Purpose                                          | Audience                                | Receipt requirement                                           |
| ----------------------- | ------------------------------------------------ | --------------------------------------- | ------------------------------------------------------------- |
| **Research experiment** | Test a hypothesis about governance in simulation | Internal                                | KRINEIA receipt per experiment                                |
| **Public demo**         | Show the system to external audiences            | External (playtesters, press, analysts) | KRINEIA receipt per session + claims-provenance entry         |
| **Production surface**  | Deployed, durable, versioned                     | External (anyone)                       | Full governance stack (CONSTITUTION, KRINEIA, receipts, ADRs) |

Research experiments may use any engine and any prototype quality. Public demos must pass a review gate (doctrinal accuracy, receipt integrity, claims honesty). Production surfaces must adopt the HUMMBL Repo Standard v0.1.

## 8. Pilot experiment specification

### Pilot: "Receipt Chain Playtest" (Stage 1)

**Hypothesis:** A player who has never heard of KRINEIA can, after 15 minutes of play in the Minecraft prototype, correctly explain what a receipt chain is and manually verify a 3-receipt chain.

**Method:**

1. Recruit 5 playtesters (no prior KRINEIA knowledge)
2. 15-minute play session in the Minecraft prototype
3. Post-play assessment: (a) explain what a receipt is, (b) verify a 3-receipt chain by comparing hashes
4. Record session with KRINEIA receipts

**Success metrics:**

- 4/5 playtesters can explain receipts
- 3/5 playtesters can verify a chain
- All sessions have KRINEIA receipts

**Failure response:** If < 3/5 can verify, the in-world receipt visualization needs redesign before Stage 2.

**Receipts:**

- One KRINEIA receipt per playtester session (5 total)
- One summary receipt with aggregate metrics
- All receipts committed to the `hummbl-minecraft-adapter` repo's chain

## 9. Risks and mitigations

| Risk                                             | Mitigation                                                                                                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Doctrine changes after Minecraft prototype       | Stage 0 exit criteria require stable doctrine; changes after Stage 1 require ADR + migration plan          |
| Minecraft adapter becomes too Minecraft-specific | Adapter interface defined in Stage 2 before second engine; Minecraft adapter refactored to conform         |
| Unreal cost overruns                             | Unreal is Stage 3 only; doctrine + schemas + 3 other engines validate the design before Unreal investment  |
| Playtesters don't understand receipts            | Pilot experiment tests this explicitly; redesign if failure response triggers                              |
| Engine vendor lock-in                            | Engine-agnostic doctrine + schemas; adapters are replaceable; no engine-specific code in hummbl-governance |
| Public demo claims not receipt-backed            | All demo claims go through claims-provenance.json protocol (per hummbl-production CONSTITUTION §3.1)       |

## 10. Open questions

1. Should the Minecraft prototype use Java Edition (modded) or Bedrock Edition (behavior pack)? (Recommendation: Java Edition for Python bridge simplicity; revisit if audience reach demands Bedrock.)
2. Should the `GameEngineAdapter` interface live in `hummbl-governance` or a new `hummbl-game-adapter` package? (Recommendation: new package, to keep hummbl-governance focused on governance, not game integration.)
3. Should the Unreal demo be downloadable or cloud-streamed? (Recommendation: downloadable first, cloud-streamed if demand emerges.)
4. Should we partner with an existing Minecraft server for the prototype, or self-host? (Recommendation: self-host for control; revisit for Stage 2 multiplayer.)
5. What is the budget for Unreal asset creation? (Open — needs operator input.)

## 11. Next steps

1. **This roadmap:** review by Board (Operator, Future Self, Governance Officer, Risk Officer, Stakeholder Proxy).
2. **On approval:** create ADR-003 in hummbl-production/docs/adr/ recording the decision to pursue this roadmap.
3. **Stage 0 work:** formalize doctrine + schemas for the 8 primitives in hummbl-governance.
4. **Stage 1 prep:** create `hummbl-minecraft-adapter` repo with the HUMMBL Repo Standard v0.1 artifact stack.
5. **Pilot experiment:** schedule 5 playtesters for the Receipt Chain Playtest.

## References

- Issue: hummbl-io/hummbl-production#408
- ChatGPT review surface: hummbl-io/hummbl-governance#981
- Simulation prior-art corpus: hummbl-io/hummbl-governance#1018
- Governance registry: hummbl-io/hummbl-governance#79
- HUMMBL Repo Standard: hummbl-io/hummbl-governance/docs/standards/HUMMBL_REPO_STANDARD.md
- KRINEIA receipt schema: hummbl-io/krineia/RECEIPT_SCHEMA.md
