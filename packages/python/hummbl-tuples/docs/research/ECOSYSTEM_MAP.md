# HUMMBL Ecosystem Map

Status: draft

## Purpose

Identify which HUMMBL repositories belong in the active ecosystem around:

- Base120
- BaseN
- tuples
- tiering and wickedness
- research and publication
- executable governance and assurance

## Canonical Core

These repos form the main technical and conceptual spine:

- `base120`
- `hummbl-governance`
- `mcp-server`
- `hummbl-agent`
- `hummbl-tuples`
- `HUMMBL-Unified-Tier-Framework`

## Research And Publication Layer

These repos support discovery, literature grounding, and publishable synthesis:

- `hummbl-research`
- `hummbl-bibliography`
- `hummbl-assurance`

## Operational And Proof Layer

These repos matter because they show execution, reproducibility, or real-world deployment:

- `hummbl-production`
- `governed-iac-reference`
- `hummbl-iac`

## Suggested Functional Roles

### `base120`

- canonical operator library
- transformation and mental-model substrate

### `hummbl-governance`

- contracts
- delegated authority
- runtime constraints
- evidence-first governance primitives

### `mcp-server`

- executable interface to Base120 and related HUMMBL capabilities

### `hummbl-agent`

- deterministic and policy-bounded agent infrastructure

### `hummbl-tuples`

- typed reasoning and governance tuple substrate
- BaseN reasoning-path semantics
- publication-oriented tuple research

### `HUMMBL-Unified-Tier-Framework`

- problem classification
- wickedness
- learning progression
- Base-N selection guidance

### `hummbl-research`

- active synthesis layer
- concept development
- exploratory framework work

### `hummbl-bibliography`

- source spine
- citation and reference infrastructure

### `hummbl-assurance`

- verification
- trust claims
- compatibility and compliance checks

### `hummbl-production`

- operational proof and real execution context

### `governed-iac-reference` / `hummbl-iac`

- infrastructure reproducibility
- governance-aware deployment patterns

## Recommended Ecosystem Story

The stack can be explained as:

1. `base120` provides the reasoning operators.
2. `HUMMBL-Unified-Tier-Framework` helps classify problems and choose reasoning scale.
3. `hummbl-tuples` makes reasoning and governance paths typed, inspectable, and publishable.
4. `hummbl-governance` and `hummbl-agent` make execution bounded and policy-aware.
5. `mcp-server` exposes the stack to agents and external tooling.
6. `hummbl-research` and `hummbl-bibliography` grow the knowledge and publication base.
7. `hummbl-assurance`, `hummbl-production`, and IaC repos provide evidence that the system can be trusted and operated.

## Secondary Or Historical

These may still matter, but they should not anchor the primary ecosystem story:

- `hummbl-dev-profile`
- `hummbl-mobile`
- `hummbl-cca-f`

## Working Rule

When adding a new repo to the ecosystem, decide explicitly which layer it belongs to:

- canonical core
- research/publication
- operational/proof
- secondary/historical

Avoid creating repos whose role is ambiguous across all four.
