#!/usr/bin/env python3
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

"""Validate that registries/fm.json changes in v1.0.x are metadata-only.

Permitted in v1.0.x:
- Adding new fields to existing FMs (with stable/null values)
- No changes to FM count, IDs, or names
- All lifecycle_state must be "stable"

Prohibited in v1.0.x:
- Adding new FMs (FM31+)
- Removing FMs
- Changing FM IDs or names
- Changing lifecycle_state from "stable"
- Any other semantic modifications
"""

import json
import sys
from pathlib import Path


def load_fm_registry(content: str) -> dict[str, object]:
    """Load FM registry from JSON content.

    Raises:
        json.JSONDecodeError: If content is not valid JSON.
        KeyError: If the registry does not contain a 'registry' key.
    """
    data: dict[str, object] = json.loads(content)
    if "registry" not in data:
        raise KeyError("FM registry JSON missing required 'registry' key")
    return data


def _validate_existing_fm(fm_id: str, before_fm: dict[str, object], after_fm: dict[str, object], errors: list[str]) -> None:
    """Validate a single FM that exists in both before and after registries."""
    if before_fm.get('name') != after_fm.get('name'):
        errors.append(f"{fm_id}: Name changed (prohibited in v1.0.x)")

    if 'lifecycle_state' in after_fm and after_fm['lifecycle_state'] != 'stable':
        errors.append(
            f"{fm_id}: lifecycle_state is '{after_fm['lifecycle_state']}' (must be 'stable' in v1.0.x)"
        )

    for core_field in ['id', 'name']:
        if core_field in before_fm and core_field not in after_fm:
            errors.append(f"{fm_id}: Core field '{core_field}' removed (prohibited)")


def validate_metadata_only_change(before_content: str, after_content: str) -> tuple[bool, list[str]]:  # type: ignore[type-arg]
    """Validate that changes are metadata-only additions.

    Returns: (is_valid, error_messages)
    """
    errors = []

    before = load_fm_registry(before_content)
    after = load_fm_registry(after_content)

    before_fms = {fm['id']: fm for fm in before['registry']}
    after_fms = {fm['id']: fm for fm in after['registry']}

    if len(before_fms) != len(after_fms):
        errors.append(f"FM count changed: {len(before_fms)} -> {len(after_fms)} (prohibited in v1.0.x)")

    removed_fms = set(before_fms.keys()) - set(after_fms.keys())
    if removed_fms:
        errors.append(f"FMs removed: {', '.join(sorted(removed_fms))} (prohibited in v1.0.x)")

    added_fms = set(after_fms.keys()) - set(before_fms.keys())
    if added_fms:
        errors.append(f"FMs added: {', '.join(sorted(added_fms))} (prohibited in v1.0.x - escalate to v1.1.0+)")

    for fm_id, before_fm in before_fms.items():
        if fm_id in after_fms:
            _validate_existing_fm(fm_id, before_fm, after_fms[fm_id], errors)

    if before.get('version') != after.get('version'):
        errors.append(
            f"Registry version changed: {before.get('version')} -> {after.get('version')} (must remain v1.0.0)"
        )

    return len(errors) == 0, errors


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <before_file> <after_file>", file=sys.stderr)
        sys.exit(1)

    before_file = Path(sys.argv[1])
    after_file = Path(sys.argv[2])

    is_valid, errors = validate_metadata_only_change(
        before_file.read_text(encoding="utf-8"),
        after_file.read_text(encoding="utf-8")
    )

    if is_valid:
        print("PASS: Registry changes are metadata-only additions (permitted in v1.0.x)")
        sys.exit(0)
    else:
        print("FAIL: Registry contains prohibited semantic changes")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
