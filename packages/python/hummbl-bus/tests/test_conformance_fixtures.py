from __future__ import annotations

import json
from pathlib import Path

import pytest

from hummbl_bus.bus_writer import (
    _normalize_timestamp,
    _parse_signing_envelope,
    escape_message,
    parse_structured_event,
    validate_tsv_integrity,
    verify_bus_message,
)
from hummbl_bus.message_signing import sign_payload, verify_signature

FIXTURES = Path(__file__).parent / "fixtures" / "conformance"


def test_wire_fixture_is_byte_exact_five_column_utf8_lf() -> None:
    raw = (FIXTURES / "wire-v1.tsv").read_bytes()

    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert b"Caf\xc3\xa9 \xe2\x98\x95 \xe2\x80\x94 \xe6\x9d\xb1\xe4\xba\xac" in raw
    for line in raw.splitlines():
        assert len(line.split(b"\t")) == 5


def test_wire_fixture_is_accepted_by_integrity_reader() -> None:
    assert validate_tsv_integrity(FIXTURES / "wire-v1.tsv") == (4, [])


def test_historical_read_fixture_preserves_offset_and_extended_envelope() -> None:
    rows = (
        (FIXTURES / "historical-read-v1.tsv").read_text(encoding="utf-8").splitlines()
    )

    assert rows[0].split("\t", 1)[0] == "2026-05-08T19:40:00-04:00"
    assert validate_tsv_integrity(FIXTURES / "historical-read-v1.tsv") == (2, [])
    assert _parse_signing_envelope(rows[1].split("\t", 4)[4]) is not None


def test_malformed_wire_fixture_reports_column_counts() -> None:
    valid, errors = validate_tsv_integrity(FIXTURES / "malformed-wire-v1.tsv")

    assert valid == 0
    assert errors == [
        "Line 1: Expected 5 columns, got 4",
        "Line 2: Expected 5 columns, got 6",
    ]


def test_escape_contract_preserves_one_physical_tsv_record() -> None:
    assert escape_message("line one\r\nline two\ttab\rthird") == (
        "line one\\nline two tab\\nthird"
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("2026-05-08T23:40:00.999Z", "2026-05-08T23:40:00Z"),
        ("2026-05-08T19:40:00-04:00", "2026-05-08T23:40:00Z"),
    ],
)
def test_timestamp_normalization_contract(source: str, expected: str) -> None:
    assert _normalize_timestamp(source) == expected


def test_shared_hmac_golden_vectors() -> None:
    corpus = json.loads((FIXTURES / "hmac-v1.json").read_text(encoding="utf-8"))
    secret = corpus["secret_utf8"].encode("utf-8")

    for vector in corpus["vectors"]:
        args = (
            secret,
            vector["timestamp"],
            vector["sender"],
            vector["recipient"],
            vector["type"],
            vector["payload"],
            vector["nonce"],
        )
        assert sign_payload(*args) == vector["signature"], vector["name"]
        assert verify_signature(*args, vector["signature"]), vector["name"]


def test_legacy_signed_envelope_fixture_verifies() -> None:
    line = (FIXTURES / "wire-v1.tsv").read_text(encoding="utf-8").splitlines()[3]
    timestamp, sender, recipient, msg_type, envelope = line.split("\t")

    assert _parse_signing_envelope(envelope) is not None
    assert verify_bus_message(
        timestamp,
        sender,
        recipient,
        msg_type,
        envelope,
        b"0123456789abcdef0123456789abcdef",
    ) == (True, "hello")


def test_legacy_host_bearing_envelope_remains_readable() -> None:
    envelope = (
        '{"c":"hello","host":"delta","n":"1746747600000-nonce123",'
        '"s":"cc04cdd55e67bbffdf24a4fb01c5a83eb0bf88a12a6b3f5ac1818cdcc2973771"}'
    )

    assert _parse_signing_envelope(envelope) == (
        "hello",
        "1746747600000-nonce123",
        "cc04cdd55e67bbffdf24a4fb01c5a83eb0bf88a12a6b3f5ac1818cdcc2973771",
    )
    assert verify_bus_message(
        "2026-05-08T23:40:00Z",
        "codex",
        "all",
        "STATUS",
        envelope,
        b"0123456789abcdef0123456789abcdef",
    ) == (True, "hello")


def test_structured_event_reader_accepts_both_existing_schema_ids() -> None:
    corpus = json.loads(
        (FIXTURES / "structured-events-v1.json").read_text(encoding="utf-8")
    )

    assert [
        parse_structured_event(json.dumps(event)) for event in corpus["accepted"]
    ] == (corpus["accepted"])


def test_structured_event_reader_rejects_malformed_and_unknown_payloads() -> None:
    corpus = json.loads(
        (FIXTURES / "structured-events-v1.json").read_text(encoding="utf-8")
    )

    assert all(
        parse_structured_event(payload) is None for payload in corpus["rejected"]
    )


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        '{"c":1,"n":"nonce","s":"signature"}',
        '{"c":"content","n":null,"s":"signature"}',
        '{"c":"content","n":"nonce"}',
        '{"c":"content","n":"nonce","s":"signature"',
    ],
)
def test_legacy_envelope_reader_rejects_malformed_shapes(payload: str) -> None:
    assert _parse_signing_envelope(payload) is None
