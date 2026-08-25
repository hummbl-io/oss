# HUMMBL Typed Tuple Envelope Specification

**draft-hummbl-tuples-governance-00**

## Status

- **Document status:** draft (version 00)
- **Canon status:** not canon
- **Issue:** #36 (B4: Author standards-track draft of tuple envelope specification)
- **Date:** 2026-07-01

## Abstract

This document specifies the HUMMBL Typed Tuple Envelope, a layered data structure for bounded delegation, evidence, and execution control in AI-native systems. The envelope consists of four layers: universal (existence), governance (judgment), domain (context), and integrity (verification). This document defines the wire format, JSON Schema bindings, and design rationale.

## 1. Introduction

### 1.1 Motivation

AI-native systems require auditable governance primitives that can record:
- What work was delegated (CONTRACT)
- What capabilities were granted (DCT)
- What context was provided (DCTX)
- What runtime events occurred (SYSTEM)
- What evidence was produced (EVIDENCE)
- What attestations were made (ATTEST)

Existing log formats lack the typed structure needed for governance auditing. This specification defines a typed tuple envelope that makes governance decisions inspectable, replayable, and verifiable.

### 1.2 Design Goals

1. **Auditability**: Every governance decision is inspectable
2. **Replayability**: Traces can be replayed for debugging
3. **Verifiability**: Integrity layer enables chain verification
4. **Minimality**: Universal layer has only 4 fields
5. **Extensibility**: Domain layer allows per-family fields
6. **Stdlib-only**: Reference implementations use only Python stdlib

### 1.3 Non-goals

- Not a protocol specification (wire transport is out of scope)
- Not a runtime specification (execution semantics are out of scope)
- Not a consensus protocol (distributed agreement is out of scope)

## 2. Layered Envelope Model

The tuple envelope consists of four layers, each adding fields for a specific purpose.

### 2.1 Layer 1: Universal (Existence)

All tuples have Layer 1 fields. These establish the tuple's existence.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tuple_type` | string | yes | Tuple class (CONTRACT, DCT, DCTX, SYSTEM, EVIDENCE, ATTEST) |
| `id` | string | yes | Unique identifier for this tuple |
| `time` | string (date-time) | yes | ISO 8601 timestamp |
| `tuple_data` | object | yes | Tuple payload (domain-specific) |

### 2.2 Layer 2: Governance (Judgment)

Governed tuples (IDP family) have Layer 2 fields. These record governance judgments.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | string | yes | Governance state (ok, blocked, degraded, violated) |
| `drift` | number | conditional | Drift score (0.0-1.0); default 0.0 |
| `tier` | integer | conditional | Governance tier (1-5); default 1 |
| `agent` | string | yes | Agent ID that created this tuple |
| `tool` | string | conditional | Tool used; default "unknown" |

### 2.3 Layer 3: Domain (Context)

Domain-specific fields vary by tuple family. See Section 3 for per-family fields.

### 2.4 Layer 4: Integrity (Verification)

Optional integrity fields for chain verification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signature` | string | no | Cryptographic signature |
| `args_hash` | string | no | Hash of tool call arguments |
| `previous_hash` | string | no | Hash of previous tuple in chain |

## 3. Tuple Classes

### 3.1 CONTRACT

Bounded work definition.

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Governance intent ID |
| `task_id` | string | yes | Task ID |
| `scope` | string | yes | Work scope description |
| `deadline` | string | no | ISO 8601 deadline |

### 3.2 DCT (Delegated Capability Token)

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Governance intent ID |
| `capabilities` | array | yes | List of granted capabilities |
| `expires_at` | string | yes | Expiration timestamp |

### 3.3 DCTX (Delegation Context)

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Governance intent ID |
| `context_type` | string | yes | Context type |
| `context_value` | any | yes | Context value |

### 3.4 SYSTEM

Runtime control-plane event.

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | yes | Event type |
| `source` | string | yes | Event source |

### 3.5 EVIDENCE

Proof of execution.

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Governance intent ID |
| `task_id` | string | yes | Task ID |
| `evidence_type` | string | yes | Evidence type |
| `evidence_data` | any | yes | Evidence payload |

### 3.6 ATTEST

Verification outcome.

**Layers**: 1 + 2 + 3/IDP

**Layer 3 fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intent_id` | string | yes | Governance intent ID |
| `attestation_type` | string | yes | Attestation type |
| `verdict` | string | yes | Verification verdict |

## 4. Wire Format

Tuples are serialized as JSON objects. The canonical wire format is a flat JSON object with all layers merged:

