# STRIDE Threat Model Coverage Matrix — HUMMBL

**Standard**: STRIDE — Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege (Shostack, 2014)
**Source**: Shostack, A. (2014). *Threat Modeling: Designing for Security*. John Wiley & Sons. ISBN 978-1-118-80999-0
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

STRIDE is a **threat-modeling taxonomy**, not a regulation or certifiable standard. Coverage means HUMMBL provides primitives that mitigate the threat category at the platform layer; application-layer threat modeling, network-level controls, and OS-level hardening remain customer responsibilities.

## Summary

6 threat categories. **6 ✅ Fulfilled at platform layer.**

| Category | Threat | Coverage | Evidence |
|----------|--------|----------|----------|
| S | Spoofing | ✅ Fulfilled | `hummbl_governance/identity.py`, `hummbl_governance/stride_mapper.py` |
| T | Tampering | ✅ Fulfilled | `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |
| R | Repudiation | ✅ Fulfilled | `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |
| I | Information Disclosure | ✅ Fulfilled | `hummbl_governance/delegation.py`, `hummbl_governance/stride_mapper.py` |
| D | Denial of Service | ✅ Fulfilled | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/stride_mapper.py` |
| E | Elevation of Privilege | ✅ Fulfilled | `hummbl_governance/delegation.py`, `hummbl_governance/stride_mapper.py` |

---

## Per-category coverage

### S — Spoofing ✅

**Threat**: An attacker impersonates a legitimate agent or system to gain unauthorized access.

**HUMMBL coverage**:
- ✅ `AgentRegistry` with trust tiers (owner/high/medium/low/system/unknown) — unregistered agents default to lowest trust
- ✅ Alias resolution prevents identity confusion attacks
- ✅ Sender validation: bus messages from unapproved identities are rejected
- ✅ `StrideMapper._check_spoofing()` flags unauthenticated cross-boundary interactions as HIGH risk

**Evidence**: `hummbl_governance/identity.py`, `hummbl_governance/stride_mapper.py`

### T — Tampering ✅

**Threat**: An attacker modifies data, code, or system state without authorization.

**HUMMBL coverage**:
- ✅ Append-only JSONL audit log — entries cannot be modified or deleted
- ✅ HMAC-SHA256 signatures on audit entries detect tampering
- ✅ Entry immutability (frozen dataclass, UUID entry_id)
- ✅ Kill-switch state files signed with HMAC-SHA256; `verify_state_file()` detects tampering
- ✅ File permissions enforced at 0o600
- ✅ `StrideMapper._check_tampering()` flags mutation actions without audit trail

**Evidence**: `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/kill_switch.py`

### R — Repudiation ✅

**Threat**: An agent denies performing an action because there is no evidence linking the agent to the action.

**HUMMBL coverage**:
- ✅ Immutable audit entries with UUID IDs — every action is permanently attributed
- ✅ Amendment chains link outcomes to authorizing delegation tokens
- ✅ HMAC signatures provide cryptographic non-repudiation
- ✅ Cross-link validation (contract_id, capability_token_id) creates verifiable execution history
- ✅ `StrideMapper._check_repudiation()` flags actions without audit records

**Evidence**: `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py`

### I — Information Disclosure ✅

**Threat**: Sensitive information is exposed to unauthorized agents or systems.

**HUMMBL coverage**:
- ✅ Least-privilege delegation tokens with resource selectors — agents only access scoped resources
- ✅ Caveat constraints (TIME_BOUND, RATE_LIMIT, APPROVAL_REQUIRED, AUDIT_REQUIRED) limit data exposure
- ✅ Classification-tag enforcement at tuple ingress (cross-ref GDPR Art. 5, ISO 27001 A.5.12)
- ✅ Pseudonymisation tuple type + masking transforms
- ✅ `StrideMapper._check_information_disclosure()` flags cross-boundary access without delegation tokens

**Evidence**: `hummbl_governance/delegation.py`, `hummbl_governance/stride_mapper.py`

### D — Denial of Service ✅

**Threat**: An agent or attacker consumes excessive resources, degrading service availability.

**HUMMBL coverage**:
- ✅ Circuit breaker (CLOSED/HALF_OPEN/OPEN) fast-fails on unresponsive services — prevents cascading failures
- ✅ Cost governor with soft cap (WARN at 80%) and hard cap (DENY) — budget-based DoS prevention
- ✅ Kill switch 4-mode halt (DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY)
- ✅ RATE_LIMIT and TIME_BOUND caveats on delegation tokens
- ✅ `StrideMapper._check_denial_of_service()` flags actions without rate limiting

**Evidence**: `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/stride_mapper.py`

### E — Elevation of Privilege ✅

**Threat**: An agent gains privileges beyond what it was granted, accessing resources or performing actions it should not be allowed to.

**HUMMBL coverage**:
- ✅ Time-bound delegation tokens with HMAC signature verification — expired or forged tokens rejected
- ✅ Caveat enforcement constrains what a compromised agent could accomplish
- ✅ `check_least_privilege()` enforces minimum-necessary permissions
- ✅ Delegation-depth limit prevents indefinite privilege chain
- ✅ Trust tiers gate access-control decisions per agent identity
- ✅ `StrideMapper._check_elevation_of_privilege()` flags cross-boundary mutations without delegation tokens as CRITICAL

**Evidence**: `hummbl_governance/delegation.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/identity.py`

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Implementation: `hummbl_governance/stride_mapper.py` (StrideMapper, ThreatFinding, StrideReport)
- Security overlap with OWASP Agentic ASI03/ASI08 — see [`owasp-agentic.md`](./owasp-agentic.md)
- Privacy overlap with GDPR Art. 5/32 — see [`gdpr.md`](./gdpr.md)
- Access-control overlap with ISO 27001 A.5.15-A.5.18 — see [`iso-27001.md`](./iso-27001.md)
