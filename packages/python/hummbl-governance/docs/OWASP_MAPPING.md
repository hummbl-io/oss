# OWASP Agentic Top 10 Compliance Mapping

> **Package**: `hummbl-governance` v1.2.2
> **Standard**: OWASP Top 10 for Agentic Applications (December 2025)
> **Date**: 2026-03-23
> **Audience**: Enterprise compliance reviewers, security-conscious developers

## Summary

`hummbl-governance` is a stdlib-only Python package providing seven governance primitives for AI agent systems: kill switch, circuit breaker, cost governor, delegation tokens, audit log, agent identity registry, and schema validator. This document maps each OWASP Agentic Top 10 risk to the modules that address it.

**Coverage snapshot**: 4 FULL, 4 PARTIAL, 2 NONE.

---

## Module Inventory

| Module | Primary Capability | Cryptography |
|--------|-------------------|--------------|
| `kill_switch.py` | Graduated emergency halt (4 modes), task exemptions | HMAC-SHA256 state integrity |
| `circuit_breaker.py` | Failure detection, cascading-failure prevention (3-state FSM) | None |
| `cost_governor.py` | SQLite-backed budget enforcement (ALLOW/WARN/DENY) | None |
| `delegation.py` | Time-bound, caveat-constrained capability tokens | HMAC-SHA256 token signing |
| `audit_log.py` | Append-only JSONL governance log, amendment chains | HMAC-SHA256 (optional) |
| `identity.py` | Agent registry, alias resolution, trust tiers | None |
| `schema_validator.py` | Stdlib-only JSON Schema validation (Draft 2020-12 subset) | None |

---

## Risk-by-Risk Mapping

### 1. Excessive Agency

**Risk**: An agent takes actions beyond its intended scope, performing unauthorized operations or exceeding its designated authority.

**Coverage**: **FULL**

| Module | Mechanism |
|--------|-----------|
| `kill_switch.py` | Four graduated halt modes (DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY). Task exemption allowlist limits what can execute during halt. |
| `delegation.py` | `DelegationToken` with `check_least_privilege()` enforces minimum-necessary permissions. Time-bound expiry (default 120 min). Caveats constrain token scope (TIME_BOUND, RATE_LIMIT, APPROVAL_REQUIRED, AUDIT_REQUIRED). |
| `identity.py` | Trust tiers (owner/high/medium/low/system/unknown) enable access-control decisions per agent identity. |
| `cost_governor.py` | Hard budget caps prevent runaway spend — a form of resource-scoped agency control. |

**Gaps**: None for the control-plane layer. Application-level permission enforcement (e.g., which tools an agent can call) must be wired by the integrator.

---

### 2. Tool Misuse

**Risk**: An agent calls tools with malicious, incorrect, or unintended parameters, causing harmful side effects.

**Coverage**: **PARTIAL**

| Module | Mechanism |
|--------|-----------|
| `schema_validator.py` | Validates tool input/output against JSON Schema — enforces type, required fields, enum constraints, pattern matching, numeric bounds. Rejects additional properties when configured. |
| `delegation.py` | Caveats can require APPROVAL_REQUIRED before tool execution. Token binding ties permissions to a specific agent context. |
| `audit_log.py` | Full audit trail of all tool invocations via DCTX/EVIDENCE tuple types. Amendment chains link outcomes to the authorizing delegation. |

**Gaps**: No runtime parameter sanitization or allowlist-based tool filtering. Schema validation is structural, not semantic — it cannot detect a syntactically valid but contextually harmful parameter (e.g., a valid path that points to a sensitive file). Integrators should add tool-call interceptors.

---

### 3. Memory Poisoning

**Risk**: An agent's memory or context is manipulated to alter its behavior, inject false information, or override safety instructions.

**Coverage**: **PARTIAL**

| Module | Mechanism |
|--------|-----------|
| `audit_log.py` | Append-only log with entry immutability (frozen dataclass, UUID entry_id). Amendment chains require referencing an existing entry — cannot fabricate history. Optional HMAC signatures detect tampering. |
| `identity.py` | Trust tiers gate which agents can write to shared state. Probation/suspended statuses can quarantine compromised agents. |
| `kill_switch.py` | HMAC-SHA256 signed state files with `verify_state_file()` detect tampering of persisted kill-switch state. File permissions enforced at 0o600. |

