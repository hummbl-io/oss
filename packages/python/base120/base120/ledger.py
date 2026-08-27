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

"""VERUM-aligned append-only audit ledger.

Persists OperatorTuple entries as JSONL. Implements exactly three operators:

  append(t)            — write one entry
  project(n)           — read the last n entries (all if n is None)
  cut(max_drift)       — return entries where drift > max_drift

VERUM invariants enforced:
  - Append-only: the file is only opened in 'a' mode; no delete or modify.
  - No self-reference: the Engine never reads its own ledger.
  - Minimal operators: exactly three public methods (append / project / cut).
  - External analysis: project() and cut() are the read surface for external
    tools; they are not called by the Engine or Operator code paths.

Zero third-party dependencies. Stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path

from base120.models import OperatorTuple

_DEFAULT_PATH = Path.home() / ".base120" / "ledger.jsonl"


class Ledger:
    """Append-only audit log for Base120 operator applications.

    Each entry is a JSONL line with the 4 VERUM fields:
      {"id": "P6", "time": "...", "state": "...", "drift": 0.15}

    Usage::

        ledger = Ledger()                    # defaults to ~/.base120/ledger.jsonl
        ledger.append(result.to_tuple())     # write one entry

        entries = ledger.project()           # read all entries
        high    = ledger.cut(max_drift=0.5)  # entries with drift > 0.5
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_PATH

    @property
    def path(self) -> Path:
        """Resolved path to the backing JSONL file."""
        return self._path

    def append(self, t: OperatorTuple) -> None:
        """Write one OperatorTuple as a JSONL line.

        Creates the file (and any parent directories) if they do not exist.
        The file is opened in append mode — existing entries are never
        modified or deleted.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"id": t.id, "time": t.time, "state": t.state, "drift": t.drift})
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def project(self, n: int | None = None) -> list[OperatorTuple]:
        """Read entries from the ledger.

        Args:
            n: If given, return the last n entries. If None, return all.
               n=0 returns an empty list. Negative n returns an empty list.

        Returns:
            Entries in insertion order (oldest first).

        Raises:
            ValueError: If a ledger line is valid JSON but missing required
                VERUM fields (id, time, state, drift).
        """
        if not self._path.exists():
            return []
        entries: list[OperatorTuple] = []
        with self._path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Corrupted ledger line {lineno} in {self._path}: {exc}"
                    ) from exc
                missing = {"id", "time", "state", "drift"} - obj.keys()
                if missing:
                    raise ValueError(
                        f"Ledger line {lineno} missing fields {missing} in {self._path}"
                    )
                entries.append(
                    OperatorTuple(
                        id=obj["id"],
                        time=obj["time"],
                        state=obj["state"],
                        drift=obj["drift"],
                    )
                )
        if n is None:
            return entries
        if n < 0:
            raise ValueError(f"n must be non-negative, got {n}")
        return entries[-n:] if n > 0 else []

    def cut(self, max_drift: float) -> list[OperatorTuple]:
        """Return entries where drift strictly exceeds max_drift.

        This is VERUM's cut() operator: surfaces decisions with deviation
        above the threshold so external analysis can inspect them.

        Args:
            max_drift: Threshold. Entries with drift > max_drift are returned.
                       Entries with drift == max_drift are NOT included.

        Returns:
            Matching entries in insertion order.
        """
        return [e for e in self.project() if e.drift > max_drift]
