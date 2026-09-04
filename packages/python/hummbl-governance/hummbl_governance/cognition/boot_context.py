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

"""Boot context builder for the Cognitive Ledger.

Produces the compact context block agents load at session start:
ledger stats plus the most recent entries.

stdlib-only.
"""

from __future__ import annotations

from collections import Counter

__all__ = ["build_boot_context"]


def build_boot_context(entries: list[dict], *, recent: int = 10) -> str:
    """Render the boot context: stats plus the *recent* newest entries."""
    if not entries:
        return "COGNITIVE LEDGER: empty (0 entries)"
    counts = Counter(str(e.get("type", "?")) for e in entries)
    by_type = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    lines = [
        f"COGNITIVE LEDGER: {len(entries)} entries ({by_type})",
        "Recent entries (newest first):",
    ]
    for entry in list(reversed(entries))[:recent]:
        content = str(entry.get("content", "")).replace("\n", " ")
        if len(content) > 100:
            content = content[:97] + "..."
        lines.append(
            f"- {entry.get('timestamp', '?')} [{entry.get('type', '?')}] "
            f"{entry.get('agent', '?')} (conf {entry.get('confidence', '?')}): {content}"
        )
    return "\n".join(lines)
