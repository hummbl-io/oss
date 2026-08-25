from __future__ import annotations

from hummbl_bus.bus_verifier import audit_bus
from hummbl_bus.bus_writer import post_message

SECRET = b"0123456789abcdef0123456789abcdef"


def test_audit_bus_counts_signed_and_unsigned_messages(tmp_path) -> None:
    bus_path = tmp_path / "messages.tsv"

    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "hello",
        secret=SECRET,
        validate=False,
    )
    post_message(
        bus_path,
        "codex",
        "all",
        "STATUS",
        "world",
        validate=False,
    )

    report = audit_bus(bus_path, secret=SECRET, known_agents={"codex", "all"})

    assert report.total_messages == 2
    assert report.signed_messages == 1
    assert report.unsigned_messages == 1
    assert report.verified_ok == 1
    assert report.verified_fail == 0
    assert report.unknown_senders == 0
    assert report.issues == []
    assert report.to_dict()["signing_coverage_pct"] == 50.0
