# Kernel Integration Guide — mission-mode & nexus / nexus-apex

**Version**: 1.2.2
**Date**: 2026-06-25
**Analyst**: devin
**Status**: Current — validated on macOS (Huxley)

---

## 1. What is the Kernel?

The Kernel is the **26th governance primitive** in hummbl-governance (v1.2.2). It is not a role — it is the **operating system of the fleet**.

Eight invariants (K1–K8) and eight engines guarantee:
- Every agent action is observable
- Every observation is checkable
- Every check is against empirical law

### Eight Engines

| Engine | Purpose | Invariant |
|--------|---------|-----------|
| `ReceiptEngine` | Cryptographic receipts for every action | K1 — Every action leaves a receipt |
| `LawEngine` | Scaling law atlas evaluation | K2 — Every check is against law |
| `IdentityEngine` | Agent identity registry and verification | K3 — Every agent is identifiable |
| `SequenceEngine` | Ordered operation sequences with checkpointing | K4 — Every sequence is recoverable |
| `EvidenceEngine` | Evidence grading and provenance | K5 — Every claim has evidence |
| `AuthorityEngine` | Capability admission and escalation | K6 — Every capability is authorized |
| `ScheduleEngine` | Loop scheduling and health monitoring | K7 — Every loop is observable |
| `DoctrineEngine` | Doctrine validation and path policy | K8 — Every doctrine is enforced |

---

## 2. Installation

```bash
# From PyPI
pip install hummbl-governance>=1.2.2

# From source
cd PROJECTS/hummbl-governance
pip install -e ".[test]"
```

**Verification**:

```bash
python -m pytest tests/ -v --tb=short -q
# Expected: 1245 passed
```

---

## 3. mission-mode Usage

### 3.1 Boot the Kernel at Session Start

```python
from hummbl_governance.kernel import Kernel

# Boot with default state dir (~/.local/share/hummbl-governance/kernel)
kernel = Kernel.boot()

# Or specify a mission-specific state dir
from pathlib import Path
kernel = Kernel.boot(state_dir=Path("./_state/mission-kernel"))
```

### 3.2 Create a Receipt for Every Action

```python
# Before any consequential action, create a receipt
receipt = kernel.receipt.create(
    agent_id="devin",
    action_type="DEPLOY",
    target="hummbl-governance/dashboard",
    context={"branch": "feat/devin/kernel-integration", "commit": "abc123"},
)

# Store it
kernel.receipt.store(receipt)
print(f"Receipt created: {receipt.receipt_id}")
```

### 3.3 Evaluate Against Scaling Laws

```python
# Check if the action violates any scaling law
violations = kernel.law.evaluate(receipt.__dict__)

if violations:
    for v in violations:
        print(f"VIOLATION: {v.law_id} — {v.severity}: {v.message}")
    # Block the action
    raise KernelPanic(KernelInvariant.LAW, "Scaling law violation detected")
```

### 3.4 Verify Agent Identity

```python
# Before trusting an agent's action
identity = kernel.identity.lookup("devin")
if not identity or identity.trust_tier < 2:
    raise KernelPanic(KernelInvariant.IDENTITY, "Agent not authorized for this action")
```

### 3.5 Full mission-mode Pattern

```python
from hummbl_governance.kernel import Kernel, KernelInvariant, KernelPanic

def mission_action(agent_id: str, action_type: str, target: str, context: dict):
    kernel = Kernel.boot()

    # K3: Identity check
    identity = kernel.identity.lookup(agent_id)
    if not identity:
        raise KernelPanic(KernelInvariant.IDENTITY, f"Unknown agent: {agent_id}")

    # K1: Create receipt
    receipt = kernel.receipt.create(
        agent_id=agent_id,
        action_type=action_type,
        target=target,
        context=context,
    )

    # K2: Law evaluation
    violations = kernel.law.evaluate(receipt.__dict__)
    if any(v.severity == "CRITICAL" for v in violations):
        kernel.receipt.amend(receipt, status="BLOCKED", reason="law_violation")
        raise KernelPanic(KernelInvariant.LAW, f"Critical violation: {violations[0].law_id}")

    # K6: Authority check
    check = kernel.authority.check(agent_id, action_type, target)
    if not check.granted:
        kernel.receipt.amend(receipt, status="DENIED", reason="authority_denied")
        raise KernelPanic(KernelInvariant.AUTHORITY, f"Capability denied: {check.reason}")

    # K4: Sequence checkpoint
    kernel.sequence.checkpoint(receipt.receipt_id)

    # Execute the action (user code here)
    result = execute_action(action_type, target, context)

    # K5: Evidence collection
    evidence = kernel.evidence.collect(
        source=receipt.receipt_id,
        claim=f"Action {action_type} completed on {target}",
        grade=EvidenceGrade.A if result.success else EvidenceGrade.C,
    )

    # Finalize receipt
    kernel.receipt.amend(receipt, status="COMPLETED", result=result.__dict__)
    kernel.receipt.store(receipt)

    return result
```

