from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_bus.replay_worker import replay_next_record
from hummbl_bus.spool import enqueue_outbound_record


def test_replay_next_record_empty_when_no_spool(tmp_path: Path) -> None:
    result = replay_next_record(
        "localhost",
        spool_dir=tmp_path / "nonexistent",
        post_func=lambda *a, **kw: {"ok": True},
    )
    assert result["status"] == "empty"


def test_replay_next_record_replays_and_removes(tmp_path: Path) -> None:
    enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-1",
        spool_dir=tmp_path,
    )
    calls = []

    def fake_post(host, sender, recipient, msg_type, message, **kw):
        calls.append((host, sender, recipient, msg_type, message, kw))
        return {"ok": True, "duplicate": False}

    result = replay_next_record(
        "localhost",
        spool_dir=tmp_path,
        post_func=fake_post,
    )
    assert result["status"] == "replayed"
    assert result["request_id"] == "req-1"
    assert len(calls) == 1
    # spool record removed after successful replay
    assert len(list(tmp_path.glob("*.json"))) == 0


def test_replay_next_record_marks_duplicate(tmp_path: Path) -> None:
    enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-2",
        spool_dir=tmp_path,
    )

    def fake_post(*a, **kw):
        return {"ok": True, "duplicate": True}

    result = replay_next_record("localhost", spool_dir=tmp_path, post_func=fake_post)
    assert result["status"] == "duplicate"
    assert len(list(tmp_path.glob("*.json"))) == 0


def test_replay_next_record_defers_on_transient_error(tmp_path: Path) -> None:
    enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-3",
        spool_dir=tmp_path,
    )

    def fake_post(*a, **kw):
        return {
            "ok": False,
            "permanent_error": False,
            "status_code": 503,
            "error": "timeout",
        }

    result = replay_next_record("localhost", spool_dir=tmp_path, post_func=fake_post)
    assert result["status"] == "deferred"
    assert result["attempts"] == 1
    # record still present
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_replay_next_record_dead_letters_permanent_error(tmp_path: Path) -> None:
    enqueue_outbound_record(
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        message="hello",
        request_id="req-4",
        spool_dir=tmp_path,
    )
    dead_letter = tmp_path / "dead.jsonl"

    def fake_post(*a, **kw):
        return {
            "ok": False,
            "permanent_error": True,
            "status_code": 422,
            "error": "bad payload",
        }

    result = replay_next_record(
        "localhost",
        spool_dir=tmp_path,
        dead_letter_path=dead_letter,
        post_func=fake_post,
    )
    assert result["status"] == "dead_lettered"
    assert len(list(tmp_path.glob("*.json"))) == 0
    lines = dead_letter.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_replay_next_record_quarantines_privileged_record(tmp_path: Path) -> None:
    """Privileged records in the spool must be dead-lettered, not replayed."""
    # enqueue_outbound_record rejects privileged types, so we write one directly
    record = {
        "schema": "hummbl_bus.spool.v1",
        "request_id": "req-5",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message": "approve",
        "created_at": "20260101T000000Z",
        "last_attempt_at": None,
        "attempt_count": 0,
    }
    spool_path = tmp_path / "20260101T000000Z--req-5.json"
    spool_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    dead_letter = tmp_path / "dead.jsonl"

    posted = False

    def fake_post(*a, **kw):
        nonlocal posted
        posted = True
        return {"ok": True}

    result = replay_next_record(
        "localhost",
        spool_dir=tmp_path,
        dead_letter_path=dead_letter,
        post_func=fake_post,
    )
    assert result["status"] == "dead_lettered"
    assert not posted  # must not have attempted to replay
    assert not spool_path.exists()
    lines = dead_letter.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_replay_next_record_privileged_without_dead_letter_raises(
    tmp_path: Path,
) -> None:
    record = {
        "schema": "hummbl_bus.spool.v1",
        "request_id": "req-6",
        "sender": "codex",
        "recipient": "all",
        "type": "DIRECTIVE",
        "message": "do thing",
        "created_at": "20260101T000000Z",
        "last_attempt_at": None,
        "attempt_count": 0,
    }
    spool_path = tmp_path / "20260101T000000Z--req-6.json"
    spool_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="dead_letter_path is required"):
        replay_next_record(
            "localhost",
            spool_dir=tmp_path,
            post_func=lambda *a, **kw: {"ok": True},
        )
