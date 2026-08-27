# HUMMBL Ultra-Minimal Payload Tiers (Air-Gapped)

**Target:** Extreme Low-Bandwidth / Air-Gapped Transfer Constraints  
**Date:** August 2026  
**Canonical Surface:** [`hummbl-governance`](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-governance), [`base120`](https://github.com/hummbl-io/base120), [`kernel`](https://github.com/hummbl-io/kernel)  

---

## 1. Where Does the 5.1 MB Come From?

In the 5.1 MB package, **88% of the weight is a single file: `tla2tools.jar` (4.5 MB)**, which is the pre-compiled Java model checker toolchain. 

If we remove the Java toolchain and evaluate the **actual HUMMBL software code**, the payload drops drastically:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   HUMMBL AIR-GAPPED PAYLOAD TIERS                      │
├───────┬────────────────────────────────┬────────────┬──────────────────┤
│ TIER  │ WHAT IS INCLUDED               │ SIZE       │ TRANSFER MEDIA   │
├───────┼────────────────────────────────┼────────────┼──────────────────┤
│ 1.    │ ULTRA-MINIMAL PURE RUNTIME     │ 378 KB     │ QR Code / Sound  │
│       │ (Governance + Base120 + Kernel)│            │ / Legacy 1.44MB  │
├───────┼────────────────────────────────┼────────────┼──────────────────┤
│ 2.    │ RAW ATOMIC KERNEL ONLY         │ 12 KB      │ Printed Text /   │
│       │ (Single-file pure python)      │            │ Single Barcode   │
├───────┼────────────────────────────────┼────────────┼──────────────────┤
│ 3.    │ FULL PROOF + JAVA MODELCHECKER │ 5.1 MB     │ Optical Disc /   │
│       │ (Runtime + TLA+ Java Runner)   │            │ Secure Flash     │
└───────┴────────────────────────────────┴────────────┴──────────────────┘
```

---

## 2. Tier 1: Pure Governance Runtime — **378 KB**

If the air-gapped facility already has Python 3.11+, you do **not** need the Java model checker at runtime. You only need the 3 Python wheels:

- `hummbl_governance-1.4.1.whl`: **326 KB**
- `base120-3.0.0.whl`: **30 KB**
- `hummbl_kernel-0.1.0.whl`: **22 KB**
- **TOTAL: 378 KB** *(Compressed: ~180 KB)*

*Fits inside a single 1.44 MB floppy disk with 75% free space, or transfers over low-frequency acoustic / optical diodes in seconds.*

---

## 3. Tier 2: The "Apocalypse / Printed Page" Micro-Kernel — **12 KB**

If an environment is so restricted that binary file transfer is forbidden (e.g., manual OCR or cross-domain human keystroke verification):

- A single, self-contained Python file containing:
  - `KillSwitch` (deterministic file-lock & state flag)
  - `DelegationToken` (pure stdlib HMAC-SHA256 signer/verifier)
  - `CircuitBreaker` (failure sliding window & half-open recovery)
  - `AuditLog` (append-only hash-chained JSONL writer)
- **Total size: ~12 KB**
- **Transfer Method:** Can be printed onto **3 sheets of paper** or encoded as a **single high-density 2D DataMatrix barcode**.

---

## 4. Why 5.1 MB Is Actually Extremely Small

In modern enterprise and defense software contexts:
- A standard Docker container with PyTorch / LangChain: **~4.2 GB - 12 GB** (800x to 2,400x larger).
- A minimal Go binary with Kubernetes client: **~45 MB** (9x larger).
- The Python Standard Library alone: **~35 MB**.

At **378 KB (Runtime)** and **5.1 MB (with full Formal TLA+ Proof Engine)**, HUMMBL is among the lightest production AI governance runtimes in existence.
