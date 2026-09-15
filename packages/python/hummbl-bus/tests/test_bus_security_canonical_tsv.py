from __future__ import annotations

from hummbl_bus.bus_security import BusIdentity, BusMessage


def test_signed_bus_message_round_trips_in_five_columns() -> None:
    identity = BusIdentity("codex", secret=b"x" * 32)
    original = identity.create_signed_message(
        "all",
        "STATUS",
        {"message": "hello\nworld", "count": 1},
    )

    encoded = original.to_tsv_line()
    decoded = BusMessage.from_tsv_line(encoded)

    assert len(encoded.split("\t")) == 5
    assert decoded.payload == original.payload
    assert decoded.nonce == original.nonce
    assert decoded.signature == original.signature
    assert identity.verify_message(decoded, check_replay=False)
