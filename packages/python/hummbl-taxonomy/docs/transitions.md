# Tier Transitions

**Status:** Draft v0.2
**Last Updated:** 2026-05-26

## Purpose

This document defines how systems move between HUMMBL intelligence tiers and
what governance changes each transition requires.

Transitions are not branding events. They are governance events.

## Transition Summary

| Transition | Capability signal | Governance signal | Default decision |
| --- | --- | --- | --- |
| `ANI -> ASPI` | Domain breadth, adaptive tool use, novel in-domain cases | Correctness-only controls no longer suffice | ASPI review |
| `ASPI -> AGI` | Stable cross-domain transfer, weakening domain bounds | Domain-scoped guardrails no longer explain risk | Containment review |
| `AGI -> ASI` | Superhuman cross-domain strategic capability | Existing containment may be insufficient | Escalate as boundary event |

## ANI To ASPI

An ANI system should be reviewed for ASPI classification when it is no longer
best understood as one tool for one task.

Signals:

- many related tasks handled by one system,
- bounded autonomous execution,
- adaptive tool use,
- strong handling of novel in-domain cases,
- visible domain-local transfer,
- governance needs shift from correctness-only to authority, audit, and
  rollback.

Governance consequence:

- add delegated authority,
- add audit receipts,
- add budget/resource limits,
- add circuit breakers and stop conditions,
- add rollback paths,
- add promotion rules.

## ASPI To AGI

An ASPI system should be reviewed for AGI classification when domain-bounded
assumptions stop holding.

Signals:

- stable transfer between unrelated domains,
- reusable abstractions across distinct world models,
- new-goal decomposition outside prior specialization,
- autonomy that is no longer intelligible as domain-bounded,
- governance controls begin depending on containment rather than collaboration.

Governance consequence:

- tighten separation of authority,
- require stronger containment,
- increase independent review,
- reduce default autonomy,
- require stronger halt and rollback guarantees,
- treat promotion as constitutional, not opportunistic.

## AGI To ASI

HUMMBL treats AGI-to-ASI as a boundary doctrine because ASI is not a current
deployment assumption.

Signals would include superhuman cross-domain strategic performance and a
capability growth loop that outpaces existing governance controls.

Governance consequence:

- escalate to theoretical containment,
- deny autonomous promotion by default,
- require human/operator authority for every material expansion,
- preserve evidence for external review,
- treat unknowns as dominant until proven otherwise.

## Recursive Self-Improvement

RSI is a transition mechanism, not a tier.

Examples:

- `ANI -> ASPI`: AutoML, hyperparameter search, and workflow accumulation may
  turn a narrow tool into a domain system.
- `ASPI -> AGI`: domain-specific tool improvement and memory may weaken domain
  boundaries.
- `AGI -> ASI`: full recursive self-improvement is a theoretical route to
  superhuman strategic capability.

RSI must be governed by both capability and governability thresholds. A
capability improvement that reduces governability is not progress.

## Denial Conditions

Promotion should be denied or held when:

- evidence is incomplete,
- classification depends on one demo,
- governance status is unknown,
- rollback or halt path is missing,
- capability exceeds the current authority tier,
- independent review is missing,
- the system is asking to classify or promote itself.
