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

"""Smoke-test an installed hummbl-governance wheel.

Run this after installing a built wheel into a clean environment. The script
removes the repository root from import paths so source-tree files cannot mask
missing wheel contents.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.resources  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
import os
import sys
import tempfile
import tomllib
from pathlib import Path


PACKAGE = "hummbl-governance"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _without_repo_paths() -> None:
    repo = REPO_ROOT.resolve()
    sys.path[:] = [
        entry
        for entry in sys.path
        if entry and not Path(entry).resolve().is_relative_to(repo)
    ]
    os.chdir(tempfile.gettempdir())


def _set_import_safe_environment() -> None:
    os.environ.setdefault("HUMMBL_SIGNING_SECRET", "installed-wheel-smoke-secret")
    os.environ.setdefault("MONITOR_STATE_DIR", tempfile.mkdtemp(prefix="hgov-monitor-smoke-"))


def _expected_console_scripts() -> set[str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    scripts = pyproject.get("project", {}).get("scripts", {})
    if not scripts:
        raise AssertionError("no [project.scripts] entries discovered in pyproject.toml")
    return set(scripts)


def _expected_data_files() -> set[str]:
    data_root = REPO_ROOT / "hummbl_governance" / "data"
    files = {path.name for path in data_root.glob("*.json")}
    if not files:
        raise AssertionError(f"no JSON data files discovered under {data_root}")
    return files


def _assert_no_runtime_dependencies() -> None:
    requires = importlib.metadata.requires(PACKAGE) or []
    runtime = [req for req in requires if "extra ==" not in req]
    if runtime:
        raise AssertionError(f"unexpected runtime dependencies: {runtime}")


def _assert_console_scripts_importable() -> None:
    entry_points = importlib.metadata.entry_points().select(group="console_scripts")
    by_name = {entry.name: entry.value for entry in entry_points}
    expected_console_scripts = _expected_console_scripts()
    missing = expected_console_scripts - set(by_name)
    if missing:
        raise AssertionError(f"missing console scripts: {sorted(missing)}")

    for script_name in sorted(expected_console_scripts):
        module_name, attr = by_name[script_name].split(":", 1)
        module = importlib.import_module(module_name)
        target = getattr(module, attr)
        if not callable(target):
            raise AssertionError(f"{script_name} target is not callable: {by_name[script_name]}")


def _assert_primitives_importable() -> None:
    import hummbl_governance

    primitive_names = {
        "AgentRegistry",
        "AuditLog",
        "BehaviorMonitor",
        "BusWriter",
        "CapabilityFence",
        "CircuitBreaker",
        "ComplianceMapper",
        "ContractNetManager",
        "ConvergenceDetector",
        "CostGovernor",
        "DelegationTokenManager",
        "GovernanceLifecycle",
        "HealthCollector",
        "KillSwitch",
        "LamportClock",
        "OutputValidator",
        "ReasoningEngine",
        "SchemaValidator",
        "StrideMapper",
    }
    missing = [name for name in sorted(primitive_names) if not hasattr(hummbl_governance, name)]
    if missing:
        raise AssertionError(f"missing package primitives: {missing}")


def _assert_data_backed_modules_work() -> None:
    data_root = importlib.resources.files("hummbl_governance").joinpath("data")
    packaged = {path.name for path in data_root.iterdir() if path.name.endswith(".json")}
    missing = _expected_data_files() - packaged
    if missing:
        raise AssertionError(f"missing packaged data files: {sorted(missing)}")

    from hummbl_governance.failure_modes import all_failure_modes
    from hummbl_governance.reasoning import ReasoningEngine

    models = ReasoningEngine().models
    if not models:
        raise AssertionError("ReasoningEngine loaded zero Base120 models from package data")

    failure_modes = all_failure_modes()
    if not failure_modes:
        raise AssertionError("failure mode registry loaded zero records from package data")


def main() -> int:
    _without_repo_paths()
    _set_import_safe_environment()
    _assert_no_runtime_dependencies()
    _assert_primitives_importable()
    _assert_console_scripts_importable()
    _assert_data_backed_modules_work()
    print("installed wheel smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
