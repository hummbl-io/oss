# Audit Surface Minimization Report

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #41 (C3: Define minimum tuple fields needed for reliable auditing)
- **Date:** 2026-07-01

## Summary

This report determines which tuple fields can be dropped without losing auditability, trading off verbosity against safety. The analysis is based on the full tuple schema, simulation traces, and synthetic incident scenarios.

## Current Full Tuple Fields

### Layer 1 (Universal) — 4 fields
| Field | Required for audit? | Rationale |
|-------|---------------------|-----------|
| tuple_type | YES | Without type, auditor cannot classify the event |
| id | YES | Without id, auditor cannot reference or order events |
| time | YES | Without time, auditor cannot build a timeline |
| tuple_data | YES | Without data, auditor cannot inspect what happened |

### Layer 2 (Governance) — 5 fields
| Field | Required for audit? | Rationale |
|-------|---------------------|-----------|
| state | YES | Without state, auditor cannot determine if governance was violated |
| drift | CONDITIONAL | Required for drift analysis; can be defaulted to 0.0 if absent |
| tier | CONDITIONAL | Required for tier-based policy checks; can be defaulted to 1 if absent |
| agent | YES | Without agent, auditor cannot attribute actions |
| tool | CONDITIONAL | Required for tool-level audits; can be "unknown" if absent |

### Layer 3 (Domain) — varies
| Field | Required for audit? | Rationale |
|-------|---------------------|-----------|
| intent_id | YES | Links tuples to governance intent |
| task_id | YES | Links tuples to specific tasks |
| Domain-specific fields | NO | Only needed for domain-level analysis, not core audit |

### Layer 4 (Integrity) — optional
| Field | Required for audit? | Rationale |
|-------|---------------------|-----------|
| signature | NO | Only needed for cryptographic verification |
| args_hash | NO | Only needed for tool-call integrity |
| previous_hash | NO | Only needed for chain verification |

## Minimum Audit Surface

The minimum set of fields required for reliable auditing:

```json
{
  "tuple_type": "CONTRACT",
  "id": "unique-id",
  "time": "2026-07-01T00:00:00Z",
  "state": "ok",
  "agent": "agent-id",
  "intent_id": "intent-id",
  "task_id": "task-id",
  "tuple_data": {}
}
```

**7 fields** (down from 11-14 in the full schema).

## Fields That Can Be Dropped

| Field | Impact of dropping | Mitigation |
|-------|-------------------|------------|
| drift | Cannot detect drift trends | Default to 0.0; flag missing drift for review |
| tier | Cannot enforce tier-based policies | Default to tier 1 (most restrictive); flag missing tier |
| tool | Cannot audit tool-level behavior | Use "unknown"; flag for follow-up |
| signature | Cannot cryptographically verify | Accept on trust; flag for high-stakes audits |
| args_hash | Cannot verify tool-call integrity | Accept on trust; flag for high-stakes audits |
| previous_hash | Cannot verify chain integrity | Accept on trust; flag for chain audits |

## Fields That Must NOT Be Dropped

| Field | Why it's critical |
|-------|-------------------|
| tuple_type | Without it, the tuple is unclassifiable |
| id | Without it, the tuple cannot be referenced or ordered |
| time | Without it, no timeline can be constructed |
| state | Without it, governance violations are invisible |
| agent | Without it, actions cannot be attributed |
| intent_id | Without it, tuples cannot be linked to governance intent |
| task_id | Without it, tuples cannot be linked to specific tasks |
| tuple_data | Without it, the tuple has no content to audit |

## Trade-off: Verbosity vs Safety

### Full tuple (14 fields)
- **Verbosity**: High (each tuple is ~200-400 bytes)
- **Safety**: Maximum (all audit dimensions covered)
- **Use case**: High-stakes governance, legal audit, compliance

### Minimum tuple (7 fields)
- **Verbosity**: Low (each tuple is ~100-150 bytes)
- **Safety**: Reduced (no drift, tier, or tool tracking)
- **Use case**: Internal monitoring, development, low-risk operations

### Recommended tuple (9 fields)
- **Verbosity**: Medium (each tuple is ~150-200 bytes)
- **Safety**: Good (includes drift and tier as defaults)
- **Use case**: Production governance with reasonable overhead

```json
{
  "tuple_type": "CONTRACT",
  "id": "unique-id",
  "time": "2026-07-01T00:00:00Z",
  "state": "ok",
  "drift": 0.0,
  "tier": 1,
  "agent": "agent-id",
  "intent_id": "intent-id",
  "task_id": "task-id",
  "tuple_data": {}
}
```

## Empirical Testing Approach

### Test 1: Gemini Incident Corpus
Run the minimum tuple set against the Gemini probation incident corpus. Can the auditor reconstruct the incident timeline with only 7 fields?

### Test 2: Synthetic Scenarios
Generate synthetic scenarios with varying tuple completeness. Measure audit accuracy as fields are removed.

### Test 3: Storage Comparison
Measure storage size for full vs minimum vs recommended tuples at scale (1K, 10K, 100K tuples).

## Do Not Infer

- Do not infer that the minimum tuple set is sufficient for all audit scenarios
- Do not infer that dropping fields is always safe (context matters)
- Do not infer that the recommended set is final (empirical testing may change it)
- Do not infer that this report constitutes a compliance recommendation

## Non-goals

- Not a compliance framework
- Not a storage optimization guide
- Not a field removal recommendation for production
