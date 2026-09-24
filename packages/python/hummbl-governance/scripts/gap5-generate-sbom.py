#!/usr/bin/env python3
"""Gap-5: Generate CycloneDX SBOM for hummbl-governance.

Generates a CycloneDX 1.5 SBOM in JSON format from pyproject.toml.
Since hummbl-governance has zero runtime dependencies, the SBOM is
straightforward: one component (the package itself) plus test deps.

Usage:
    python scripts/gap5-generate-sbom.py [--output PATH]

NIST 800-53 CM-6 (Configuration Settings), CM-8 (Information System
Component Inventory), SLSA Level 2+.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import uuid
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

# PEP 508: leading distribution name, extras in [], then a version specifier.
_DEP_NAME_RE = re.compile(r"^\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
_SPDX_EXPR_RE = re.compile(r"\b(?:AND|OR|WITH)\b")
_SPDX_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*$")

# Content signatures for license-file detection. Order matters: check the
# more specific variant first (BSD-3 before BSD-2, LGPL before GPL).
_LICENSE_SIGNATURES: list[tuple[str, tuple[str, ...]]] = [
    ("Apache-2.0", ("Apache License", "Version 2.0")),
    ("LGPL-3.0-only", ("GNU LESSER GENERAL PUBLIC LICENSE", "Version 3")),
    ("GPL-3.0-only", ("GNU GENERAL PUBLIC LICENSE", "Version 3")),
    ("MPL-2.0", ("Mozilla Public License", "2.0")),
    ("BSD-3-Clause", ("Redistribution and use in source and binary forms", "Neither the name of")),
    ("BSD-2-Clause", ("Redistribution and use in source and binary forms",)),
    ("MIT", ("Permission is hereby granted, free of charge",)),
]


def _license_entry(value: str) -> dict:
    """Build a CycloneDX licenses[] entry from a declared license string."""
    value = value.strip()
    if _SPDX_EXPR_RE.search(value):
        return {"expression": value}
    if _SPDX_ID_RE.match(value):
        return {"license": {"id": value}}
    return {"license": {"name": value}}


def _detect_license_file(repo_path: Path, rel_path: str) -> str | None:
    """Identify a license file's SPDX id by content signature, or None."""
    try:
        text = (repo_path / rel_path).read_text(encoding="utf-8", errors="replace")[:200_000]
    except OSError:
        return None
    for spdx_id, needles in _LICENSE_SIGNATURES:
        if all(n in text for n in needles):
            return spdx_id
    return None


def _resolve_licenses(
    license_info: object, license_files: list, repo_path: Path
) -> tuple[list, list[str], list[str]]:
    """Resolve declared license metadata into CycloneDX license entries.

    Returns (entries, declared_files, undetected_files). Never emits a
    license name that was not declared or content-detected — an
    undetermined file leaves ``entries`` unchanged and lands in
    ``undetected_files`` instead of producing a fabricated claim.
    """
    entries: list = []
    declared_files: list[str] = []
    undetected: list[str] = []

    def _detect_files(paths) -> None:
        for rel in paths:
            rel = str(rel)
            declared_files.append(rel)
            detected = _detect_license_file(repo_path, rel)
            if detected:
                entry = {"license": {"id": detected}}
                if entry not in entries:
                    entries.append(entry)
            else:
                undetected.append(rel)

    if isinstance(license_info, str):
        if license_info.strip():
            entries.append(_license_entry(license_info))
    elif isinstance(license_info, dict):
        text = license_info.get("text") or ""
        if text.strip():
            entries.append(_license_entry(text))
        file_keys = (
            license_info.get("files")
            or license_info.get("license-files")
            or ([license_info["file"]] if license_info.get("file") else [])
        )
        if file_keys:
            _detect_files(file_keys)
    if license_files:
        _detect_files(license_files)
    return entries, declared_files, undetected


