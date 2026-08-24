# Inventory: Dependencies for HUMMBL Air-Gapped Work

**Classification:** System Architecture & Enclave Deployment Inventory  
**Target Environment:** Air-gapped enclaves, SCIF environments, offline military/financial compute zones  
**Governing Policy:** Zero Third-Party Production Runtime Dependencies  
**Date:** August 2026  
**Canonical Surface:** [`oss`](file:///<repo-root>/PROJECTS/oss), [`hummbl-governance`](file:///<repo-root>/PROJECTS/hummbl-governance), [`krineia`](file:///<repo-root>/PROJECTS/krineia)  

---

## 1. Production Core Runtime (`dependencies = []`)

For operational execution inside an air-gapped enclave, our production packages have **ZERO third-party runtime dependencies**. They require only a pristine base system installation.

```
┌────────────────────────────────────────────────────────────────────────┐
│             AIR-GAPPED PRODUCTION RUNTIME DEPENDENCIES                 │
├──────────────────────────┬───────────────────────┬─────────────────────┤
│  PACKAGE                 │ RUNTIME DEPENDENCIES  │ REQUIRED BASE HOST  │
├──────────────────────────┼───────────────────────┼─────────────────────┤
│ • hummbl-governance      │ NONE (0 / stdlib)     │ Python >= 3.11      │
│ • base120                │ NONE (0 / stdlib)     │ Python >= 3.11      │
│ • hummbl-kernel          │ NONE (0 / stdlib)     │ Python >= 3.10      │
│ • hummbl-bus             │ NONE (0 / stdlib)     │ Python >= 3.11      │
│ • hummbl-tuples          │ NONE (0 / stdlib)     │ Python >= 3.11      │
│ • hummbl-bif             │ NONE (0 / stdlib)     │ Python >= 3.11      │
│ • hummbl-cognition       │ NONE (0 / stdlib)     │ Python >= 3.11      │
└──────────────────────────┴───────────────────────┴─────────────────────┘
```

### Python Standard Library Modules Utilized (Air-Gapped Core):
- **Cryptographic Hashing & MAC:** `hashlib`, `hmac`, `secrets` (for HMAC-SHA256 tokens and Merkle roots)
- **Data Serialization & Typing:** `json`, `dataclasses`, `typing`, `enum`, `pathlib`
- **File System & Locks:** `os`, `sys`, `time`, `datetime`, `fcntl` (POSIX) / `msvcrt` (Windows)
- **Networking/Protocols (Local IPC):** `socket`, `http.server`, `urllib.parse`

---

## 2. Formal Mathematical Proof & Verification Suite (`KRINEIA`)

To independently verify our TLA+ formal specifications and model checking offline in an air-gapped environment:

```
┌────────────────────────────────────────────────────────────────────────┐
│             AIR-GAPPED FORMAL PROOF DEPENDENCIES                       │
├──────────────────────────┬───────────────────────┬─────────────────────┤
│  COMPONENT               │ LOCAL ARTIFACT        │ HOST REQUIREMENT    │
├──────────────────────────┼───────────────────────┼─────────────────────┤
│ • TLC Model Checker      │ tla2tools.jar (4.5MB) │ OpenJDK / JRE >= 11 │
│ • TLA+ Specification     │ KRINEIA.tla           │ (Text file)         │
│ • Model Configuration    │ KRINEIA.cfg           │ (Text file)         │
│ • Lean 4 (Optional)      │ lean / lake binaries  │ Standalone binary   │
└──────────────────────────┴───────────────────────┴─────────────────────┘
```

*All TLC tools are self-contained within `krineia/papers/krineia-invariants/tla/tla2tools.jar` — requiring only local Java execution without external network access.*

---

## 3. Development, Testing & Optional Extras (Pre-Packaged for Enclaves)

If developers need to run the full test suite, linting, or cryptographic primitives inside an isolated environment, the following wheels must be pre-mirrored into the local air-gapped artifact repository (e.g., local wheelhouse):

### A. Testing & Linting Suite (`[test]` extra)
- `pytest >= 7.0` (and `pytest-cov >= 4.0`, `coverage`)
- `ruff >= 0.4` (Standalone fast linter/formatter)
- `setuptools >= 68.0`, `wheel`, `build >= 1.0`

### B. Optional Primitives Extra (`[primitives]` extra)
- `cryptography >= 42.0` *(Only used for optional hardware-accelerated Ed25519/RSA asymmetric signing; HMAC-SHA256 uses pure Python stdlib)*

---

## 4. Polyglot Reference Runtimes (Air-Gapped)

For our polyglot governance kernels:
- **Rust Implementation (`hummbl-tuples-rs`):** Zero external crates; standard `std::collections`, `std::time`, `sha2`. Requires `rustc >= 1.75`.
- **Go Implementation (`hummbl-tuples-go`):** Zero third-party packages; stdlib `crypto/hmac`, `crypto/sha256`, `encoding/json`. Requires `go >= 1.21`.

---

## 5. Summary: Air-Gapped Manifest Checklist

To spin up a fully operational, mathematically verified HUMMBL node in a disconnected air-gapped facility:

1. **Host OS:** Linux (Ubuntu/RHEL/Debian) or Windows Server.
2. **Runtime:** Python 3.11+ (Standard CPython binary).
3. **Formal Verification:** OpenJDK 11+ (to execute `tla2tools.jar`).
4. **HUMMBL Source Wheels:** `hummbl_governance-1.4.1-py3-none-any.whl`, `base120-3.0.0-py3-none-any.whl`, `hummbl_kernel-0.1.0-py3-none-any.whl`.
5. **External Packages:** **0 packages required.**
