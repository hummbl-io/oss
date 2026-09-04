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

"""Query engine for the Cognitive Ledger.

stdlib-only.
"""

from __future__ import annotations

import json
from typing import Any

__all__ = ["filter_entries"]


def filter_entries(
    entries: list[dict],
    *,
    entry_type: str | None = None,
    scope: str | None = None,
    agent: str | None = None,
    since: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Filter *entries* by type, scope, agent, and a ``YYYY-MM-DD`` *since* date.

    Results are returned newest-first (reverse file order).  ``since`` compares
    against the entry timestamp's date prefix (UTC).
    """
    out: list[dict] = []
    for entry in reversed(entries):
        if entry_type and entry.get("type") != entry_type:
            continue
        if scope and entry.get("scope") != scope:
            continue
        if agent and entry.get("agent") != agent:
            continue
        if since:
            ts = str(entry.get("timestamp", ""))
            if ts[:10] < since:
                continue
        out.append(entry)
        if limit is not None and len(out) >= limit:
            break
    return out


def render(entry: dict, content_width: int = 120) -> str:
    """Render one entry as a compact JSON line for CLI output."""
    slim: dict[str, Any] = {
        "id": entry.get("id"),
        "timestamp": entry.get("timestamp"),
        "type": entry.get("type"),
        "agent": entry.get("agent"),
        "confidence": entry.get("confidence"),
        "content": str(entry.get("content", ""))[:content_width],
    }
    return json.dumps(slim, ensure_ascii=False)
