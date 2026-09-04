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

"""Cognitive Ledger Protocol (CLP) — append-only shared agent memory.

Restores the documented ``python -m hummbl_governance.cognition`` CLI
(post / query / search / reindex / boot / state).  All writes pass a
content scan (prompt-injection, credential-leak, exfiltration, invisible-
Unicode checks) and append under an exclusive lock.

Ledger storage lives at ``<root>/_state/cognition/ledger.jsonl`` where
``<root>`` resolves to (in order): ``$HUMMBL_GOVERNANCE_ROOT``, the nearest
ancestor of the current working directory containing a ``hummbl_governance``
package directory, or this package's install root.

This module is stdlib-only.
"""

from __future__ import annotations

from hummbl_governance.cognition.indexer import build_index, load_index, search_index
from hummbl_governance.cognition.ledger_writer import (
    ENTRY_TYPES,
    LEDGER_VERSION,
    MAX_TAGS,
    SCOPES,
    append_entry,
    ledger_path,
    load_entries,
    resolve_root,
)
from hummbl_governance.cognition.query import filter_entries
from hummbl_governance.cognition.scanner import ContentScanError

__all__ = [
    "ENTRY_TYPES",
    "LEDGER_VERSION",
    "MAX_TAGS",
    "SCOPES",
    "ContentScanError",
    "append_entry",
    "build_index",
    "filter_entries",
    "ledger_path",
    "load_entries",
    "load_index",
    "resolve_root",
    "search_index",
]

__version__ = "0.1.0"
