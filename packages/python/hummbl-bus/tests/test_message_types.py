from __future__ import annotations

from hummbl_bus.bus_utils import parse_bus_line, register_message_type
from hummbl_bus.message_types import (
    CANONICAL_MESSAGE_TYPES,
    LEGACY_MESSAGE_TYPES,
    READABLE_MESSAGE_TYPES,
)


def test_canonical_types_include_core_protocol() -> None:
    """The core protocol types from the fleet must be present."""
    expected = {"PROPOSAL", "ACK", "STATUS", "DECISION", "SITREP", "MILESTONE"}
    assert expected <= CANONICAL_MESSAGE_TYPES


def test_canonical_types_include_belief_audit() -> None:
    """BELIEF_AUDIT (added 2026-09-02 from incident governance research) is canonical."""
    assert "BELIEF_AUDIT" in CANONICAL_MESSAGE_TYPES
    assert "BELIEF_AUDIT" not in LEGACY_MESSAGE_TYPES


def test_readable_is_canonical_plus_legacy() -> None:
    assert READABLE_MESSAGE_TYPES == CANONICAL_MESSAGE_TYPES | LEGACY_MESSAGE_TYPES


def test_canonical_and_legacy_are_disjoint() -> None:
    """Legacy types must not appear in canonical -- new writes reject them."""
    assert not (CANONICAL_MESSAGE_TYPES & LEGACY_MESSAGE_TYPES)


def test_parse_bus_line_valid() -> None:
    line = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\thello world"
    result = parse_bus_line(line)
    assert result is not None
    assert result["timestamp"] == "2026-08-15T12:00:00Z"
    assert result["from"] == "codex"
    assert result["to"] == "all"
    assert result["type"] == "STATUS"
    assert result["message"] == "hello world"


def test_parse_bus_line_preserves_embedded_tabs() -> None:
    """Fields beyond the first four are joined back with tab."""
    line = "2026-08-15T12:00:00Z\tcodex\tall\tSTATUS\tcol1\tcol2"
    result = parse_bus_line(line)
    assert result is not None
    assert result["message"] == "col1\tcol2"


def test_parse_bus_line_rejects_header() -> None:
    assert parse_bus_line("timestamp_utc\tfrom\tto\ttype\tmessage") is None


def test_parse_bus_line_rejects_blank() -> None:
    assert parse_bus_line("") is None


def test_parse_bus_line_rejects_comment() -> None:
    assert parse_bus_line("# a comment") is None


def test_parse_bus_line_rejects_short_row() -> None:
    assert parse_bus_line("only\ttwo\tfields") is None


def test_parse_bus_line_rejects_garbage_type() -> None:
    """Defense-in-depth against compounding corruption (#1727)."""
    line = "2026-08-15T12:00:00Z\tcodex\tall\tSTA2026-01-01\thello"
    assert parse_bus_line(line) is None


def test_parse_bus_line_accepts_legacy_type() -> None:
    """Readers must accept historical rows with legacy types."""
    line = "2026-01-01T00:00:00Z\tclaude-code\tall\tAAR\thistorical review"
    result = parse_bus_line(line)
    assert result is not None
    assert result["type"] == "AAR"


def test_register_message_type_extends_allowed() -> None:
    """Custom types can be registered at import time."""
    line = "2026-08-15T12:00:00Z\tcodex\tall\tCUSTOM_TYPE\thello"
    assert parse_bus_line(line) is None  # not registered yet
    register_message_type("CUSTOM_TYPE")
    result = parse_bus_line(line)
    assert result is not None
    assert result["type"] == "CUSTOM_TYPE"
