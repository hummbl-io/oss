# HUMMBL Tuple Conformance Specification v0.1

## Status

- **Concept status:** candidate
- **Canon status:** not canon
- **Issue:** #33 (B1: Build a portable tuple conformance test suite)

## Purpose

A repo-agnostic conformance specification that any downstream implementation of HUMMBL tuples can use to self-verify. Derived from `reference_impl/validate_examples.py` and the schema set in `schemas/`.

## Conformance Requirements

### 1. Envelope Structure (Layer 1)

Every tuple MUST have:

| Field | Type | Constraint |
|-------|------|-----------|
| `tuple_type` | string | Non-empty, must match a known tuple class |
| `id` | string | Non-empty, unique within a trace |
| `time` | string | ISO 8601 timestamp, non-empty |
| `tuple_data` | object | Non-null container for domain fields |

### 2. Governance Fields (Layer 2 — IDP tuples only)

IDP tuples (CONTRACT, DCT, DCTX, SYSTEM, EVIDENCE, ATTEST, PROMOTION_RECEIPT, REVOCATION) MUST have:

| Field | Type | Constraint |
|-------|------|-----------|
| `state` | string | enum: ok, blocked, error |
| `drift` | number | float, >= 0.0 |
| `tier` | integer | >= 0 |
| `agent` | string | Non-empty |
| `tool` | string | Non-empty |

### 3. Integrity Fields (Layer 4 — optional)

If present:

| Field | Type | Constraint |
|-------|------|-----------|
| `signature` | string | Hex string, non-empty |
| `args_hash` | string | SHA-256 hex, 64 chars |
| `previous_hash` | string | SHA-256 hex, 64 chars |

### 4. Tuple Type Constants

Each tuple class has a fixed `tuple_type` value:

| Class | tuple_type | Layer 2 Required? |
|-------|-----------|-------------------|
| CONTRACT | "CONTRACT" | Yes |
| DCT | "DCT" | Yes |
| DCTX | "DCTX" | Yes |
| SYSTEM | "SYSTEM" | Yes |
| EVIDENCE | "EVIDENCE" | Yes |
| ATTEST | "ATTEST" | Yes |
| PROMOTION_RECEIPT | "PROMOTION_RECEIPT" | Yes |
| REVOCATION | "REVOCATION" | Yes |

### 5. Additional Properties

Top-level schemas use `"additionalProperties": false`. Downstream implementations MUST reject tuples with unknown top-level fields. Note: the `tuple_data` container in core schemas (CONTRACT, EVIDENCE, REVOCATION) allows additional properties within `tuple_data` itself, as domain fields vary by tuple class.

### 6. Validation Behavior

A conformant implementation MUST:

1. Reject tuples missing required fields
2. Reject tuples with wrong `tuple_type` const value
3. Reject tuples with invalid enum values
4. Reject tuples with `additionalProperties` violations
5. Accept tuples that match all schema constraints

## Test Vectors

Test vectors are in `conformance/test_vectors.jsonl`. Each vector has:

```json
{
  "vector_id": "string",
  "tuple_type": "string",
  "input": { ... tuple ... },
  "expected_result": "valid" | "invalid",
  "expected_violations": ["gate_name", ...],
  "description": "string"
}
```

## Usage

Downstream implementers:

1. Load test vectors from `conformance/test_vectors.jsonl`
2. For each vector, validate the input tuple against the corresponding schema
3. Compare the result to `expected_result`
4. Report any mismatches as conformance failures

## Do Not Infer

- Do not infer that passing conformance means full HUMMBL compliance
- Do not infer that these test vectors cover all edge cases
- Do not infer that the conformance suite is a substitute for integration testing
- Do not infer that the tuple taxonomy is finalized

## Non-goals

- Not a runtime execution specification
- Not a protocol definition
- Not a replacement for repo-local tests
