# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.4.x   | Yes (current)      |
| 1.0.x   | Yes (security fixes only) |
| < 1.0   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in hummbl-governance, please report it responsibly:

1. **Email:** security@hummbl.io
2. **Do NOT** open a public GitHub issue for security vulnerabilities
3. Include: description of the vulnerability, steps to reproduce, and potential impact
4. You can expect an initial response within 48 hours

## Scope

This policy covers the `hummbl_governance` Python package (v1.4.1) and its 34
implemented governance primitives covering safety, cost, identity, compliance,
reasoning, coordination, physical-AI, execution assurance, and the governance
Kernel. Full primitive inventory in the project README.

The package is CI-tested on Python 3.11, 3.12, and 3.13 (GitHub Actions matrix).
Python 3.14 support is not claimed until the CI matrix includes it. Current package test-count claims are
governed by `docs/TEST_COUNT_AUTHORITY.md`; as of 2026-08-23,
`python -m pytest --collect-only -q tests` collects 2314 tests.

## Audit-log signature semantics

The `AuditLog` supports two signature verification modes:

1. **Presence-check (default, backward-compatible):** `require_signature=True`
   with no `hmac_key`. Entries must have a non-empty `signature` field, but the
   field is not cryptographically verified against the entry body. A warning is
   logged at construction time. Suitable for development and non-adversarial
   environments.

2. **HMAC-verified (recommended for production):** Pass `hmac_key=<32 bytes>`
   and `strict_hmac=True`. `append()` computes HMAC-SHA256 over a canonical
   form of the entry (excluding the signature itself) and rejects entries
   whose signature does not match (`E_AUDIT_SIGNATURE_INVALID`).
   `verify_entry()` re-verifies any entry on read. This satisfies
   NIST SP 800-53 AU-6 (audit review, analysis, and reporting) and aligns
   with SP 800-92 (protection of audit log integrity).

Callers compute the signature as:

```python
import hmac
from hashlib import sha256
sig = hmac.new(key, AuditLog.canonical_bytes(entry), sha256).hexdigest()
```

See `hummbl_governance/audit_log.py` and `tests/test_audit_log.py`
(`TestHmacVerification`) for implementation and test coverage.
