"""The README documents a `hummbl-mcp-basen` command; keep it declared and resolvable."""

import importlib
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_console_script_is_declared_and_resolves():
    scripts = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["scripts"]
    module_name, _, attr = scripts["hummbl-mcp-basen"].partition(":")

    assert callable(getattr(importlib.import_module(module_name), attr))
