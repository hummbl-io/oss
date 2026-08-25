from __future__ import annotations

import importlib


def test_public_package_imports() -> None:
    module = importlib.import_module("hummbl_bus")

    assert module.__name__ == "hummbl_bus"
    assert hasattr(module, "BusMessage")
    assert hasattr(module, "SecureTSVEncoder")
    assert hasattr(module, "SecureTSVDecoder")


def test_secure_tsv_round_trip() -> None:
    from hummbl_bus import BusMessage, SecureTSVDecoder, SecureTSVEncoder

    message = BusMessage(
        timestamp="2026-05-08T23:10:00Z",
        from_id="codex",
        to_id="all",
        message_type="STATUS",
        payload="line one\nline two\twith tab",
    )

    encoded = SecureTSVEncoder.encode_message(message)
    decoded = SecureTSVDecoder.decode_line(encoded)

    assert decoded == message
