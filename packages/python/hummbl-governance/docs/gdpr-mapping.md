# GDPR Evidence Mapping — hummbl-governance v1.2.2

**Reference:** Regulation (EU) 2016/679 (General Data Protection Regulation)
**Generated:** 2026-05-14
**Coverage:** 6 articles (Art 5, 6, 25, 28, 30, 32)

---

## Article Mappings

### Art. 5 — Principles (lawfulness, fairness, transparency, purpose limitation)

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| INTENT tuples | INTENT | Captures stated objectives, purpose, and agent identity |

### Art. 6 — Lawfulness of Processing

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| CONTRACT tuples | CONTRACT | Proves consent/contract/legitimate interest basis per operation |

### Art. 25 — Data Protection by Design and by Default

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| DelegationTokenManager | DCT | ops_allowed and resource_selectors restrict scope |
| CapabilityFence | CAPABILITY_FENCE | Enforces minimum-necessary access per agent role |

### Art. 28 — Processor Obligations

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| DelegationTokenManager | DCTX | Delegation chain proves processor binding and scope |

### Art. 30 — Records of Processing Activities

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| DCTX, CONTRACT, ATTEST, EVIDENCE | Multiple | Records who processed what, under whose authority |

### Art. 32 — Security of Processing

| Primitive | Tuple type | Evidence |
|-----------|------------|----------|
| All signed entries | Multiple | Cryptographic integrity proof via HMAC-SHA256 |

---

## Gaps

- Art. 7 (Conditions for consent): Requires UI/legal workflow, not code-level
- Art. 35 (DPIA): Requires organizational risk assessment beyond library scope
- Art. 12–23 (Data subject rights): Require operational processes

---

## Usage

```bash
python -m hummbl_governance.compliance_mapper --framework gdpr --days 30
```

## Boundary

HUMMBL is not a Data Protection Authority. This mapping produces technical evidence artifacts that can support a GDPR compliance program. It does not constitute a legal opinion or a regulatory determination of compliance.
