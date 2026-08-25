from __future__ import annotations

import json
from pathlib import Path

from hummbl_bus.replay_ledger import (
    DEFAULT_REPLAY_LEDGER_PATH,
    lookup_request,
    record_request,
    resolve_replay_ledger_path,
)


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
        sender="codex",
        recipient="all",
        msg_type="STATUS",
        origin_machine="host-01",
        correlation_id="corr-abc",
        bus_path="/path/to/bus.tsv",
        ledger_path=ledger,
    )
    found = lookup_request("req-2", ledger_path=ledger)
    assert found is not None
    assert found["origin_machine"] == "host-01"
    assert found["correlation_id"] == "corr-abc"
    assert found["bus_path"] == "/path/to/bus.tsv"


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
