"""Byte-identical TSV parity tests (release gate #8).

These tests assert that hummbl-bus produces a stable, documented TSV format
for a fixed message set. The format is the canonical 5-column coordination
bus TSV::

    timestamp_utc\tfrom\tto\ttype\tmessage\n

with:
- Timestamp in ``%Y-%m-%dT%H:%M:%SZ`` format
- Message escaped via ``escape_message`` (newlines → literal ``\\n``, tabs → spaces)
- Signed messages wrapped in ``{"c": ..., "n": ..., "s": ...}`` JSON envelope

Since hummbl-governance is not importable in the hummbl-bus venv, these tests use
golden expected-output strings that encode the exact byte format. hummbl-bus
was extracted from hummbl-governance's writer, so matching these golden bytes =
format parity. If hummbl-governance's format ever diverges, a cross-repo test in
hummbl-governance's CI would catch it; these tests ensure hummbl-bus's format
remains stable and documented.

Unsigned messages are fully deterministic (fixed timestamp → exact byte match).
Signed messages use a random nonce, so those tests assert the envelope format
structure via regex and verify the HMAC signature is valid.
"""

from __future__ import annotations

import json
import re

from hummbl_bus.bus_writer import (
    escape_message,
    post_message,
)
from hummbl_bus.message_signing import verify_signature

SECRET = b"0123456789abcdef0123456789abcdef"  # pragma: allowlist secret
FIXED_TS = "2026-08-15T12:00:00Z"


def _read_bus(bus_path) -> str:
    """Read bus file and return raw content (preserving trailing newline)."""
    return bus_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Unsigned message parity — exact byte match
# ---------------------------------------------------------------------------


def test_unsigned_simple_message_byte_parity(tmp_path) -> None:
    """A simple unsigned STATUS message must produce exact TSV bytes."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "hello world",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello world\n"
    assert _read_bus(bus) == expected


def test_unsigned_empty_recipient_byte_parity(tmp_path) -> None:
    """Broadcast recipient 'all' must be preserved exactly."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "claude-code",
        "all",
        "SITREP",
        "daily standup complete",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = (
        "2026-08-15T12:00:00Z\tclaude-code\tall\tSITREP\tdaily standup complete\n"
    )
    assert _read_bus(bus) == expected


def test_unsigned_directed_message_byte_parity(tmp_path) -> None:
    """A directed message (to specific agent) must preserve recipient."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "devin",
        "PROPOSAL",
        "merge PR #22",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = "2026-08-15T12:00:00Z\tcodex\tdevin\tPROPOSAL\tmerge PR #22\n"
    assert _read_bus(bus) == expected


# ---------------------------------------------------------------------------
# Escaping parity — special characters in message body
# ---------------------------------------------------------------------------


def test_newline_escaping_byte_parity(tmp_path) -> None:
    """Newlines in message body must be escaped to literal \\n."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "line1\nline2\nline3",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tline1\\nline2\\nline3\n"
    assert _read_bus(bus) == expected


def test_carriage_return_escaping_byte_parity(tmp_path) -> None:
    """Carriage returns (\\r\\n and lone \\r) must be escaped to literal \\n."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "line1\r\nline2\rline3",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tline1\\nline2\\nline3\n"
    assert _read_bus(bus) == expected


def test_tab_escaping_byte_parity(tmp_path) -> None:
    """Tabs in message body must be replaced with spaces (not escaped)."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "col1\tcol2\tcol3",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tcol1 col2 col3\n"
    assert _read_bus(bus) == expected


def test_mixed_special_chars_byte_parity(tmp_path) -> None:
    """Mixed newlines + tabs + unicode must produce exact escaped output."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "row1\tdata\nrow2\tdata — em dash",
        timestamp=FIXED_TS,
        validate=False,
    )
    expected = (
        "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\trow1 data\\nrow2 data — em dash\n"
    )
    assert _read_bus(bus) == expected


# ---------------------------------------------------------------------------
# Correlation ID parity — injection format
# ---------------------------------------------------------------------------


def test_correlation_id_injection_byte_parity(tmp_path) -> None:
    """Correlation ID must be prepended as 'correlation_id=<id>, <message>'."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "hello world",
        timestamp=FIXED_TS,
        correlation_id="corr-abc123",
        validate=False,
    )
    expected = (
        "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\t"
        "correlation_id=corr-abc123, hello world\n"
    )
    assert _read_bus(bus) == expected


def test_correlation_id_with_special_chars_byte_parity(tmp_path) -> None:
    """Correlation ID injection + newline escaping must compose correctly."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "line1\nline2",
        timestamp=FIXED_TS,
        correlation_id="corr-xyz",
        validate=False,
    )
    expected = (
        "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\t"
        "correlation_id=corr-xyz, line1\\nline2\n"
    )
    assert _read_bus(bus) == expected


# ---------------------------------------------------------------------------
# Signed message parity — envelope format + signature verification
# ---------------------------------------------------------------------------

_SIGNED_ENVELOPE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\t"
    r"[^\t]+\t"  # from
    r"[^\t]+\t"  # to
    r"[^\t]+\t"  # type
    r'\{"c":"[^"]*","n":"[0-9a-f-]+","s":"[0-9a-f]{64}"\}\n$'
)


def test_signed_message_envelope_format_parity(tmp_path) -> None:
    """Signed message must match the {"c","n","s"} envelope format exactly."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "hello world",
        timestamp=FIXED_TS,
        secret=SECRET,
        validate=False,
    )
    raw = _read_bus(bus)
    assert _SIGNED_ENVELOPE_RE.match(raw), f"envelope format mismatch: {raw!r}"


