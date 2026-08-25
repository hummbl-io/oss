# HUMMBL Source Inventory

Canonical HUMMBL/Base120/BaseN constructs referenced by the crosswalk. Each
entry carries a verified authority locator.

## Base120 canonical kernel

**Authority locator:** `api/src/base120.ts` (SHA `5800ea8712b5e1a1b64d3e1687aab92b1895a78e`)
**Public surface:** `https://hummbl.io/glossary/base120`
**Status:** Immutable, open-source, 120 operators across 6 transformations.

### Transformations and representative models cited in the crosswalk

| Code | Name                                         | Transformation | Definition (verbatim from canon)                                                     |
| ---- | -------------------------------------------- | -------------- | ------------------------------------------------------------------------------------ |
| P3   | Identity Stack                               | Perspective    | Recognize that individuals operate from multiple nested identities simultaneously    |
| P5   | Empathy Mapping                              | Perspective    | Systematically capture what stakeholders see, think, feel, and do in their context   |
| P10  | Context Windowing                            | Perspective    | Define explicit boundaries in time, space, and scope for analysis or action          |
| P16  | Identity-Context Reciprocity                 | Perspective    | Recognize how identities shape interpretations and contexts reinforce identities     |
| IN7  | Boundary Testing                             | Inversion      | Explore extreme conditions to find system limits and breaking points                 |
| IN16 | Inverse Optimization                         | Inversion      | Maximize worst outcomes to understand system vulnerabilities                         |
| IN19 | Harm Minimization (Via Negativa)             | Inversion      | Improve by removing harmful elements rather than adding beneficial ones              |
| CO5  | Emergence                                    | Composition    | Recognize higher-order behavior arising from component interactions                  |
| CO13 | Cross-Domain Analogy                         | Composition    | Transfer solution patterns from one domain to solve problems in another              |
| CO15 | Combinatorial Design                         | Composition    | Systematically explore option combinations to find optimal configurations            |
| CO20 | Holistic Integration                         | Composition    | Unify disparate elements into coherent, seamless whole where boundaries dissolve     |
| DE11 | Scope Delimitation                           | Decomposition  | Define precise boundaries of what is included versus excluded from consideration     |
| DE17 | Orthogonalization                            | Decomposition  | Ensure factors vary independently without correlation or interdependence             |
| RE2  | Feedback Loops                               | Recursion      | Create mechanisms where system outputs influence future inputs                       |
| RE5  | Fractal Reasoning                            | Recursion      | Recognize self-similar patterns repeating across different scales                    |
| RE8  | Bootstrapping                                | Recursion      | Build capability using currently available resources, then use that to build more    |
| RE20 | Recursive Governance (Guardrails that Learn) | Recursion      | Establish rules that adapt based on their own effectiveness                          |
| SY2  | System Boundaries                            | Systems        | Define what is inside versus outside system scope for analysis or design             |
| SY8  | Homeostasis/Dynamic Equilibrium              | Systems        | Understand self-regulating mechanisms maintaining stable states despite disturbances |
| SY11 | Governance Patterns                          | Systems        | Design decision rights, accountability structures, and coordination mechanisms       |
| SY14 | Risk & Resilience Engineering                | Systems        | Build systems that fail gracefully and recover automatically                         |
| SY15 | Multi-Scale Alignment                        | Systems        | Ensure strategy, operations, and execution cohere across organizational levels       |
| SY20 | Systems-of-Systems Coordination              | Systems        | Manage interactions between independent systems with emergent behaviors              |

## BaseN generative framework

**Authority locator:** `web/glossary/basen.html`
**Public surface:** `https://hummbl.io/glossary/basen`
**Status:** Proprietary. Produces candidates; governance promotes them.

Key constructs:

- **Generative lattice framework.** Produces arbitrary N-sized operator and
  model lattices. No output is canonical merely because BaseN generated it.
- **Three-layer architecture.** Base120 (frozen OSS kernel) -> Domain120
  (field-specific ratified 6x20 lattices) -> BaseN (generative engine).
- **Promotion ladder.** Generated -> Candidate -> Curated -> Validated ->
  Ratified -> Published -> Deprecated. Each step requires explicit evidence.
- **"BaseN proposes, governance reviews, receipts prove."** No self-authorization.

## Governance primitives (hummbl-governance)

**Authority locator:** `web/primitives/` (8 marketed primitives)
**PyPI:** `hummbl-governance` v1.2.2, 34 primitives (26 core + 8 kernel sub-primitives)
**Public surface:** `https://hummbl.io/primitives/`

Primitives cited in the crosswalk:

| Primitive          | Public surface                           | Purpose                                                                       |
| ------------------ | ---------------------------------------- | ----------------------------------------------------------------------------- |
| Kill Switch        | `web/primitives/kill-switch.html`        | Four-mode emergency stop (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY). |
| Circuit Breaker    | `web/primitives/circuit-breaker.html`    | Failure isolation (CLOSED, HALF_OPEN, OPEN) with configurable thresholds.     |
| Delegation Tokens  | `web/primitives/delegation-tokens.html`  | Bounded authority tokens with scope, expiry, and receipt.                     |
| Delegation Context | `web/primitives/delegation-context.html` | Context payload carried with delegated authority.                             |
| Governance Bus     | `web/primitives/governance-bus.html`     | Append-only coordination message log.                                         |
| MCP Attestation    | `web/primitives/mcp-attestation.html`    | Cryptographic attestation of MCP tool provenance.                             |

## Internal constructs referenced by the issue (not on public surface)

These constructs are named in issue #751 but are not documented on the public
website. They are internal HUMMBL operating concepts. The crosswalk references
them where the issue specifically requests comparison, but marks their
authority locator as `INTERNAL_NOT_PUBLICLY_DOCUMENTED`.

| Construct                                                         | Authority locator                  | Notes                                                                                                                        |
| ----------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Frugal Activation                                                 | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Least-invasive governed intervention routing. Referenced in issue #751 H4.                                                   |
| Min-of-constituents constraint                                    | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Digital-twin composition limit. Referenced in issue #751.                                                                    |
| Digital-twin composition                                          | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Composing agent twins from constituent agents. Referenced in issue #751.                                                     |
| Agent lifecycle (quarantine, revalidation, rebinding, retirement) | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Degradation and recovery lifecycle. Referenced in issue #751.                                                                |
| Evidence graph                                                    | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Claim-posture distinction graph. Referenced in issue #751.                                                                   |
| "Cheapest correct model wins"                                     | `INTERNAL_NOT_PUBLICLY_DOCUMENTED` | Selection rule applied only after correctness, safety, privacy, reliability, and governance gates. Referenced in issue #751. |

## Verification method

All Base120 model definitions were read directly from `api/src/base120.ts`
on 2026-07-21. The file SHA matches the issue's referenced blob. All public
glossary and primitives pages were read from the working tree on the same
date. Internal constructs are marked as such; no public claim is made about
their exact semantics beyond what the issue text states.
