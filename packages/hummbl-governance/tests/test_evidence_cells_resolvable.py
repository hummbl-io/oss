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

"""Test that coverage matrix evidence cells are resolvable or explicitly marked draft.

Implements hummbl-governance#29 enforcement: every backtick-quoted code reference
in matrix Evidence columns must either resolve against the real CLI / file system
or carry an explicit [DRAFT ...] marker.

Stdlib + pytest only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_evidence_cells import classify_reference, scan_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_evidence_cells.py"
COVERAGE_DIR = REPO_ROOT / "docs" / "coverage"


def _run_validator_strict() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--matrix-dir", str(COVERAGE_DIR), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_validator_script_runs():
    """The validator runs against current matrices."""
    result = _run_validator_strict()
    assert result.returncode in (0, 1), f"Validator crashed: {result.stderr}"


def test_missing_python_paths_are_unresolvable():
    """Missing Python path evidence must fail strict accounting, not pass as unknown."""
    kind, status = classify_reference("services/kill_switch_core.py")
    assert kind == "file-path"
    assert status == "unresolvable"


def test_scan_matrix_counts_missing_python_paths_as_unresolvable():
    """Strict-mode callers rely on the unresolvable counter, so missing paths must increment it."""
    with TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "sample.md"
        matrix.write_text("| Evidence |\n|---|\n| `missing/local_path.py` |\n", encoding="utf-8")

        result = scan_matrix(matrix, repo_root=Path(tmp))

    assert result["by_status"]["unresolvable"] == 1


def test_no_unresolvable_evidence_cells_in_strict_mode():
    """Every compliance_mapper invocation either uses real CLI flags or is [DRAFT]-marked.

    The strict-mode exit code is 1 if any unresolvable cells remain. This test
    asserts exit-0, meaning the relabel pass has fully covered the matrix corpus.
    """
    result = _run_validator_strict()
    assert result.returncode == 0, (
        f"Validator found unresolvable evidence cells (exit={result.returncode}).\n"
        f"Output:\n{result.stdout}\n"
        f"Fix: either implement the missing CLI flag in compliance_mapper.py, "
        f"or run scripts/relabel_unresolvable_evidence.py to apply [DRAFT] prefix."
    )


def test_relabel_script_is_idempotent():
    """Re-running the relabel script does not double-prefix already-drafted cells."""
    relabel_script = REPO_ROOT / "scripts" / "relabel_unresolvable_evidence.py"
    # Dry-run a second time; should report all skipped (already drafted)
    result = subprocess.run(
        [sys.executable, str(relabel_script), "--matrix-dir", str(COVERAGE_DIR), "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    # If anything in TOTAL relabeled is non-zero on a fresh dry-run, the previous
    # pass didn't fully take effect.
    assert "TOTAL relabeled: 0" in result.stdout, (
        f"Relabel script is not idempotent — second pass would change files.\n"
        f"Output:\n{result.stdout}"
    )
