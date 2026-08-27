# HUMMBL Contingency Plan

**Version:** 1.0
**Scope:** All packages in `hummbl-io/oss`
**Reference:** NIST SP 800-53 Rev 5 CP-2 (Contingency Plan), CP-9 (System Backup), CP-10 (System Recovery)

---

## 1. Purpose

This document defines the contingency planning posture for HUMMBL OSS packages.
It identifies the runtime primitives that support continuity and recovery, the
gaps that require organizational procedures, and the deployment-level controls
operators must implement.

## 2. Runtime Continuity Primitives

The following primitives are implemented in code and provide runtime-level
contingency support:

| Primitive | Package | CP Control | Function |
|-----------|---------|------------|----------|
| `CircuitBreaker` | `hummbl-governance` | CP-2 | Failure detection, automatic recovery (CLOSED→OPEN→HALF_OPEN) |
| `KillSwitch` | `hummbl-governance` | CP-2 | Graduated halt (DISENGAGED→HALT_NONCRITICAL→HALT_ALL→EMERGENCY) |
| `RecoveryVerifier` | `hummbl-governance` | CP-10 | Post-incident recovery verification |
| `CostGovernor` | `hummbl-governance` | CP-2 | Budget reallocation after incidents |
| `ReceiptIntegrityMonitor` | `hummbl-governance` | CP-9 | Detects audit log corruption (gaps, hash-chain breaks) |
| `ReplayLedger` | `hummbl-bus` | CP-9 | Append-only record of accepted bus writes for replay |
| `AuditLog` (rotation + retention) | `hummbl-governance` | CP-9 | Daily rotation, configurable retention (default 180 days) |

## 3. Operator Responsibilities

The following controls are **not** implemented in code and require operator
action at the deployment level:

### CP-9: System Backup

- **Audit logs:** Back up the `AuditLog` directory daily. Logs rotate daily
  and compress to `.jsonl.gz` after 10MB. Retention is 180 days by default.
- **Bus TSV files:** Back up the coordination bus file. The `ReplayLedger`
  provides an append-only record but is not a substitute for off-site backup.
- **Receipt files:** Back up the `ReceiptEngine` JSONL file and the HMAC secret
  file. Loss of the HMAC key means historical receipts cannot be verified.
- **Ed25519 keys:** Back up the principal key file referenced by
  `BUS_PRINCIPAL_PUBLIC_KEY_FILE`. Loss of the private key means historical
  bus messages cannot be re-verified.

### CP-10: System Recovery

- **RTO (Recovery Time Objective):** Define per deployment. For single-host
  bus deployments, RTO is typically the time to restore the host and restart
  the bus daemon.
- **RPO (Recovery Point Objective):** Defined by the backup cadence. With
  daily backups, RPO is up to 24 hours of bus writes.
- **Recovery procedure:**
  1. Restore host (if hardware failure)
  2. Restore bus TSV file from backup
  3. Restore audit log directory from backup
  4. Restore HMAC secret file and Ed25519 keys
  5. Restart bus daemon and agents
  6. Run `ReceiptIntegrityMonitor` to verify audit chain integrity
  7. Run `bus_verifier` to verify bus message signatures
  8. Verify `CircuitBreaker` states are reset to CLOSED

### CP-2: Contingency Plan

- **Testing cadence:** Test the recovery procedure at least annually.
- **Alternate processing:** For multi-host deployments, designate a standby
  host that can assume the bus writer role.
- **Communication plan:** Define who is notified when the KillSwitch is
  activated or the CircuitBreaker enters OPEN state.

## 4. Gap Register

| Gap | Priority | Mitigation |
|-----|----------|------------|
| No automated backup procedure | P2 | Operator implements cron-based or managed backup |
| No failover automation | P2 | Operator designates standby host; bus writer role is transferable |
| No RTO/RPO defined in code | P3 | Deployment-specific; documented here as guidance |
| No automated recovery testing | P3 | Operator schedules annual recovery test |
| No alternate processing site | P3 | Deployment-specific; not applicable to single-host OSS |

## 5. Incident-to-Contingency Bridge

When an incident triggers `KillSwitch(EMERGENCY)` or `CircuitBreaker(OPEN)`:

1. **Immediate:** The system halts non-critical or all operations automatically.
2. **Assessment:** Operator reviews audit log and bus state to determine cause.
3. **Containment:** Operator may isolate the affected host or revoke DCTs.
4. **Recovery:** Operator follows the CP-10 recovery procedure above.
5. **Re-entry:** `CircuitBreaker(HALF_OPEN)` allows limited retry; operator
   monitors before returning to `CLOSED`.

## 6. Review Cadence

This plan should be reviewed:
- When new continuity primitives are added to the codebase
- When deployment topology changes (single-host → multi-host)
- Annually, as part of the security review cycle
- After any incident that activates the KillSwitch or CircuitBreaker
