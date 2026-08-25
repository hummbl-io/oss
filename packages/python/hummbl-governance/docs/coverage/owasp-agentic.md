# OWASP Agentic Top 10 Coverage Matrix — HUMMBL

**Standard**: OWASP Top 10 for Agentic Applications (December 2025) — ASI01 through ASI10
**Source**: https://owasp.org/www-project-agentic-threats/
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

OWASP Agentic Top 10 is a **risk catalog**, not a regulation. No certification. Coverage means HUMMBL provides primitives that detect, prevent, or mitigate the risk at the platform layer; application-layer prompt engineering, execution sandboxing, and product-level safety controls remain customer responsibilities.

## Summary

10 risk categories. **6 ✅ Fulfilled at platform layer · 3 🟡 Partial (require app-layer completion) · 1 ⚪ Boundary (execution sandbox layer).**

| ID | Risk | Coverage | Evidence |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | ✅ Fulfilled | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/stride_mapper.py` |
| ASI02 | Tool Misuse | 🟡 Partial | `hummbl_governance/schema_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| ASI03 | Identity & Privilege Abuse | ✅ Fulfilled | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/compliance_mapper.py` |
| ASI04 | Supply Chain | ✅ Fulfilled | `hummbl_governance/schema_validator.py`, `hummbl_governance/identity.py`, `.github/workflows/ci.yml` |
| ASI05 | Unexpected Code Execution | ⚪ Boundary | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| ASI06 | Memory & Context Poisoning | 🟡 Partial | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py`, `hummbl_governance/kill_switch.py` |
| ASI07 | Insecure Inter-Agent Comms | ✅ Fulfilled | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`, `hummbl_governance/compliance_mapper.py` |
| ASI08 | Cascading Failures | ✅ Fulfilled | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/compliance_mapper.py` |
| ASI09 | Human-Agent Trust Exploitation | 🟡 Partial | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| ASI10 | Rogue Agents | ✅ Fulfilled | `hummbl_governance/kill_switch.py`, `hummbl_governance/identity.py`, `hummbl_governance/circuit_breaker.py` |

---

## Per-category coverage

### ASI01 — Agent Goal Hijack ✅

**Risk**: An attacker manipulates an agent's planning or goal-setting to redirect it toward malicious objectives, often through crafted inputs or adversarial prompts.

**HUMMBL coverage**:
- ✅ INTENT-tuple lifecycle: every agent action carries a declared objective; goal-hijack-induced behavior deviates from INTENT and triggers governance bus anomaly detection
- ✅ `generate_owasp_report()` maps ASI01 from INTENT tuples — proves lifecycle traceability
- ✅ Kill switch 4-mode halt (DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY) for runaway agents
- ✅ Delegation tokens bound to specific agent and context via `TokenBinding` — hijacked agent's tokens are scope-limited
- ✅ Time-bound expiry limits window of exploitation
- ✅ STRIDE Elevation of Privilege check flags cross-boundary mutations without delegation tokens

**Evidence**: `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/stride_mapper.py`

### ASI02 — Tool Misuse 🟡

**Risk**: An agent calls tools with malicious, incorrect, or unintended parameters, causing harmful side effects.

**HUMMBL coverage**:
- ✅ Schema validation: validates tool input/output against JSON Schema — enforces type, required fields, enum constraints, pattern matching, numeric bounds
- ✅ Delegation caveats can require APPROVAL_REQUIRED before tool execution
- ✅ Token binding ties permissions to a specific agent context
- ✅ Full audit trail of all tool invocations via DCTX/EVIDENCE tuple types
- 🟡 No runtime parameter sanitization or allowlist-based tool filtering — schema validation is structural, not semantic; cannot detect syntactically valid but contextually harmful parameters

**Evidence**: `hummbl_governance/schema_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py`

### ASI03 — Identity & Privilege Abuse ✅

**Risk**: An agent abuses its assigned identity or privileges to access resources or perform actions beyond its intended scope.

**HUMMBL coverage**:
- ✅ `AgentRegistry` with trust tiers (owner/high/medium/low/system/unknown) — access-control decisions per agent identity
- ✅ `check_least_privilege()` enforces minimum-necessary permissions
- ✅ Delegation-depth limit prevents indefinite privilege chain
- ✅ `generate_owasp_report()` maps ASI03 from DCT tuples — proves delegation enforcement
- ✅ Probation/suspended statuses quarantine compromised agents
- ✅ Unknown agents default to lowest trust

**Evidence**: `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/compliance_mapper.py`

### ASI04 — Supply Chain ✅

**Risk**: Compromised dependencies, plugins, or model providers introduce malicious functionality into the agent system.

**HUMMBL coverage**:
- ✅ Zero third-party runtime dependencies — stdlib only, eliminates primary supply-chain attack surface
- ✅ `pip-audit` blocking in CI — dependency-CVE gate
- ✅ SBOM generation per release (cross-ref ISO 27001 A.5.21, NIST CSF GV.SC-04)
- ✅ Supplier-DCT tuples track model providers and data sources
- ✅ `generate_owasp_report()` maps ASI04 from signed entries — proves supply-chain provenance
- ✅ Schema validation prevents malformed payloads from compromised external sources

