# hummbl-validation

Small, dependency-free validation primitives shared across the HUMMBL fleet:
argument guards, a tolerant JSONL reader, state-file quarantine, and a Package
URL (PURL) parser.

These replace guard clauses that were duplicated across packages. The module is
deliberately minimal — it is not a schema framework and does not compete with
`pydantic` or `jsonschema`.

- MIT OR Apache-2.0
- Python >= 3.11, no runtime dependencies

## Install

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-validation
```

## Argument guards

Each guard returns the validated value so it can be used inline, and raises
`TypeError` or `ValueError` with the offending parameter name.

```python
from hummbl_validation import (
    require_non_negative,
    require_non_empty_str,
    require_type,
)

def schedule(name: str, retries: int) -> None:
    name = require_non_empty_str("name", name)
    retries = require_non_negative("retries", retries)
```

`require_type(name, value, expected_type)` checks `isinstance` and preserves the
value's type for static analysis.

## JSONL reading

`read_jsonl` reads newline-delimited JSON into a list and takes an `on_error` policy —
`"raise"`, `"skip"`, or `"error_dict"` — so a single corrupt line does not have
to abort a whole ingest.

```python
from hummbl_validation import read_jsonl

for record in read_jsonl("events.jsonl", on_error="skip"):
    handle(record)
```

## State quarantine

`quarantine_corrupt_state(path, error_stock=...)` moves an unparseable state
file aside instead of deleting it, so a bad write is recoverable and the next
run can start clean. The caller detects the parse failure and decides when to
quarantine; this function does not parse or validate the file itself.

## Package URLs

```python
from hummbl_validation import parse, normalize

purl = parse("pkg:pypi/Hummbl-Governance@1.5.1")
print(purl.type, purl.name, purl.version)

print(normalize("pkg:PyPI/Some_Pkg@1.0"))
```

`parse()` returns a `PURL` with normalized components; `normalize()` re-emits a
PURL string in canonical form. Both raise `ValueError` on malformed strings and `TypeError` for non-string input.
