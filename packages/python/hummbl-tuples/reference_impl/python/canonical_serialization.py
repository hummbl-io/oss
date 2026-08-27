"""
Canonical serialization helpers shared across Python tuple implementations.

Per CANONICAL_SERIALIZATION_v1.md:
- Compact separators (no whitespace)
- Keys sorted by UTF-8 code point order
- Non-ASCII emitted as raw UTF-8 (ensure_ascii=False)
- Floats serialized as strings with 4 decimal places
- Null/None values omitted
- Arrays preserve insertion order
"""

import json
import math
from typing import Any


def _stringize_floats(obj: Any) -> Any:
    """Recursively convert floats to strings with 4 decimal places."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj  # bool before int check (bool is subclass of int)
    if isinstance(obj, float):
        if math.isnan(obj):  # NaN
            return "NaN"
        if obj == float("inf"):
            return "Infinity"
        if obj == float("-inf"):
            return "-Infinity"
        return f"{obj:.4f}"
    if isinstance(obj, int):
        return obj
    if isinstance(obj, dict):
        return {k: _stringize_floats(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, (list, tuple)):
        return [_stringize_floats(v) for v in obj]
    return obj


def canonical_json(obj: dict) -> str:
    """Canonical JSON per CANONICAL_SERIALIZATION_v1.md.

    - Compact separators (no whitespace)
    - Keys sorted by UTF-8 code point order
    - Non-ASCII emitted as raw UTF-8 (ensure_ascii=False)
    - Floats serialized as strings with 4 decimal places
    - None values omitted
    """
    prepared = _stringize_floats(obj)
    return json.dumps(prepared, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def canonical_hash(obj: dict, exclude_fields: set[str] | None = None) -> str:
    """Compute SHA-256 content hash of a dict.

    Per CANONICAL_SERIALIZATION_v1.md §5: excludes integrity-layer fields
    (previous_hash, args_hash, signature) by default.
    """
    import hashlib

    d = {k: v for k, v in obj.items() if v is not None}
    exclude = exclude_fields or {"previous_hash", "args_hash", "signature"}
    for field in exclude:
        d.pop(field, None)
    # Also exclude from nested tuple_data
    td = d.get("tuple_data")
    if isinstance(td, dict):
        td = {k: v for k, v in td.items() if v is not None}
        for field in exclude:
            td.pop(field, None)
        d["tuple_data"] = td
    return hashlib.sha256(canonical_json(d).encode("utf-8")).hexdigest()
