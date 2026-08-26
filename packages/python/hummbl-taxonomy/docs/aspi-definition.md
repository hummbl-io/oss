# Artificial Specific Intelligence

**Status:** Draft v0.2
**Last Updated:** 2026-05-26

## Definition

Artificial Specific Intelligence (ASPI) is an AI system that demonstrates
expert-level competence across a coherent domain or task class, including the
ability to reason about novel problems within that domain, transfer knowledge
between related subdomains, and improve its performance through experience,
tools, memory, or feedback, but which does not generalize to arbitrary domains
outside its scope.

## Why ASPI Exists

ANI and AGI do not describe many deployed frontier agent systems well.

Calling those systems ANI understates their transfer, autonomy, and domain
breadth. Calling them AGI overstates their generality and encourages the wrong
governance posture.

ASPI names the middle tier: domain-deep, bounded, useful, and governable.

## ASPI Evaluation Axes

| Axis | ANI | ASPI | AGI |
| --- | --- | --- | --- |
| Domain breadth | Single task | Coherent domain or task class | Arbitrary domains |
| Novelty handling | Weak outside expected patterns | Strong on novel in-domain cases | Strong across unrelated domains |
| Transfer | Little or none | Domain-local and adjacent | Cross-domain |
| Autonomy | Direct invocation | Guided autonomy with guardrails | Broader self-directed planning |
| World model | Task-local | Domain-specific | General |
| Governance posture | Deterministic control | Delegation, audit, reversibility, bounded autonomy | Containment-first |

## ASPI Governance Requirements

ASPI governance is the governance of bounded autonomous expertise.

An ASPI deployment should be able to answer:

- what domain the system may operate in,
- what mission authorizes current action,
- what actions it may take autonomously,
- what budget or resource envelope it may consume,
- what evidence supports its decisions,
- what policy version governs its action,
- what stops it when it degrades,
- what prevents it from escalating beyond domain or rung.

If these cannot be answered, the system may still be ASPI by capability, but it
is not governed ASPI.

## Governed ASPI

A governed ASPI system is an ASPI system whose capability may become action only
through:

- declared mission authority,
- explicit capability grants,
- append-only evidence receipts,
- reversible or stoppable execution,
- independent review for consequential changes,
- promotion rules for capability/rung escalation.

This is the target shape for governed agents.

## Boundary Tests

### ANI -> ASPI

Review for ASPI when:

- one system handles many related tasks in one domain,
- in-domain novelty handling becomes strong,
- transfer appears across adjacent subproblems,
- tool use becomes adaptive,
- governance shifts from correctness-only to authority, audit, and rollback.

### ASPI -> AGI

Review for AGI when:

- competence is no longer bounded by one domain family,
- cross-domain transfer is stable,
- world-model assumptions become general,
- the system can decompose new goals outside prior specialization,
- existing domain-scoped governance no longer explains the risk.

## Core Claim

ASPI is not a marketing label and not a rhetorical midpoint. It is the missing
operational tier where governed autonomy becomes economically and technically
real.
