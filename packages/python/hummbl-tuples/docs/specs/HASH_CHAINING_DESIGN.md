# Hash Chaining Layer Design

Status: draft
Scope: optional Layer 4 integrity extension for tuple accountability chains
Related: issue #29, `schemas/extensions/hash_chaining.schema.json`, `tests/test_hash_chaining.py`

## 1. Why This Matters

Tuples are append-only governance records. Without a linking primitive,
each tuple stands alone — a reviewer can inspect a single record but
cannot easily prove that an unbroken chain of custody connects a
`CONTRACT` to its `EVIDENCE` to its `ASSESS`.

Hash chaining gives tuples a tamper-evident backbone: each tuple can
optionally record the SHA-256 hash of its predecessor, so that any
after-the-fact modification of an earlier tuple breaks the chain
visible to any downstream verifier.

This is **tamper-evidence, not tamper-resistance**. Chaining detects
modification; it does not prevent it. Prevention requires external
storage guarantees, signatures, or append-only logs.

## 2. Design Goals

1. **Optional** — not every use case needs chaining. Tuples without
   `previous_hash` are valid and first-class.
2. **Stdlib only** — SHA-256 via `hashlib`, no third-party crypto.
3. **Frozen-friendly** — chaining produces a new frozen instance; the
   original tuple is never mutated.
4. **Hash excludes integrity fields** — `previous_hash`, `args_hash`,
   and `signature` are excluded from the hash payload so that linking a
   tuple into a chain does not change the hash of its content.
5. **Deterministic serialization** — `json.dumps(..., sort_keys=True)`
   so the same logical tuple always produces the same hash regardless
   of field order.

## 3. Schema Extension

The extension is defined in
`schemas/extensions/hash_chaining.schema.json` and adds three optional
fields to any tuple:

| Field           | Type             | Purpose                                      |
|-----------------|------------------|----------------------------------------------|
| `previous_hash` | `string \| null` | SHA-256 of the predecessor tuple (64 hex)    |
| `args_hash`     | `string \| null` | SHA-256 of tool call arguments, for replay   |
| `signature`     | `string \| null` | Cryptographic signature over tuple content   |

All fields are optional (`required: []`). A tuple with none of them is
unchained; a tuple with `previous_hash` set is linked.

The `previous_hash` pattern is `^[a-f0-9]{64}$` (lowercase SHA-256 hex).

## 4. Hash Computation

The hash of a tuple is computed over its canonical JSON form with
integrity-layer fields removed:

```python
d = asdict(self)
d.pop("timestamp", None)  # legacy alias, excluded for stability
d.pop("previous_hash", None)  # Layer 4 — would be circular
d.pop("args_hash", None)  # Layer 4
d.pop("signature", None)  # Layer 4
stable_json = json.dumps(d, sort_keys=True)
return hashlib.sha256(stable_json.encode("utf-8")).hexdigest()
```

Excluding `previous_hash` from the hash payload is what makes chaining
possible: a tuple's content hash is fixed at creation time, and the
chain link can be set or cleared later without invalidating it.

## 5. API

### 5.1 `with_chain(previous_hash) -> TypedTuple`

Returns a **new** frozen tuple with `previous_hash` set. The original
instance is unchanged. Passing `None` clears the chain link.

Raises `TypeError` if the tuple class does not declare a `previous_hash`
field.

### 5.2 `verify_chain(predecessor_hash) -> bool`

Returns `True` if `self.previous_hash` equals `predecessor_hash`, or if
both are `None` (unchained). Returns `False` on mismatch.

This is a pairwise check — it verifies one link, not the whole chain.
Full-chain verification is the caller's responsibility: walk the chain
tuple by tuple and call `verify_chain` at each step.

## 6. Worked Examples

Three examples live in `examples/hash_chaining/`:

| File             | Tuple type | Role                  | `previous_hash` |
|------------------|------------|-----------------------|-----------------|
| `chain_step1.json` | `CONTRACT`  | Genesis (chain root)  | `null`          |
| `chain_step2.json` | `EVIDENCE`  | Linked to step 1      | 64-hex          |
| `chain_step3.json` | `ASSESS`    | Linked to step 2      | 64-hex          |

The genesis tuple has `previous_hash: null`. Each subsequent tuple
records the hash of its predecessor. Tampering with any earlier tuple
changes its hash, which breaks the `verify_chain` check at the next
tuple in the chain.

## 7. Non-Goals

- **No signature verification** — the `signature` field is reserved but
  signing/verification is out of scope for this extension. It will be
  addressed by a separate cryptographic-signature extension.
- **No chain storage** — this extension defines the on-tuple field and
  the pairwise verify primitive. Chain storage, indexing, and retrieval
  are system-level concerns.
- **No consensus** — there is no notion of a canonical chain. Multiple
  chains can coexist; verification is local to a given sequence.

## 8. Security Considerations

- **SHA-256** is used for hash chaining. As of 2026, SHA-256 has no
  practical collision or preimage attacks.
- **Tamper-evidence only** — an attacker who can rewrite the entire
  chain can recompute all hashes. This extension detects modification
  against a stored reference, not against an adversary who controls
  storage.
- **Deterministic JSON** — `sort_keys=True` is required. Any consumer
  that recomputes hashes must use the same serialization or verification
  will fail silently.
- **Field exclusion** — any future integrity-layer field added to
  `TypedTuple` must also be excluded from the hash payload, or chaining
  will break. The exclusion list is in `TypedTuple.hash` and must be
  kept in sync with the schema extension.
