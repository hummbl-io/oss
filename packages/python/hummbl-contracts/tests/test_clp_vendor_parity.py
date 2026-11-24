"""Regression test ensuring clp.ledger_entry.schema.json vendor enum stays in parity with hummbl-cognition."""
from __future__ import annotations

import json
import re
from pathlib import Path

from hummbl_contracts.schema_validator import validate_entry_dict

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "cognition"
    / "clp.ledger_entry.schema.json"
)
COGNITION_MODELS = (
    REPO_ROOT
    / "packages"
    / "python"
    / "hummbl-cognition"
    / "src"
    / "hummbl_cognition"
    / "models.py"
)


def _extract_cognition_vendors() -> set[str]:
    text = COGNITION_MODELS.read_text(encoding="utf-8")
    m = re.search(r"VALID_VENDORS\s*=\s*frozenset\(\s*\{(.*?)\}\s*\)", text, re.DOTALL)
    assert m, "Could not locate VALID_VENDORS in hummbl_cognition/models.py"
    return set(re.findall(r'"([a-z0-9_-]+)"', m.group(1)))


def test_clp_schema_vendor_enum_superset_of_cognition_valid_vendors():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_vendors = set(schema["properties"]["vendor"]["enum"])
    cognition_vendors = _extract_cognition_vendors()
    missing = cognition_vendors - schema_vendors
    assert not missing, f"clp.ledger_entry.schema.json missing vendors from hummbl-cognition: {sorted(missing)}"


def test_clp_schema_accepts_newly_aligned_vendors():
    for vendor in ("xai", "minimax", "cognition", "deepseek", "openrouter", "zai"):
        entry = {
            "id": "clp-0123456789ab",
            "timestamp": "2026-11-24T03:00:00Z",
            "agent": "test-agent",
            "vendor": vendor,
            "model": "test-model",
            "type": "discovery",
            "scope": "project",
            "content": "Vendor schema parity check.",
            "content_hash": "a" * 64,
        }
        is_valid, errors = validate_entry_dict(entry)
        assert is_valid and errors == [], (
            f"Unexpected validation errors for vendor={vendor}: {errors}"
        )
