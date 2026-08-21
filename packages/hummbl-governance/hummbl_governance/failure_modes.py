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

"""HUMMBL governance failure mode registry.

Loads the FM registry (fm.json), error catalog (err.json), and subclass
mappings (mappings.json) from the package data directory.

All three sources originated in the base120 governance substrate and were
migrated here in v0.4.0 as the canonical home for HUMMBL error taxonomy.

Usage::

    from hummbl_governance.failure_modes import get_fm, classify_subclass

    fm = get_fm("FM15")           # FailureModeRecord(id="FM15", name="Schema Non-Compliance")
    fms = classify_subclass("02") # ["FM15"]
    errs = get_errors_for_fm("FM15")  # [{"id": "ERR-SCHEMA-001", "fm": ["FM15"], "severity": "fatal"}]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"


@dataclass(frozen=True, slots=True)
class FailureModeRecord:
    """A single entry from the FM registry."""

    id: str    # e.g. "FM1"
    name: str  # e.g. "Specification Ambiguity"


@dataclass(frozen=True, slots=True)
class ErrorRecord:
    """A structured error code mapping to one or more failure modes."""

    id: str             # e.g. "ERR-SCHEMA-001"
    fm: tuple[str, ...]  # e.g. ("FM15",)
    severity: str       # "fatal" | "escalation" | "warning"


# ---------------------------------------------------------------------------
# Internal loaders — called once, results cached
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_fm_registry() -> dict[str, FailureModeRecord]:
    with open(_DATA_DIR / "fm.json", encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        rec["id"]: FailureModeRecord(id=rec["id"], name=rec["name"])
        for rec in data["registry"]
    }


@lru_cache(maxsize=1)
def _load_err_catalog() -> list[ErrorRecord]:
    with open(_DATA_DIR / "err.json", encoding="utf-8") as fh:
        data = json.load(fh)
    return [
        ErrorRecord(
            id=rec["id"],
            fm=tuple(rec.get("fm", [])),
            severity=rec.get("severity", "unknown"),
        )
        for rec in data["registry"]
    ]


@lru_cache(maxsize=1)
def _load_mappings() -> dict[str, list[str]]:
    with open(_DATA_DIR / "mappings.json", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("mappings", {})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def all_failure_modes() -> list[FailureModeRecord]:
    """Return all 30 failure mode records, ordered by FM number."""
    registry = _load_fm_registry()
    return sorted(registry.values(), key=lambda r: int(r.id[2:]))


def get_fm(fm_id: str) -> FailureModeRecord | None:
    """Look up a failure mode by its ID (e.g. "FM15").

    Returns None if the ID is not in the registry.
    """
    return _load_fm_registry().get(fm_id)


def classify_subclass(subclass: str) -> list[str]:
    """Map a subclass code to a list of failure mode IDs.

    Args:
        subclass: Two-digit subclass string, e.g. "02" or "13".

    Returns:
        List of FM codes that apply to this subclass, e.g. ["FM15"].
        Empty list if the subclass has no mapping.
    """
    return list(_load_mappings().get(subclass, []))


def get_errors_for_fm(fm_id: str) -> list[ErrorRecord]:
    """Return all structured error records that reference a given FM.

    Args:
        fm_id: A failure mode ID, e.g. "FM15".

    Returns:
        List of ErrorRecord objects whose fm tuple contains fm_id.
    """
    return [rec for rec in _load_err_catalog() if fm_id in rec.fm]


def all_error_records() -> list[ErrorRecord]:
    """Return all error records from the catalog."""
    return list(_load_err_catalog())
