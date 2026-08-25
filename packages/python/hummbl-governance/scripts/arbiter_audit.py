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

"""Arbiter audit for CI job."""

import json
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "arbiter", "score", ".", "--json"],
    capture_output=True,
    text=True,
)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
if result.returncode != 0:
    raise SystemExit(result.returncode)

payload_start = result.stdout.find("{")
if payload_start == -1:
    raise SystemExit("arbiter score did not emit JSON output")

report = json.loads(result.stdout[payload_start:])
score = float(report["overall"])
if score < 90.0:
    raise SystemExit(f"Arbiter score {score} is below the 90.0 threshold")

print(f"Arbiter score {score} meets threshold")
