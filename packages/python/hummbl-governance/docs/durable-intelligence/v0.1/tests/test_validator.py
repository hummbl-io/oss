#!/usr/bin/env python3
"""Tests for the Durable Intelligence Doctrine receipt validator."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate import validate_receipt

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestValidReceipts(unittest.TestCase):
    def test_valid_full_receipt(self):
        errors = validate_receipt(load_fixture("valid-full-receipt.json"))
        self.assertEqual(errors, [], f"Expected no errors: {errors}")

    def test_valid_readonly_receipt(self):
        errors = validate_receipt(load_fixture("valid-readonly-receipt.json"))
        self.assertEqual(errors, [], f"Expected no errors: {errors}")


class TestInvalidReceipts(unittest.TestCase):
    def test_invalid_unverified_claim(self):
        """Claim says 'verified' but no connector/test_runner/shell in tools."""
        errors = validate_receipt(load_fixture("invalid-unverified-claim.json"))
        self.assertTrue(
            any("verified" in e and "tools" in e for e in errors),
            f"Expected capability bounding error: {errors}"
        )

    def test_invalid_mutation_lie(self):
        """Action claims PR creation but mutations_made is empty."""
        errors = validate_receipt(load_fixture("invalid-mutation-lie.json"))
        self.assertTrue(
            any("mutations_made" in e for e in errors),
            f"Expected mutation truthfulness error: {errors}"
        )

    def test_invalid_capability_overclaim(self):
        """Only read_only tool but claims verified via connector."""
        errors = validate_receipt(load_fixture("invalid-capability-overclaim.json"))
        self.assertTrue(
            any("verified" in e and "tools" in e for e in errors),
            f"Expected capability bounding error: {errors}"
        )


class TestSemanticRules(unittest.TestCase):
    def _base_receipt(self) -> dict:
        return {
            "schema_version": "agent_session_receipt.v0.1",
            "session_id": "test-001",
            "source_agent": "devin",
            "environment": {"host": "test", "platform": "test", "python_version": "3.13"},
            "tools_available": ["shell", "filesystem"],
            "repository_or_system_scope": [],
            "starting_state": {"branch": "main", "head_commit": "abc"},
            "actions_attempted": [],
            "mutations_made": [],
            "claims": [],
            "decisions": [],
            "negative_knowledge": [],
            "open_questions": [],
            "next_actions": [],
            "authority_boundaries": {"allowed": [], "disallowed": [], "escalation": None},
            "receipt_destination": "github_issue",
            "completion_status": "COMPLETED"
        }

    def test_verified_claim_without_tools_fails(self):
        r = self._base_receipt()
        r["tools_available"] = ["read_only"]
        r["claims"] = [{"claim": "test", "posture": "verified", "evidence_ref": None}]
        errors = validate_receipt(r)
        self.assertTrue(any("verified" in e for e in errors))

    def test_verified_claim_with_connector_ok(self):
        r = self._base_receipt()
        r["tools_available"] = ["connector"]
        r["claims"] = [{"claim": "test", "posture": "verified", "evidence_ref": "gh"}]
        errors = validate_receipt(r)
        self.assertEqual(errors, [], f"Expected no errors: {errors}")

    def test_mutation_truthfulness_action_without_mutation(self):
        r = self._base_receipt()
        r["actions_attempted"] = [{
            "action": "Created PR #999",
            "result": "succeeded",
            "evidence_ref": None
        }]
        r["mutations_made"] = []
        errors = validate_receipt(r)
        self.assertTrue(any("mutations_made" in e for e in errors))

    def test_mutation_truthfulness_with_mutation_ok(self):
        r = self._base_receipt()
        r["actions_attempted"] = [{
            "action": "Created PR #999",
            "result": "succeeded",
            "evidence_ref": None
        }]
        r["mutations_made"] = [{
            "artifact_type": "pr",
            "identifier": "999",
            "created": True
        }]
        errors = validate_receipt(r)
        self.assertEqual(errors, [], f"Expected no errors: {errors}")

    def test_invalid_posture_fails(self):
        r = self._base_receipt()
        r["claims"] = [{"claim": "test", "posture": "maybe_true", "evidence_ref": None}]
        errors = validate_receipt(r)
        self.assertTrue(any("posture" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
