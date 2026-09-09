"""Tests for Base120 Record envelope creation."""

import unittest
import uuid

from hummbl_eval.base120 import Base120Formatter
from hummbl_eval.base120_records import (
    Base120RecordError,
    create_base120_record,
    extract_base120_metadata,
)


class Base120RecordTests(unittest.TestCase):
    def test_create_record_from_formatter(self) -> None:
        fmt = Base120Formatter("test-skill", "audit")
        # Simulate some output
        import io
        from unittest.mock import patch

        output = io.StringIO()
        with patch("sys.stdout", output):
            fmt.header()
            fmt.section("Overview", "P6")
            fmt.metric("Count", 5)
            fmt.finding(
                title="Missing eval",
                severity="CRIT",
                why="No ground truth.",
                reveals="Untestable.",
                action="Create eval/.",
                code="DE1",
            )
            fmt.footer()

        record = create_base120_record(
            output_text=output.getvalue(),
            skill_name="test-skill",
            actor_id="actor:test-skill",
            source_id="node:test",
            source_sequence=1,
        )

        self.assertEqual(record.record_type, "hummbl:Base120Report")
        self.assertEqual(record.schema_id, "hummbl:base120-report")
        self.assertEqual(record.schema_version, "0.1.0")
        self.assertTrue(record.payload_digest.startswith("sha256:"))
        self.assertEqual(uuid.UUID(record.record_id.removeprefix("urn:uuid:")).version, 7)

    def test_record_payload_contains_metadata(self) -> None:
        record = create_base120_record(
            output_text=(
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "Base120 Applied: DE1, P6\n"
            ),
            skill_name="test-skill",
            actor_id="actor:test-skill",
            source_id="node:test",
            source_sequence=2,
        )

        payload = record.payload
        self.assertEqual(payload["skill_name"], "test-skill")
        self.assertIn("applied_codes", payload)
        self.assertIn("DE1", payload["applied_codes"])
        self.assertIn("P6", payload["applied_codes"])
        self.assertIn("output_text", payload)
        self.assertIn("Base120 Cognitive Structuring", payload["output_text"])

    def test_record_is_immutable(self) -> None:
        record = create_base120_record(
            output_text=(
                "test-skill (Base120 Cognitive Structuring) | all | 2026-08-11\n"
                "Base120 Applied: P6\n"
            ),
            skill_name="test-skill",
            actor_id="actor:test-skill",
            source_id="node:test",
            source_sequence=3,
        )

        # Record is frozen — payload_bytes is immutable
        original_digest = record.payload_digest
        payload = record.payload
        payload["skill_name"] = "tampered"
        # Record's digest should be unchanged
        self.assertEqual(record.payload_digest, original_digest)

    def test_extract_metadata_from_output(self) -> None:
        output = (
            "test-skill (Base120 Cognitive Structuring) | audit | 2026-08-11\n"
            "======================================================================\n\n"
            "## Overview (P6: Point-of-View Anchoring)\n"
            "  Count: 5\n\n"
            "## Findings (DE1: Root Cause Analysis)\n"
            "    [CRIT] Issue\n"
            "      [DE1] Why: reason\n"
            "      Reveals: insight\n"
            "      Action: fix\n\n"
            "Base120 Applied: DE1, P6\n"
            "======================================================================"
        )
        metadata = extract_base120_metadata(output)
        self.assertEqual(metadata["skill_name"], "test-skill")
        self.assertEqual(metadata["subtitle"], "audit")
        self.assertEqual(set(metadata["applied_codes"]), {"DE1", "P6"})

    def test_extract_metadata_from_minimal_output(self) -> None:
        output = "skill (Base120 Cognitive Structuring) | all | 2026-08-11\nBase120 Applied: P6\n"
        metadata = extract_base120_metadata(output)
        self.assertEqual(metadata["skill_name"], "skill")
        self.assertEqual(metadata["applied_codes"], ["P6"])

    def test_rejects_empty_output(self) -> None:
        with self.assertRaises(Base120RecordError):
            create_base120_record(
                output_text="",
                skill_name="test-skill",
                actor_id="actor:test",
                source_id="node:test",
                source_sequence=1,
            )

    def test_rejects_output_without_base120_header(self) -> None:
        with self.assertRaises(Base120RecordError):
            create_base120_record(
                output_text="Just some plain text without Base120.",
                skill_name="test-skill",
                actor_id="actor:test",
                source_id="node:test",
                source_sequence=1,
            )


if __name__ == "__main__":
    unittest.main()
