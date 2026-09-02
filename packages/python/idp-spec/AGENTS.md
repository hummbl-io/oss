# AGENTS.md — idp-spec

## Project

**idp-spec** — HUMMBL Intelligent Delegation Profile (IDP): deterministic, cryptography-backed delegation for multi-agent systems. Reference implementation of the six-tuple delegation framework (DCTX → CONTRACT → EVIDENCE → ATTEST → DCT → GOVERNANCE_BUS).

## Scope

- In scope: IDP specification and reference implementation, HMAC-SHA256 signed capability tokens, governance bus (append-only hash-chained audit log), delegation context lifecycle, six core invariants (I1-I6)
- Out of scope: Agent runtime execution, MCP/A2A protocol implementation, tuple taxonomy maintenance

## Setup

```bash
cd packages/python/idp-spec
pip install -e ".[test]"
```

## Testing

```bash
python -m pytest tests/ -v
```

124 tests covering delegation context, delegation token, governance bus, and audit goldplate checks.

## Conventions

- Python 3.11+ required
- Zero third-party runtime dependencies (stdlib only)
- Optional `hummbl-governance` integration via `[governance]` extra
- Feature flag: `ENABLE_IDP=true` enables enforcement, `false` is no-op pass-through
- Six invariants: I1 (No Unverifiable Delegation), I2 (Least Privilege), I3 (Bounded Chain Depth ≤3), I4 (Evidence Before Verify), I5 (Explicit Replan), I6 (Audit Completeness)
- MIT OR Apache-2.0 license