**Gaps**: No runtime memory integrity checking for agent context windows. No content-addressable storage for retrieval corpora. Poisoned prompts within the context window are not detected by these modules — that requires an application-layer content filter.

---

### 4. Intent Hijacking

**Risk**: An attacker manipulates an agent's planning or goal-setting to redirect it toward malicious objectives, often through crafted inputs or adversarial prompts.

**Coverage**: **PARTIAL**

| Module | Mechanism |
|--------|-----------|
| `delegation.py` | Tokens are bound to a specific agent and context via `TokenBinding`. Caveat enforcement constrains what a hijacked agent could accomplish even if its intent is altered. Time-bound expiry limits the window of exploitation. |
| `kill_switch.py` | Emergency halt can terminate a hijacked agent's execution. HALT_ALL mode stops everything except safety-critical tasks. |
| `audit_log.py` | Full audit trail enables post-incident forensic analysis of when intent diverged from expected behavior. |

**Gaps**: No real-time intent monitoring or anomaly detection. No semantic comparison between declared intent and observed actions. Detection is post-hoc (via audit log), not preventive. Integrators should add intent-verification checkpoints at planning boundaries.

---

### 5. Planning Chain Coercion

**Risk**: An attacker manipulates a multi-step planning chain to insert malicious steps or alter the execution order, exploiting the agent's sequential reasoning.

**Coverage**: **PARTIAL**

| Module | Mechanism |
|--------|-----------|
| `delegation.py` | Each delegation step requires a signed token — an attacker cannot insert unauthorized steps without a valid HMAC signature. Caveat chains (e.g., AUDIT_REQUIRED) force visibility at each step. |
| `audit_log.py` | Amendment chains and cross-link validation (contract_id, capability_token_id) create a verifiable execution history. Inserted or reordered steps would break the chain. |
| `kill_switch.py` | Can halt execution mid-chain if anomalous behavior is detected. |

**Gaps**: No formal plan verification (e.g., comparing an execution plan against a policy spec before running). No step-ordering enforcement beyond what delegation tokens implicitly provide. Multi-step plans with dynamic tool selection are not constrained to a pre-approved graph.

---

### 6. Insufficient Output Validation

**Risk**: Agent outputs are consumed by downstream systems without validation, enabling injection attacks, data corruption, or propagation of harmful content.

**Coverage**: **PARTIAL** (structural only)

| Module | Mechanism |
|--------|-----------|
| `schema_validator.py` | Validates output structure against JSON Schema — type checking, required fields, enum constraints, string patterns, numeric bounds, additional-property rejection. |
| `audit_log.py` | Logs all outputs for post-hoc review. EVIDENCE tuple type records output alongside the authorizing context. |

**Gaps**: No semantic output validation (e.g., detecting PII, harmful content, or injection payloads in free-text fields). No output sanitization layer. Schema validation catches structural violations but not adversarial content within valid structures. Integrators should add content-safety filters on agent outputs before passing to downstream consumers.

---

### 7. Unsafe Code Execution

**Risk**: An agent generates and executes code without proper sandboxing, enabling arbitrary code execution, file system access, or network exploitation.

**Coverage**: **NONE**

`hummbl-governance` operates at the governance and policy layer, not the execution sandbox layer. No modules provide:
- Code sandboxing or isolation
- Filesystem access restrictions
- Network policy enforcement
- Container or VM-level isolation

**Recommendation**: Pair hummbl-governance with an execution sandbox (e.g., gVisor, Firecracker, or language-level sandboxing). Use `DelegationToken` caveats to require APPROVAL_REQUIRED before code-execution tool calls, and `AuditLog` to record all code-execution events.

---

### 8. Denial of Service / Resource Exhaustion

**Risk**: An agent consumes excessive compute, memory, API calls, or other resources, degrading service availability for other agents or users.

**Coverage**: **FULL**

| Module | Mechanism |
|--------|-----------|
| `cost_governor.py` | SQLite-backed budget tracking with soft cap (WARN at 80%) and hard cap (DENY). Per-provider and per-model spend breakdown. Daily tracking with configurable retention. Budget alert callbacks. |
| `circuit_breaker.py` | Prevents cascading failures by fast-failing when a service is unresponsive (OPEN state). Configurable failure threshold (default 5) and recovery timeout (default 30s). |
| `kill_switch.py` | HALT_NONCRITICAL preserves essential services while stopping discretionary work. HALT_ALL stops everything except safety tasks. |
| `delegation.py` | RATE_LIMIT caveat constrains token usage rate. TIME_BOUND caveat prevents indefinite resource consumption. |

