# Governance Per Tier

**Status:** Draft v0.2
**Last Updated:** 2026-05-26

## Purpose

This document defines the governance posture each HUMMBL intelligence tier
requires.

Capability tier is not the same as governed status. A system can be ANI, ASPI,
AGI, or ASI and still be ungoverned.

## Governance Status

| Status | Minimum meaning |
| --- | --- |
| `ungoverned` | Capability can become action without sufficient mission authority, evidence, review, reversibility, or stop controls |
| `partially-governed` | Some controls exist, but material requirements are missing |
| `governed` | Capability becomes action only through mission authority, bounded grants, receipts, review, and stop or rollback paths |

## Tier Matrix

| Tier | Main risk | Required posture | Primary whether question |
| --- | --- | --- | --- |
| `ANI` | brittle narrow tool used incorrectly | deterministic control | whether the tool is correct and safe enough to invoke |
| `ASPI` | bounded expert acts beyond authority | autonomy-with-guardrails | whether the agent may act inside bounded domain authority |
| `AGI` | general actor escapes domain assumptions | containment-first | whether the system remains governable while generalizing |
| `ASI` | superhuman strategic capability exceeds containment | theoretical containment | what containment regime could be adequate |

## ANI Governance

ANI governance usually requires:

- correctness checks,
- misuse prevention,
- access control,
- output validation,
- monitoring for distribution shift,
- rate limits or quota controls where needed.

ANI usually does not require full runtime constitutional machinery while it
remains truly narrow.

## ASPI Governance

ASPI governance requires:

- declared mission authority,
- explicit delegated authority,
- bounded autonomy,
- audit/evidence receipts,
- cost and resource controls,
- circuit breakers,
- kill switches or stop states,
- rollback paths,
- promotion policy.

ASPI systems should not escalate themselves from local testing to public,
production, cloud, cluster, or organizational authority without policy approval.

## AGI Governance

AGI governance requires containment-first assumptions because domain bounds no
longer provide the primary safety boundary.

Required controls include:

- separation of search, execution, and governance authority,
- strong promotion law,
- governability scoring,
- human/operator review triggers,
- artifact manifests,
- rollback/halt paths,
- shadow evaluation of governance policy,
- denial when capability outpaces governability.

## ASI Governance

ASI governance is boundary doctrine. Do not claim deployable ASI controls as
validated.

Minimum posture:

- explicit uncertainty,
- denial-by-default for autonomous promotion,
- containment-first review,
- evidence preservation,
- external/independent review for any material claim,
- no self-authorization or self-modification without law.

## The Whether Gate

Every governed system should expose four decisions:

1. `can_act`: capability exists.
2. `may_act`: authority and policy permit action.
3. `should_continue`: evidence still supports continuing.
4. `must_stop`: stop, escalation, rollback, or review condition has fired.

The gap between `can_act` and `may_act` is where governance lives.
