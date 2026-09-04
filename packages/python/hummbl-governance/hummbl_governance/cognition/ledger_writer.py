# Copyright 2024-2026 HUMMBL, LLC
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

stdlib-only.
"""

from __future__ import annotations

import json
import os
import time
import uuid
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
    "append_entry",
    "ledger_path",
    "load_entries",
    "resolve_root",
]

LEDGER_VERSION = 1
ENTRY_TYPES = ("lesson", "decision", "discovery", "correction", "convention")
SCOPES = ("project", "module", "file", "convention", "process")
MAX_TAGS = 10
LOCK_TIMEOUT_SECONDS = 10.0


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
    """Return the ledger JSONL path under *root* (default: :func:`resolve_root`)."""
    return (root or resolve_root()) / "_state" / "cognition" / "ledger.jsonl"


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
) -> dict:
    """Scan, validate, and append one entry; return the persisted record."""
    _validate(entry_type=entry_type, scope=scope, tags=tags, confidence=confidence)
    scan_entry(content, evidence=evidence, tags=tags)

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
    path = ledger_path(root)
    with _exclusive_lock(path.with_suffix(".lock")):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
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
