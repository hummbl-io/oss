# HUMMBL Cryptographic Policy

**Version:** 1.0
**Scope:** All packages in `hummbl-io/oss`
**Reference:** NIST SP 800-53 Rev 5 SC-13 (Cryptographic Protection), SI-7 (Software and Firmware Integrity)

---

## 1. Approved Algorithms

| Algorithm | Use Case | Standard | Status |
|-----------|----------|----------|--------|
| SHA-256 | Hashing, HMAC construction | FIPS 180-4 | Approved |
| HMAC-SHA256 | Message authentication, audit log signing, receipt integrity | FIPS 198-1 | Approved |
| AES-256-GCM | Authenticated encryption at rest (`sovereign_cryptosystem.py`) | FIPS 197, SP 800-38D | Approved |
| Ed25519 | Principal authentication, bus message signing | FIPS 186-5 | Approved |

## 2. Prohibited Algorithms

The following are **not** used anywhere in the codebase:

- MD5, SHA-1 (broken collision resistance)
- RSA < 2048 bits (insufficient key size)
- DES, 3DES (deprecated)
- RC4, Blowfish (not approved)
- Any custom/unreviewed cryptographic primitive

## 3. Random Number Generation

- `secrets.token_bytes()` (CSPRNG) is used for all key generation.
- `os.urandom()` is the underlying source on all platforms.
- No use of `random.random()` or any PRNG for security purposes.

## 4. Key Management

### 4.1 Current State

Keys are resolved from environment variables per component:

| Variable | Consumer | Purpose |
|----------|----------|---------|
| `BUS_SIGNING_SECRET` | `hummbl-bus` | HMAC-SHA256 bus message signing |
| `RECEIPTENGINE_HMAC_KEY` | `hummbl-governance` Kernel | Receipt integrity signing |
| `HUMMBL_SIGNING_SECRET` | `hummbl-governance` (fallback) | Kill switch, audit log |
| `MISSION_MODE_SIGNING_KEY` | `hummbl-governance` | Mission mode tuples |
| `BUS_PRINCIPAL_PUBLIC_KEY_FILE` | `hummbl-bus` | Ed25519 principal verification |

### 4.2 Key Storage

- HMAC secret files are created with `0o600` permissions (owner read/write only).
- Ed25519 public keys are loaded from configurable file paths.
- No keys are hardcoded in source code.

### 4.3 Key Derivation

**Current:** `sovereign_cryptosystem.py` derives keys via SHA-256 of concatenated strings. This is informal and not compliant with NIST SP 800-108.

**Roadmap:** Replace with HKDF-SHA256 (RFC 5869) for all key derivation. The standard library does not include HKDF; a stdlib-only implementation is tracked as a roadmap item.

### 4.4 Key Rotation

- DCTs (Delegation Capability Tokens) support expiry and revocation, limiting credential lifetime.
- No automated key rotation ceremony exists yet. Manual rotation requires updating the environment variable and restarting the service.
- **Roadmap:** Implement a key hierarchy (master key → per-package derived keys via HKDF) to enable rotation without service-wide restarts.

## 5. FIPS 140-2/140-3 Compliance

**Current status:** Not FIPS-validated.

- Python `hashlib`/`hmac` rely on the underlying OpenSSL build. On a FIPS-enabled system, these will use FIPS-approved implementations.
- `cryptography>=42.0` (optional dependency) supports a FIPS provider via OpenSSL.
- No FIPS self-test or algorithm allowlist is enforced.

**Path to FIPS compliance:**
1. Run on a FIPS-enabled OS (RHEL 9 in FIPS mode, Ubuntu Pro FIPS, etc.)
2. Use `cryptography` with the FIPS provider
3. Add a startup self-test that verifies only FIPS-approved algorithms are available
4. Engage a CMVP-accredited lab for module validation (out of scope for OSS)

## 6. Transport Security

- `hummbl-bus` bridge uses plain HTTP by default. WireGuard encryption is provided by Tailscale at the network layer.
- `hummbl-cognition` agenthub bridge uses `urllib.request` with `ssl._create_default_https_context` for HTTPS.
- **Recommendation:** For production deployments, terminate TLS at a reverse proxy in front of the bus bridge. Enforce TLS 1.2+ (TLS 1.3 preferred).

## 7. Encryption at Rest

- Audit logs, receipt files, and bus TSV files are stored as plaintext on disk with `0o600` file permissions.
- `sovereign_cryptosystem.py` provides AES-256-GCM authenticated encryption but is not the default for persisted data.
- **Recommendation:** For deployments requiring encryption at rest, use filesystem-level encryption (LUKS, BitLocker) or apply `sovereign_cryptosystem.py` as a wrapper.

## 8. Signature Verification

### Audit Log

`AuditLog` supports two modes (see `SECURITY.md`):

1. **Presence-check** (default): `require_signature=True` without `hmac_key`. Signatures are presence-checked, not cryptographically verified.
2. **HMAC-verified** (recommended): `hmac_key` + `strict_hmac=True`. `append()` verifies HMAC-SHA256 over canonical entry bytes; `verify_entry()` re-verifies on read.

For NIST SP 800-53 AU-6 compliance, use mode 2.

### Coordination Bus

- `bus_verifier.py` verifies HMAC-SHA256 signatures on bus messages.
- `bus_ed25519_verifier.py` verifies Ed25519 signatures on privileged event types.
- `authority.py` consumes nonces for replay protection.
- `bus_policy.py` enforces `PERMISSIVE`/`WARN`/`STRICT` signing levels. Use `STRICT` for production.

### Receipt Engine

- `receipt_engine.py` signs receipts with HMAC-SHA256.
- `receipt_integrity_monitor.py` checks for sequence gaps, hash-chain breaks, and timestamp anomalies.
- File persistence (`file_persistence.py`) verifies signatures on read.

## 9. Review Cadence

This policy should be reviewed:
- When a new cryptographic primitive is added to the codebase
- When a NIST standard is updated (e.g., FIPS 186-5, SP 800-38D)
- Annually, as part of the security review cycle
- After any cryptographic vulnerability disclosure affecting approved algorithms
