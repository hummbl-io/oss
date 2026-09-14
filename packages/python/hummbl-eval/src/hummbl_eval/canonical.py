"""Canonical JSON subset and byte digests.

``hummbl-jcs-1`` deliberately accepts a conservative RFC 8785 subset: floats are
rejected and exact decimals or large integers must be schema-constrained strings.
That keeps stdlib-only Python 3.11 implementations cross-runtime deterministic.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

MAX_SAFE_INTEGER = (2**53) - 1


class CanonicalizationError(ValueError):
    """Input cannot be represented by the HUMMBL canonical JSON profile."""


def _validate(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise CanonicalizationError(f"{path}: integer exceeds interoperable range")
        return
    if isinstance(value, float):
        raise CanonicalizationError(f"{path}: floats are not accepted; use an exact string")
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise CanonicalizationError(f"{path}: invalid Unicode") from exc
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"{path}: object keys must be strings")
            _validate(key, f"{path}.<key>")
            _validate(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, memoryview)):
        for index, item in enumerate(value):
            _validate(item, f"{path}[{index}]")
        return
    raise CanonicalizationError(f"{path}: unsupported type {type(value).__name__}")


def canonicalize_json(value: Any) -> bytes:
    """Return deterministic UTF-8 bytes for the accepted JSON subset."""

    _validate(value)
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return rendered.encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise CanonicalizationError(str(exc)) from exc


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalizationError(f"duplicate object key: {key}")
        result[key] = value
    return result


def load_json(text: str | bytes) -> Any:
    """Parse JSON while rejecting duplicate keys and non-finite numbers."""

    def reject_constant(value: str) -> None:
        raise CanonicalizationError(f"non-finite number: {value}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=reject_constant,
        )
    except CanonicalizationError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    _validate(value)
    return value


def digest_bytes(value: bytes) -> str:
    """Return the framework's lowercase SHA-256 content identifier."""

    return f"sha256:{hashlib.sha256(value).hexdigest()}"
