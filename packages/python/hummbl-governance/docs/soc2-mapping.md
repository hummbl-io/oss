# SOC 2 Mapping — hummbl-governance v1.2.2

**Reference:** AICPA Trust Service Criteria (TSC 2017)
**Generated:** 2026-05-14
**Coverage:** 3 controls (CC6.1, CC6.3, CC7.2)

---

## Control Mappings

### CC6.1 — Logical Access Security

| Attribute | Value |
|-----------|-------|
| Primitive | DelegationTokenManager |
| Tuple type | DCT |
| Evidence | Per-token issuer/subject/ops_allowed/resource_selectors |
| Test | `test_dct_maps_to_cc61` |

Each DCT tuple cryptographically binds an issuer to a subject with scoped operations and resources. This proves that logical access is authorized, scoped, and auditable.

### CC6.3 — Identity & Authentication

| Attribute | Value |
|-----------|-------|
| Primitive | AgentRegistry + DelegationTokenManager |
| Tuple type | DCT |
| Evidence | Subject/issuer identity records with trust tiers |
| Test | `test_dct_maps_to_cc63` |

AgentRegistry canonicalization resolves aliases to identities. Trust tiers (low/medium/high) map to authentication assurance levels.

### CC7.2 — Monitoring & Logging

| Attribute | Value |
|-----------|-------|
| Primitive | AuditLog + BusWriter |
| Tuple type | All signed entries |
| Evidence | HMAC-SHA256 signed append-only bus entries |
| Test | `test_signed_maps_to_cc72` |

Every governance event with a cryptographic signature provides continuous monitoring evidence per CC7.2.

---

## Gaps

- CC5.x (Governance): Organizational controls requiring board/management oversight
- CC6.2, CC6.4–CC6.8: Additional access management controls
- CC7.1, CC7.3–CC7.5: Operations and change management
- CC8.x: Change management controls
- CC9.x: Risk mitigation controls

---

## Usage

```bash
python -m hummbl_governance.compliance_mapper --framework soc2 --days 7
```

Generates a `ComplianceReport` with per-control JSON evidence arrays.

## Boundary

HUMMBL is not a SOC 2 auditor. This mapping produces technical evidence artifacts. A SOC 2 Type II examination requires an accredited CPA firm. The primitives support — but do not replace — that examination.
