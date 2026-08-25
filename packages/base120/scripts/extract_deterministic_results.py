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

"""Extract deterministic fields from pytest JSON report for hash comparison."""

import json
import sys


def extract_deterministic_fields(input_path: str, output_path: str) -> None:
    """Extract only deterministic fields from pytest JSON report.

    Args:
        input_path: Path to the pytest JSON report
        output_path: Path to write the cleaned JSON
    """
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # Extract deterministic fields only (no timing, no duration)
    results = {
        'summary': data['summary'],
        'tests': [
            {
                'nodeid': t['nodeid'],
                'outcome': t['outcome'],
                'call': t.get('call', {}).get('longrepr', '')
            }
            for t in data['tests']
        ]
    }

    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(results, f, sort_keys=True, indent=2)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json>", file=sys.stderr)
        sys.exit(1)

    extract_deterministic_fields(sys.argv[1], sys.argv[2])