**Evidence**: `hummbl_governance/schema_validator.py`, `hummbl_governance/identity.py`, `.github/workflows/ci.yml`, `hummbl_governance/compliance_mapper.py`

### ASI05 — Unexpected Code Execution ⚪

**Risk**: An agent generates and executes code without proper sandboxing, enabling arbitrary code execution, filesystem access, or network exploitation.

**HUMMBL coverage**:
- ✅ Delegation caveats can require APPROVAL_REQUIRED before code-execution tool calls
- ✅ Audit log records all code-execution events for forensic analysis
- ⚪ **Boundary**: HUMMBL operates at the governance and policy layer, not the execution sandbox layer. No modules provide code sandboxing, filesystem access restrictions, network policy enforcement, or container/VM-level isolation. This is an infrastructure concern outside the package scope.

**Evidence**: `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py`

### ASI06 — Memory & Context Poisoning 🟡

**Risk**: An agent's memory or context is manipulated to alter its behavior, inject false information, or override safety instructions.

**HUMMBL coverage**:
- ✅ Append-only audit log with entry immutability (frozen dataclass, UUID entry_id) — cannot fabricate history
- ✅ Optional HMAC signatures detect tampering
- ✅ Trust tiers gate which agents can write to shared state
- ✅ Kill-switch state files signed with HMAC-SHA256; `verify_state_file()` detects tampering
- ✅ `generate_owasp_report()` maps ASI06 (code-audit evidenced)
- 🟡 No runtime memory integrity checking for agent context windows; no content-addressable storage for retrieval corpora — poisoned prompts within the context window are not detected by these modules

**Evidence**: `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py`, `hummbl_governance/kill_switch.py`

### ASI07 — Insecure Inter-Agent Comms ✅

**Risk**: Communication between agents is intercepted, modified, or spoofed, enabling man-in-the-middle attacks or message injection.

**HUMMBL coverage**:
- ✅ HMAC-SHA256 signed delegation tokens — communication authenticity verified
- ✅ Append-only governance bus with sender identity validation — rejects messages from unapproved identities
- ✅ DCTX tuples provide cryptographically verifiable delegation context
- ✅ `generate_owasp_report()` maps ASI07 from DCTX + signed entries — proves inter-agent comms integrity
- ✅ Amendment chains and cross-link validation create verifiable execution history

**Evidence**: `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`, `hummbl_governance/compliance_mapper.py`

### ASI08 — Cascading Failures ✅

**Risk**: A failure in one agent or service cascades to dependent agents, causing widespread system failure.

**HUMMBL coverage**:
- ✅ Circuit breaker (CLOSED/HALF_OPEN/OPEN) — fast-fails on unresponsive services, prevents cascading failures
- ✅ Configurable failure threshold (default 5) and recovery timeout (default 30s)
- ✅ Kill switch HALT_NONCRITICAL preserves essential services while stopping discretionary work
- ✅ `generate_owasp_report()` maps ASI08 from CIRCUIT_BREAKER/KILLSWITCH entries — proves failure containment
- ✅ State change callbacks for monitoring and alerting integration

**Evidence**: `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/compliance_mapper.py`

### ASI09 — Human-Agent Trust Exploitation 🟡

**Risk**: An attacker exploits the trust relationship between humans and agents, tricking humans into taking harmful actions based on agent outputs.

**HUMMBL coverage**:
- ✅ Full audit trail enables post-incident forensic analysis of trust exploitation
- ✅ Delegation tokens require human-in-the-loop for INTENT classes outside delegation scope
- ✅ Transparency tuples disclose AI authorship per EU AI Act Art. 50
- ✅ `generate_owasp_report()` maps ASI09 (code-audit evidenced)
- 🟡 No real-time trust-verification or anomaly detection between human-agent interaction boundaries — detection is post-hoc (via audit log), not preventive

**Evidence**: `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`

### ASI10 — Rogue Agents ✅

**Risk**: An agent operates outside its designated parameters, ignoring constraints, safety instructions, or oversight mechanisms.

**HUMMBL coverage**:
- ✅ Kill switch 4-mode halt — emergency halt can terminate rogue agent's execution immediately
- ✅ `AgentRegistry` with probation/suspended statuses — rogue agents can be quarantined
- ✅ Circuit breaker isolates rogue agents from dependent services
- ✅ Cost governor hard cap (DENY) prevents runaway spend by rogue agents
- ✅ `generate_owasp_report()` maps ASI10 (code-audit evidenced)
- ✅ Delegation token expiry limits rogue agent's window of operation

**Evidence**: `hummbl_governance/kill_switch.py`, `hummbl_governance/identity.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/compliance_mapper.py`

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Implementation: `hummbl_governance/compliance_mapper.py` (`generate_owasp_report()` maps ASI01-ASI10)
- Existing OWASP doc: `docs/OWASP_MAPPING.md` (detailed module-by-module mapping)
- LLM Top 10 overlap — see [`owasp-llm.md`](./owasp-llm.md)
- STRIDE overlap (Spoofing=ASI03, DoS=ASI08, EoP=ASI03/ASI10) — see [`stride.md`](./stride.md)
- Supply-chain overlap with ISO 27001 A.5.21, NIST CSF GV.SC — see [`iso-27001.md`](./iso-27001.md), [`nist-csf.md`](./nist-csf.md)
