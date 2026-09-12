from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _project_metadata() -> dict[str, Any]:
    document = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return document["project"]


def test_default_install_has_no_third_party_dependencies() -> None:
    project = _project_metadata()

    assert project.get("dependencies") == []


def test_ed25519_support_is_an_explicit_optional_extra() -> None:
    project = _project_metadata()
    optional = project["optional-dependencies"]

    assert optional["security"] == ["cryptography>=42.0"]


def test_source_has_no_undeclared_third_party_imports() -> None:
    allowed = {"cryptography", "hummbl_bus"}
    violations: list[str] = []

    for path in (PROJECT_ROOT / "src" / "hummbl_bus").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules = [node.module]
            for module in modules:
                root = module.split(".", 1)[0]
                if root not in sys.stdlib_module_names and root not in allowed:
                    relative = path.relative_to(PROJECT_ROOT).as_posix()
                    violations.append(f"{relative}:{node.lineno}: {module}")

    assert violations == []
