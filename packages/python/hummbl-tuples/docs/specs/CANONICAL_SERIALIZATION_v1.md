# Canonical Tuple Serialization v1

Status: candidate
Scope: cross-language byte-identical serialization for HUMMBL tuples
Related: TUPLES_v2.md, HASH_CHAINING_DESIGN.md, conformance/spec.md, issue #33

## 1. Purpose

A tuple's content hash must be identical regardless of which programming language
serialized it. Without canonical serialization, the hash chain breaks silently
across languages: Python, TypeScript, Rust, and Go all serialize JSON differently
in key ordering, float formatting, whitespace, and Unicode handling.

This spec defines the single canonical form. All language implementations MUST
produce byte-identical output for the same logical tuple.

## 2. Design Goals

1. **Byte-identical across languages** — same tuple, same bytes, same hash
2. **Simple enough to implement in any language** — no exotic algorithms
3. **Stable** — the canonical form does not change between versions
4. **Forward-compatible** — new fields can be added without breaking existing hashes
5. **Hash-excludes-integrity** — integrity-layer fields excluded from content hash (per HASH_CHAINING_DESIGN.md)

## 3. Canonical Serialization Rules

### 3.1 Encoding

- UTF-8, no BOM
- JSON object (not array, not bare value)
- Compact form: no whitespace between tokens, no trailing whitespace
- No trailing newline (the changelog appends `\n` as record separator)
- Field order: keys sorted lexicographically by UTF-8 code point order (see §4)

### 3.2 String Escaping

- Standard JSON string escaping per RFC 8259
- `\u` escape ONLY for characters that require it (control characters U+0000-U+001F)
- ASCII printable characters (U+0020-U+007E) are NOT `\u`-escaped
- Non-ASCII characters (U+0080 and above) are emitted as raw UTF-8 bytes, NOT `\u`-escaped
  - Rationale: `\u` escaping is locale-dependent in some implementations; raw UTF-8 is unambiguous
  - This means the canonical form is NOT ASCII-safe — it contains raw UTF-8 bytes
  - Transport layers that require ASCII safety must apply base64 or similar AFTER canonical serialization

### 3.3 Numbers

- **Integers:** bare digits, no leading zeros, no `+` sign, no decimal point
  - `42` not `42.0`, not `+42`, not `042`
- **Floats:** serialized as strings with fixed 4 decimal places
  - `"0.7500"` not `0.75`, not `0.75000000000000004`
  - Rationale: float binary representation differs across languages (IEEE 754 is
    consistent, but string conversion is not). String-serializing with fixed
    precision eliminates the entire class of float-formatting bugs.
  - The string is quoted in JSON: `"0.7500"`
  - Consumers parse the string to float when needed
  - `0.0` → `"0.0000"`, `1.0` → `"1.0000"`, `0.1` → `"0.1000"`
  - Negative: `-0.5` → `"-0.5000"`
  - Special values: `NaN`, `Infinity`, `-Infinity` → `"NaN"`, `"Infinity"`, `"-Infinity"`

### 3.4 Null and Absent

- `null` values are **omitted** (absent key = null, present key = explicit value)
- This is the existing convention in both Python implementations
- An explicit `null` in input is treated the same as an absent key

### 3.5 Arrays

- Preserve insertion order (do NOT sort array elements)
- Arrays of objects: each object is serialized with sorted keys, but array order is preserved
- Empty arrays: `[]` (present, not omitted)

### 3.6 Booleans

- `true` or `false` (lowercase, per JSON spec)

## 4. Key Ordering (Unicode Collation)

Keys are sorted by **UTF-8 code point order** (not locale-dependent string comparison).

This is the same as:
- Python's `sorted()` on `str` (code point order)
- Rust's `BTreeMap<String, _>` (byte order for UTF-8 strings, which is code point order for BMP)
- Go's `sort.Strings()` (byte order, same as code point order for UTF-8)

This is NOT the same as:
- JavaScript's `Array.prototype.sort()` with default comparator (converts to string, then UTF-16 code unit order — differs for non-BMP characters)
- Locale-dependent collation (e.g., `Intl.Collator`)

**For ASCII keys** (which covers all current HUMMBL tuple fields): all implementations agree.
**For non-ASCII keys** (future-proofing for non-English field names): implementations MUST
sort by UTF-8 byte order, which is equivalent to Unicode code point order for the Basic
Multilingual Plane.

**Implementation note for TypeScript/JavaScript:** do NOT use `Array.prototype.sort()`
with default comparator. Use:
```typescript
keys.sort((a, b) => {
  const aBuf = Buffer.from(a, 'utf-8');
  const bBuf = Buffer.from(b, 'utf-8');
  return Buffer.compare(aBuf, bBuf);
});
```

## 5. Hash Computation

The content hash of a tuple is computed over its canonical JSON form with
integrity-layer fields removed (per HASH_CHAINING_DESIGN.md):

```
1. Serialize the tuple to canonical JSON (§3)
2. Remove integrity-layer fields: previous_hash, args_hash, signature
3. Re-serialize with sorted keys (removing fields may change key set)
4. Compute SHA-256 over the UTF-8 bytes of the result
5. The hash is a lowercase hex string (64 characters)
```

