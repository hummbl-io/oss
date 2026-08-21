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

"""Release artifact checks for built wheels.

These tests intentionally inspect the distributable wheel instead of relying on
editable installs, which can mask missing package data or console entry modules.
"""

from __future__ import annotations

import configparser
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str], *, cwd: Path) -> None:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "command failed: "
            + " ".join(args)
            + f"\nexit code: {result.returncode}"
            + f"\nstdout:\n{result.stdout}"
            + f"\nstderr:\n{result.stderr}"
        )


def _single_path(paths: list[Path], label: str) -> Path:
    if len(paths) != 1:
        raise AssertionError(f"expected exactly one {label}, found {len(paths)}: {paths}")
    return paths[0]


def _expected_data_files() -> set[str]:
    data_root = REPO_ROOT / "hummbl_governance" / "data"
    files = {f"hummbl_governance/data/{path.name}" for path in data_root.glob("*.json")}
    if not files:
        raise AssertionError(f"no JSON data files discovered under {data_root}")
    return files


def _expected_console_modules() -> dict[str, str]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    scripts = pyproject.get("project", {}).get("scripts", {})
    if not scripts:
        raise AssertionError("no [project.scripts] entries discovered in pyproject.toml")
    return {name: target.split(":", 1)[0].strip() for name, target in scripts.items()}


def _module_file_candidates(module_name: str) -> set[str]:
    module_path = module_name.replace(".", "/")
    return {f"{module_path}.py", f"{module_path}/__init__.py"}


def _build_wheel_from_source(tmp_path: Path) -> Path:
    wheel_dir = tmp_path / "wheelhouse"
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
        ],
        cwd=REPO_ROOT,
    )
    return _single_path(list(wheel_dir.glob("hummbl_governance-*.whl")), "wheel")


def _build_wheel_from_sdist(tmp_path: Path) -> Path:
    sdist_dir = tmp_path / "sdist"
    _run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--outdir",
            str(sdist_dir),
        ],
        cwd=REPO_ROOT,
    )
    sdist = _single_path(list(sdist_dir.glob("hummbl_governance-*.tar.gz")), "sdist")

    wheel_dir = tmp_path / "wheel-from-sdist"
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(sdist),
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
        ],
        cwd=tmp_path,
    )
    return _single_path(list(wheel_dir.glob("hummbl_governance-*.whl")), "wheel built from sdist")


def _wheel_names(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        return set(archive.namelist())


def _entry_points(wheel: Path) -> dict[str, str]:
    with zipfile.ZipFile(wheel) as archive:
        entry_points_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt")
        )
        parser = configparser.ConfigParser()
        parser.read_string(archive.read(entry_points_name).decode("utf-8"))
    return dict(parser["console_scripts"])


@pytest.fixture(scope="module", params=("source", "sdist"))
def built_wheel(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp(f"release-artifact-{request.param}")
    if request.param == "source":
        return _build_wheel_from_source(tmp_path)
    if request.param == "sdist":
        return _build_wheel_from_sdist(tmp_path)
    raise AssertionError(f"unknown artifact source: {request.param}")


def test_wheel_includes_runtime_data_files(built_wheel: Path) -> None:
    names = _wheel_names(built_wheel)
    missing = _expected_data_files() - names
    assert not missing


def test_console_script_entry_modules_are_in_wheel(built_wheel: Path) -> None:
    names = _wheel_names(built_wheel)
    entry_points = _entry_points(built_wheel)
    expected_modules = _expected_console_modules()

    assert set(expected_modules) <= set(entry_points)
    missing: list[str] = []
    for script_name, expected_module in sorted(expected_modules.items()):
        module_name = entry_points[script_name].split(":", 1)[0].strip()
        if module_name != expected_module:
            missing.append(f"{script_name} -> {module_name} (expected {expected_module})")
            continue
        if not (_module_file_candidates(module_name) & names):
            missing.append(f"{script_name} -> {module_name}")

    assert not missing
