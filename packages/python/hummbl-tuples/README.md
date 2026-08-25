# HUMMBL Typed Tuples

[![PyPI](https://img.shields.io/pypi/v/hummbl-tuples)](https://pypi.org/project/hummbl-tuples/)

Typed governance tuples for bounded delegation, evidence, and execution control in AI-native systems.

**The governance tuple is the minimal atomic record that proves a governed AI decision happened — not that someone claimed it did.**

## Scientific Grounding

This repo also defines the tuple pattern for scientific grounding:

- `EVIDENCE` for source-grounding and claim-linkage events
- `ATTEST` for distinct verifier review of that evidence
- `PROMOTION_RECEIPT` only for later promotion decisions

See [SCIENTIFIC_GROUNDING.md](SCIENTIFIC_GROUNDING.md) and the examples:

- `examples/evidence.scientific-source-grounded.json`
- `examples/attest.scientific-source-grounded.json`

## Layered Envelope (TUPLES v2)

All tuples use a layered envelope. Lower layers are universal; higher layers apply only where governance semantics are needed.

| Layer | Fields | Applies to | Purpose |
|-------|--------|-----------|---------|
| **1 — Universal** | `tuple_type`, `id`, `time`, `tuple_data` | All tuples | Identity + temporality |
| **2 — Governance** | `state`, `drift`, `tier`, `agent`, `tool` | IDP governance tuples | Outcome + deviation (VERUM-aligned) |
| **3 — Domain** | Per-family fields | Each family independently | Domain-specific semantics |
| **4 — Integrity** | `signature`, `args_hash`, `previous_hash` | Optional, any tuple | Tamper evidence + chain linkage |

VERUM's 4 node fields (`id`, `time`, `state`, `drift`) are deliberately split: `id`/`time` establish *existence* (universal), while `state`/`drift` establish *judgment* (governance-specific). See [TUPLES_v2.md](docs/specs/TUPLES_v2.md) §8 for the rationale.

## Tuple Taxonomy

Six governance tuple types (Layer 1 + 2 + 3/IDP):

| Type | Role |
|------|------|
| `CONTRACT` | Bounded work definition — objective, allowed tools, evidence requirements |
| `DCT` | Delegated capability token — authority issuance with monotonic attenuation |
| `DCTX` | Delegation context — lifecycle state machine and parent-child linkage |
| `SYSTEM` | Runtime control-plane event — adapter invocation, enforcement, denial |
| `EVIDENCE` | Execution proof — completion outcome, cost, duration |
| `ATTEST` | Verification outcome — evidence hash, verifier identity, pass/fail |

Two additional governance-control tuple types are included for distributed
mesh operations:

| Type | Role |
|------|------|
| `PROMOTION_RECEIPT` | Governed promotion decision across environments or trust/compute rungs |
| `REVOCATION` | Explicit withdrawal of delegated authority |

Plus three research/experiment families (Layer 1 + 3, no governance overhead):

- **BaseN** (8 types): reasoning experiment instrumentation
- **Nodezero** (4 types): experiment control tuples
- **Bio** (11 types, experimental): bio-cognitive signal tuples

## Quick Start

```bash
# Validate all examples against schemas
make validate

# Run the test suite
make test

# Run the governance simulation
make simulate
python3 test_simulation.py
```

Requires Python 3.10+. Zero third-party runtime dependencies (stdlib only).

Canonical versioned taxonomy:

- [TYPED_TUPLE_TAXONOMY.md](docs/specs/TYPED_TUPLE_TAXONOMY.md)

## Repo Layout

```
docs/specs/          Canonical tuple specs (TUPLES_v2 is current)
schemas/             JSON Schemas for tuple classes (21 core)
schemas/experimental Bio-governance schemas (11, not yet promoted)
examples/            Sanitized tuple examples (26 fixtures)
hummbl_tuples/       Python reference implementation
  simulation/        Deterministic governance simulation prototype
reference_impl/      Stdlib-only validators
comparisons/         Tuple vs adjacent approaches
research_notes/      Hypotheses, experiments, open questions
novelty_quest/       Candidate claims, objections, negative results
adrs/                Architectural decision records (4 ADRs)
```

## Governance Simulation

A deterministic rule-based governance simulator exercises the tuple schemas as an execution surface. It models a multi-agent system with delegation, probation, scope denial, and recovery — producing 29-event traces that validate against the JSON Schemas.

```bash
make simulate                                          # scalar trace summary
python3 -m hummbl_tuples.simulation --out /tmp/trace.json  # full JSON trace
python3 test_simulation.py                             # regression assertions
```

The simulator is bitwise-deterministic under a fixed seed, enabling reproducible parameter sweeps.

## Publication

This repo is the companion artifact for:

- **"The Governance Tuple: An Atomic Record for Auditable Agentic AI Decision-Making"** — formalizes the (CONTRACT, DCT, EVIDENCE) triple and proves four accountability properties
- **"A Typed Delegation-Governance Tuple Profile for Multi-Agent Runtime Control"** (CRAI 2026) — the six-tuple IDP profile with composability evidence
- **"Append-Only as Proof"** — the VERUM governance sovereignty framework

ORCID: [0009-0002-5620-1103](https://orcid.org/0009-0002-5620-1103)

## Key Design Decisions

| ADR | Decision |
|-----|----------|
| [ADR-001](adrs/ADR-001-create-dedicated-tuple-repo.md) | Create a dedicated tuple spec repo |
| [ADR-002](adrs/ADR-002-repo-scope.md) | Scope: spec + research, not runtime |
| [ADR-003](adrs/ADR-003-governance-simulation-mvp.md) | Governance simulation as research instrument |
| [ADR-004](adrs/ADR-004-verum-fields-and-tier-model.md) | Layered convergence (VERUM + tier model) |

## Related

- **Runtime implementation**: the production `BaseNTuple` dataclass lives in a separate repo (HMAC-SHA256 signing, JSONL persistence, tier classification as policy-as-code)
- **VERUM**: append-only audit sovereignty framework — 4 invariants for governance proof
- **Base120**: governed reasoning vocabulary — 120 operators in 6 families

## License

Apache 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
