# Copyright 2024-2026 HUMMBL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Write path for the Cognitive Ledger.

Append-only JSONL storage with an exclusive inter-process lock.
Entry schema mirrors the existing on-disk ledger (12 keys):

    id, type, assurance_level, evidence, content, tags, agent,
    timestamp, confidence, model, scope, vendor

Provenance enforcement (default-on; opt out via ``enforce_provenance=False``
or the ``--no-skill-invoke-check`` CLI flag): before persisting, the writer
reads the coordination bus TSV and rejects the entry unless a
``SKILL_INVOKE`` row from the same agent exists within
``SKILL_INVOKE_WINDOW_SECONDS`` (default 300s). This closes the gap between
the documented protocol ("emit SKILL_INVOKE before any stateful action") and
the write path, which previously did not check.

stdlib-only at import time. Writes optionally delegate to
``hummbl_cognition`` when that package is importable (ADR-025 O2 shim).
"""

from __future__ import annotations

import json
import os
import time
import uuid
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Iterator

from hummbl_governance.cognition.scanner import scan_entry

__all__ = [
    "ENTRY_TYPES",
    "LEDGER_VERSION",
    "MAX_TAGS",
    "SCOPES",
    "ProvenanceError",
    "append_entry",
    "bus_path",
    "ledger_path",
    "load_entries",
    "resolve_root",
    "verify_skill_invoke",
]

LEDGER_VERSION = 1
ENTRY_TYPES = ("lesson", "decision", "discovery", "correction", "convention")
SCOPES = ("project", "module", "file", "convention", "process")
MAX_TAGS = 10
LOCK_TIMEOUT_SECONDS = 10.0

# Provenance enforcement: a ledger post is rejected unless a SKILL_INVOKE bus
# row from the same agent exists within this window (seconds). 300s is the
# default; override with $SKILL_INVOKE_WINDOW_SECONDS.
SKILL_INVOKE_WINDOW_SECONDS = float(
    os.environ.get("SKILL_INVOKE_WINDOW_SECONDS", "300")
)
SKILL_INVOKE_TYPE = "SKILL_INVOKE"


class ProvenanceError(RuntimeError):
    """Raised when provenance enforcement is on and no recent SKILL_INVOKE exists."""


def resolve_root() -> Path:
    """Resolve the hummbl-governance root directory.

    Order: ``$HUMMBL_GOVERNANCE_ROOT``; the nearest ancestor of the current
    working directory that contains a ``hummbl_governance`` package directory;
    this package's install root.
    """
    env = os.environ.get("HUMMBL_GOVERNANCE_ROOT")
    if env:
        return Path(env)
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "hummbl_governance").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def ledger_path(root: Path | None = None) -> Path:
    """Return the ledger JSONL path.

    Resolution order:

    1. ``$COGNITION_LEDGER`` — absolute path to the ledger file (highest priority).
    2. *root* argument, if provided.
    3. ``<resolve_root()>/_state/cognition/ledger.jsonl`` (default).
    """
    env = os.environ.get("COGNITION_LEDGER")
    if env and root is None:
        return Path(env)
    return (root or resolve_root()) / "_state" / "cognition" / "ledger.jsonl"


def bus_path(root: Path | None = None) -> Path:
    """Return the coordination bus TSV path.

    Mirrors the resolution in hummbl_bus.bus_writer so the ledger writer can
    locate the bus without importing the bus package (which would create a
    cross-package dependency). Resolution order:

    1. ``$COORDINATION_BUS`` — absolute path to the bus file (highest priority).
    2. *root* argument, if provided.
    3. ``<resolve_root()>/_state/coordination/messages.tsv`` (default).
    4. ``~/.cache/bus/messages.tsv`` (local mirror fallback).
    """
    env = os.environ.get("COORDINATION_BUS")
    if env and root is None:
        return Path(env)
    candidate = (root or resolve_root()) / "_state" / "coordination" / "messages.tsv"
    if candidate.is_file():
        return candidate
    return Path.home() / ".cache" / "bus" / "messages.tsv"


def _parse_bus_timestamp(ts: str) -> datetime | None:
    """Parse a bus row timestamp (ISO 8601 with Z suffix). Best-effort."""
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts[:-1]).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def verify_skill_invoke(
    agent: str,
    *,
    window_seconds: float | None = None,
    bus: Path | None = None,
    now: datetime | None = None,
) -> bool:
    """Return True if a SKILL_INVOKE row from *agent* exists in the bus within the window.

    Reads the coordination bus TSV (format: ``timestamp_utc\\tfrom\\tto\\ttype\\tmessage``)
    and looks for the most recent row whose ``type`` is ``SKILL_INVOKE`` and whose
    ``from`` matches *agent*. Returns True if that row's timestamp is within
    *window_seconds* of *now* (both default to module constants / utcnow).

    Returns False if the bus file is missing, unreadable, or contains no
    qualifying row. Never raises on a missing or malformed bus file — the
    caller decides whether to treat "no proof" as a hard failure via
    ``enforce_provenance``.
    """
    if window_seconds is None:
        window_seconds = SKILL_INVOKE_WINDOW_SECONDS
    if now is None:
        now = datetime.now(timezone.utc)
    path = bus or bus_path()
    if not path.is_file():
        return False
    latest: datetime | None = None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        row_type = parts[3].strip()
        if row_type != SKILL_INVOKE_TYPE:
            continue
        if parts[1].strip() != agent:
            continue
        ts = _parse_bus_timestamp(parts[0].strip())
        if ts is None:
            continue
        if latest is None or ts > latest:
            latest = ts
    if latest is None:
        return False
    # Make both sides offset-aware for the comparison.
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    age = (now - latest).total_seconds()
    return 0 <= age <= window_seconds


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def _exclusive_lock(lock_path: Path) -> Iterator[None]:
    """Hold an exclusive advisory lock on *lock_path* for the block duration."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh: IO[str] = open(lock_path, "a+", encoding="utf-8")  # noqa: SIM115
    try:
        fh.write("0")
        fh.flush()
        fh.seek(0)
        _lock_fd(fh, lock_path)
        try:
            yield
        finally:
            _unlock_fd(fh)
    finally:
        fh.close()


