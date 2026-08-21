from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_memory_system_registry import validate_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "memory_system_registry.candidate.json"
MARKDOWN = ROOT / "docs" / "MEMORY_SYSTEM_REGISTRY.md"


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_memory_system_registry_validates():
    # In CI only hummbl-governance is checked out; cross-repo path existence
    # (hummbl-governance, local-home) is verified locally, not in CI.
    assert validate_registry(REGISTRY, MARKDOWN, available_repos={"hummbl-governance"}) == []


def test_registry_entries_use_structured_paths():
    data = _registry()
    for entry in data["entries"]:
        assert "current_home" not in entry
        assert entry["paths"]
        for path_entry in entry["paths"]:
            assert {"repo", "path", "path_type", "exists_checked", "exists"} <= path_entry.keys()


def test_registry_records_evidence_commands():
    data = _registry()
    commands = data["evidence"]["commands"]
    assert len(commands) >= 4
    for command in commands:
        assert command["purpose"]
        assert command["workdir"]
        assert command["command"]
        assert command["result"]


def test_markdown_mentions_all_registry_ids_and_candidates():
    data = _registry()
    markdown = MARKDOWN.read_text(encoding="utf-8")
    for entry in data["entries"]:
        assert f"`{entry['id']}`" in markdown
    for candidate in data["repo_candidates"]:
        assert f"`{candidate['name']}`" in markdown
