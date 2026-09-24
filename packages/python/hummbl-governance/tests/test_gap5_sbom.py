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

"""Tests for gap-5 SBOM generation and CI pinning audit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# Load scripts via importlib (hyphenated filenames)
_scripts = Path(__file__).parent.parent / "scripts"


def _load_module(filename: str, mod_name: str):
    path = _scripts / filename
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sbom_mod = _load_module("gap5-generate-sbom.py", "gap5_sbom")
pinning_mod = _load_module("gap5-audit-ci-pinning.py", "gap5_pinning")


class TestSBOMGeneration:
    def test_generate_sbom_for_real_repo(self) -> None:
        repo = Path(__file__).parent.parent
        sbom = sbom_mod.generate_sbom(repo)
        assert sbom["bomFormat"] == "CycloneDX"
        assert sbom["specVersion"] == "1.5"
        assert "components" in sbom
        assert len(sbom["components"]) >= 1

    def test_sbom_has_main_component(self) -> None:
        repo = Path(__file__).parent.parent
        sbom = sbom_mod.generate_sbom(repo)
        main = sbom["metadata"]["component"]
        assert main["name"] == "hummbl-governance"
        assert main["version"] == "1.5.0"
        assert main["purl"] == "pkg:pypi/hummbl-governance@1.5.0"

    def test_sbom_has_zero_runtime_deps(self) -> None:
        """hummbl-governance has zero runtime dependencies."""
        repo = Path(__file__).parent.parent
        sbom = sbom_mod.generate_sbom(repo)
        main = sbom["metadata"]["component"]
        props = {p["name"]: p["value"] for p in main.get("properties", [])}
        assert props.get("hummbl:runtime_deps") == "0"

    def test_sbom_includes_test_deps(self) -> None:
        repo = Path(__file__).parent.parent
        sbom = sbom_mod.generate_sbom(repo)
        component_names = [c["name"] for c in sbom["components"]]
        assert "pytest" in component_names
        assert "ruff" in component_names

    def test_sbom_missing_pyproject(self, tmp_path: Path) -> None:
        sbom = sbom_mod.generate_sbom(tmp_path)
        assert sbom == {}

    def test_sbom_is_json_serializable(self) -> None:
        repo = Path(__file__).parent.parent
        sbom = sbom_mod.generate_sbom(repo)
        json.dumps(sbom)


class TestCIPinningAudit:
    def test_real_repo_is_pinned(self) -> None:
        """hummbl-governance CI should be fully SHA-pinned."""
        repo = Path(__file__).parent.parent
        violations = pinning_mod.audit_repo(repo)
        assert violations == [], f"Unpinned actions: {violations}"

    def test_detects_floating_tag(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text("steps:\n  - uses: actions/checkout@v4\n")
        violations = pinning_mod.audit_repo(tmp_path)
        assert len(violations) == 1
        assert violations[0]["action"] == "actions/checkout"
        assert violations[0]["ref"] == "v4"

    def test_sha_pinned_is_ok(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text("steps:\n  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n")
        violations = pinning_mod.audit_repo(tmp_path)
        assert violations == []

    def test_detects_main_branch_ref(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text("steps:\n  - uses: actions/checkout@main\n")
        violations = pinning_mod.audit_repo(tmp_path)
        assert len(violations) == 1
        assert violations[0]["ref"] == "main"

    def test_local_action_is_ok(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf = wf_dir / "ci.yml"
        wf.write_text("steps:\n  - uses: ./local-action\n")
        violations = pinning_mod.audit_repo(tmp_path)
        assert violations == []

    def test_no_workflows_dir(self, tmp_path: Path) -> None:
        violations = pinning_mod.audit_repo(tmp_path)
        assert violations == []


class TestSBOMDefectFixes:
    """Defect coverage: fabricated license claims + marker leakage (review finding)."""

    def _repo(self, tmp_path: Path, pyproject: str, files: dict | None = None) -> Path:
        (tmp_path / "pyproject.toml").write_text(pyproject)
        for rel, content in (files or {}).items():
            (tmp_path / rel).write_text(content)
        return tmp_path

    def test_license_files_content_detected_not_fabricated(self, tmp_path: Path) -> None:
        repo = self._repo(
            tmp_path,
            '[project]\nname="p"\nversion="1.0.0"\nlicense={license-files=["L"]}\n',
            {"L": "MIT License\n\nPermission is hereby granted, free of charge\n"},
        )
        sbom = sbom_mod.generate_sbom(repo)
        assert sbom["metadata"]["component"]["licenses"] == [{"license": {"id": "MIT"}}]

    def test_undetectable_license_file_not_claimed(self, tmp_path: Path) -> None:
        repo = self._repo(
            tmp_path,
            '[project]\nname="p"\nversion="1.0.0"\nlicense={license-files=["C"]}\n',
            {"C": "All rights reserved.\n"},
        )
        sbom = sbom_mod.generate_sbom(repo)
        main = sbom["metadata"]["component"]
        assert main["licenses"] == []
        props = {p["name"]: p["value"] for p in main["properties"]}
        assert props["hummbl:license_undetected"] == "C"

    def test_marker_stripped_from_dep_version(self, tmp_path: Path) -> None:
        repo = self._repo(
            tmp_path,
            '[project]\nname="p"\nversion="1.0.0"\n'
            '[project.optional-dependencies]\ntest=["dep==2.9.0.post0; python_version >= \'3.8\'"]\n',
        )
        sbom = sbom_mod.generate_sbom(repo)
        dep = sbom["components"][1]
        assert dep["version"] == "2.9.0.post0"
        assert "python_version" not in json.dumps(dep)

    def test_range_dep_omits_version(self, tmp_path: Path) -> None:
        repo = self._repo(
            tmp_path,
            '[project]\nname="p"\nversion="1.0.0"\n'
            '[project.optional-dependencies]\ntest=["dep>=2.0"]\n',
        )
        sbom = sbom_mod.generate_sbom(repo)
        dep = sbom["components"][1]
        assert "version" not in dep
        props = {p["name"]: p["value"] for p in dep["properties"]}
        assert props["hummbl:version_spec"] == ">=2.0"
