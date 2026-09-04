"""Tests for the claims and evidence ledger tool.

Covers:
- Claim and evidence creation
- Validation (schema, required fields, enum values)
- Querying by trust tier, review gate, gate status, tags
- Tuple cross-referencing (evidence_tuple_ids, attest_tuple_ids)
- Conversion to EVIDENCE and ATTEST tuple dicts
- Append-only ledger integrity
- CLI smoke tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the tools directory is importable
TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from claims_ledger import (  # noqa: E402
    add_claim,
    add_evidence,
    link_attest_tuple,
    link_evidence_tuple,
    query_claims,
    get_claim,
    validate,
    stats,
    to_evidence_tuple,
    to_attest_tuple,
    _read_ledger,
    VALID_TRUST_TIERS,
    VALID_REVIEW_GATES,
    VALID_CLAIM_TYPES,
    VALID_EVIDENCE_TYPES,
    VALID_GRADES,
    VALID_SUPPORTS,
)


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    """Return a fresh ledger path in a temp directory."""
    return tmp_path / "test_ledger.jsonl"


# ---------------------------------------------------------------------------
# Claim creation
# ---------------------------------------------------------------------------


class TestAddClaim:
    def test_add_claim_basic(self, ledger_path: Path) -> None:
        entry = add_claim(
            claim="Tuple hashing is deterministic",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        assert entry["id"] == "CLM-001"
        assert entry["trust_tier"] == "experimental"
        assert entry["claim_type"] == "hypothesis"
        assert entry["evidence_ids"] == []
        assert entry["evidence_tuple_ids"] == []
        assert entry["attest_tuple_ids"] == []
        assert entry["tags"] == []
        assert entry["review_gate"] == "none"
        assert entry["gate_status"] == "n/a"
        assert entry["confidence"] == "low"
        assert ledger_path.exists()

    def test_add_claim_with_optional_fields(self, ledger_path: Path) -> None:
        entry = add_claim(
            claim="Test claim with all fields",
            trust_tier="validated",
            claim_type="conclusion",
            source="research_notes/2026-09-03-test.md",
            confidence="high",
            falsifier="If hashing is non-deterministic",
            review_gate="review",
            gate_status="approved",
            evidence_tuple_ids=["ev-tuple-001"],
            attest_tuple_ids=["attest-tuple-001"],
            tags=["hashing", "integrity"],
            notes="Important finding",
            path=ledger_path,
        )
        assert entry["falsifier"] == "If hashing is non-deterministic"
        assert entry["evidence_tuple_ids"] == ["ev-tuple-001"]
        assert entry["attest_tuple_ids"] == ["attest-tuple-001"]
        assert entry["tags"] == ["hashing", "integrity"]
        assert entry["notes"] == "Important finding"

    def test_add_claim_increments_id(self, ledger_path: Path) -> None:
        add_claim(
            claim="First claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        entry2 = add_claim(
            claim="Second claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        assert entry2["id"] == "CLM-002"

    def test_add_claim_invalid_trust_tier(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="invalid trust_tier"):
            add_claim(
                claim="Bad tier",
                trust_tier="playground",  # PSI stage name, not valid here
                claim_type="hypothesis",
                source="test",
                path=ledger_path,
            )

    def test_add_claim_invalid_claim_type(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="invalid claim_type"):
            add_claim(
                claim="Bad type",
                trust_tier="untrusted",
                claim_type="guess",
                source="test",
                path=ledger_path,
            )

    def test_add_claim_invalid_confidence(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="invalid confidence"):
            add_claim(
                claim="Bad confidence",
                trust_tier="untrusted",
                claim_type="hypothesis",
                source="test",
                confidence="very-high",
                path=ledger_path,
            )

    def test_all_trust_tiers_accepted(self, ledger_path: Path) -> None:
        for tier in VALID_TRUST_TIERS:
            entry = add_claim(
                claim=f"Claim at {tier}",
                trust_tier=tier,
                claim_type="observation",
                source="test",
                path=ledger_path,
            )
            assert entry["trust_tier"] == tier

    def test_all_review_gates_accepted(self, ledger_path: Path) -> None:
        for gate in VALID_REVIEW_GATES:
            entry = add_claim(
                claim=f"Claim at gate {gate}",
                trust_tier="untrusted",
                claim_type="observation",
                source="test",
                review_gate=gate,
                path=ledger_path,
            )
            assert entry["review_gate"] == gate


# ---------------------------------------------------------------------------
# Evidence creation
# ---------------------------------------------------------------------------


class TestAddEvidence:
    def test_add_evidence_basic(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        ev = add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test_run.py",
            path=ledger_path,
        )
        assert ev["id"] == "EV-001"
        assert ev["claim_id"] == "CLM-001"
        assert ev["evidence_type"] == "test"
        assert ev["supports"] == "true"
        assert ev["grade"] == "C"
        assert ev["attest_tuple_id"] is None

    def test_add_evidence_with_attest_link(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        ev = add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test_run.py",
            attest_tuple_id="ATTEST-abc123",
            path=ledger_path,
        )
        assert ev["attest_tuple_id"] == "ATTEST-abc123"

    def test_add_evidence_backlinks_to_claim(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test_run.py",
            path=ledger_path,
        )
        entries = _read_ledger(ledger_path)
        claim_entry = next(e for e in entries if e["id"] == "CLM-001")
        assert "EV-001" in claim_entry["evidence_ids"]

    def test_add_evidence_unknown_claim(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="claim CLM-999 not found"):
            add_evidence(
                claim_id="CLM-999",
                evidence_type="test",
                source="test",
                path=ledger_path,
            )

    def test_add_evidence_invalid_type(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        with pytest.raises(ValueError, match="invalid evidence_type"):
            add_evidence(
                claim_id=claim["id"],
                evidence_type="rumor",
                source="test",
                path=ledger_path,
            )

    def test_all_evidence_types_accepted(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        for i, etype in enumerate(VALID_EVIDENCE_TYPES):
            ev = add_evidence(
                claim_id=claim["id"],
                evidence_type=etype,
                source=f"source-{i}",
                path=ledger_path,
            )
            assert ev["evidence_type"] == etype

    def test_all_grades_and_supports(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        for grade in VALID_GRADES:
            for supports in VALID_SUPPORTS:
                ev = add_evidence(
                    claim_id=claim["id"],
                    evidence_type="observation",
                    source="test",
                    supports=supports,
                    grade=grade,
                    path=ledger_path,
                )
                assert ev["grade"] == grade
                assert ev["supports"] == supports


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidate:
    def test_validate_empty_ledger(self, ledger_path: Path) -> None:
        assert validate(ledger_path) == []

    def test_validate_valid_ledger(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Valid claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test.py",
            path=ledger_path,
        )
        assert validate(ledger_path) == []

    def test_validate_duplicate_id(self, ledger_path: Path) -> None:
        add_claim(
            claim="First",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        # Manually append a duplicate ID
        with ledger_path.open("a") as f:
            f.write(
                json.dumps(
                    {
                        "id": "CLM-001",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "trust_tier": "untrusted",
                        "claim": "Duplicate",
                        "claim_type": "observation",
                        "source": "test",
                        "evidence_ids": [],
                        "review_gate": "none",
                        "gate_status": "n/a",
                        "confidence": "low",
                        "tags": [],
                    }
                )
                + "\n"
            )
        errors = validate(ledger_path)
        assert any("duplicate id" in e for e in errors)

    def test_validate_evidence_orphan(self, ledger_path: Path) -> None:
        # Write an evidence entry that references a non-existent claim
        with ledger_path.open("w") as f:
            f.write(
                json.dumps(
                    {
                        "id": "EV-001",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "claim_id": "CLM-999",
                        "evidence_type": "test",
                        "source": "test",
                        "supports": "true",
                        "grade": "C",
                    }
                )
                + "\n"
            )
        errors = validate(ledger_path)
        assert any("references unknown claim" in e for e in errors)


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------


class TestQuery:
    def test_query_by_trust_tier(self, ledger_path: Path) -> None:
        for tier in ["untrusted", "experimental", "validated"]:
            add_claim(
                claim=f"Claim at {tier}",
                trust_tier=tier,
                claim_type="observation",
                source="test",
                path=ledger_path,
            )
        results = query_claims(trust_tier="experimental", path=ledger_path)
        assert len(results) == 1
        assert results[0]["trust_tier"] == "experimental"

    def test_query_by_gate_status(self, ledger_path: Path) -> None:
        add_claim(
            claim="Approved claim",
            trust_tier="validated",
            claim_type="conclusion",
            source="test",
            gate_status="approved",
            path=ledger_path,
        )
        add_claim(
            claim="Candidate claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            gate_status="candidate",
            path=ledger_path,
        )
        results = query_claims(gate_status="approved", path=ledger_path)
        assert len(results) == 1
        assert results[0]["gate_status"] == "approved"

    def test_query_by_tags(self, ledger_path: Path) -> None:
        add_claim(
            claim="Tagged claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            tags=["hashing", "integrity"],
            path=ledger_path,
        )
        add_claim(
            claim="Untagged claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        results = query_claims(tags=["hashing"], path=ledger_path)
        assert len(results) == 1
        assert "hashing" in results[0]["tags"]

    def test_query_no_matches(self, ledger_path: Path) -> None:
        add_claim(
            claim="Test",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        results = query_claims(trust_tier="canonical", path=ledger_path)
        assert results == []


# ---------------------------------------------------------------------------
# Get claim with evidence
# ---------------------------------------------------------------------------


class TestGetClaim:
    def test_get_claim_with_evidence(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test.py",
            grade="A",
            path=ledger_path,
        )
        add_evidence(
            claim_id=claim["id"],
            evidence_type="observation",
            source="manual check",
            supports="partial",
            grade="B",
            path=ledger_path,
        )
        result = get_claim("CLM-001", path=ledger_path)
        assert result is not None
        assert result["id"] == "CLM-001"
        assert len(result["_evidence"]) == 2
        assert result["_evidence"][0]["grade"] == "A"
        assert result["_evidence"][1]["supports"] == "partial"

    def test_get_claim_not_found(self, ledger_path: Path) -> None:
        assert get_claim("CLM-999", path=ledger_path) is None


# ---------------------------------------------------------------------------
# Tuple linking
# ---------------------------------------------------------------------------


class TestTupleLinking:
    def test_link_evidence_tuple(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        updated = link_evidence_tuple(
            claim["id"], "ev-tuple-abc", path=ledger_path
        )
        assert updated is not None
        assert "ev-tuple-abc" in updated["evidence_tuple_ids"]

    def test_link_attest_tuple(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        updated = link_attest_tuple(
            claim["id"], "attest-tuple-xyz", path=ledger_path
        )
        assert updated is not None
        assert "attest-tuple-xyz" in updated["attest_tuple_ids"]

    def test_link_evidence_tuple_idempotent(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        link_evidence_tuple(claim["id"], "ev-1", path=ledger_path)
        link_evidence_tuple(claim["id"], "ev-1", path=ledger_path)
        result = get_claim(claim["id"], path=ledger_path)
        assert result is not None
        assert result["evidence_tuple_ids"].count("ev-1") == 1

    def test_link_unknown_claim(self, ledger_path: Path) -> None:
        assert link_evidence_tuple("CLM-999", "ev-1", path=ledger_path) is None
        assert link_attest_tuple("CLM-999", "at-1", path=ledger_path) is None


# ---------------------------------------------------------------------------
# Tuple conversion
# ---------------------------------------------------------------------------


class TestTupleConversion:
    def test_to_evidence_tuple(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Tuple hashing is deterministic",
            trust_tier="validated",
            claim_type="conclusion",
            source="research_notes/test.md",
            path=ledger_path,
        )
        tup = to_evidence_tuple(claim["id"], path=ledger_path)
        assert tup["tuple_type"] == "EVIDENCE"
        assert tup["id"] == claim["id"]
        assert tup["tuple_data"]["event"] == "Tuple hashing is deterministic"
        assert tup["tuple_data"]["evidence_id"] == claim["id"]
        assert tup["tier"] == 2  # validated -> 2
        assert tup["tool"] == "claims_ledger"

    def test_to_evidence_tuple_untrusted_tier_zero(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Untrusted claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        tup = to_evidence_tuple(claim["id"], path=ledger_path)
        assert tup["tier"] == 0

    def test_to_evidence_tuple_unknown_claim(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="not found"):
            to_evidence_tuple("CLM-999", path=ledger_path)

    def test_to_attest_tuple(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="experimental",
            claim_type="hypothesis",
            source="test",
            path=ledger_path,
        )
        add_evidence(
            claim_id=claim["id"],
            evidence_type="test",
            source="test.py",
            grade="A",
            path=ledger_path,
        )
        tup = to_attest_tuple(
            claim["id"],
            verifier_id="codex",
            passed=True,
            findings=["All tests pass"],
            path=ledger_path,
        )
        assert tup["tuple_type"] == "ATTEST"
        assert tup["tuple_data"]["verifier_id"] == "codex"
        assert tup["tuple_data"]["passed"] is True
        assert tup["tuple_data"]["evidence_hash"]  # non-empty SHA-256
        assert len(tup["tuple_data"]["evidence_hash"]) == 64  # SHA-256 hex
        assert "All tests pass" in tup["tuple_data"]["findings"]

    def test_to_attest_tuple_no_evidence(self, ledger_path: Path) -> None:
        claim = add_claim(
            claim="Test claim",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        tup = to_attest_tuple(
            claim["id"], verifier_id="devin", passed=False, path=ledger_path
        )
        # Evidence hash of empty list is still a valid SHA-256
        assert len(tup["tuple_data"]["evidence_hash"]) == 64
        assert tup["tuple_data"]["passed"] is False

    def test_to_attest_tuple_unknown_claim(self, ledger_path: Path) -> None:
        with pytest.raises(ValueError, match="not found"):
            to_attest_tuple("CLM-999", verifier_id="test", passed=True, path=ledger_path)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_stats_empty(self, ledger_path: Path) -> None:
        s = stats(ledger_path)
        assert s["total_claims"] == 0
        assert s["total_evidence"] == 0

    def test_stats_with_data(self, ledger_path: Path) -> None:
        c1 = add_claim(
            claim="Claim 1",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        c2 = add_claim(
            claim="Claim 2",
            trust_tier="validated",
            claim_type="conclusion",
            source="test",
            gate_status="approved",
            evidence_tuple_ids=["ev-tup-1"],
            path=ledger_path,
        )
        add_evidence(
            claim_id=c1["id"],
            evidence_type="test",
            source="test.py",
            path=ledger_path,
        )
        s = stats(ledger_path)
        assert s["total_claims"] == 2
        assert s["total_evidence"] == 1
        assert s["by_trust_tier"] == {"untrusted": 1, "validated": 1}
        assert s["by_gate_status"]["approved"] == 1
        assert s["by_evidence_supports"]["true"] == 1
        assert s["claims_with_evidence_tuples"] == 1
        assert s["claims_with_attest_tuples"] == 0


# ---------------------------------------------------------------------------
# Append-only integrity
# ---------------------------------------------------------------------------


class TestAppendOnly:
    def test_ledger_is_append_only(self, ledger_path: Path) -> None:
        """Entries are never deleted; new entries are appended."""
        add_claim(
            claim="First",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        first_lines = ledger_path.read_text().strip().split("\n")
        assert len(first_lines) == 1

        add_claim(
            claim="Second",
            trust_tier="untrusted",
            claim_type="observation",
            source="test",
            path=ledger_path,
        )
        second_lines = ledger_path.read_text().strip().split("\n")
        assert len(second_lines) == 2
        # First line unchanged
        assert json.loads(first_lines[0])["claim"] == "First"
        assert json.loads(second_lines[0])["claim"] == "First"
        assert json.loads(second_lines[1])["claim"] == "Second"


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


class TestCLI:
    def test_cli_add_claim_and_validate(self, tmp_path: Path) -> None:
        ledger = tmp_path / "cli_ledger.jsonl"
        tool_path = TOOLS_DIR / "claims_ledger.py"

        result = subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "add-claim",
                "--claim",
                "CLI test claim",
                "--trust-tier",
                "experimental",
                "--type",
                "hypothesis",
                "--source",
                "cli-test",
                "--confidence",
                "medium",
                "--tags",
                "cli",
                "test",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "Added claim CLM-001" in result.stdout

        result = subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "validate",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "validation passed" in result.stdout

    def test_cli_stats(self, tmp_path: Path) -> None:
        ledger = tmp_path / "cli_ledger.jsonl"
        tool_path = TOOLS_DIR / "claims_ledger.py"

        subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "add-claim",
                "--claim",
                "Stats test",
                "--trust-tier",
                "validated",
                "--type",
                "conclusion",
                "--source",
                "test",
            ],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "stats",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        s = json.loads(result.stdout)
        assert s["total_claims"] == 1
        assert s["by_trust_tier"]["validated"] == 1

    def test_cli_to_evidence_tuple(self, tmp_path: Path) -> None:
        ledger = tmp_path / "cli_ledger.jsonl"
        tool_path = TOOLS_DIR / "claims_ledger.py"

        subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "add-claim",
                "--claim",
                "Conversion test",
                "--trust-tier",
                "experimental",
                "--type",
                "hypothesis",
                "--source",
                "test",
            ],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                str(tool_path),
                "--ledger-path",
                str(ledger),
                "to-evidence-tuple",
                "CLM-001",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        tup = json.loads(result.stdout)
        assert tup["tuple_type"] == "EVIDENCE"
        assert tup["tuple_data"]["event"] == "Conversion test"
