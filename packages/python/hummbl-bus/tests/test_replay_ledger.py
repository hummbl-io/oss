from __future__ import annotations

import json
import multiprocessing as mp
import queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from hummbl_bus.replay_ledger import (
    DEFAULT_REPLAY_LEDGER_PATH,
    REMOTE_WRITE_REQUEST_SCHEMA,
    lookup_request,
    record_request,
    request_guard,
    resolve_replay_ledger_path,
)


def _guard_worker(
    ledger_path: str,
    entered: object,
    release: object,
) -> None:
    with request_guard("req-cross-process", ledger_path=ledger_path):
        entered.put(True)
        release.get(timeout=10)


def test_default_ledger_path_uses_hummbl_bus_namespace() -> None:
    assert DEFAULT_REPLAY_LEDGER_PATH.startswith("hummbl_bus/")


def test_resolve_ledger_path_with_override(tmp_path: Path) -> None:
    result = resolve_replay_ledger_path(tmp_path / "custom.jsonl")
    assert result == tmp_path / "custom.jsonl"


def test_lookup_request_returns_none_when_ledger_missing(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    assert lookup_request("req-1", ledger_path=ledger) is None


def test_record_and_lookup_request(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    record = record_request(
        request_id="req-1",
        operation="seed_import",
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        ledger_path=ledger,
    )
    assert record["request_id"] == "req-1"
    assert record["operation"] == "seed_import"
    assert record["type"] == "STATUS"
    assert "accepted_at" in record

    found = lookup_request("req-1", ledger_path=ledger)
    assert found is not None
    assert found["request_id"] == "req-1"


def test_lookup_request_returns_none_for_unknown_id(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    record_request(
        request_id="req-1",
        operation="seed_import",
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        ledger_path=ledger,
    )
    assert lookup_request("req-999", ledger_path=ledger) is None


def test_record_request_with_optional_fields(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    record_request(
        request_id="req-2",
        operation="remote_write",
        state="accepted",
        client_id="codex",
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        origin_machine="anvil",
        correlation_id="corr-abc",
        bus_path="/path/to/bus.tsv",
        request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
        request_sha256="a" * 64,
        message_sha256="b" * 64,
        client_timestamp="2026-08-30T23:59:00Z",
        written_timestamp="2026-08-31T00:00:00Z",
        authorized_content_sha256="b" * 64,
        persisted_message_sha256="c" * 64,
        row_sha256="d" * 64,
        ledger_path=ledger,
    )
    found = lookup_request("req-2", ledger_path=ledger)
    assert found is not None
    assert found["origin_machine"] == "anvil"
    assert found["state"] == "accepted"
    assert found["client_id"] == "codex"
    assert found["correlation_id"] == "corr-abc"
    assert found["bus_path"] == "/path/to/bus.tsv"
    assert found["request_schema"] == REMOTE_WRITE_REQUEST_SCHEMA
    assert found["request_sha256"] == "a" * 64
    assert found["message_sha256"] == "b" * 64
    assert found["client_timestamp"] == "2026-08-30T23:59:00Z"
    assert found["written_timestamp"] == "2026-08-31T00:00:00Z"
    assert found["row_sha256"] == "d" * 64


def test_v2_accepted_remote_write_requires_complete_append_linkage(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="complete append linkage"):
        record_request(
            request_id="req-incomplete",
            operation="remote_write",
            state="accepted",
            sender="codex",
            recipient="all",
            msg_type="STATUS",
            request_schema=REMOTE_WRITE_REQUEST_SCHEMA,
            request_sha256="a" * 64,
            message_sha256="b" * 64,
            ledger_path=tmp_path / "ledger.jsonl",
        )


def test_lookup_request_returns_latest_matching_receipt(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    for accepted_at in ("2026-08-30T23:58:00Z", "2026-08-30T23:59:00Z"):
        record_request(
            request_id="req-latest",
            operation="remote_write",
            sender="codex",
            recipient="all",
            msg_type="STATUS",
            accepted_at=accepted_at,
            ledger_path=ledger,
        )

    found = lookup_request("req-latest", ledger_path=ledger)
    assert found is not None
    assert found["accepted_at"] == "2026-08-30T23:59:00Z"


def test_record_request_appends_multiple(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    for i in range(3):
        record_request(
            request_id=f"req-{i}",
            operation="seed_import",
            sender="codex",
            recipient="all",
            msg_type="STATUS",
            ledger_path=ledger,
        )
    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    for line in lines:
        record = json.loads(line)
        assert record["request_id"].startswith("req-")


def test_lookup_request_skips_malformed_lines(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("not json\n\n", encoding="utf-8")
    record_request(
        request_id="req-1",
        operation="seed_import",
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        ledger_path=ledger,
    )
    found = lookup_request("req-1", ledger_path=ledger)
    assert found is not None
    assert found["request_id"] == "req-1"


def test_concurrent_receipt_writes_are_serialized(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"

    def write_receipt(index: int) -> dict[str, object]:
        return record_request(
            request_id=f"req-thread-{index}",
            operation="remote_write",
            state="accepted",
            client_id="codex",
            sender="codex",
            recipient="all",
            msg_type="STATUS",
            ledger_path=ledger,
        )

    with ThreadPoolExecutor(max_workers=16) as executor:
        records = list(executor.map(write_receipt, range(16)))

    assert len(records) == 16
    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 16
    assert len({json.loads(line)["request_id"] for line in lines}) == 16


def test_request_guard_serializes_across_processes(tmp_path: Path) -> None:
    ledger = str(tmp_path / "ledger.jsonl")
    context = mp.get_context("spawn")
    first_entered = context.Queue()
    first_release = context.Queue()
    second_entered = context.Queue()
    second_release = context.Queue()
    first = context.Process(
        target=_guard_worker,
        args=(ledger, first_entered, first_release),
    )
    second = context.Process(
        target=_guard_worker,
        args=(ledger, second_entered, second_release),
    )
    first.start()
    try:
        assert first_entered.get(timeout=10) is True
        second.start()
        try:
            second_entered.get(timeout=0.5)
            entered_while_locked = True
        except queue.Empty:
            entered_while_locked = False
        assert entered_while_locked is False

        first_release.put(True)
        assert second_entered.get(timeout=10) is True
        second_release.put(True)
    finally:
        first_release.put(True)
        second_release.put(True)
        first.join(timeout=10)
        if second.pid is not None:
            second.join(timeout=10)
        if first.is_alive():
            first.terminate()
        if second.pid is not None and second.is_alive():
            second.terminate()

    assert first.exitcode == 0
    assert second.exitcode == 0
