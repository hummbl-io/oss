# HUMMBL Tuple Reference Implementations

Cross-language reference implementations of the HUMMBL Typed Tuple specification.

All implementations produce **byte-identical** canonical JSON and SHA-256 hashes
per [CANONICAL_SERIALIZATION_v1.md](../../docs/specs/CANONICAL_SERIALIZATION_v1.md).

## Implementations

| Language | Directory | Status | Dependencies |
|----------|-----------|--------|--------------|
| Python | `python/` | ✅ Live | stdlib only |
| TypeScript | `typescript/` | ✅ Live | Node.js stdlib |
| Go | `go/` | ✅ Live (9 tests, 8 conformance vectors) | stdlib only |
| Rust | `rust/` | 📝 Written (cargo not installed for testing) | serde_json, sha2 |

## Canonical Serialization Rules

1. **Compact JSON** — no whitespace between tokens
2. **Sorted keys** — UTF-8 byte order (not locale-dependent)
3. **Raw UTF-8** — non-ASCII characters not `\u`-escaped
4. **Nulls omitted** — absent key = null, present key = explicit value
5. **Floats as strings** — 4 decimal places (`0.75` → `"0.7500"`)
6. **Arrays preserve order** — do not sort array elements
7. **Integrity fields excluded from hash** — `previous_hash`, `args_hash`, `signature`

## Running Tests

### Python
```bash
python validate_examples.py
```

### TypeScript
```bash
npx ts-node conformance_test.ts
```

### Go
```bash
cd go && go test -v
```

### Rust
```bash
cd rust && cargo test
```

### Cross-Language Verification
```bash
python cross_lang_verify.py
```

## Conformance

Each implementation must pass the [conformance test vectors](../../conformance/test_vectors.jsonl)
and produce identical SHA-256 hashes for the same logical tuple.
