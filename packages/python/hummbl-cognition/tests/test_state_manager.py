"""Tests for hummbl_cognition.state_manager — atomic state read/write with locking."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_cognition.state_manager import (
    ConcurrencyError,
    read_state,
    write_state,
)
from hummbl_cognition.models import SharedState


class TestReadState:
    def test_read_nonexistent_returns_default(self, tmp_state_path: Path) -> None:
        state = read_state(tmp_state_path)
        assert state.version == 0
        assert state.active_agents == {}

    def test_read_existing_state(self, tmp_state_path: Path) -> None:
        state = SharedState(version=5, updated_by="agent-1")
        write_state(state, state_path=tmp_state_path)
        read = read_state(tmp_state_path)
        assert read.version == 5
        assert read.updated_by == "agent-1"

    def test_read_corrupt_json_returns_default(
        self, tmp_state_path: Path
    ) -> None:
        tmp_state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_state_path.write_text("{invalid json", encoding="utf-8")
        state = read_state(tmp_state_path)
        assert state.version == 0


class TestWriteState:
    def test_write_creates_file(self, tmp_state_path: Path) -> None:
        state = SharedState(version=1, updated_by="agent-1")
        write_state(state, state_path=tmp_state_path)
        assert tmp_state_path.exists()
        data = json.loads(tmp_state_path.read_text(encoding="utf-8"))
        assert data["version"] == 1

    def test_write_overwrites(self, tmp_state_path: Path) -> None:
        s1 = SharedState(version=1, updated_by="agent-1")
        write_state(s1, state_path=tmp_state_path)
        s2 = SharedState(version=2, updated_by="agent-2")
        write_state(s2, state_path=tmp_state_path)
        data = json.loads(tmp_state_path.read_text(encoding="utf-8"))
        assert data["version"] == 2
        assert data["updated_by"] == "agent-2"

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        state_path = tmp_path / "nested" / "state.json"
        state = SharedState(version=1)
        write_state(state, state_path=state_path)
        assert state_path.exists()

    def test_write_with_matching_expected_version(
        self, tmp_state_path: Path
    ) -> None:
        s1 = SharedState(version=1)
        write_state(s1, state_path=tmp_state_path)
        s2 = SharedState(version=2)
        write_state(s2, state_path=tmp_state_path, expected_version=1)
        assert read_state(tmp_state_path).version == 2

    def test_write_with_mismatched_expected_version_raises(
        self, tmp_state_path: Path
    ) -> None:
        s1 = SharedState(version=1)
        write_state(s1, state_path=tmp_state_path)
        s2 = SharedState(version=2)
        with pytest.raises(ConcurrencyError, match="Version mismatch"):
            write_state(s2, state_path=tmp_state_path, expected_version=99)

    def test_write_without_expected_version_succeeds(
        self, tmp_state_path: Path
    ) -> None:
        s1 = SharedState(version=1)
        write_state(s1, state_path=tmp_state_path)
        s2 = SharedState(version=2)
        # No expected_version — should always succeed
        write_state(s2, state_path=tmp_state_path)
        assert read_state(tmp_state_path).version == 2

    def test_roundtrip_complex_state(self, tmp_state_path: Path) -> None:
        state = SharedState(version=10, updated_by="agent-x")
        state.active_agents["agent-1"] = {"task": "building", "status": "active"}
        state.claimed_files["/path/to/file"] = {"agent": "agent-1"}
        state.active_decisions.append({"id": "dec-1", "rationale": "because"})
        write_state(state, state_path=tmp_state_path)
        restored = read_state(tmp_state_path)
        assert restored.version == 10
        assert "agent-1" in restored.active_agents
        assert restored.active_agents["agent-1"]["task"] == "building"
        assert "/path/to/file" in restored.claimed_files
        assert len(restored.active_decisions) == 1
