from __future__ import annotations

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

    assert decoded == message


def test_legacy_encoding_round_trip() -> None:
    encoded = SecureTSVEncoder.encode_legacy_message(
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        "plain\ttext\nhere",
    )

    decoded = SecureTSVDecoder.decode_line(encoded)

    assert decoded.version == "legacy"
    assert decoded.payload == "plain text here"


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
    assert lines[0].split("\t") == SecureTSVEncoder.COLUMNS

    decoded = SecureTSVDecoder.decode_line(lines[1])
    assert decoded.from_id == "codex"
    assert decoded.to_id == "all"
    assert decoded.message_type == "STATUS"
    assert decoded.payload == {"message": "hello"}


def test_sanitize_for_tsv_removes_control_characters() -> None:
    sanitized = sanitize_for_tsv("a\tb\r\nc")

    assert "\t" not in sanitized
    assert "\n" not in sanitized
    assert "\r" not in sanitized