```json
{
  "tuple_type": "CONTRACT",
  "id": "contract-001",
  "time": "2026-07-01T00:00:00Z",
  "state": "ok",
  "drift": 0.0,
  "tier": 1,
  "agent": "agent-alpha",
  "tool": "task-delegator",
  "intent_id": "intent-001",
  "task_id": "task-001",
  "scope": "Analyze dataset X",
  "deadline": "2026-07-02T00:00:00Z",
  "tuple_data": {},
  "signature": "optional",
  "args_hash": "optional",
  "previous_hash": "optional"
}
```

### 4.1 Field Ordering

Field ordering is not significant. Implementations SHOULD preserve insertion order for readability but MUST NOT rely on it.

### 4.2 Unknown Fields

Implementations MUST ignore unknown fields when validating. This allows forward compatibility with new layers.

### 4.3 Encoding

All tuples MUST be encoded as UTF-8 JSON. Implementations MUST NOT use other encodings.

## 5. JSON Schema Bindings

Each tuple class has a corresponding JSON Schema in `schemas/`:

- `schemas/contract.schema.json`
- `schemas/dct.schema.json`
- `schemas/dctx.schema.json`
- `schemas/system.schema.json`
- `schemas/evidence.schema.json`
- `schemas/attest.schema.json`

Schemas use Draft 2020-12. The `$id` field follows the pattern:
```
https://hummbl.dev/schemas/tuples/{schema_name}
```

## 6. Design Rationale

### 6.1 Why Layers?

Layers separate concerns:
- Layer 1 (existence) is needed for all tuples, even research tuples
- Layer 2 (governance) is only needed for governed (IDP) tuples
- Layer 3 (domain) varies by family, allowing extensibility
- Layer 4 (integrity) is optional, adding overhead only when needed

### 6.2 Why Flat (Not Nested)?

A flat structure is easier to:
- Validate with JSON Schema
- Query with standard tools (jq, SQL)
- Serialize and deserialize
- Reason about in documentation

### 6.3 Why `tuple_data` Instead of `payload`?

`tuple_data` is consistent with the tuple metaphor. `payload` is too generic and could be confused with network protocol payloads.

### 6.4 Why Optional Integrity?

Not all use cases require cryptographic verification. Making Layer 4 optional reduces overhead for low-stakes scenarios while enabling it for high-stakes ones.

## 7. Known Limitations

1. **No built-in encryption**: Tuples are plaintext. Encryption is a transport concern.
2. **No built-in access control**: Tuples do not specify who can read them. Access control is a system concern.
3. **No schema evolution**: This draft does not specify how schemas evolve over time. See SCHEMA_VERSIONING.md.
4. **No distributed consensus**: Tuples are local. Distributed agreement is out of scope.
5. **Single-agent authorship**: Each tuple has one `agent` field. Multi-agent co-authorship is not modeled.

## 8. Security Considerations

1. **Integrity**: Layer 4 fields (signature, args_hash, previous_hash) provide integrity but are optional. High-stakes use cases SHOULD use them.
2. **Replay attacks**: The `time` field helps detect replay attacks but is not sufficient. Implementations SHOULD use `previous_hash` for chain verification.
3. **Sensitive data**: Tuples may contain sensitive data in `tuple_data`. Implementations MUST ensure appropriate access controls.
4. **Agent spoofing**: The `agent` field is not authenticated by default. Layer 4 signatures can authenticate the agent.

## 9. IANA Considerations

None. This document does not define any IANA-registries.

## 10. References

- ADR-003: Governance Simulation MVP
- ADR-004: Layered Envelope Architecture
- `docs/specs/TYPED_TUPLE_TAXONOMY.md`: Canonical tuple taxonomy
- `schemas/`: JSON Schema files

## 11. Appendix A: Example Tuples

### 11.1 Minimal CONTRACT Tuple

```json
{
  "tuple_type": "CONTRACT",
  "id": "contract-001",
  "time": "2026-07-01T00:00:00Z",
  "tuple_data": {}
}
```

### 11.2 Full CONTRACT Tuple

```json
{
  "tuple_type": "CONTRACT",
  "id": "contract-001",
  "time": "2026-07-01T00:00:00Z",
  "state": "ok",
  "drift": 0.1,
  "tier": 2,
  "agent": "agent-alpha",
  "tool": "task-delegator",
  "intent_id": "intent-001",
  "task_id": "task-001",
  "scope": "Analyze dataset X",
  "deadline": "2026-07-02T00:00:00Z",
  "tuple_data": {"priority": "high"},
  "signature": "sig-001",
  "args_hash": "hash-001",
  "previous_hash": "hash-000"
}
```

## Do Not Infer

- Do not infer that this draft is a final specification
- Do not infer that the wire format is immutable (future drafts may change it)
- Do not infer that the schema bindings are complete (experimental schemas exist)
- Do not infer that this document constitutes an RFC submission
