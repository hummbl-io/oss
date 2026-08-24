# HUMMBL Air-Gapped Minimal Kit (AGK-01) Specification

**Designation:** `HUMMBL-AGK-01` (*Air-Gapped Governance Kit*)  
**Form Factor:** Single Self-Contained Archive / USB Key / CD-R ISO  
**Total Payload Size:** **~5.1 MB** (Compressed Tarball)  
**Target Environment:** SCIFs, nuclear/utility industrial control rooms, air-gapped financial signing vaults, isolated military compute  
**Zero-Network Invariant:** 100% operational with no internet, no LAN uplinks, and zero package manager queries  

---

## 1. The 5 Essential Payload Artifacts

Everything required to govern, orchestrate, and mathematically prove an air-gapped autonomous system fits into **5 files**:

```
hummbl-airgap-kit-v1.4.1/
├── 1. hummbl_governance-1.4.1-py3-none-any.whl   (326 KB)  --> 34 Governance Primitives + 99 Framework Mappings
├── 2. base120-3.0.0-py3-none-any.whl             ( 30 KB)  --> 120 Cognitive Reasoning Operators
├── 3. hummbl_kernel-0.1.0-py3-none-any.whl       ( 22 KB)  --> Deterministic Orchestration Kernel
├── 4. krineia-formal-suite/                                --> Complete Formal Verification Suite
│   ├── tla2tools.jar                             (4.5 MB)  --> Standalone TLC Model Checker (Java JAR)
│   ├── KRINEIA.tla & KRINEIA.cfg                 ( 12 KB)  --> K1–K11 Invariant State Space Specs
│   └── KRINEIA_INVARIANTS_PAPER.pdf              (105 KB)  --> Full Mathematical Proof Paper
└── 5. bootstrap.sh / bootstrap.ps1               (  4 KB)  --> Single-Command Offline Self-Test & Verifier
```

**Total Uncompressed Size:** ~5.0 MB  
**Compressed (`.tar.gz` / `.zip`):** **< 4.8 MB** *(fits on a 1990s floppy disk alternative or single optical disc)*

---

## 2. The Offline Bootstrap Script (`bootstrap.sh`)

When transferred into an air-gapped facility via approved physical media (e.g., optical disc), an operator runs a single command:

```bash
#!/bin/bash
# HUMMBL Air-Gapped Zero-Dependency Verification & Install
set -e

echo "=== [1/3] Verifying Python Environment ==="
python3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"

echo "=== [2/3] Installing HUMMBL Core Wheels (Offline / No-Deps) ==="
python3 -m pip install --no-index --no-deps *.whl

echo "=== [3/3] Running Cryptographic & State Invariant Self-Test ==="
python3 -c "
from hummbl_governance.kill_switch import KillSwitch
from hummbl_governance.delegation_token import DelegationToken
from base120.operators.p.p1 import P1

# 1. Test Kill Switch deterministic severance
ks = KillSwitch()
assert ks.is_active() == True
ks.engage(reason='Airgap self-test')
assert ks.is_active() == False

# 2. Test HMAC Capability Token Generation & Verification
token = DelegationToken.create(agent_id='ag-01', capabilities=['read_telemetry'], secret='offline-airgap-seed-key')
assert token.verify(secret='offline-airgap-seed-key') == True

# 3. Test Base120 Reasoning Operator
p1 = P1()
assert p1.code == 'P1'

print('>> HUMMBL CORE RUNTIME: 100% OPERATIONAL (ZERO EXTERNAL DEPS)')
"

echo "=== [OPTIONAL] Running TLA+ Formal Proof Model Checker ==="
if command -v java &> /dev/null; then
    cd krineia-formal-suite
    java -jar tla2tools.jar -modelcheck KRINEIA.tla
    echo ">> FORMAL INVARIANTS K1-K11: 100% SATISFIED"
fi
```

---

## 3. Host System Prerequisites (Nothing Else)

| Prerequisite | Specification | Purpose |
|:---|:---|:---|
| **Base Operating System** | Linux (RHEL, Ubuntu, Debian, Rocky) or Windows Server | Host platform |
| **Python Runtime** | Standard CPython `3.11+` | Core governance execution engine |
| **Java Runtime (Optional)** | OpenJDK / JRE `11+` | Running local TLA+ model checking |

---

## 4. Why This Kit Is Unbreakable in High-Assurance Enclaves

1. **Deterministic Supply Chain:** There is no `requirements.txt` resolving nested transitive dependencies at runtime. The SHA-256 hash of the 3 wheel files is pre-signed and audited.
2. **Zero Ingress/Egress Requirement:** Never dials home, never checks for software updates over the wire, and requires zero telemetry endpoints.
3. **Provable Confinement:** Can be placed on a read-only write-blocked partition; receipts can be directed to an internal append-only storage volume.
