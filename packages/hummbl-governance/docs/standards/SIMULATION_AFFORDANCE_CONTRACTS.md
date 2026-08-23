# Simulation-Affordance Contract Canonicalization

Status: draft extraction packet for issue #164.
Last verified: 2026-07-03.

## Purpose

`<private-repo>/hummbl-governed-quest-sim` now contains implementation
evidence for Minecraft/Fabric governed simulation contracts. This document
extracts candidate governance truth from that evidence without promoting the
prototype itself into canon.

Implementation evidence remains in `<private-repo>`. Canonical governance
truth enters `hummbl-governance` only after human and governance review.

## Evidence Baseline

Source repository: `hummbl-io/<private-repo>`.
Evidence commit: `1838d30e553003115c1acaa11b7c1a993d7d6cf3`.
Commit summary: `chore(deps): bump gradle/actions from 4 to 6 (#546)`.

The inventory below was read from that commit, not from a moving branch.

## Implementation Evidence Inventory

| Evidence area | Source path at `1838d30e...` | Governance relevance |
|---|---|---|
| Package overview and transfer framing | `hummbl-governed-quest-sim/README.md` | Defines engine-agnostic, deterministic, receipt-based, adapter-driven simulation posture. |
| Python adapter contract | `hummbl-governed-quest-sim/src/governance/adapter/contract.py` | States adapter identity, capabilities, lifecycle, action/observation, deterministic providers, and error taxonomy. |
| Python Fabric contract shell | `hummbl-governed-quest-sim/src/governance/adapter/fabric_contract.py` | States Fabric is renderer/executor/observer/forwarder only and may not define governance truth. |
| Java Fabric adapter contract | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/adapter/AdapterContract.java` | Mirrors the adapter contract at the Java/Fabric boundary. |
| Python-Java bridge protocol | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/adapter/bridge/BridgeProtocol.java` | Defines bridge protocol, envelope types, and shared error kind names. |
| Receipt forwarding | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/adapter/bridge/ReceiptForward.java` | States Java forwards observed receipts; Python kernel decides acceptance, rejection, or chaining. |
| Receipt chain | `hummbl-governed-quest-sim/src/governance/receipt_chain.py` | Defines append-only SHA-256 linked receipts with deterministic clock and ID injection. |
| Scenario replay | `hummbl-governed-quest-sim/src/governance/scenarios/runner.py` | Defines deterministic scenario execution, expected receipt checks, chain verification, and state assertions. |
| Adapter conformance | `hummbl-governed-quest-sim/src/governance/adapter/conformance.py` | Defines 10 conformance gates for capabilities, dispatch, state observation, receipt forwarding, lifecycle, taxonomy, negative regression, determinism, reset, and teardown. |
| Tunnel gates | `hummbl-governed-quest-sim/src/governance/adapter/tunnel_scenarios.py` | Defines 12 tunnel-specific gates including permit, role, owner allowlist, toll, denial receipts, transit receipts, and gate order. |
| Runtime smoke | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/RuntimeSmokeTest.java` | Implementation evidence for automated runtime contact verification. |
| Fabric world manifestation | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/WorldManifestor.java` | Implementation evidence for renderer-only world manifestation. |
| Runtime replay engine | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/ScenarioReplayEngine.java` | Implementation evidence for replaying governance scenarios through the Fabric boundary. |
| Runtime pilot engines | `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/BoundedPilotEngine.java`, `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/ScaledPilotEngine.java`, `hummbl-governed-quest-sim/fabric-adapter/src/main/java/dev/hummbl/gqs/runtime/EndurancePilotEngine.java` | Implementation evidence for bounded, scaled, and endurance pilot execution. |
| Python adapter tests | `hummbl-governed-quest-sim/tests/test_adapter_contract.py`, `hummbl-governed-quest-sim/tests/test_adapter_conformance.py`, `hummbl-governed-quest-sim/tests/test_fabric_adapter.py` | Adapter-specific validation evidence; not itself canonical truth. |
| Scenario and determinism tests | `hummbl-governed-quest-sim/tests/test_scenarios.py`, `hummbl-governed-quest-sim/tests/test_tunnel_scenarios.py`, `hummbl-governed-quest-sim/tests/test_determinism_closure.py` | Deterministic replay and tunnel validation evidence; not itself canonical truth. |
| Runtime and bridge tests | `hummbl-governed-quest-sim/tests/test_p0_runtime_smoke.py`, `hummbl-governed-quest-sim/tests/test_p0_manifestation.py`, `hummbl-governed-quest-sim/tests/test_bridge_contract.py`, `hummbl-governed-quest-sim/fabric-adapter/src/test/java/dev/hummbl/gqs/FabricAdapterContractTest.java` | Runtime-contact, manifestation, bridge, and Java adapter validation evidence. |

## PR-to-Contract Mapping

