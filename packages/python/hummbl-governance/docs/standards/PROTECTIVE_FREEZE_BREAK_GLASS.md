# Protective Freeze and Break-Glass Revocation Primitives

Status: candidate primitive design note for issue #149.
Last updated: 2026-07-03.

This document is public-safe. It does not contain live credentials, token
values, private account internals, or production revocation instructions. The
primitive names remain candidate until namespace audit and approval.

## Purpose

Incident-time controls need to be strong enough to stop high-risk mutation, but
bounded enough to avoid unreviewed lockouts, irreversible availability harm, or
credential churn without a recovery path.

This design note defines four candidate primitives:

- `PROTECTIVE_FREEZE`
- `BREAK_GLASS_REVOKE`
- `RECOVERY_RECEIPT`
- `HUMAN_REENABLE_REQUIRED`

## Candidate Semantics

### `PROTECTIVE_FREEZE`

Intent: prevent mutation on a protected surface after a high-risk trigger.

Required fields:

- protected surface;
- freeze trigger;
- allowed scope;
- blocked actions;
- default duration or explicit expiry;
- override authority;
- receipt path;
- human re-enable rule.

Pass condition: freeze scope, duration, authority, and recovery route are all
declared before the freeze is applied.

Fail condition: freeze is open-ended, overbroad, self-approved by the actor that
triggered it, or missing a re-enable path.

### `BREAK_GLASS_REVOKE`

Intent: revoke or disable credentials, tokens, keys, or connector grants during
an incident.

Required fields:

- incident identifier;
- asset references, not raw credential values;
- approver;
- revocation scope;
- rollback or restoration route;
- post-revocation validation;
- monitoring window;
- receipt path.

Pass condition: revocation target is bounded, approved, recoverable, and
validated without exposing secret material.

Fail condition: raw tokens are copied into the receipt, scope is `all assets`
without approval, or recovery path is absent.

### `RECOVERY_RECEIPT`

Intent: make incident recovery reviewable after freeze or revocation.

Required fields:

- incident identifier;
- revoked or frozen asset references;
- freeze window;
- authority chain;
- validation steps;
- restored assets;
- assets intentionally left disabled;
- residual risk;
- post-restore monitoring plan.

Pass condition: a reviewer can determine what changed, who approved it, how it
was validated, and what remains risky.

Fail condition: the receipt says only that an incident was handled, without
asset scope, authority, validation, or residual-risk evidence.

### `HUMAN_REENABLE_REQUIRED`

Intent: prevent automatic re-enable for sensitive credentials and protected
publishing surfaces.

Required fields:

- applies-to list;
- minimum reviewer role or count;
- evidence required;
- post-restore monitoring;
- expiry or follow-up issue.

Pass condition: a human reviewer approves re-enable after validation evidence is
available.

Fail condition: automation re-enables sensitive access without review, or a
single author re-enables their own high-consequence surface.

## Dry-Run Surfaces

| Surface | Example trigger | Freeze action | Revoke action | Required recovery route |
|---|---|---|---|---|
| Package publishing | suspicious package metadata or release anomaly | block publish workflow and release tags | rotate package publishing token reference | verify new token, dry-run publish metadata, human re-enable |
| Agent credentials | agent identity or scope compromise | disable agent write capabilities | revoke agent token reference | reissue scoped credential, validate identity, monitor bus and repo activity |
| Repository tokens | leaked or overprivileged repo token reference | block protected workflow mutation | revoke token reference or GitHub app grant | restore least-privilege token, verify branch protections and workflow checks |
| Connector credentials | connector grant suspected compromised | pause connector write operations | revoke connector grant reference | reconnect with scoped grant, validate no private data leakage |

## Adversarial Fixtures

The fixture file includes rejected cases for:

- overbroad revoke;
- missing recovery path;
- missing human approval;
- token leakage marker.

These are dry-run examples only. They do not carry live credential material.

## Required Gates Before Live Integration

1. Namespace audit promotes or renames the candidate primitive names.
2. Receipt schema is reviewed and either adopted or replaced.
3. Dry-run fixtures pass validation without exposing credential values.
4. Tabletop drill verifies freeze, revoke, recovery, and human re-enable flow.
5. Operator or delegated incident authority approves any live integration.

## Out of Scope

- No live credential revocation.
- No package publishing freeze.
- No connector mutation.
- No repository settings mutation.
- No production policy enforcement.