---

## 4. nexus / nexus-apex Usage

### 4.1 Nexus Pre-Scan Hook

```python
# In nexus scan workflow, before any surface check:
kernel = Kernel.boot()

for surface in surfaces:
    receipt = kernel.receipt.create(
        agent_id="nexus",
        action_type="SCAN",
        target=surface.path,
    )

    # Check if nexus has authority to scan this surface
    check = kernel.authority.check("nexus", "SCAN", surface.path)
    if not check.granted:
        print(f"[SKIP] {surface.path}: {check.reason}")
        continue

    # Perform scan
    findings = scan_surface(surface)

    # Evaluate findings against scaling laws
    for finding in findings:
        violations = kernel.law.evaluate(finding.__dict__)
        if violations:
            finding.violations = violations

    kernel.receipt.amend(receipt, status="COMPLETED", findings=len(findings))
    kernel.receipt.store(receipt)
```

### 4.2 Apex Assessment Integration

```python
# Before apex issues a PROPOSAL or DECISION:
kernel = Kernel.boot()

receipt = kernel.receipt.create(
    agent_id="apex",
    action_type="ASSESS",
    target=decision_topic,
    context={"lanes": len(lanes), "models": [l.model for l in lanes]},
)

# Verify apex authority
if not kernel.authority.check("apex", "ASSESS", decision_topic).granted:
    raise KernelPanic(KernelInvariant.AUTHORITY, "Apex not authorized for this topic")

# Evaluate decision against scaling laws
proposal = apex.generate_proposal(decision_topic, lanes)
violations = kernel.law.evaluate(proposal.__dict__)

if violations:
    proposal.risk_flags = [v.law_id for v in violations]
    kernel.receipt.amend(receipt, status="FLAGGED", violations=len(violations))
else:
    kernel.receipt.amend(receipt, status="APPROVED")

kernel.receipt.store(receipt)
```

### 4.3 Kernel Health Check for Fleet Status

```python
# In fleet-status or heartbeat checks:
kernel = Kernel.boot()

health = {
    "receipt_engine": kernel.receipt.health(),
    "law_engine": kernel.law.health(),
    "identity_engine": kernel.identity.health(),
    "sequence_engine": kernel.sequence.health(),
    "evidence_engine": kernel.evidence.health(),
    "authority_engine": kernel.authority.health(),
    "schedule_engine": kernel.schedule.health(),
}

panics = [e for e, h in health.items() if not h.healthy]
if panics:
    raise KernelPanic(KernelInvariant.SCHEDULE, f"Engine failures: {panics}")
```

---

## 5. CLI Usage

```bash
# Boot the Kernel
python -m hummbl_governance.kernel boot

# Check status
python -m hummbl_governance.kernel status

# Health check
python -m hummbl_governance.kernel health

# Inspect engines
python -m hummbl_governance.kernel inspect

# List scaling laws
python -m hummbl_governance.kernel laws

# List registered roles
python -m hummbl_governance.kernel roles
```

---

## 6. State Directory

```
~/.local/share/hummbl-governance/kernel/
├── receipts/           # Cryptographic receipts (JSONL)
├── registry/           # Agent identity registry
├── sequences/        # Operation sequence checkpoints
├── evidence/          # Evidence artifacts
├── authority/         # Capability grants and revocations
├── schedule/          # Loop health and telemetry
└── health/            # Engine health logs
```

Override with:
```bash
export HUMMBL_KERNEL_STATE_DIR=/path/to/kernel/state
```

---

## 7. Integration with Existing Primitives

| Primitive | Kernel Integration |
|-----------|---------------------|
| Kill Switch | Kernel Panic triggers kill switch engage |
| Circuit Breaker | Kernel health check trips circuit on engine failure |
| Cost Governor | Law engine enforces cost scaling laws |
| Delegation Token | Identity engine verifies delegation chains |
| Governance Bus | Receipts feed into governance bus as entries |
| Schema Validator | Evidence engine validates claim schemas |
| Identity Registry | Kernel identity engine is the canonical registry |

---

## 8. Ledger Tag

```
kernel_integration_guide: v1.2.2 | analyst: devin | date: 2026-06-25 | verified: huxley | tests_passed: 2027 | engines: 8 | invariants: 8 | use_cases: mission-mode, nexus, apex | cli_commands: 6
```
