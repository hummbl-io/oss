# SINT Concept Extraction

Status: draft guidance

Purpose: record what HUMMBL should learn from the local `sint-protocol` review
without adopting SINT branding, dependency shape, roadmap claims, or partnership
framing.

## Context

The local `sint-protocol` fork was created after upstream invited external
collaboration. Upstream did not continue that collaboration path. HUMMBL should
therefore treat SINT as external source material, not a dependency, partnership,
or endorsed roadmap.

SINT is Apache-2.0 licensed in the reviewed local checkout. Copying code would
require preserving license and attribution. The preferred path is cleaner:
reuse architectural patterns in HUMMBL-owned language, schemas, fixtures, and
tests.

## Do Not Adopt

- SINT project name, package names, or brand surface.
- Claims of partnership, collaboration, endorsement, or compatibility.
- Physical-world validation claims unless HUMMBL reproduces the validation.
- Tokenomics or speculative engine/avatar layers.
- Dependency-heavy TypeScript implementation as a primitive authority.
- Any direct package dependency on the SINT monorepo.

## Concepts Worth Cherry-Picking

### 1. Single Policy Choke Point

Every consequential action should pass through one enforcement function before
execution. Adapters translate protocol-specific requests into a common request
shape; adapters do not make authorization decisions.

HUMMBL primitive candidate:

```text
PolicyGate.intercept(request) -> PolicyDecision
```

Required invariants:

- no bypass for governed writes,
- fail-closed for malformed requests,
- deterministic decision receipts,
- all denials include a policy reason,
- all escalations name the approving authority required.

### 2. Attenuation-Only Delegation

Delegated authority may only narrow the parent grant. A child grant cannot add
new actions, broaden resources, remove caveats, extend expiry, or reduce audit
requirements.

HUMMBL primitive candidate:

```text
DelegationGrant.child_of(parent).is_attenuated() == true
```

Required invariants:

- child actions are a subset of parent actions,
- child resources are equal or narrower,
- child expiry is not later than parent expiry,
- child caveats are equal or stricter,
- delegation depth is bounded.

### 3. Append-Only Evidence Ledger

Every gate decision should emit an append-only event with sequence, timestamp,
actor, request reference, decision, reason, previous hash, and current hash.

HUMMBL primitive candidate:

```text
EvidenceLedger.append(event) -> Receipt
EvidenceLedger.verify() -> VerificationResult
```

Required invariants:

- no update/delete correction path,
- corrections are new events,
- sequence numbers are monotonic,
- previous-hash linkage is checked,
- canonical serialization is fixture-tested across languages.

### 4. Bridge Adapter Pattern

External protocols should terminate at adapters that map into a HUMMBL request
shape. The adapter layer owns translation only. The policy layer owns decisions.

HUMMBL primitive candidate:

```text
Adapter.translate(external_call) -> GovernedRequest
PolicyGate.intercept(GovernedRequest) -> PolicyDecision
```

Required invariants:

- translation is deterministic,
- unknown operations map to deny or unsupported,
- adapter metadata is preserved in the decision receipt,
- adapter tests use canonical fixtures.

### 5. Conformance Matrix

Protocol claims should be backed by executable fixtures, not prose-only status.

HUMMBL primitive candidate:

```text
contracts/conformance.json
tests/fixtures/<domain>/<case>.json
```

Required invariants:

- each fulfilled row points to a fixture or test,
- each partial row names the missing evidence,
- each external-language binding declares which fixtures it passes,
- status labels distinguish designed, simulated, locally tested, and deployed.

## Proposed HUMMBL Names

These names avoid SINT vocabulary while preserving the useful structure.

| SINT-like concept | HUMMBL-owned term |
|---|---|
| Policy Gateway | Policy Gate |
| Capability Token | Delegation Grant |
| Evidence Ledger | Governance Receipt Ledger |
| Bridge | Adapter |
| Approval Tier | Consequence Tier |
| Conformance Certification Matrix | Fixture Conformance Matrix |

## Implementation Order

1. Define the shared request, decision, and receipt schemas in
   `hummbl-library`.
2. Add Python reference dataclasses and fixture round-trips.
3. Add Rust verifier support for receipt-chain verification.
4. Add TypeScript SDK/UI type validation only after schemas stabilize.
5. Add Go bindings only where a concrete `agy` or daemon surface needs them.

## Attribution Boundary

If a future change copies SINT source code or text, include Apache-2.0 license
preservation and file-level attribution. If a future change only implements the
general architectural ideas above, no SINT naming should appear in runtime
surfaces, public claims, package metadata, or user-facing documentation.

## Current Decision

Adopt/adapt the concepts. Do not depend on SINT. Do not claim collaboration.
Do not promote physical-AI claims without HUMMBL-owned validation evidence.
