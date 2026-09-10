"""Record envelopes for Base120 cognitive structuring reports.

Wraps Base120 report output in immutable ``Record`` envelopes with SHA-256
content digests, making reports auditable, diffable, and traceable across
the fleet.
"""

from __future__ import annotations

import re
from typing import Any

from .records import Record


class Base120RecordError(ValueError):
    """A Base120 record envelope cannot be created from the given input."""


_HEADER_RE = re.compile(r"^(.+?)\s+\(Base120 Cognitive Structuring\)\s*\|\s*(.+?)\s*\|")
_FOOTER_RE = re.compile(r"Base120 Applied:\s*(.+)")


def extract_base120_metadata(output_text: str) -> dict[str, Any]:
    """Extract skill name, subtitle, and applied codes from Base120 output.

    Returns a dict with keys: ``skill_name``, ``subtitle``, ``applied_codes``.
    """
    skill_name = "unknown"
    subtitle = "all"
    applied_codes: list[str] = []

    header_match = _HEADER_RE.search(output_text)
    if header_match:
        skill_name = header_match.group(1).strip()
        subtitle = header_match.group(2).strip()

    footer_match = _FOOTER_RE.search(output_text)
    if footer_match:
        footer_text = footer_match.group(1).strip()
        applied_codes = [c.strip() for c in footer_text.split(",") if c.strip()]

    return {
        "skill_name": skill_name,
        "subtitle": subtitle,
        "applied_codes": applied_codes,
    }


def create_base120_record(
    output_text: str,
    skill_name: str,
    actor_id: str,
    source_id: str,
    source_sequence: int,
    *,
    maturity: str = "candidate",
    confidentiality: str = "internal",
) -> Record:
    """Create an immutable Record envelope from a Base120 report.

    The record payload contains:
    - ``skill_name``: name of the skill that produced the report
    - ``subtitle``: scope/context of the report
    - ``applied_codes``: list of Base120 operator codes used
    - ``output_text``: the full Base120 structured output text

    Args:
        output_text: The full Base120 report text (must contain the header).
        skill_name: Name of the skill that produced the report.
        actor_id: Identity of the skill/agent that produced the report.
        source_id: Source machine or node identifier.
        source_sequence: Monotonic sequence number for this source.
        maturity: Record maturity level (default: ``candidate``).
        confidentiality: Confidentiality level (default: ``internal``).

    Returns:
        An immutable ``Record`` with a SHA-256 content digest.

    Raises:
        Base120RecordError: If the output text is empty or lacks the Base120 header.
    """
    if not output_text:
        raise Base120RecordError("output_text must not be empty")
    if "Base120 Cognitive Structuring" not in output_text:
        raise Base120RecordError("output_text must contain a Base120 Cognitive Structuring header")

    metadata = extract_base120_metadata(output_text)

    payload: dict[str, Any] = {
        "skill_name": skill_name,
        "subtitle": metadata["subtitle"],
        "applied_codes": metadata["applied_codes"],
        "output_text": output_text,
    }

    return Record.create(
        record_type="hummbl:Base120Report",
        schema_id="hummbl:base120-report",
        schema_version="0.1.0",
        payload=payload,
        actor_id=actor_id,
        source_id=source_id,
        source_sequence=source_sequence,
        maturity=maturity,
        confidentiality=confidentiality,
    )