def _lock_fd(fh: IO[str], lock_path: Path) -> None:
    if os.name == "nt":
        import msvcrt

        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"could not acquire ledger lock: {lock_path}")
                time.sleep(0.05)
    else:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)


def _unlock_fd(fh: IO[str]) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass  # best-effort unlock; the fd close releases the lock anyway


def _validate(
    *,
    entry_type: str,
    scope: str,
    tags: list[str],
    confidence: float,
) -> None:
    if entry_type not in ENTRY_TYPES:
        raise ValueError(f"invalid type {entry_type!r}; expected one of {ENTRY_TYPES}")
    if scope not in SCOPES:
        raise ValueError(f"invalid scope {scope!r}; expected one of {SCOPES}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence must be within [0.0, 1.0], got {confidence}")
    if len(tags) > MAX_TAGS:
        raise ValueError(f"at most {MAX_TAGS} tags allowed, got {len(tags)}")


def append_entry(
    content: str,
    *,
    entry_type: str,
    scope: str,
    tags: list[str],
    agent: str,
    vendor: str,
    model: str,
    confidence: float = 0.8,
    evidence: str = "",
    assurance_level: str = "SELF",
    root: Path | None = None,
    enforce_provenance: bool = True,
    bus: Path | None = None,
) -> dict:
    """Scan, validate, and append one entry; return the persisted record.

    Provenance is enforced by default: the writer reads the coordination bus
    and raises :class:`ProvenanceError` unless a ``SKILL_INVOKE`` row from
    *agent* exists within :data:`SKILL_INVOKE_WINDOW_SECONDS`. This makes the
    documented protocol ("emit SKILL_INVOKE before any stateful action")
    enforced at the write path rather than a convention the caller must
    remember. Pass ``enforce_provenance=False`` to bypass (e.g., for legacy
    callers that have not yet been migrated). *bus* overrides the bus path
    for tests.
    """
    _validate(entry_type=entry_type, scope=scope, tags=tags, confidence=confidence)
    scan_entry(content, evidence=evidence, tags=tags)
    if enforce_provenance and not verify_skill_invoke(agent, bus=bus):
        raise ProvenanceError(
            f"no recent SKILL_INVOKE from agent {agent!r} in the coordination bus "
            f"(window={SKILL_INVOKE_WINDOW_SECONDS}s); emit SKILL_INVOKE before "
            "posting to the ledger, or pass enforce_provenance=False / "
            "--no-skill-invoke-check to bypass"
        )

    warnings.warn(
        "hummbl_governance.cognition writes are deprecated (ADR-025 D2). "
        "This release shims to hummbl_cognition when importable; the shim "
        "will be removed in a subsequent hummbl-governance release. Use "
        "python -m hummbl_cognition post.",
        DeprecationWarning,
        stacklevel=2,
    )

    path = ledger_path(root)
    delegated = _delegate_to_cognition(
        content=content,
        entry_type=entry_type,
        scope=scope,
        tags=list(tags),
        agent=agent,
        vendor=vendor,
        model=model,
        confidence=confidence,
        evidence=evidence,
        assurance_level=assurance_level,
        path=path,
    )
    if delegated is not None:
        return delegated

    record = {
        "id": str(uuid.uuid4()),
        "type": entry_type,
        "assurance_level": assurance_level,
        "evidence": evidence,
        "content": content,
        "tags": list(tags),
        "agent": agent,
        "timestamp": _timestamp(),
        "confidence": confidence,
        "model": model,
        "scope": scope,
        "vendor": vendor,
    }
    with _exclusive_lock(path.with_suffix(".lock")):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _delegate_to_cognition(
    *,
    content: str,
    entry_type: str,
    scope: str,
    tags: list[str],
    agent: str,
    vendor: str,
    model: str,
    confidence: float,
    evidence: str,
    assurance_level: str,
    path: Path,
) -> dict | None:
    """Write via hummbl_cognition when that package is importable.

    Returns the persisted record, or None when hummbl_cognition is absent
    or the vendor is outside its closed enum, so the caller can fall back
    to the local JSONL writer. Other exceptions (scan failure, I/O) propagate.
    """
    try:
        from hummbl_cognition.ledger_writer import post_entry
        from hummbl_cognition.models import (
            VALID_VENDORS,
            LedgerEntry,
            compute_content_hash,
        )
    except ImportError:
        return None

    if vendor not in VALID_VENDORS:
        return None

    entry_id = f"clp-{uuid.uuid4().hex[:12]}"
    timestamp = _timestamp()
    content_hash = compute_content_hash(
        agent=agent,
        vendor=vendor,
        model=model,
        entry_type=entry_type,
        scope=scope,
        content=content,
    )
    entry = LedgerEntry(
        id=entry_id,
        timestamp=timestamp,
        agent=agent,
        vendor=vendor,
        model=model,
        type=entry_type,
        scope=scope,
        content=content,
        content_hash=content_hash,
        evidence=evidence or None,
        confidence=confidence,
        tags=tuple(tags),
        assurance_level=assurance_level or None,
    )
    written = post_entry(entry, ledger_path=path)
    record = written.to_dict()
    record.setdefault("tags", list(tags))
    record.setdefault("evidence", evidence)
    record.setdefault("assurance_level", assurance_level)
    return record


def load_entries(root: Path | None = None) -> list[dict]:
    """Load all well-formed entries (malformed lines are skipped).

    Reads with ``errors="replace"`` so a legacy cp1252-encoded byte in the
    shared ledger degrades to a replacement character instead of crashing
    every read (observed in production 2026-09-02).
    """
    path = ledger_path(root)
    if not path.is_file():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