def _parse_dep(dep: str) -> tuple[str, str, str]:
    """Parse a PEP 508 dependency string into (name, pinned_version, spec).

    Environment markers (``; ...``) are stripped before parsing so they
    cannot leak into version fields. ``pinned_version`` is only populated
    for an exact ``==`` pin — range specifiers are constraints, not a
    resolved version, and are preserved in ``spec`` for transparency.
    """
    base = dep.split(";", 1)[0].strip()
    match = _DEP_NAME_RE.match(base)
    if not match:
        return base, "", ""
    name = match.group(1)
    spec = base[match.end() :].strip()
    spec = re.sub(r"^\[[^\]]*\]\s*", "", spec)  # extras are not versions
    version = ""
    if spec.startswith("=="):
        version = spec[2:].split(",", 1)[0].strip()
    return name, version, spec


def generate_sbom(repo_path: Path) -> dict:
    """Generate a CycloneDX 1.5 SBOM from pyproject.toml.

    Args:
        repo_path: Path to the repository root (containing pyproject.toml).

    Returns:
        CycloneDX SBOM as a dict.
    """
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        print(f"ERROR: pyproject.toml not found at {pyproject}", file=sys.stderr)
        return {}

    with open(pyproject, "rb") as f:
        config = tomllib.load(f)

    project = config.get("project", {})
    name = project.get("name", "unknown")
    version = project.get("version", "0.0.0")
    description = project.get("description", "")
    license_info = project.get("license", {})

    # Compute package file hash
    pkg_init = repo_path / "hummbl_governance" / "__init__.py"
    pkg_hash = ""
    if pkg_init.exists():
        pkg_hash = hashlib.sha256(pkg_init.read_bytes()).hexdigest()

    # Build components list
    components = []

    # Main package component
    main_component = {
        "type": "library",
        "bom-ref": f"pkg:pypi/{name}@{version}",
        "name": name,
        "version": version,
        "description": description,
        "licenses": [],
        "purl": f"pkg:pypi/{name}@{version}",
        "properties": [
            {"name": "hummbl:runtime_deps", "value": "0"},
            {"name": "hummbl:pkg_sha256", "value": pkg_hash},
        ],
    }

    # License — derived from declared metadata or file content, never assumed
    license_files = project.get("license-files") or project.get("license_files") or []
    lic_entries, lic_declared, lic_undetected = _resolve_licenses(
        license_info, license_files, repo_path
    )
    main_component["licenses"] = lic_entries
    if lic_declared:
        main_component["properties"].append(
            {"name": "hummbl:license_files", "value": ",".join(lic_declared)}
        )
    if lic_undetected:
        main_component["properties"].append(
            {"name": "hummbl:license_undetected", "value": ",".join(lic_undetected)}
        )

    components.append(main_component)

    # Test dependencies (from optional-dependencies.test)
    test_deps = project.get("optional-dependencies", {}).get("test", [])
    test_dep_refs: list[str] = []
    for dep in test_deps:
        dep_name, dep_version, dep_spec = _parse_dep(dep)

        comp = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{dep_name}",
            "name": dep_name,
            "scope": "optional",
            "purl": f"pkg:pypi/{dep_name}",
            "properties": [
                {"name": "hummbl:dependency_type", "value": "test"},
            ],
        }
        if dep_version:
            comp["version"] = dep_version
            comp["bom-ref"] = f"pkg:pypi/{dep_name}@{dep_version}"
            comp["purl"] = f"pkg:pypi/{dep_name}@{dep_version}"
        if dep_spec:
            comp["properties"].append({"name": "hummbl:version_spec", "value": dep_spec})
        components.append(comp)
        test_dep_refs.append(comp["bom-ref"])

    # Build SBOM
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": "HUMMBL",
                    "name": "gap5-sbom-generator",
                    "version": "1.0.0",
                }
            ],
            "component": main_component,
        },
        "components": components,
        "dependencies": [
            {
                "ref": f"pkg:pypi/{name}@{version}",
                "dependsOn": test_dep_refs,
            }
        ],
    }

    return sbom


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CycloneDX SBOM")
    parser.add_argument("--output", default="sbom.cdx.json", help="Output file path")
    parser.add_argument("--repo", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_path = Path(args.repo)
    sbom = generate_sbom(repo_path)
    if not sbom:
        return 1

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    print(f"SBOM generated: {output_path}", file=sys.stderr)
    print(f"  Format: CycloneDX 1.5", file=sys.stderr)
    print(f"  Components: {len(sbom.get('components', []))}", file=sys.stderr)
    print(f"  Main: {sbom['metadata']['component']['name']}@{sbom['metadata']['component']['version']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
