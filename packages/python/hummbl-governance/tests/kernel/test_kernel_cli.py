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

"""Tests for the Kernel CLI.

Covers all subcommands by mocking sys.argv and calling cli.main().
"""

from __future__ import annotations

import json
import sys
import tempfile
from unittest.mock import patch

from hummbl_governance.kernel.cli import main


class TestKernelCLI:
    """Test each CLI subcommand."""

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        """Run cli.main with the given argv, capture stdout/stderr, return (code, out, err)."""
        with patch.object(sys, "argv", argv):
            import io
            out_buf = io.StringIO()
            err_buf = io.StringIO()
            with patch.object(sys, "stdout", out_buf), patch.object(sys, "stderr", err_buf):
                code = main()
            return code, out_buf.getvalue(), err_buf.getvalue()

    def test_no_command_prints_help(self) -> None:
        code, out, _ = self._run(["kernel"])
        assert code == 1
        assert "Commands" in out or "usage" in out.lower()

    def test_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "status"])
            assert code == 0
            data = json.loads(out)
            assert "booted" in data or "engines" in data or "healthy" in data

    def test_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "health"])
            assert code == 0
            data = json.loads(out)
            assert "identities" in data or "receipts_total" in data

    def test_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "boot"])
            assert code == 0
            assert "booted" in out.lower()

    def test_laws(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "laws"])
            assert code == 0
            assert "law" in out.lower()

    def test_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "roles"])
            assert code == 0

    def test_inspect_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            code, out, err = self._run(["kernel", "--state-dir", tmpdir, "inspect", "nonexistent-agent"])
            assert code == 1
            assert "not found" in err.lower()

    def test_model_registry_list(self) -> None:
        code, out, err = self._run(["kernel", "model-registry", "list"])
        assert code == 0
        assert "Models:" in out

    def test_model_registry_stats(self) -> None:
        code, out, err = self._run(["kernel", "model-registry", "stats"])
        assert code == 0
        data = json.loads(out)
        assert "count" in data

    def test_model_registry_get_not_found(self) -> None:
        code, out, err = self._run(["kernel", "model-registry", "get", "nonexistent-model"])
        assert code == 1
        assert "not found" in out.lower()

    def test_model_registry_best_no_models_for_metric(self) -> None:
        code, out, err = self._run(["kernel", "model-registry", "best", "--metric", "nonexistent_metric"])
        assert code == 1
        assert "no models" in out.lower() or "not found" in out.lower()
