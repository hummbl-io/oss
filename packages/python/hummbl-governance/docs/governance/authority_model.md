# HUMMBL Agent Fleet Authority Model

**Standard:** S8 #18 (structured authority model artifact)
**Issue:** #414 (gap-9)
**Federal standards:** NIST 800-53 AC-2 (Account Management), AC-5 (Separation of Duties), CM-3 (Configuration Change Control)
**Date:** 2026-08-27
**Status:** ACTIVE

## Purpose

This document defines who can authorize which classes of mutations, under
what scope, with what limits, and with what revocation path. It replaces
the heuristic markdown charter parsing (`str.split('|')` and substring
matching) in `AuthorityEngine` with a structured, machine-readable policy.

## Mutation classification

All fleet mutations are classified into four severity levels:

| Severity | Description | Examples |
|----------|-------------|----------|
| LOW | Read-only, informational, non-state-changing | bus post, status check, read API call, issue comment |
| MEDIUM | State-changing, reversible, non-destructive | commit, PR creation, PR merge (non-force), branch creation, label, close issue |
| HIGH | Destructive or hard-to-reverse | repo archive, branch/repo/file deletion, force-push, secret rotation, remove branch protection |
| CRITICAL | Org-level or cryptographic infrastructure | org-level setting change, signing key rotation, remove force-push protection fleet-wide |

## Authorization matrix

| Role | Trust tier | LOW | MEDIUM | HIGH | CRITICAL |
|------|-----------|-----|--------|------|----------|
| operator (human_reviewer) | 5 | auto | auto | with self-attestation | with self-attestation |
| devin (agent_author) | 2 | auto | with authority check | with DECISION receipt | with DECISION receipt |
| codex (agent_author) | 2 | auto | with authority check | with DECISION receipt | with DECISION receipt |
| claude-code (agent_author) | 2 | auto | with authority check | with DECISION receipt | with DECISION receipt |
| opencode (agent_author) | 2 | auto | with authority check | with DECISION receipt | with DECISION receipt |
| gemini (agent_author) | 2 | auto | with authority check | with DECISION receipt | with DECISION receipt |

**Legend:**
- **auto**: permitted automatically after identity resolution
- **with authority check**: permitted after `AuthorityEngine.check()` verifies scope and limit
- **with DECISION receipt**: two-person rule ΓÇö requires operator DECISION receipt (posted to bus with operator principal proof)
- **with self-attestation**: operator can self-attest (single-person authority for human reviewer)

## Two-person rule

For HIGH and CRITICAL mutations, the two-person rule applies:

1. The agent requests authorization by posting a PROPOSAL to the bus
2. The operator reviews and posts a DECISION receipt (requires operator principal proof)
3. The agent includes the DECISION receipt ID in the mutation gate call
4. The pre-mutation gate (gap-1) verifies the receipt before permitting

**Exception:** The operator (human_reviewer, tier 5) can self-attest for
HIGH/CRITICAL mutations ΓÇö the two-person rule is satisfied by the human
reviewer's own authority at tier 5.

## Scope and limits

### Per-role scope

| Role | Scope |
|------|-------|
| operator | All repos, all operations, all severities |
| devin | Assigned repos, operations within authority charter, up to HIGH with receipt |
| codex | Assigned repos, operations within authority charter, up to HIGH with receipt |
| claude-code | Assigned repos, operations within authority charter, up to HIGH with receipt |
| opencode | Assigned repos, operations within authority charter, up to HIGH with receipt |
| gemini | Assigned repos, operations within authority charter, up to HIGH with receipt |

### Per-role limits

| Role | Limits |
|------|--------|
| operator | None (full authority) |
| agent_author (all) | Cannot exercise HIGH/CRITICAL without operator DECISION receipt; cannot rotate keys; cannot change org-level settings; cannot remove branch protection |

## Revocation procedures

### Key revocation

1. Operator generates a new key (per GPG key generation runbook)
2. Update signing identity registry: set old key to `revoked`, add new key entry with `active`
3. Update git config and GitHub
4. Commit the registry update
5. Post REVOCATION notice to bus

### Authority revocation

1. Operator updates `authority_policy.json`: set role's `authorities` entry to `revoked: true`
2. The `AuthorityEngine` reads the structured policy and denies revoked authorities
3. Post REVOCATION notice to bus with affected agent and authority

### Agent suspension

1. Operator updates `identity_registry.json`: set agent's `status` to `suspended`
2. `IdentityEngine.resolve()` returns `None` for suspended agents
3. Pre-mutation gate blocks all mutations for suspended agents (identity not found)
4. Post SUSPENSION notice to bus

## Structured policy

The machine-readable policy is at `hummbl_governance/data/authority_policy.json`.
The `AuthorityEngine` loads this policy instead of parsing markdown charters.

### Policy schema

```json
{
  "schema_version": "1.0.0",
  "roles": {
    "<role_id>": {
      "trust_tier": <int>,
      "authorities": {
        "<authority_name>": {
          "scope": "<scope description>",
          "limit": "<limit description>",
          "max_severity": "LOW|MEDIUM|HIGH|CRITICAL",
          "requires_receipt": <bool>,
          "revoked": <bool>
        }
      }
    }
  }
}
```

## Integration with pre-mutation gate (gap-1)

The pre-mutation gate calls `AuthorityEngine.check()` which loads this
structured policy. The flow:

1. Gate resolves agent identity (pluggable resolver, gap-1)
2. Gate classifies mutation severity (gap-1)
3. Gate calls `AuthorityEngine.check()` with the structured policy
4. For HIGH/CRITICAL, gate verifies operator DECISION receipt (two-person rule)
5. Gate returns `GateDecision` (permitted/denied with reason)

## Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-27 | Initial authority model created (gap-9) | devin |
