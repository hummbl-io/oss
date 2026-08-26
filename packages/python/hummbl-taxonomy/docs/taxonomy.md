# HUMMBL Intelligence Taxonomy

**Status:** Draft v0.2
**Last Updated:** 2026-05-26

## Purpose

This is the canonical HUMMBL taxonomy for classifying AI systems by capability
scope and governance posture. It consolidates the local ANI, ASPI, and AGI
doctrine into one citable reference.

The taxonomy is useful only when classification changes governance assumptions.
It is not a naming exercise.

## Two Axes

HUMMBL separates two questions:

1. **Capability tier:** what kind of intelligence does the system exhibit?
2. **Governance status:** whether that capability may become action.

The first axis asks what the system can do. The second asks whether it may act
under mission authority, evidence, reversibility, review, and stop conditions.

## Capability Tiers

| Tier | Name | Scope | Governance posture | Current use |
| --- | --- | --- | --- | --- |
| `ANI` | Artificial Narrow Intelligence | One task or tightly bounded workflow | Deterministic control | Deployed baseline |
| `ASPI` | Artificial Specific Intelligence | One coherent domain or task class | Autonomy-with-guardrails | Primary governed-agent deployment tier |
| `AGI` | Artificial General Intelligence | Arbitrary domains | Containment-first | Future escalation tier |
| `ASI` | Artificial Superintelligence | Beyond human across arbitrary domains | Theoretical containment | Boundary doctrine only |

## ANI

Artificial Narrow Intelligence is optimized for one task, one narrow function,
or one tightly bounded workflow.

ANI systems usually have:

- narrow task scope,
- weak transfer outside that scope,
- low autonomous discretion,
- governance needs focused on correctness, reliability, misuse prevention, and
  access control.

The main ANI classification risk is leaving a system classified as ANI after it
has accumulated domain breadth, adaptive tool use, and bounded autonomy.

## ASPI

Artificial Specific Intelligence is an AI system that demonstrates expert-level
competence across a coherent domain or task class, including the ability to
reason about novel problems within that domain, transfer knowledge between
related subdomains, and improve its performance through experience, tools,
memory, or feedback, without generalizing to arbitrary domains outside its
scope.

ASPI systems usually have:

- coherent domain breadth,
- strong novel problem handling in-domain,
- transfer across adjacent subdomains,
- guided autonomy under guardrails,
- a domain-specific world model,
- governance needs centered on authority, auditability, reversibility,
  promotion control, and runtime stops.

ASPI is HUMMBL's primary near-term deployment tier for governed agents.

## AGI

Artificial General Intelligence is the candidate tier for systems whose
competence is no longer bounded by one coherent domain or task class.

AGI review begins when a system shows stable cross-domain transfer, general
world-model construction, new-goal decomposition outside prior specialization,
and autonomy that is no longer intelligible as domain-bounded.

AGI governance cannot be treated as scaled-up ASPI governance. The posture moves
from collaboration-first to containment-first.

## ASI

Artificial Superintelligence is the boundary tier for systems that would exceed
human performance across arbitrary domains and strategic horizons.

HUMMBL treats ASI as a boundary doctrine, not a current deployment assumption.
Its purpose in the taxonomy is to force explicit escalation and containment
thinking before systems approach superhuman strategic capability.

## Governed Status

Capability tier does not by itself make a system governed.

| Status | Meaning |
| --- | --- |
| `ungoverned` | Capability may act without sufficient mission authority, evidence, review, reversibility, or stop controls |
| `partially-governed` | Some controls exist, but at least one material requirement is missing |
| `governed` | Capability may become action only through declared mission authority, bounded capability grants, evidence receipts, independent review, and defined stop or rollback paths |

Examples:

- A spam classifier is usually `ANI / partially-governed` until evidence,
  monitoring, and misuse controls are in place.
- A coding agent with repo access is usually `ASPI / ungoverned` if it can
  mutate code without mission authority and review.
- A mission-bound coding agent with capability grants, receipts, review, and
  stop rules is `ASPI / governed`.

## The Whether Gate

The key governance question is not only whether a system can act. It is whether
it may act.

The minimum whether gates are:

| Gate | Question |
| --- | --- |
| `can_act` | Does the system have the relevant capability? |
| `may_act` | Is the action authorized under the current mission, policy, and capability grant? |
| `should_continue` | Does evidence still support continuing the mission? |
| `must_stop` | Has a stop, escalation, rollback, or review condition fired? |

If these gates cannot be answered from artifacts, the system should not be
classified as governed.

## Promotion Rule

Promotion between tiers is a governance event.

- `ANI -> ASPI`: review when the system stops being one tool for one task and
  starts showing domain breadth, transfer, adaptive tool use, or bounded
  autonomy.
- `ASPI -> AGI`: review when domain boundaries weaken and cross-domain transfer
  becomes stable.
- `AGI -> ASI`: treat as theoretical containment escalation until concrete
  evidence exists.

No system may self-promote. Promotion requires evidence, denial conditions, a
rollback or halt path, and independent review.

## Classification Rule

Classify by stable operating behavior under governance, not by brand, benchmark,
model size, or a single impressive demo.

Use the strongest stable tier supported across most dimensions:

- domain breadth,
- novelty handling,
- transfer,
- autonomy,
- world-model breadth,
- governance requirements.

When in doubt, classify conservatively and escalate for review.
