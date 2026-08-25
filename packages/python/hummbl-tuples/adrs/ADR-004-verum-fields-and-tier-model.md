# ADR-004: Incorporate VERUM Fields and Tier Model into Tuple Envelope

Date: 2026-04-17
Updated: 2026-04-17
Status: accepted

## Context

The hummbl-tuples spec (TUPLES_v1, Mar 27) and the shipped BaseNTuple runtime (PR #473, Apr 17) diverged significantly. They represent two generations of thinking about the tuple envelope:

**TUPLES_v1 envelope** (spec, this repo):
```
tuple_type, timestamp, intent_id, task_id, tuple_data, [entry_id], [signature]
```

**BaseNTuple dataclass** (runtime, founder-mode):
```
id, time, state, drift,                         # VERUM 4-node
agent, tool, args_hash, evidence, tier,          # Governance
contract_id, dct_id, dct_chain_depth,            # Authority
previous_hash,                                   # Chain
signature                                        # Integrity
```

Key divergences:

1. **VERUM 4-node fields** (`id`, `time`, `state`, `drift`) — absent from spec schemas entirely. These are the theoretical foundation of HUMMBL's sovereignty claim.
2. **Tier model** (0-3) — absent from spec. The tier determines which fields are required, making it structurally load-bearing in the runtime.
3. **Lineage fields** (`intent_id`, `task_id`) — present in spec schemas but absent from BaseNTuple.
4. **Nesting model** — spec uses `tuple_data` wrapper object; BaseNTuple is flat.
5. **Name mismatches** — `entry_id` vs `id`, `timestamp` vs `time`.

The spec must evolve to reflect the runtime's lessons, or the runtime must be corrected to match the spec. Leaving them diverged means the publication artifact (this repo) doesn't represent the production system, undermining both the paper and the standard.

## Decision Options

### Option A: Spec absorbs BaseNTuple model (flat, VERUM-first)

Rejected. Forces flat model on all domains; loses `tuple_data` separation.

### Option B: BaseNTuple adapts to spec model (nested, type-discriminated)

Rejected. Buries VERUM fields (`state`, `drift`) inside `tuple_data`, undermining the theoretical claim that VERUM is foundational. The tier model has no home.

### Option C: Merge forward — uniform 8-field envelope

Rejected. Forces VERUM governance fields (`state`, `drift`, `tier`, `agent`, `tool`) onto research tuples (BaseN experiments, Bio-governance) where they have no semantic meaning. A `MODEL_SELECTED` tuple recording which Base120 model was picked doesn't meaningfully have `state: "ok"` or `drift: 0.3`.

### Option D: Layered convergence (accepted)

The envelope is structured in layers. Each tuple type declares which layers it participates in. Lower layers are universal; higher layers are domain-specific.

**Layer 1 — Universal** (all tuples):
```
tuple_type    string   REQUIRED   stable class identifier
id            string   REQUIRED   immutable record identifier (was entry_id)
time          string   REQUIRED   UTC ISO 8601 timestamp (was timestamp)
tuple_data    object   REQUIRED   type-specific payload
```

**Layer 2 — Governance** (IDP + runtime governance tuples only):
```
state         string   REQUIRED   outcome: "ok", "blocked", "error"
drift         number   REQUIRED   deviation from setpoint [0.0, 1.0]
tier          integer  REQUIRED   governance tier (0-3)
agent         string   REQUIRED   actor identity
tool          string   REQUIRED   namespaced tool name
```

**Layer 3 — Domain-specific** (per envelope family):
```
IDP:       intent_id, task_id
BaseN:     problem_id, run_id, control_mode
Nodezero:  run_id
Bio:       subject_id, run_id, control_mode
```

**Layer 4 — Integrity** (optional, any tuple):
```
args_hash       string   OPTIONAL   SHA-256 of canonical JSON args
signature       string   OPTIONAL   HMAC-SHA256 integrity marker
previous_hash   string   OPTIONAL   chain link (Tier 3 only)
contract_id     string   OPTIONAL   authority reference (Tier 2+)
dct_id          string   OPTIONAL   delegation token reference (Tier 2+)
dct_chain_depth integer  OPTIONAL   delegation depth (Tier 2+)
```

## Decision

**Option D: Layered convergence.**

Rationale:
- VERUM fields are first-class but only where they have semantic meaning
- Research/experiment tuples (BaseN, Bio) keep their domain envelopes without governance overhead
- The paper can demonstrate *judgment* about which tuples need governance
- The tier model is explicit in Layer 2 governance tuples
- Backward compatibility: existing schemas add 2 universal fields (`id`, `time`) and rename `timestamp`/`entry_id`
- The runtime BaseNTuple maps cleanly to Layer 1 + Layer 2 + Layer 4

## Migration Plan

### Phase 1: Spec
1. Write `docs/specs/TUPLES_v2.md` with layered envelope definition
2. Update `TUPLE_TAXONOMY.md` to reference layers and tier model

### Phase 2: Schemas
3. All 32 schemas gain Layer 1 fields (`id`, `time`) as required
4. IDP schemas (contract, dct, dctx, evidence, attest, system) gain Layer 2 fields
5. Rename `timestamp` → `time`, `entry_id` → `id` in IDP schemas
6. BaseN, Nodezero, Bio schemas retain their domain envelopes unchanged (Layer 3)
7. Layer 4 fields added as optional where relevant

### Phase 3: Examples + Validator + Tests
8. Update all 37 examples with `id` and `time` fields
9. Update IDP examples with `state`, `drift`, `tier`, `agent`, `tool`
10. Update validator to enforce Layer 1 + family-specific validation
11. Update Python classes and tests
12. `make validate` — all examples pass

### Phase 4: Runtime Sync (separate repo)
13. Add `tuple_type`, `intent_id`, `task_id` to BaseNTuple in founder-mode
14. Map BaseNTuple fields to Layer 1 + Layer 2 + Layer 4

## Consequences

- TUPLES_v1 becomes superseded (retained for git history)
- The spec and runtime converge for the first time
- The arXiv paper can cite a single coherent layered envelope
- Research tuples are not burdened with governance overhead
- The VERUM theoretical claim is testable against governance tuples specifically
- The distinction between "governed" and "observed" tuples becomes a publishable design choice

## Open Questions

- Should Bio-governance tuples adopt Layer 2? (Currently no — they describe biological signals, not governed decisions. If bio signals gain governance enforcement, they should upgrade.)
- Should `tuple_data` move to Layer 3? (No — it's universal. Every tuple needs a type-specific payload.)
