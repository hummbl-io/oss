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

"""Public documentation checks for the Base120 package surface."""

from __future__ import annotations

import tomllib
from pathlib import Path

import base120

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_readme_advertises_current_sdk_surface() -> None:
    readme = _read("README.md")

    unsupported_claims = [
        "Python code has been removed",
        "base120 validate-contract path/to",
        "from base120.validators",
        "from base120.observability",
    ]
    for claim in unsupported_claims:
        assert claim not in readme

    assert "from base120 import Engine, Ledger" in readme
    assert "from base120 import Engine" in readme
    assert "base120 list" in readme
    assert "base120 get P6" in readme
    assert "base120 prompt P6" in readme
    assert "base120 families" in readme
    assert "pip install base120" in readme


def test_readme_advertises_pypi_install() -> None:
    readme = _read("README.md")
    assert "pip install base120" in readme
    assert "From PyPI" in readme


def test_readme_does_not_reference_stripped_internal_files() -> None:
    readme = _read("README.md")
    stripped_refs = [
        "GOVERNANCE.md",
        "KRINEIA.md",
        "REPO_HEALTH.md",
        "PACKAGE_IDENTITY_RECEIPT",
        "CONSTITUTION.md",
        "DOCTRINE.md",
        "hummbl.repo.yaml",
        "docs/observability.md",
        "docs/contract-units.md",
        "docs/governance-decision-tree.md",
    ]
    for ref in stripped_refs:
        assert ref not in readme, f"README references stripped internal file: {ref}"


def test_public_package_identity_is_clear() -> None:
    assert 'name = "base120"' in _read("pyproject.toml")
    readme = _read("README.md")
    assert "base120" in readme.lower()


def test_documented_sdk_version_matches_package_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]

    assert base120.__version__ == version
    assert version in _read("README.md")


def test_no_hummbl_dev_refs_in_public_files() -> None:
    """Public files must not reference the old hummbl-dev org."""
    public_files = [
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "llms.txt",
    ]
    for relative in public_files:
        if (ROOT / relative).exists():
            text = _read(relative)
            assert "hummbl-dev" not in text, f"{relative} still references hummbl-dev"
