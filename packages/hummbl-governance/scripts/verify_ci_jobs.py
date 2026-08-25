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

"""Verify required CI jobs passed for ci-aggregate job.

When detect-changes determines a docs-only change, expensive jobs are
intentionally skipped. "skipped" is an acceptable result in that case.
"""

import os
import sys

code_changed = os.environ.get("NEEDS_DETECT_CHANGES_CODE", "unknown")
print(f"code_changed={code_changed}")

results = {
    "test": os.environ.get("NEEDS_TEST_RESULT", "unknown"),
    "install-smoke": os.environ.get("NEEDS_INSTALL_SMOKE_RESULT", "unknown"),
    "lint": os.environ.get("NEEDS_LINT_RESULT", "unknown"),
    "arbiter-governance": os.environ.get("NEEDS_ARBITER_GOVERNANCE_RESULT", "unknown"),
    "coverage-matrix-validate": os.environ.get("NEEDS_COVERAGE_MATRIX_VALIDATE_RESULT", "unknown"),
}

failed = 0
for job, result in results.items():
    # "skipped" is acceptable when detect-changes determined docs-only
    if result not in ("success", "skipped"):
        print(f"{job} finished with result: {result}")
        failed = 1
    elif result == "skipped":
        print(f"{job} skipped (docs-only change)")

sys.exit(failed)