**Reconciliation of existing implementations:**
- `hummbl_tuples/base.py` currently excludes: `timestamp, previous_hash, args_hash, signature`
- `basen_tuple.py` currently excludes: `signature` only
- **Canonical (this spec):** exclude `previous_hash, args_hash, signature` only
  - `timestamp` is not a field in TUPLES v2 (it's `time` in Layer 1) — the exclusion in
    `base.py` is a legacy alias and should be removed
  - `args_hash` is excluded because it is itself a hash of tool arguments (including it
    would create a circular dependency if args_hash is computed over the tuple)
  - `signature` is excluded because it is computed over the content hash (including it
    would be circular)
  - `previous_hash` is excluded because chaining links are set after creation (per
    HASH_CHAINING_DESIGN.md §4)

## 6. Separator Standard

**Canonical:** compact separators — `","` and `":"` (no spaces)

This matches `basen_tuple.py` (the runtime implementation). The `base.py` (spec
implementation) must be updated to use compact separators.

**Rationale:** compact form is smaller, produces consistent bytes, and is the
convention in hash-chain systems (Bitcoin, IPFS, etc.).

## 7. Field Naming Convention

All tuple field names are:
- ASCII (no non-ASCII field names)
- snake_case (lowercase with underscores)
- No leading or trailing underscores
- Maximum length: 64 characters

This ensures key ordering is unambiguous across all implementations.

## 8. Language Implementation Notes

### Python
```python
import json
def canonical_json(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
```

### TypeScript
```typescript
function canonicalJson(obj: Record<string, unknown>): string {
  return JSON.stringify(sortKeysByUtf8(obj));
}
function sortKeysByUtf8(obj: Record<string, unknown>): Record<string, unknown> {
  const sorted: Record<string, unknown> = {};
  const keys = Object.keys(obj).sort((a, b) =>
    Buffer.compare(Buffer.from(a, 'utf-8'), Buffer.from(b, 'utf-8'))
  );
  for (const key of keys) {
    const val = obj[key];
    if (val === null || val === undefined) continue;
    if (typeof val === 'number' && !Number.isInteger(val)) {
      sorted[key] = val.toFixed(4);
    } else {
      sorted[key] = val;
    }
  }
  return sorted;
}
```

### Rust
```rust
// Use serde_json with BTreeMap (auto-sorts keys by byte order)
// Floats must be string-serialized before serde_json::to_string
// See reference_impl/rust/src/lib.rs for full implementation
```

### Go
```go
// Use sort.Strings(keys) for key ordering (byte order = UTF-8 code point order)
// Custom encoder for compact JSON with raw UTF-8 and float string-serialization
// See reference_impl/go/tuple.go for full implementation
```

## 9. Conformance

A conformant implementation MUST:
1. Produce byte-identical output to the Python reference for all test vectors
2. Sort keys by UTF-8 code point order
3. Use compact separators (no whitespace)
4. String-serialize floats with 4 decimal places
5. Omit null/absent values
6. Exclude integrity-layer fields from hash computation
7. Compute SHA-256 over the UTF-8 bytes of the canonical form

A conformant implementation MUST NOT:
1. Use locale-dependent string comparison for key sorting
2. Use default JSON.stringify without key sorting
3. Include whitespace in the output
4. Serialize floats as JSON numbers (must be strings)
5. Include integrity-layer fields in the hash payload

## 10. Test Vectors

The existing `conformance/test_vectors.jsonl` has 8 vectors. This spec requires
expanding to at least 20 vectors covering:
- Tuples with only Layer 1 fields
- Tuples with Layer 2 governance fields
- Tuples with Layer 3 domain fields
- Tuples with Layer 4 integrity fields (hash excludes these)
- Tuples with float values (verify string serialization)
- Tuples with non-ASCII string values (verify raw UTF-8)
- Tuples with nested objects (verify recursive key sorting)
- Tuples with arrays (verify insertion order preserved)
- Tuples with empty arrays
- Tuples with null values (verify omission)
- Tuples with boolean values
- Tuples with mixed types

Each vector includes the expected canonical JSON bytes and the expected SHA-256 hash.

## 11. Non-Goals

- This spec does not define transport (how tuples are sent between systems)
- This spec does not define storage (how tuples are persisted)
- This spec does not define the tuple taxonomy (what fields exist)
- This spec does not define governance (who can create tuples)
- This spec does not address natural-language content inside tuple fields (see §12)

## 12. Natural-Language Content (Future)

### 12.1 Audit of Text-Bearing Fields (2026-08-19)

Audit of all 34 schemas identified the following tuple fields that carry
natural-language text and would need `lang` tags in a future i18n extension:

| Field | Schemas | Type |
|---|---|---|
| `override_reason` | bio_override, hitl_override | Free-text justification for overriding a decision |
| `rationale` | control_mode_set | Free-text explanation of control mode choice |
| `notes` | experiment_run_assigned, path_comparison, trace_evidence_record, trace_evidence_tuple | Free-text annotations |
| `selection_rationale` | model_candidate, model_selected, posttraining_trace, transformation_candidate, transformation_selected | Free-text explanation of model/operator selection |
| `reason` | revocation | Free-text reason for revocation |

**Total: 5 field names across 13 schemas.** These are the only fields that carry
natural-language text. All other string fields are identifiers, hashes, enums,
or structured values that don't require language tags.

JSON Schema metadata fields (`title`, `description`) are NOT tuple data — they
are schema documentation and do not need lang tags.

### 12.2 Future Extension Plan

For cross-language TEXT durability (English vs Japanese vs Arabic), a future
v1.1 extension may add:
- A `lang` field tag on text-bearing fields (e.g., `lang: "en"`, `lang: "ja"`)
- Unicode normalization form (NFC recommended for canonical text)
- This is deferred to v1.1 — current spec handles ASCII field names and raw UTF-8 values correctly
- When implemented, the 5 fields above are the complete set that need `lang` tags