def test_signed_message_signature_verifies(tmp_path) -> None:
    """The HMAC signature in the envelope must verify against the secret."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "hello world",
        timestamp=FIXED_TS,
        secret=SECRET,
        validate=False,
    )
    raw = _read_bus(bus).rstrip("\n")
    parts = raw.split("\t")
    assert len(parts) == 5
    envelope = json.loads(parts[4])
    assert set(envelope.keys()) == {"c", "n", "s"}

    # Verify the signature
    verify_signature(
        SECRET,
        FIXED_TS,
        "codex",
        "all",
        "STATUS",
        {"message": envelope["c"]},
        envelope["n"],
        envelope["s"],
    )  # No exception = valid signature


def test_signed_message_with_newlines_envelope_parity(tmp_path) -> None:
    """Signed message with newlines: inner content JSON-encoded, envelope stays single-line."""
    bus = tmp_path / "messages.tsv"
    post_message(
        str(bus),
        "codex",
        "all",
        "STATUS",
        "line1\nline2",
        timestamp=FIXED_TS,
        secret=SECRET,
        validate=False,
    )
    raw = _read_bus(bus)
    # The raw TSV line must be single-line (no actual newlines in the envelope)
    assert raw.count("\n") == 1, (
        f"expected exactly 1 newline (line terminator), got {raw.count(chr(10))}"
    )
    assert _SIGNED_ENVELOPE_RE.match(raw), f"envelope format mismatch: {raw!r}"
    # The "c" field contains the original newlines, JSON-encoded as \n in the
    # envelope string. json.loads decodes them back to actual newlines.
    parts = raw.rstrip("\n").split("\t")
    envelope = json.loads(parts[4])
    assert envelope["c"] == "line1\nline2", f"content mismatch: {envelope['c']!r}"
    # The raw envelope JSON must contain the JSON escape \n (not actual newline)
    assert "\\n" in parts[4], f"JSON escape \\n not found in envelope: {parts[4]!r}"


# ---------------------------------------------------------------------------
# Multi-message sequence parity
# ---------------------------------------------------------------------------


def test_multi_message_sequence_byte_parity(tmp_path) -> None:
    """Multiple messages must produce exact concatenated TSV with trailing newlines."""
    bus = tmp_path / "messages.tsv"
    messages = [
        ("2026-08-15T12:00:00Z", "codex", "all", "STATUS", "first"),
        ("2026-08-15T12:00:01Z", "devin", "codex", "ACK", "second"),
        ("2026-08-15T12:00:02Z", "claude-code", "all", "SITREP", "third\nline2"),
    ]
    for ts, frm, to, mtype, msg in messages:
        post_message(str(bus), frm, to, mtype, msg, timestamp=ts, validate=False)

    expected = (
        "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tfirst\n"
        "2026-08-15T12:00:01Z\tdevin\tcodex\tACK\tsecond\n"
        "2026-08-15T12:00:02Z\tclaude-code\tall\tSITREP\tthird\\nline2\n"
    )
    assert _read_bus(bus) == expected


# ---------------------------------------------------------------------------
# escape_message unit parity — direct format assertions
# ---------------------------------------------------------------------------


def test_escape_message_format_parity() -> None:
    """escape_message must produce the documented format for all edge cases."""
    assert escape_message("hello") == "hello"
    assert escape_message("line1\nline2") == "line1\\nline2"
    assert escape_message("line1\r\nline2") == "line1\\nline2"
    assert escape_message("line1\rline2") == "line1\\nline2"
    assert escape_message("col1\tcol2") == "col1 col2"
    assert escape_message("") == ""
    assert escape_message("no special chars") == "no special chars"


def test_escape_message_idempotent_for_already_escaped() -> None:
    """Already-escaped content (literal \\n) must not be double-escaped."""
    # The literal string "line1\\nLine2" (backslash-n, not newline) should
    # pass through unchanged — escape_message only converts actual newlines.
    assert escape_message("line1\\nline2") == "line1\\nline2"


# ---------------------------------------------------------------------------
# Column count parity — TSV must always be exactly 5 columns
# ---------------------------------------------------------------------------


def test_tsv_always_five_columns(tmp_path) -> None:
    """Every line in the bus must have exactly 5 tab-separated columns."""
    bus = tmp_path / "messages.tsv"
    test_cases = [
        ("simple", "hello"),
        ("with newlines", "a\nb\nc"),
        ("with tabs", "x\ty\tz"),
        ("with correlation", "msg"),
        ("empty message", ""),
    ]
    for i, (_, msg) in enumerate(test_cases):
        post_message(
            str(bus),
            "codex",
            "all",
            "STATUS",
            msg,
            timestamp=f"2026-08-15T12:00:0{i}Z",
            correlation_id=f"corr-{i}" if i == 3 else None,
            validate=False,
        )

    lines = _read_bus(bus).splitlines()
    assert len(lines) == 5
    for line in lines:
        parts = line.split("\t")
        assert len(parts) == 5, f"expected 5 columns, got {len(parts)}: {line!r}"
