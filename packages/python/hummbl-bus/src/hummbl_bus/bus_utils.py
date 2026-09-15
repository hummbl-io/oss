"""Shared bus TSV parsing utilities.

Canonical single-line parser for the coordination bus TSV format::

    timestamp_utc\\tfrom\\tto\\ttype\\tmessage

All modules that need to parse bus lines should import ``parse_bus_line``
from here rather than duplicating the logic.

Promoted from hummbl-governance/bus/bus_utils.py 2026-08-15.
"""

from __future__ import annotations

import re

from hummbl_bus.message_types import READABLE_MESSAGE_TYPES

# Allowed message types for the coordination bus. A line whose type field
# (column 4) is not in this set is treated as corrupted and rejected (returns
# None) rather than silently accepted with a garbage type. This catches the
# compounding-corruption failure mode where a partial write merges two lines
# and the reader sees a concatenated type field like "STA2026-01-01T...".
# The set is intentionally a module-level frozenset so it can be extended by
# callers that register custom types without modifying this file.
_ALLOWED_MESSAGE_TYPES: set[str] = set(READABLE_MESSAGE_TYPES)


def parse_bus_line(line: str) -> dict[str, str] | None:
    """Parse a single TSV bus line into a dict.

    Returns a dict with keys ``timestamp``, ``from``, ``to``, ``type``,
    ``message``, or ``None`` for header lines, blank lines, comments,
    malformed rows, and rows with an unrecognized type field.

    The message field preserves any literal tab characters (fields beyond
    the first four are joined back with ``\\t``).

    Type validation: the type field (column 4) is checked against the
    allowed message types. A corrupted line with a garbage type (e.g. from
    a partial-write concatenation) returns ``None`` instead of being
    silently accepted. This is defense-in-depth against the compounding
    corruption documented in issue #1727.
    """
    line = line.rstrip("\n\r")
    if not line or line.startswith(("#", "timestamp")):
        return None

    parts = line.split("\t")
    if len(parts) < 5:
        return None

    msg_type = parts[3].strip().upper()
    if msg_type not in _ALLOWED_MESSAGE_TYPES:
        return None

    return {
        "timestamp": parts[0],
        "from": parts[1],
        "to": parts[2],
        "type": parts[3],
        "message": "\t".join(parts[4:]),
    }


def extract_tag(body: str, tag: str) -> str | None:
    """Extract ``tag=value`` from a bus message body.

    Single canonical implementation shared by ``lane_classifier`` and
    ``inference_tier`` to avoid regex duplication.

    Args:
        body: The raw message body text.
        tag: The tag name to search for (e.g. ``"priority"``, ``"lane"``).

    Returns:
        The tag value, or ``None`` if the tag is not present.
    """
    pattern = rf"\b{re.escape(tag)}=([^;,\s]+)"
    match = re.search(pattern, body)
    if match:
        return match.group(1)
    return None
