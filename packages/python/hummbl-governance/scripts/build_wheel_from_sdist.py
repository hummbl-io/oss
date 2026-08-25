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

"""Build wheel from sdist for install-smoke CI job."""

from pathlib import Path
import subprocess
import sys

sdists = list(Path("dist-smoke").glob("hummbl_governance-*.tar.gz"))
if len(sdists) != 1:
    raise SystemExit(f"expected exactly one sdist, found {len(sdists)}: {sdists}")
subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "wheel",
    str(sdists[0]),
    "--no-deps",
    "--wheel-dir",
    "dist-from-sdist",
])