**Gaps**: None at the governance layer. No OS-level resource limits (cgroups, memory caps) — those are infrastructure concerns outside this package's scope.

---

### 9. Supply Chain Vulnerabilities

**Risk**: Compromised dependencies, plugins, or model providers introduce malicious functionality into the agent system.

**Coverage**: **FULL**

| Module | Mechanism |
|--------|-----------|
| (Package-level) | **Zero third-party runtime dependencies** — stdlib only. This eliminates the primary supply-chain attack surface (compromised PyPI packages, transitive dependency exploits). |
| `schema_validator.py` | Validates all data crossing trust boundaries against JSON Schema — prevents malformed payloads from compromised external sources. |
| `identity.py` | Agent registry with trust tiers ensures only known, approved agents interact with the system. Unknown agents default to lowest trust. |

**Gaps**: No model-provider integrity verification (e.g., signed model weights or API response attestation). No plugin sandboxing — if the integrator adds plugins, those are outside hummbl-governance's scope.

---

### 10. Logging and Monitoring Failures

**Risk**: Insufficient logging, monitoring, or alerting allows security incidents to go undetected, hindering forensic analysis and incident response.

**Coverage**: **FULL**

| Module | Mechanism |
|--------|-----------|
| `audit_log.py` | Append-only JSONL governance log with: daily rotation, 180-day retention, gzip compression, 0o600 file permissions, UUID entry IDs, amendment chains, cross-link validation. Six tuple types (DCTX, CONTRACT, EVIDENCE, ATTEST, DCT, SYSTEM). Query by intent, task, entry_id, contract, or amendment chain. |
| `kill_switch.py` | Full history of all mode transitions with timestamps. State change subscriber notifications for alerting integration. |
| `circuit_breaker.py` | State change callbacks for monitoring/alerting. Failure count and timestamp tracking. |
| `cost_governor.py` | Budget alert callbacks on WARN/DENY decisions. Full spend history in SQLite with per-provider breakdown. |

**Gaps**: No built-in alerting transport (e.g., email, Slack, PagerDuty). The package provides callbacks and log files — integrators must wire these to their alerting infrastructure.

---

## Coverage Matrix

| # | OWASP Risk | Coverage | Primary Modules | Key Gap |
|---|-----------|----------|----------------|---------|
| 1 | Excessive Agency | **FULL** | kill_switch, delegation, identity, cost_governor | — |
| 2 | Tool Misuse | **PARTIAL** | schema_validator, delegation, audit_log | No semantic parameter validation |
| 3 | Memory Poisoning | **PARTIAL** | audit_log, identity, kill_switch | No runtime context integrity checks |
| 4 | Intent Hijacking | **PARTIAL** | delegation, kill_switch, audit_log | No real-time intent monitoring |
| 5 | Planning Chain Coercion | **PARTIAL** | delegation, audit_log, kill_switch | No formal plan verification |
| 6 | Insufficient Output Validation | **PARTIAL** | schema_validator, audit_log | No semantic/content-safety filtering |
| 7 | Unsafe Code Execution | **NONE** | — | Out of scope (execution sandbox layer) |
| 8 | DoS / Resource Exhaustion | **FULL** | cost_governor, circuit_breaker, kill_switch, delegation | — |
| 9 | Supply Chain Vulnerabilities | **FULL** | (stdlib-only), schema_validator, identity | No model-provider attestation |
| 10 | Logging & Monitoring Failures | **FULL** | audit_log, kill_switch, circuit_breaker, cost_governor | No built-in alerting transport |

---

## Recommendations for Full Coverage

1. **Content-safety filter** (addresses risks 2, 3, 4, 6): Add an output/input content scanner for PII, injection payloads, and adversarial prompts. Could be a thin wrapper around schema_validator with semantic rules.

2. **Execution sandbox integration** (addresses risk 7): Document recommended sandboxing approaches (gVisor, Firecracker, WASM) and provide a `SandboxPolicy` interface that integrators implement.

3. **Intent monitor** (addresses risks 4, 5): Add an `IntentVerifier` that compares declared task intent against observed tool calls, using the existing audit_log as the evidence source.

4. **Alerting transport** (addresses risk 10): Add optional alerting backends (webhook, SMTP) that consume the existing callback hooks from kill_switch, circuit_breaker, and cost_governor.
