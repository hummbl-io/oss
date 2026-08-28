# HUMMBL Intelligent Delegation Profile (IDP)

> Deterministic, cryptography-backed delegation for multi-agent systems.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Zero Runtime Deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen.svg)]()

---

## What is IDP?

The **Intelligent Delegation Profile (IDP)** is a specification and reference implementation for safe, verifiable delegation between autonomous AI agents. It treats the LLM as a non-privileged user-space process and enforces governance at the **kernel level** — before any tool call, file write, or inter-agent message is executed.

IDP is the missing "authorization layer" between:
- **MCP** (agent → tool interface)
- **A2A** (agent → agent messaging)

MCP says *what tools are available*. A2A says *how agents communicate*. **IDP says *who is authorized to use what, with what proof*.**

---

## The Six-Tuple Framework

```
DCTX  →  CONTRACT  →  EVIDENCE  →  ATTEST  →  DCT  →  GOVERNANCE_BUS
```

| Tuple | Purpose |
|---|---|
| **DCTX** (Delegation Context) | Immutable context: delegator, delegatee, scope, constraints |
| **CONTRACT** | Pre/post conditions with formal invariants (least privilege, bounded depth) |
| **EVIDENCE** | Artifacts proving work completion (test results, output hashes, metrics) |
| **ATTEST** | Cryptographic verification linking evidence to the delegation chain |
| **DCT** (Delegation Capability Token) | HMAC-SHA256 signed, time-bounded, scope-limited authorization token |
| **GOVERNANCE BUS** | Append-only, hash-chained audit log of all delegation events |

---

## Quick Start

```python
import os
from pathlib import Path
from idp_spec import (
    DelegationContext,
    GovernanceBus,
    TokenBinding,
    create_token,
    validate_token,
)

# 1. Ensure IDP is enabled
os.environ["ENABLE_IDP"] = "true"
secret = b"my-secure-hmac-key-32bytes-long!"

# 2. Create an HMAC-SHA256 capability token
binding = TokenBinding(task_id="task-001", contract_id="contract-001")
dct = create_token(
    issuer="scheduler",
    subject="briefing_service",
    ops_allowed=["generate", "write_briefing"],
    binding=binding,
    secret=secret,
    expiry_minutes=120,
)

# 3. Validate the token
valid, error_code = validate_token(dct, secret=secret, binding=binding, operation="generate")
assert valid

# 4. Create a delegation context
dctx = DelegationContext(
    intent_id="intent-001",
    task_id="task-001",
    delegator_id="scheduler",
    delegatee_id="briefing_service",
    contract_id="contract-001",
)

# 5. Log to governance bus
bus = GovernanceBus(base_dir=Path("./_state/governance"))
bus.append(
    intent_id=dctx.intent_id,
    task_id=dctx.task_id,
    tuple_type="DCT",
    tuple_data={"token_id": dct.token_id, "subject": dct.subject},
    contract_id=dctx.contract_id,
    capability_token_id=dct.token_id,
)
```

---

## Core Invariants

IDP enforces six invariants derived from production multi-agent operations:

| Invariant | Description | Enforcement |
|---|---|---|
| **I1** No Unverifiable Delegation | Every delegation MUST have a CONTRACT, DCTX, and EVIDENCE requirement | DCT validation before tool calls |
| **I2** Least Privilege | Delegatee receives ONLY the capabilities needed for its scope | DCT `ops_allowed` ⊆ CONTRACT.allowed_tools |
| **I3** Bounded Chain Depth | No delegation chain longer than 3 levels | `chain_depth` counter, reject if > 3 |
| **I4** Evidence Before Verify | ATTEST cannot run without EVIDENCE artifacts | Pre-commit hook blocks commit without tests |
| **I5** Explicit Replan | On CONTRACT violation, delegator must explicit replan (no auto-retry) | Circuit breaker HALF_OPEN requires explicit approval |
| **I6** Audit Completeness | Full DCTX + EVIDENCE + ATTEST chain logged for every delegation | Append-only JSONL with SHA-256 hash chaining |

---

## Key Differentiators

| Feature | IDP | Typical agent framework |
|---|---|---|
| **Delegation model** | Capability tokens with trust decay | Implicit or prompt-based authority |
| **Chain depth** | Mathematically bounded (max 3) | Unbounded or not tracked |
| **Replan after failure** | Explicit human approval required | Auto-retry loops |
| **Audit** | Append-only JSONL with hash chaining | Ephemeral logs or none |
| **Dependencies** | **Zero third-party runtime dependencies** | Often depends on crypto libs, DBs |
| **Side-effect interception** | Deterministic policy at sink boundaries | Prompt-level filtering (bypassable) |

---

## Installation

```bash
pip install idp-spec
```

**Requires Python 3.11+.** No external runtime dependencies.

For optional `hummbl-governance` identity kernel integration:

```bash
pip install "idp-spec[governance]"
```

---

## Feature Flag

IDP is designed for zero-overhead adoption:

```bash
# Default: disabled (backward compatible pass-through)
ENABLE_IDP=false python my_script.py

# Full enforcement
ENABLE_IDP=true python my_script.py
```

When disabled, all IDP operations are no-ops — existing code paths are unchanged.

---

## Project Status

| Component | Status |
|---|---|
| DCT (DelegationCapabilityToken) | Production — HMAC-SHA256, expiry, scope binding |
| Governance Bus | Production — append-only JSONL, daily rotation, 90-day retention |
| Delegation Context | Production — 7-state state machine, depth bounds, replan limits |
| Lateral Authority (bus-level) | Phase 1 logging complete, Phase 2 enforcement in development |
| Taint Propagation | Experimental — feature-flagged, instruction-level tracking |
| Evidence / Attestation | Planned — post-commit hook integration |

---

## Testing

```bash
cd packages/python/idp-spec
pip install -e ".[test]"
python -m pytest tests/ -v
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
