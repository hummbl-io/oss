"""Core validation primitives for the HUMMBL fleet.

Each primitive replaces a duplicated pattern identified in the
2026-08-18 audit batch. See hummbl-governance#323.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypeVar

T = TypeVar("T")

OnErrorHandler = Literal["raise", "skip", "error_dict"]


def require_non_negative(name: str, value: int | float) -> int | float:
    """Validate that *value* is non-negative.

    Replaces ~15 duplicated ``if x < 0: raise ValueError(...)`` guards
    across the audit PRs.
    """
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")
    return value


def require_non_empty_str(name: str, value: str) -> str:
    """Validate that *value* is a non-empty string."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def require_type(name: str, value: T, expected_type: type[T]) -> T:
    """Validate that *value* is an instance of *expected_type*."""
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{name} must be {expected_type.__name__}, got {type(value).__name__}"
        )
    return value


def read_jsonl(
    path: str | Path,
    *,
    on_error: OnErrorHandler = "raise",
) -> list[dict[str, Any]]:
    """Read a JSONL file with an explicit error-handling policy.

    Args:
        path: Path to the JSONL file.
        on_error: How to handle corrupt lines:
            - ``"raise"``: raise ``ValueError`` on first corrupt line (default).
            - ``"skip"``: skip corrupt lines with a warning to stderr.
            - ``"error_dict"``: include corrupt lines as ``{"_error": ..., "_line": n}``.

    Returns:
        List of parsed JSON objects.
    """
    results: list[dict[str, Any]] = []
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"JSONL file not found: {p}")

    with open(p, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                if on_error == "raise":
                    raise ValueError(
                        f"Corrupt JSON at {p}:{line_num}: {exc}"
                    ) from exc
                elif on_error == "skip":
                    import sys
                    print(
                        f"WARNING: skipping corrupt line {line_num} in {p}: {exc}",
                        file=sys.stderr,
                    )
                    continue
                elif on_error == "error_dict":
                    results.append({
                        "_error": str(exc),
                        "_line": line_num,
                        "_raw": stripped[:200],
                    })
                    continue
            if isinstance(obj, dict):
                results.append(obj)
            else:
                if on_error == "raise":
                    raise ValueError(
                        f"Non-dict entry at {p}:{line_num}: type={type(obj).__name__}"
                    )
                elif on_error == "skip":
                    import sys
                    print(
                        f"WARNING: skipping non-dict line {line_num} in {p}",
                        file=sys.stderr,
                    )
                    continue
                elif on_error == "error_dict":
                    results.append({
                        "_error": "non-dict entry",
                        "_line": line_num,
                    })
                    continue
    return results


def quarantine_corrupt_state(
    path: str | Path,
    *,
    error_stock: str | Path | None = None,
    alert: bool = False,
) -> Path:
    """Move corrupt persistent state to a quarantine sidecar before reinitializing.

    Implements the quarantine-before-reset convention from hummbl-governance#325.

    1. Moves the corrupt file to ``<path>.corrupt.<timestamp>``
    2. Logs to an append-only error stock (if *error_stock* is provided):
       - File path
       - Detection timestamp
       - SHA-256 hash of corrupt content
       - (optional) error message
    3. If *alert* is True, raises ``RuntimeError`` to halt the caller.

    Args:
        path: Path to the corrupt state file.
        error_stock: Path to an append-only JSONL error log. If None,
            only the sidecar is created.
        alert: If True, raise ``RuntimeError`` after quarantining.

    Returns:
        Path to the quarantined sidecar file.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"State file not found: {p}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sidecar = p.with_suffix(f"{p.suffix}.corrupt.{timestamp}")

    # Compute hash before moving
    content = p.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()

    # Move to sidecar
    shutil.move(str(p), str(sidecar))

    # Set restrictive permissions
    try:
        os.chmod(sidecar, 0o600)
    except OSError:
        pass  # Windows may not support Unix permissions

    # Log to error stock
    if error_stock is not None:
        es = Path(error_stock)
        es.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": timestamp,
            "file": str(p),
            "sha256": sha256,
            "sidecar": str(sidecar),
            "size_bytes": len(content),
        }
        with open(es, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    if alert:
        raise RuntimeError(
            f"Corrupt state quarantined to {sidecar}. "
            f"SHA-256: {sha256}. Halting per security policy."
        )

    return sidecar
