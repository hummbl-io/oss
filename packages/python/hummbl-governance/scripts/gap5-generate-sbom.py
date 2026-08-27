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
import sys
import time
import uuid
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


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

    # License
    if isinstance(license_info, dict):
        lic_text = license_info.get("text", "")
        if lic_text:
            main_component["licenses"] = [{"license": {"id": lic_text}}]
        elif license_info.get("license-files"):
            main_component["licenses"] = [{"license": {"name": "Apache-2.0"}}]
    elif isinstance(license_info, str):
        main_component["licenses"] = [{"license": {"id": license_info}}]

    components.append(main_component)

    # Test dependencies (from optional-dependencies.test)
    test_deps = project.get("optional-dependencies", {}).get("test", [])
    for dep in test_deps:
        # Parse dependency string (e.g., "pytest>=7.0")
        dep_name = dep.split(">=")[0].split("<=")[0].split("==")[0].split(">")[0].split("<")[0].strip()
        dep_version = ""
        if ">=" in dep:
            dep_version = dep.split(">=")[1].strip()
        elif "==" in dep:
            dep_version = dep.split("==")[1].strip()

        comp = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{dep_name}",
            "name": dep_name,
            "version": dep_version,
            "scope": "optional",
            "purl": f"pkg:pypi/{dep_name}",
            "properties": [
                {"name": "hummbl:dependency_type", "value": "test"},
            ],
        }
        components.append(comp)

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
                "dependsOn": [f"pkg:pypi/{d.split('>')[0].split('=')[0].strip()}" for d in test_deps],
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
