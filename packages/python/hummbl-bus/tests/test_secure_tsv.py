from __future__ import annotations

from datetime import datetime

import pytest

from hummbl_bus.secure_tsv import (
    BusMessage,
    SecureTSVDecoder,
    SecureTSVEncoder,
    append_message_to_bus,
    sanitize_for_tsv,
)


def test_secure_tsv_round_trip_dict_payload() -> None:
    message = BusMessage(
        timestamp="2026-05-08T23:40:00Z",
        from_id="codex",
        to_id="all",
        message_type="STATUS",
        payload={"message": "hello", "nested": {"alpha": 1}},
    )

    encoded = SecureTSVEncoder.encode_message(message)
    decoded = SecureTSVDecoder.decode_line(encoded)

    assert len(encoded.split("\t")) == 5
    assert decoded == message


def test_append_message_to_bus_writes_header_and_row(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    append_message_to_bus(
        bus_path,
        "codex",
        "all",
        "STATUS",
        {"message": "hello"},
        timestamp="2026-05-08T23:40:00Z",
    )

    lines = bus_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert all(len(line.split("\t")) == 5 for line in lines)
    assert len(SecureTSVEncoder.COLUMNS) == 5

    decoded = SecureTSVDecoder.decode_line(lines[0])
    assert decoded.from_id == "codex"
    assert decoded.to_id == "all"
    assert decoded.message_type == "STATUS"
    assert decoded.payload == {"message": "hello"}


def test_append_message_to_bus_default_timestamp_is_canonical(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    append_message_to_bus(
        bus_path,
        "codex",
        "all",
        "STATUS",
        {"message": "hello"},
    )

    row = bus_path.read_text(encoding="utf-8").strip()
    timestamp = row.split("\t", 1)[0]
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    assert parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == timestamp


def test_append_message_round_trips_when_bus_signing_secret_is_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    bus_path = tmp_path / "messages.tsv"
    monkeypatch.setenv("BUS_SIGNING_SECRET", "s" * 32)

    append_message_to_bus(
        bus_path,
        "codex",
        "all",
        "STATUS",
        {"message": "hello"},
        timestamp="2026-05-08T23:40:00Z",
    )

    row = bus_path.read_text(encoding="utf-8").strip()
    assert SecureTSVDecoder.decode_line(row).payload == {"message": "hello"}


def test_plaintext_five_column_pv_object_is_not_secure_tsv_envelope() -> None:
    payload = '{"p":"aGVsbG8=","v":"1.0"}'
    row = f"2026-05-08T23:40:00Z\tcodex\tall\tSTATUS\t{payload}"

    decoded = SecureTSVDecoder.decode_line(row)

    assert decoded.version == "legacy"
    assert decoded.payload == payload


def test_sanitize_for_tsv_removes_control_characters() -> None:
    sanitized = sanitize_for_tsv("a\tb\r\nc")

    assert "\t" not in sanitized
    assert "\n" not in sanitized
    assert "\r" not in sanitized


def test_legacy_append_rejects_privileged_type(tmp_path) -> None:
    with pytest.raises(PermissionError, match="privileged"):
        append_message_to_bus(
            tmp_path / "messages.tsv",
            "codex",
            "all",
            "DECISION",
            {"message": "approve"},
        )
