# HUMMBL Intelligent Delegation Profile (IDP)

> Deterministic, cryptography-backed delegation for multi-agent systems.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Zero Runtime Deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen.svg)]()

---

## What is IDP?

The **Intelligent Delegation Profile (IDP)** is a specification and Python library reference implementation for verifiable delegation between autonomous AI agents. It models the LLM as a non-privileged user-space process and provides deterministic token, delegation-context, and audit-log primitives that host gateways can invoke before executing tool calls, file writes, or inter-agent messages.

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

> **Terminology note:** `DCT` stands for **Delegation Capability Token**, distinct from `DCTX` (**Delegation Context**). See [`docs/architecture/NOMENCLATURE.md`](../../../docs/architecture/NOMENCLATURE.md) for canonical definitions and scope boundaries.

---

## Quick Start

From this repository, install the cognition integration before writing to the
governance log:

```sh
cd packages/python/idp-spec
python -m pip install ".[cognition]"
```

The base package remains dependency-free. Governance log appends raise
`RuntimeError` if the scrubber cannot be imported, fails, or returns an invalid
result; rejected entries are neither written nor buffered. Appends snapshot
JSON-serializable `tuple_data` and pseudonymize recognized patterns in its
string values, including nested arrays. Recognized PII in dictionary keys is
rejected rather than renaming fields. Metadata identifiers are not scrubbed,
and pattern matching does not guarantee that all personal data is removed.

`append_audit_entry()` automatically signs the detached, scrubbed payload that
it stores. Direct callers can request the same behavior with
`GovernanceBus.append(..., auto_sign=True)`. Set a persistent `DCT_SECRET` for
signatures that can be checked after the process exits.

When supplying your own signature, first call
`idp_spec.governance_bus.prepare_audit_tuple_data()`, sign that returned data,
and append the same data and signature. Further redaction rejects the append
with `IDP_E_AUDIT_IMMUTABLE`; caller signatures are never silently rewritten.
Append checks signature presence and preserves the signed payload, but does
not authenticate caller signatures. `verify_chain()` checks hash linkage,
not HMAC signatures.

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
| **Side-effect interception** | Deterministic policy primitives for sink-boundary integration | Prompt-level filtering (bypassable) |

---

## Installation

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/idp-spec
```

**Requires Python 3.11+.** No external runtime dependencies.

For optional `hummbl-governance` identity kernel integration:

```bash
pip install "idp-spec[governance]"
```

---

## Feature Flag

The IDP helpers default to `ENABLE_IDP=true` when the variable is unset. Setting it to `false` (or any unrecognized value) **fails closed** across all three core modules — token creation/validation/least-privilege checks (`delegation_token`), lifecycle methods (`delegation_context`), and audit log writes (`GovernanceBus.append()` returns `(False, IDP_E_AUDIT_INCOMPLETE)` without writing). There is no silent authorization or audit bypass:

| `ENABLE_IDP` value | `delegation_token` | `delegation_context` | `GovernanceBus.append()` |
|---|---|---|---|
| unset / `"true"` (case-insensitive) | Enabled (normal validation) | Enabled (normal transitions) | Enabled (scrubs & writes entry) |
| `"false"` / empty / unrecognized | Fails closed (`RuntimeError` on create; `False` on validate/check) | Lifecycle methods (`transition`, `can_subdelegate`, `create_child`) fail closed (`IDP_E_DISABLED`); root creation (`create_root`, `create_root_context`) is not gated | Fails closed (`(False, IDP_E_AUDIT_INCOMPLETE)`, nothing written) |

```bash
# IDP helpers enabled by default
ENABLE_IDP=true python my_script.py

# IDP helpers reject requests (fail closed)
ENABLE_IDP=false python my_script.py
```

These settings describe the IDP token library. They do **not** establish that every host tool, file write, or agent message is intercepted. Enforcement at a side-effect boundary requires explicit integration and verification of that integration path. Evidence/attestation and some lateral authority components remain incomplete as noted in Project Status.

---

## Project Status

| Component | Status |
|---|---|
| DCT (DelegationCapabilityToken) | Production — HMAC-SHA256, expiry, scope binding |
| Governance Bus | Production — append-only JSONL, daily rotation, 180-day default retention |
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

MIT OR Apache-2.0 — see [LICENSE](LICENSE).
