# Invariant Decision Recommendation: K9-K11, D6-D7

**Status:** APPROVED_WITH_CONSTRAINTS — enum promotion of K9-K11 and D6-D7 approved by operator 2026-06-26
**Date:** 2026-06-26 (corrected from 2026-07-14 — original was future-dated relative to session)
**Steward:** HUMMBL Research Institute
**Decision needed:** Should K9-K11 be added to `KernelInvariant` enum (KernelPanic on violation) or kept as doctrine-level guidance? Same for D6-D7 in `DoctrineInvariant` enum.
**Receipt note:** Original date `2026-07-14` was future-dated relative to the actual session date `2026-06-26`. Corrected with this receipt note per operator instruction.

---

## Context

The primitive expansion (`hummbl-primitive-expansion-v0.1.md`) proposed 5 new invariants:

| ID | Name | Invariant | Proposed primitive | Status |
|---|---|---|---|---|
| K9 | REVERSIBILITY | Every governed action declares a rollback path or is explicitly marked irreversible | P28 Rollback | Implemented |
| K10 | RECOVERY | Re-engagement after halt requires root-cause verification and operator approval | P29 RecoveryVerifier | Implemented |
| K11 | INTEGRITY | Receipt sequences are complete and unbroken | P30 ReceiptIntegrityMonitor | Implemented |
| D6 | CONTESTABILITY | Affected parties can flag AI decisions for human review | P31 Contestability | Not started |
| D7 | DOCTRINE_AMENDMENT | Changes to invariants themselves are governed | P38 DoctrineAmendment | Not started |

## Decision framework

**Kernel invariant (K-series):** Violation causes `KernelPanic` — the Kernel halts, isolates, or quarantines the violating agent. This is the strongest enforcement. Use for invariants where violation means the system's integrity is fundamentally compromised.

**Doctrine invariant (D-series):** Violation prevents stage promotion (playground → sandbox → innovations → fleet) but doesn't cause a KernelPanic. The agent can continue operating but cannot promote its work. Use for invariants where violation is a governance process failure, not a system integrity failure.

**Guidance only (no enum):** No automated enforcement. Documented as best practice. Use for invariants that are aspirational or where automated enforcement would be premature.

---

## Recommendations

### K9 REVERSIBILITY → **Add to KernelInvariant enum**

**Reasoning:** Reversibility is a system integrity property. An irreversible action without a recorded risk acceptance means the system has made a binding commitment without governance — this is a fundamental integrity violation, not a process failure. P28 Rollback already enforces this at the schema level; adding K9 to the enum makes violation a KernelPanic.

**Risk:** Some legitimate actions are irreversible (e.g., sending an email, making a payment). K9 doesn't prohibit irreversibility — it requires that irreversibility be explicitly accepted with a recorded risk. This is compatible with real-world operations.

**Confidence:** 0.85

### K10 RECOVERY → **Add to KernelInvariant enum**

**Reasoning:** Re-engagement after halt without root-cause verification is a safety violation. If the system halted because of a bug, re-engaging without fixing the bug will reproduce the failure. This is directly analogous to K1 (RECEIPT) — it's a fundamental integrity property. P29 RecoveryVerifier already enforces this at the schema level.

**Risk:** K10 could slow recovery in urgent situations. Mitigation: the operator can approve re-engagement with conditions (gradual/canary strategy) rather than blocking it entirely.

**Confidence:** 0.85

### K11 INTEGRITY → **Add to KernelInvariant enum**

**Reasoning:** Receipt integrity is the foundation of the entire governance system. If receipt sequences have gaps or hash chains are broken, every receipt is suspect — this directly undermines K1 (RECEIPT) and K4 (TEMPORAL). K11 is not a new invariant but an enforcement mechanism for K1 and K4. Adding it to the enum makes detection automatic.

**Risk:** False positives from clock skew or network partitions could cause unnecessary panics. Mitigation: P30 ReceiptIntegrityMonitor distinguishes between sequence gaps (K4), hash chain breaks (K1), and timestamp anomalies — only the first two should trigger KernelPanic; timestamp anomalies should be warnings.

**Confidence:** 0.9

### D6 CONTESTABILITY → **Add to DoctrineInvariant enum**

**Reasoning:** Contestability is a governance process property, not a system integrity property. If an AI decision cannot be contested, the system is operating without human oversight — but this is a process failure (the agent shouldn't be promoted to fleet stage), not a system integrity failure (the receipts are still valid). D-series is the right level.

**Risk:** D6 could be used to block legitimate decisions through frivolous contestation. Mitigation: D6 should require evidence or justification for the contest, not just a bare flag.

**Confidence:** 0.75

### D7 DOCTRINE_AMENDMENT → **Add to DoctrineInvariant enum**

**Reasoning:** Changes to invariants without governance is a meta-governance failure. If invariants can be changed without operator approval, the entire governance system is compromised — but this is a process failure (the change shouldn't be promoted), not a system integrity failure (the existing invariants are still valid). D-series is the right level.

**Risk:** D7 could slow legitimate invariant evolution. Mitigation: D7 should have a fast-track for urgent invariant changes (e.g., security vulnerabilities) with post-hoc ratification.

**Confidence:** 0.8

---

## Summary recommendation

| Invariant | Recommendation | Confidence | Enforcement level |
|---|---|---|---|
| K9 REVERSIBILITY | Add to `KernelInvariant` enum | 0.85 | KernelPanic |
| K10 RECOVERY | Add to `KernelInvariant` enum | 0.85 | KernelPanic |
| K11 INTEGRITY | Add to `KernelInvariant` enum | 0.9 | KernelPanic |
| D6 CONTESTABILITY | Add to `DoctrineInvariant` enum | 0.75 | Stage promotion block |
| D7 DOCTRINE_AMENDMENT | Add to `DoctrineInvariant` enum | 0.8 | Stage promotion block |

**All 5 should be added to their respective enums.** None should remain as guidance-only — the primitives that enforce them (P28-P30 implemented, P31/P38 proposed) are designed for automated enforcement.

## Implementation plan (pending operator approval)

1. Add K9, K10, K11 to `KernelInvariant` enum in `invariants.py`
2. Add D6, D7 to `DoctrineInvariant` enum in `doctrine_engine.py`
3. Update docstrings: "eight" → "eleven" and "five" → "seven"
4. Update PRIMITIVES.md invariant tables
5. Add tests verifying K9-K11 and D6-D7 are recognized by the enum
6. Wire P28-P30 enforcement to raise `KernelPanic(K9/K10/K11)` on violation

## Operator decision

- [x] Approve K9-K11 as KernelInvariant enum values (KernelPanic enforcement) — APPROVED 2026-06-26
- [x] Approve D6-D7 as DoctrineInvariant enum values (stage promotion block) — APPROVED 2026-06-26
- [x] Constraints: K9 scoped to durable-state mutations + irreversible external side effects; K10 scoped to re-engagement after halt/quarantine/open breaker; K11 sequence/hash only (timestamp anomalies are warnings); D6 requires evidence for contest; D7 blocks ungated amendments
