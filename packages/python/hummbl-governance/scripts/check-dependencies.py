#!/usr/bin/env python3
"""Dependency drift check for claim-safe repository policy.

The check focuses on:
- declared runtime dependencies in pyproject.toml
- runtime imports in tracked package/module files
- local dependency manifests under requirements.txt and requirements/*.txt
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    import tomli as tomllib  # type: ignore


@dataclass
class DependencyReport:
    declared_runtime: list[str]
    found_external: dict[str, set[str]]
    manifest_violations: list[str]
    requirements_files: list[str]
    status: str


def load_pyproject(root: pathlib.Path) -> tuple[dict[str, Any], list[str]]:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}, ["pyproject.toml missing"]
    parsed = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    deps = parsed.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list):
        return parsed, ["project.dependencies not a list"]
    return parsed, [str(dep).strip() for dep in deps if str(dep).strip()]


def normalized_package_name(value: str) -> str:
    return re.split(r"[>=<~=! ]", value, maxsplit=1)[0].strip().lower().replace("-", "_")


def handler_catches_import_error(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name) and handler.type.id == "ImportError":
        return True
    if isinstance(handler.type, ast.Tuple):
        return any(isinstance(item, ast.Name) and item.id == "ImportError" for item in handler.type.elts)
    return False


def _collect_imports(node: ast.AST, optional: bool = False) -> tuple[set[str], set[str]]:
    required: set[str] = set()
    optional_imports: set[str] = set()

    def visit(current: ast.AST, in_optional: bool = False) -> None:
        if isinstance(current, ast.Try):
            catches_import_error = any(handler_catches_import_error(handler) for handler in current.handlers)
            for child in current.body:
                visit(child, in_optional or catches_import_error)
            for child in current.orelse:
                visit(child, in_optional)
            for child in current.finalbody:
                visit(child, in_optional)
            for handler in current.handlers:
                for child in handler.body:
                    visit(child, in_optional)
            return

        if isinstance(current, ast.Import):
            for alias in current.names:
                name = alias.name.split(".")[0]
                if name:
                    if in_optional:
                        optional_imports.add(name)
                    else:
                        required.add(name)
            return

        if isinstance(current, ast.ImportFrom):
            if current.level and current.level > 0:
                return
            if current.module:
                name = current.module.split(".")[0]
                if in_optional:
                    optional_imports.add(name)
                else:
                    required.add(name)
            return

        for child in ast.iter_child_nodes(current):
            visit(child, in_optional)

    visit(node, optional)
    return required, optional_imports


def parse_imports(path: pathlib.Path) -> tuple[set[str], set[str]]:
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), set()
    return _collect_imports(tree)


def scan_py_root(root: pathlib.Path) -> dict[str, set[str]]:
    scopes = {
        "hummbl_governance": set(),
        "scripts": set(),
        "root": set(),
    }

    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts or ".venv" in py_file.parts:
            continue

        rel = py_file.relative_to(root)
        rel_parts = set(rel.parts)
        rel_name = rel.name.lower()

        # Skip build artifacts and generated folders
        if rel_parts.intersection({"build", "dist", ".eggs", "_state", ".ruff_cache", ".coverage"}):
            continue

        # Skip test modules to avoid treating test-only imports as runtime deps
        if rel_name.startswith("test_") or rel_name.endswith("_test.py") or rel_name == "conftest.py":
            continue
        if "tests" in rel.parts:
            continue

        try:
            required_imports, _ = parse_imports(py_file)
        except OSError:
            continue

        if any(part in str(py_file) for part in ["\\hummbl_governance\\", "/hummbl_governance/"]):
            bucket = "hummbl_governance"
        elif any(part in str(py_file) for part in ["\\hummbl_governance\\", "/hummbl_governance/"]):
            bucket = "hummbl_governance"
        elif any(part in str(py_file) for part in ["\\scripts\\", "/scripts/"]):
            bucket = "scripts"
        else:
            bucket = "root"

        scopes[bucket].update(required_imports)

    return scopes


def discover_internal_modules(root: pathlib.Path) -> set[str]:
    modules: set[str] = set()
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts or ".venv" in py_file.parts:
            continue
        stem = py_file.stem
        if stem:
            modules.add(stem)
        if len(py_file.parts) >= 2:
            modules.add(py_file.parent.name)
    modules.update({"hummbl_governance", "hummbl_governance", "scripts", "tests", "__future__"})
    return modules


def is_stdlib_module(name: str) -> bool:
    try:
        import sys

        if hasattr(sys, "stdlib_module_names"):
            return name in sys.stdlib_module_names
    except (AttributeError, TypeError):
        pass
    return name in {
        "argparse",
        "asyncio",
        "base64",
        "collections",
        "datetime",
        "difflib",
        "functools",
        "hashlib",
        "json",
        "logging",
        "os",
        "pathlib",
        "re",
        "subprocess",
        "sys",
        "time",
        "typing",
        "uuid",
        "dataclasses",
        "math",
        "threading",
        "tomllib",
        "__future__",
    }


def classify_scope(scope_imports: dict[str, set[str]], internal_modules: set[str]) -> dict[str, set[str]]:
    external_by_scope: dict[str, set[str]] = {}
    for scope, imports in scope_imports.items():
        external: set[str] = set()
        for module in sorted(imports):
            low = module.replace("-", "_")
            if is_stdlib_module(module) or module in internal_modules:
                continue
            external.add(low)
        external_by_scope[scope] = external
    return external_by_scope


def find_requirements(root: pathlib.Path) -> list[pathlib.Path]:
    candidates = [root / "requirements.txt"]
    requirements_dir = root / "requirements"
    if requirements_dir.exists():
        candidates.extend(requirements_dir.glob("*.txt"))
    return [p for p in candidates if p.exists()]


def scan_requirements_file(path: pathlib.Path) -> list[str]:
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r ") or line.startswith("--"):
            continue
        entries.append(normalized_package_name(line))
    return entries


def build_report(root: pathlib.Path) -> DependencyReport:
    parsed, declared_issues = load_pyproject(root)
    declared = declared_issues[:] if parsed == {} else []
    if parsed:
        declared = [normalized_package_name(entry) for entry in parsed.get("project", {}).get("dependencies", [])]
    scope_imports = scan_py_root(root)
    internal_modules = discover_internal_modules(root)
    external = classify_scope(scope_imports, internal_modules)

    requirements_files = []
    manifest_violations: list[str] = []
    req_files = find_requirements(root)
    declared_set = set(declared)
    for req in req_files:
        requirements_files.append(str(req))
        declared_set.update(scan_requirements_file(req))

    for scope, externals in external.items():
        if scope in {"hummbl_governance", "hummbl_governance"} and externals:
            for item in sorted(externals):
                if item not in declared_set:
                    manifest_violations.append(f"{scope} import '{item}' not in declared runtime manifests")

    status = "pass"
    if manifest_violations or declared_issues:
        status = "fail"

    return DependencyReport(
        declared_runtime=declared,
        found_external=external,
        manifest_violations=manifest_violations + declared_issues,
        requirements_files=requirements_files,
        status=status,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check dependency and import drift")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on any violation")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    return parser.parse_args()


def report_to_payload(report: DependencyReport) -> dict[str, Any]:
    return {
        "declared_runtime": report.declared_runtime,
        "found_external": {k: sorted(v) for k, v in sorted(report.found_external.items())},
        "manifest_violations": report.manifest_violations,
        "requirements_files": report.requirements_files,
        "status": report.status,
    }


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.repo).resolve()
    report = build_report(root)
    payload = report_to_payload(report)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Declared runtime deps: {len(report.declared_runtime)}")
        print(f"Status: {report.status}")
        for scope, modules in sorted(report.found_external.items()):
            extra = ", ".join(sorted(modules)) if modules else "none"
            print(f"  {scope}: {extra}")
        if report.manifest_violations:
            print("Violations:")
            for violation in report.manifest_violations:
                print(f"  - {violation}")

    if args.strict and report.status != "pass":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
