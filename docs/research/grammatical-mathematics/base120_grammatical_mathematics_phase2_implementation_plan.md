# Base120 Grammatical-Mathematics Phase 2 Implementation Plan

**Status:** `experimental_not_canonical`
**Issue:** [hummbl-production#773](https://github.com/hummbl-io/hummbl-production/issues/773)
**Source corpus:** `base120_grammatical_mathematics_seed20_corpus.json`
**Base120 blob SHA:** `5800ea8712b5e1a1b64d3e1687aab92b1895a78e`

## 1. Scope and authority boundary

This is a research-only, library-only Phase 2 Seed20 grammatical-mathematics
interpreter. It does **not** promote a law, alter ontology, or change Base120
canon.

- `api/src/base120.ts` is immutable canon: byte-for-byte unchanged.
- Experimental signatures are hypotheses that resolve canonical Seed20 models
  through `getModelByCode`; no canonical names or definitions are duplicated.
- The implementation is deterministic/static: no LLM calls, no public HTTP
  endpoint, no automatic semantic scoring, no weighted aggregate evaluator,
  no ontology mutation, no canon promotion.

## 2. Seed20 model selection

20 models selected from Base120's 120, balanced across 6 transformations:

| Domain          | Count | Codes                 |
| --------------- | ----- | --------------------- |
| Frame (P)       | 3     | P1, P10, P17          |
| Inverse (IN)    | 3     | IN3, IN7, IN18        |
| Composite (CO)  | 2     | CO1, CO5              |
| Decomposer (DE) | 4     | DE1, DE5, DE7, DE11   |
| Recursive (RE)  | 4     | RE1, RE6, RE8, RE20   |
| System (SY)     | 4     | SY2, SY11, SY18, SY19 |

Selection criteria: every gold experiment (GM-000 through GM-014) has its
required models in the set. Coverage across all 6 transformations. No
transformation over-represented relative to its experimental load.

## 3. Relation vocabulary

| Symbol | Name                               | Description                                      |
| ------ | ---------------------------------- | ------------------------------------------------ |
| ∘      | compose (sequential ladder)        | Sequential: output of A feeds into B             |
| ⊗      | parallel (parallel lattice)        | Parallel: A and B run, results joined            |
| map    | map (explicit collection lift)     | Explicit named lift over a collection            |
| κ      | closure                            | Close over output to create reusable abstraction |
| μ      | fixedpoint (recursive/fixed-point) | Recursive application until fixpoint, depth 1..3 |
| ⊥      | barrier (type barrier)             | No valid composition; type incompatibility       |

**Collection lifting must be an explicit named `map`, never a silent coercion.**

## 4. Type system

### 4.1 Semantic types (experimental)

Each Seed20 model has an experimental signature with:

- `input_types`: which semantic types it can accept
- `output_type`: the semantic type it produces
- `max_recursion_depth`: 1..3

Six domain types: `Frame`, `Inverse`, `Composite`, `Decomposer`, `Recursive`,
`System`.

### 4.2 Closed subtype graph

20 subtypes (one per model), organized under 6 domain types under a top
`Model` type. The graph is **closed**: no extension is possible at runtime.

```
Model
├── Frame
│   ├── Frame.FirstPrinciples (P1)
│   ├── Frame.Contextual (P10)
│   └── Frame.Reframing (P17)
├── Inverse
│   ├── Inverse.Reversal (IN3)
│   ├── Inverse.Boundary (IN7)
│   └── Inverse.KillCriteria (IN18)
├── Composite
│   ├── Composite.Synergy (CO1)
│   └── Composite.Emergent (CO5)
├── Decomposer
│   ├── Decomposer.Causal (DE1)
│   ├── Decomposer.Dimensional (DE5)
│   ├── Decomposer.Pareto (DE7)
│   └── Decomposer.Scope (DE11)
├── Recursive
│   ├── Recursive.Improvement (RE1)
│   ├── Recursive.Meta (RE6)
│   ├── Recursive.Bootstrap (RE8)
│   └── Recursive.Governance (RE20)
└── System
    ├── System.Boundary (SY2)
    ├── System.Governance (SY11)
    ├── System.Telemetry (SY18)
    └── System.Meta (SY19)
```

### 4.3 Domain compatibility matrix

Determines the default relation for cross-domain pairs:

| A \ B      | Frame | Inverse | Composite | Decomposer | Recursive | System |
| ---------- | ----- | ------- | --------- | ---------- | --------- | ------ |
| Frame      | ∘     | ∘       | map       | map        | ∘         | ∘      |
| Inverse    | ∘     | ∘       | ⊥         | ⊥          | ⊥         | ∘      |
| Composite  | ∘     | ⊥       | ⊗         | ∘          | ⊥         | ∘      |
| Decomposer | ∘     | ⊥       | ∘         | ∘          | ⊥         | ∘      |
| Recursive  | ∘     | ∘       | ⊥         | ⊥          | μ         | ∘      |
| System     | ∘     | ⊥       | ⊥         | ⊥          | ⊥         | ∘      |

### 4.4 Subtype-level type barriers

Specific subtype pairs that override domain compatibility:

| Source subtype       | Target subtype         | Relation | Reason                                           |
| -------------------- | ---------------------- | -------- | ------------------------------------------------ |
| Inverse.KillCriteria | Recursive.Bootstrap    | ⊥        | Terminate-then-generate is type-invalid (GM-001) |
| Inverse.KillCriteria | Recursive.Improvement  | ⊥        | Kill criteria blocks improvement recursion       |
| Decomposer.Pareto    | Decomposer.Dimensional | ⊥        | Reduction of a reduction is void                 |

## 5. Module structure

```
api/src/grammatical-math/
├── types.ts          # Semantic types, subtypes, signature interfaces
├── seed20.ts         # SEED20_CODES, signature metadata, canonical resolution
├── subtype-graph.ts  # Closed subtype graph (no extension)
├── relations.ts      # Relation vocabulary, domain compat, subtype barriers
├── matrix.ts         # 20×20 pair matrix, relation counts
├── constructors.ts   # Deterministic expression constructors (∘, ⊗, map, κ, μ)
├── typechecker.ts    # Strong type checker, recursion depth 1..3
├── receipts.ts       # Six-field promotion receipt validation
├── experiments.ts    # GM-000 through GM-014 gold experiments
└── index.ts          # Library-only exports (no public endpoint)
```

## 6. Expression constructors

All constructors are deterministic and strongly typed:

- `compose(a, b)` — sequential ladder. Requires `output_type(a) ∈ input_types(b)`.
- `parallel(a, b, joinName)` — parallel lattice. Requires explicit named join.
- `map(model, collectionName)` — explicit collection lift. Requires named collection.
- `closure(model)` — close over output. Same-model application.
- `fixedpoint(model, depth)` — recursive application. Depth must be 1..3; 4 is rejected.

**No hidden adapters, coercions, or collection lifts.** `map` and parallel
joins require explicit named inputs.

## 7. Type checker

The type checker verifies:

1. All model codes resolve through canonical `getModelByCode`.
2. Input/output type compatibility for each composition.
3. Recursion depth is bounded 1..3; depth 4 is rejected.
4. No silent coercions or hidden adapters.
5. `map` requires an explicit named collection.
6. `parallel` requires an explicit named join.

## 8. Promotion receipts

Six-field receipt:

| Field                     | Type           | Description                                     |
| ------------------------- | -------------- | ----------------------------------------------- |
| `experiment_id`           | string         | e.g., "GM-000"                                  |
| `result`                  | string         | e.g., "valid", "type_invalid", "noncommutative" |
| `evidence`                | string         | Deterministic proof trace                       |
| `timestamp`               | string         | ISO 8601                                        |
| `external_human_approval` | string \| null | Approver identifier, or null                    |
| `receipt_hash`            | string         | SHA-256 of the above five fields                |

**Ratification requires `external_human_approval` to be present and non-null.**
Missing approval prevents ratification. The module cannot self-authorize.

## 9. Gold experiments

15 experiments (GM-000 through GM-014), including negative results:

| ID     | Name                             | Expected result             | Failure expected? |
| ------ | -------------------------------- | --------------------------- | ----------------- |
| GM-000 | Seed instantiation               | valid                       | No                |
| GM-001 | Type barrier                     | type_invalid                | **Yes**           |
| GM-002 | Lattice correction with join     | valid_with_join             | No                |
| GM-003 | Context-decomposition commutator | noncommutative              | No                |
| GM-004 | Double problem reversal          | non_involutive              | No                |
| GM-005 | Context idempotence              | conditional                 | No                |
| GM-006 | System-boundary idempotence      | conditional                 | No                |
| GM-007 | Decompose-recompose conservation | partial_conservation        | No                |
| GM-008 | Governance-telemetry order       | noncommutative              | No                |
| GM-009 | Boundary alternation             | candidate                   | No                |
| GM-010 | Recursive meta-model selection   | local_fixed_point           | No                |
| GM-011 | Generate then terminate          | order_constrained           | No                |
| GM-012 | Recursive evaluator governance   | valid_externally_authorized | No                |
| GM-013 | Output vs receipt equivalence    | distinction_preserved       | No                |
| GM-014 | Reduce/search commutator         | noncommutative              | No                |

Natural-language semantic findings remain fixture assertions; no fabricated
deterministic calculations for them.

## 10. Local validation plan

1. `npm --prefix api run test:run` — all tests pass
2. `npm --prefix api run lint` — no lint errors
3. `npm --prefix api run format:check` — prettier passes
4. `npx --prefix api tsc --noEmit` — type checking passes
5. `api/src/base120.ts` SHA unchanged
6. No endpoint, schema, or documentation leaks
7. All 15 GM experiments produce expected results
8. Recursion depth 4 is rejected
9. GM-001 type barrier is an expected failure
10. Promotion receipts without external approval cannot ratify

## 11. Execution constraints

- **Run validation locally only.** Do not open a branch PR.
- The repository has GitHub-hosted `pull_request` workflows; even a draft PR
  can consume prohibited Actions minutes.
- Preserve local test receipts and postpone branch push/PR creation until
  the restriction is lifted or the relevant workflows are converted to
  approved self-hosted execution.