| Production PR | Merged evidence | Candidate governance surface |
|---|---|---|
| `<private-repo>#489` | Engine-agnostic governance kernel and nine-primitives simulator | Simulation kernel remains implementation evidence; canonical truth is the engine-agnostic pattern and receipt requirement. |
| `<private-repo>#494` | Adapter Contract | Candidate canonical adapter boundary: identity, capabilities, lifecycle, action/observation, providers, errors. |
| `<private-repo>#496` | Fabric Adapter Skeleton | Candidate Fabric doctrine: Fabric may manifest but not govern. |
| `<private-repo>#498` | Python-Java Bridge Contract | Candidate bridge envelope contract: action, observation, receipt_forward, error. |
| `<private-repo>#500` | P0 Runtime Smoke | Runtime contact is evidence only; canonical truth is that engine contact requires automated gate verification. |
| `<private-repo>#505` | P1 Tunnel Runtime Manifestation | Candidate tunnel invariants: gates, denial receipts, transit receipts, and ordered gate evaluation. |
| `<private-repo>#526` | Integrated Scenario Replay Demo | Candidate replay contract: deterministic receipt sequence plus final-state assertions. |
| `<private-repo>#528` | Short 2-3 agent bounded pilot | Pilot evidence only; outputs are play-generated candidates pending review. |
| `<private-repo>#530` | 5-10 agent bounded pilot | Scale evidence only; outputs are not canon without promotion review. |
| `<private-repo>#532` | 24h pilot infrastructure | Candidate operational contract: rollback, logging, and receipt export are required for endurance pilots. |
| `<private-repo>#536` | Adapter Conformance Suite and WebAdapterContract | Candidate conformance gate set for any simulation adapter. |

## Candidate Canonical Contracts

### Adapter Boundary

An adapter is a renderer, executor, observer, and receipt forwarder. It is not a
governor. It must not define, override, veto, or validate governance outcomes
except through declared conformance checks.

Minimum adapter contract:

- stable adapter ID and version,
- declared primitive capabilities,
- scenario lifecycle: initialize, reset, teardown,
- canonical action application,
- engine-agnostic state observation,
- receipt forwarding without mutation,
- deterministic clock and ID injection for replay,
- structured error taxonomy.

### Fabric Boundary

Fabric/Minecraft may manifest districts, paths, agents, trials, vaults, mines,
tunnels, quests, receipts, and world events. It may not decide:

- verdicts,
- role legitimacy,
- ownership or custody validity,
- extraction authorization,
- tunnel traversal authorization,
- quest completion or claim validity,
- receipt validity.

Those outcomes remain kernel decisions.

### Receipt Semantics

Every consequential governance action must produce an append-only receipt.
Receipt chains are engine-agnostic and tamper-evident by hash linkage.
Adapters may store or forward receipts, but the kernel decides whether a
receipt is accepted into the governance chain.

### Replay Determinism

Replayable scenarios require deterministic timestamp and ID providers. A
scenario replay contract should verify:

- expected receipt count,
- expected receipt types and actors in sequence,
- receipt-chain integrity,
- final-state assertions,
- expected failure reasons where a scenario is supposed to fail.

### Tunnel Invariants

Tunnels are gated transitions between layers or spaces. Candidate canonical
invariants:

- open tunnel without gates permits transit,
- permit gates deny missing or invalid permits,
- role gates deny agents without the required role,
- owner allowlists deny unlisted agents,
- toll gates require an economy integration or an explicit test-mode waiver,
- multiple gates evaluate in declared order,
- the first failing gate determines denial reason,
- denial emits a denial receipt,
- successful transit emits a transit receipt,
- nonexistent tunnel traversal fails without transit receipt.

### Conformance Gates

Any promoted simulation adapter should pass or explicitly waive these gates:

- capability declaration,
- action dispatch,
- state observation,
- receipt forwarding,
- lifecycle gate,
- error taxonomy,
- negative regression,
- determinism,
- reset clean,
- teardown release.

## Transfer Limits

Minecraft/Fabric output is play-generated candidate evidence. It does not
become canonical governance truth until recorded human review and explicit
governance approval promote it with:

1. implementation evidence reference,
2. prior-art or transfer-limit analysis,
3. conformance evidence,
4. recorded human review decision and governance approval record,
5. explicit statement of what is and is not being promoted.

Prototype paths, scenario wording, gameplay affordances, pilot counts, and
runtime logs remain implementation evidence unless separately promoted.

## Open Gates Before Canon Promotion

- Decide whether these contracts remain docs-only standards or become schemas.
- Decide where bridge envelope schemas should live if promoted.
- Decide whether tunnel gate semantics belong in `hummbl-governance` runtime
  primitives, simulation standards, or a separate package.
- Confirm whether WebAdapterContract evidence should be included in the same
  adapter conformance standard.
- Confirm which pilot receipts are sufficient for play-generated candidate
  promotion.
- Confirm whether `docs/SIMULATION_AFFORDANCE_TEMPLATE.md` should reference
  this extraction packet after review.

## Review Summary

The production implementation supports extracting governance language for:

- adapter boundary,
- Fabric non-governance doctrine,
- bridge envelope classes,
- receipt-chain semantics,
- deterministic scenario replay,
- tunnel gates,
- adapter conformance gates,
- pilot transfer limits.

This draft intentionally does not copy production implementation into this
repository and does not mark any Minecraft/Fabric output as promoted canon.

