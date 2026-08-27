from __future__ import annotations

import json
from pathlib import Path

import pytest
from hummbl_bus.spool import (
    DEFAULT_SPOOL_DIR,
    enqueue_outbound_record,
    list_spool_records,
    load_spool_record,
    mark_spool_attempt,
    move_spool_record_to_dead_letter,
    remove_spool_record,
    resolve_spool_dir,
    save_spool_record,
)


def test_default_spool_dir_uses_hummbl_bus_namespace() -> None:
    assert DEFAULT_SPOOL_DIR.startswith("hummbl_bus/")


def test_resolve_spool_dir_with_override(tmp_path: Path) -> None:
    result = resolve_spool_dir(tmp_path / "custom")
    assert result == tmp_path / "custom"


def test_enqueue_outbound_record_creates_file(tmp_path: Path) -> None:
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-1",
        spool_dir=tmp_path,
    )
    assert path.exists()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["schema"] == "hummbl_bus.spool.v1"
    assert record["sender"] == "codex"
    assert record["type"] == "STATUS"
    assert record["message"] == "hello"
    assert record["request_id"] == "req-1"
    assert record["attempt_count"] == 0
    assert record["last_attempt_at"] is None


def test_enqueue_outbound_record_with_correlation_and_origin(tmp_path: Path) -> None:
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-2",
        correlation_id="corr-abc",
        origin_machine="laptop-1",
        spool_dir=tmp_path,
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["correlation_id"] == "corr-abc"
    assert record["origin_machine"] == "laptop-1"


def test_enqueue_outbound_record_redacts_bridge_url_credentials(tmp_path: Path) -> None:
    """#1761: credentials in bridge_url must be redacted before persisting."""
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-3",
        bridge_url="https://user:password@host.example.com/path?token=sk-abc123def456ghi789jkl012mno345",  # pragma: allowlist secret
        spool_dir=tmp_path,
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    url = record["bridge_url"]
    assert "password" not in url
    assert "sk-abc123" not in url
    assert "<redacted>" in url


def test_enqueue_outbound_record_rejects_privileged_type(tmp_path: Path) -> None:
    """DECISION/DIRECTIVE cannot be spooled -- require live authenticated delivery."""
    with pytest.raises(PermissionError, match="privileged bus messages"):
        enqueue_outbound_record(
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="approve",
            request_id="req-4",
            spool_dir=tmp_path,
        )


def test_list_spool_records_returns_oldest_first(tmp_path: Path) -> None:
    for i in range(3):
        enqueue_outbound_record(
            sender="codex",
            recipient="all",
            msg_type="STATUS",
            message=f"msg-{i}",
            request_id=f"req-{i}",
            spool_dir=tmp_path,
            created_at=f"2026-01-0{i + 1}T00:00:00Z",
        )
    records = list_spool_records(tmp_path)
    assert len(records) == 3
    # oldest first = sorted by filename (timestamp-based)
    first = json.loads(records[0].read_text(encoding="utf-8"))
    assert first["created_at"] == "2026-01-01T00:00:00Z"


def test_list_spool_records_empty_when_dir_missing(tmp_path: Path) -> None:
    assert list_spool_records(tmp_path / "nonexistent") == []


def test_mark_spool_attempt_increments_count(tmp_path: Path) -> None:
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-5",
        spool_dir=tmp_path,
    )
    updated = mark_spool_attempt(path)
    assert updated["attempt_count"] == 1
    assert updated["last_attempt_at"] is not None
    updated = mark_spool_attempt(path)
    assert updated["attempt_count"] == 2


def test_save_and_load_spool_record(tmp_path: Path) -> None:
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-6",
        spool_dir=tmp_path,
    )
    record = load_spool_record(path)
    record["custom_field"] = "updated"
    save_spool_record(path, record)
    reloaded = load_spool_record(path)
    assert reloaded["custom_field"] == "updated"


def test_remove_spool_record(tmp_path: Path) -> None:
    path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-7",
        spool_dir=tmp_path,
    )
    assert path.exists()
    remove_spool_record(path)
    assert not path.exists()
    # idempotent
    remove_spool_record(path)


def test_move_spool_record_to_dead_letter(tmp_path: Path) -> None:
    spool_path = enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-8",
        spool_dir=tmp_path / "spool",
    )
    dead_letter = tmp_path / "dead_letters.jsonl"
    move_spool_record_to_dead_letter(
        spool_path, reason="test failure", dead_letter_path=dead_letter
    )
    assert not spool_path.exists()
    lines = dead_letter.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["reason"] == "test failure"
    assert entry["source"] == "replay_worker"
    payload = entry["payload"]
    assert payload["request_id"] == "req-8"
