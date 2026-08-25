# HUMMBL Bus First-Principles Proposal

Scope: portable coordination bus and bridge | Authority: operator review | Status: PROPOSED

## Primitives and invariants

Primitives are actor, authenticated principal, sender claim, message, canonical
append authority, durable row, reader, request ID, evidence, queue, and reviewer.
The system must preserve one authoritative history, bounded and attributable
authority, append integrity, historical readability, deterministic compatibility,
and reversible deployment across variants.

## Retained D1 candidates

### FP-BUS-001 — One authoritative append

Statement: a coordination event has operational meaning only when exactly one
admitted authority appends it to the canonical history.

Whether-test: during every injected bridge, network, client, and disk failure,
does an acknowledged request produce exactly one canonical row and zero shadow
rows? Verification uses fault tests, request receipts, and path hashes.

Failure mode: split histories, duplicate action, or false acknowledgment.

### FP-BUS-002 — Authentication is not identity

Statement: possession of a transport credential cannot by itself authorize an
arbitrary sender identity or message authority.

Whether-test: can a shared bearer post as `human`, another agent, or a privileged
principal without an explicit mapping and proof? The required answer is no.

Failure mode: authenticated impersonation and meaningless provenance.

### FP-BUS-003 — Evidence precedes privileged effect

Statement: a privileged message cannot enter canonical history unless its live,
fresh, principal-bound authority evidence is verified before append.

Whether-test: are unsigned, stale, replayed, unknown-key, offline-spooled, and
legacy-transport privileged requests rejected before append?

Failure mode: durable authority is created from an unverifiable assertion.

### FP-BUS-004 — Compatibility is an evidence claim

Statement: two versions are compatible only in a stated direction and scope that
has passed shared conformance evidence.

Whether-test: does every compatibility edge name versions, direction, artifacts,
behavior, fixtures, and results? Unknown compatibility must fail closed.

Failure mode: ordinal version assumptions silently corrupt interoperability.

### FP-BUS-005 — History remains interpretable

Statement: evolution cannot make retained canonical evidence unreadable or
change its original meaning.

Whether-test: can the current supported reader verify every retained golden and
archive corpus without rewriting historical rows?

Failure mode: an append-only ledger becomes operationally mutable through parser
obsolescence.

### FP-BUS-006 — Acknowledgment implies durability

Statement: a successful write receipt must correspond to the promised durable
state, not merely a userspace buffer mutation.

Whether-test: after crash injection at every write boundary, does each acknowledged
request remain recoverable exactly once and each unacknowledged request have an
unambiguous retry outcome?

Failure mode: success claims diverge from recoverable state.

## Derived policies, not first principles

- Five-column TSV is a current wire policy and mechanism, not a timeless axiom.
- Stdlib-only is a package policy; optional security extras may justify explicit
  dependencies without violating the deeper authority and evidence invariants.
- HMAC `{c,n,s}` is a mechanism. The invariant is verifiable integrity bound to
  appropriate identity and context.
- Tailscale-only reachability is a deployment policy, not identity proof.
- One canary at a time is an SRE procedure that protects attributable evidence.

## Stress tests

The candidates survive offline clients, multiple operating systems, bridge
replacement, schema evolution, and alternate cryptography. They do not require
hummbl-governance, a specific vendor, or a particular file path. FP-BUS-001 must not
be misread as requiring a single physical server; it requires one admitted
authority per event. FP-BUS-005 permits explicit archive adapters rather than
forcing every future hot path to carry every historical implementation.

## Adoption gate

These principles remain proposals until the operator reviews them alongside the
wire contract, threat model, compatibility matrix, and representative negative
tests. Adoption must be a separate signed decision; this planning PR cannot
self-canonize them.
