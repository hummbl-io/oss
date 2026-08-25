"""Tests for hummbl_cognition/issueops_receipt.py

Covers receipt construction, validation, append-only JSONL persistence,
content hashing, and CLI entry points.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from hummbl_cognition.issueops_receipt import (
    DEFAULT_RECEIPT_LOG_PATH,
    SCHEMA_PATH,
    VALID_SOURCES,
    VALID_SEVERITIES,
    IssueOpsReceiptError,
    append_receipt,
    create_receipt,
    main,
    read_receipts,
    validate_receipt,
)


# =============================================================================
# Constants / schema presence
# =============================================================================


def test_schema_file_exists():
    """The IssueOps run receipt schema file must exist on disk."""
    assert SCHEMA_PATH.exists(), f"schema not found at {SCHEMA_PATH}"


def test_schema_loads_as_valid_json():
    """The schema must parse as valid JSON."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["title"] == "IssueOps Run Receipt Schema"
    assert "run_id" in schema["required"]


def test_valid_sources():
    """VALID_SOURCES must include the canonical IssueOps origins."""
    assert "chatgpt-connector" in VALID_SOURCES
    assert "arbiter-audit" in VALID_SOURCES
    assert "manual" in VALID_SOURCES


def test_valid_severities():
    """VALID_SEVERITIES must include the four standard levels."""
    assert VALID_SEVERITIES == frozenset({"low", "medium", "high", "critical"})


def test_default_log_path():
    """Default log path points to the cognition state dir."""
    assert "issueops_receipts.jsonl" in DEFAULT_RECEIPT_LOG_PATH
    assert "_state/cognition/" in DEFAULT_RECEIPT_LOG_PATH


# =============================================================================
# create_receipt
# =============================================================================


def test_create_receipt_minimal():
    """A minimal receipt with only source and agent is valid."""
    receipt = create_receipt(source="manual", agent="devin")
    assert receipt["run_id"].startswith("issueops-")
    assert receipt["timestamp"].endswith("Z")
    assert receipt["source"] == "manual"
    assert receipt["agent"] == "devin"
    assert receipt["issues_created"] == []
    assert receipt["issues_closed"] == []
    assert receipt["issues_commented"] == []
    assert receipt["total_issues_processed"] == 0
    assert receipt["evidence_refs"] == []
    assert "content_hash" in receipt


def test_create_receipt_full():
    """A fully-populated receipt validates and computes total correctly."""
    receipt = create_receipt(
        source="arbiter-audit",
        agent="devin",
        issues_created=[
            {
                "repo": "hummbl-io/hummbl-governance",
                "number": 979,
                "title": "ops: create IssueOps run receipt schema",
                "category": "governance",
                "severity": "high",
            }
        ],
        issues_closed=[
            {"repo": "hummbl-io/hummbl-governance", "number": 100, "reason": "resolved"}
        ],
        issues_commented=[
            {"repo": "hummbl-io/hummbl-governance", "number": 979},
        ],
        evidence_refs=["https://example.com/audit-report-001"],
        notes="Initial IssueOps run",
    )
    # 979 appears in created + commented, 100 in closed => 2 unique
    assert receipt["total_issues_processed"] == 2
    assert len(receipt["issues_created"]) == 1
    assert receipt["issues_created"][0]["severity"] == "high"
    assert receipt["notes"] == "Initial IssueOps run"


def test_create_receipt_dedup_total():
    """total_issues_processed deduplicates by (repo, number)."""
    receipt = create_receipt(
        source="chatgpt-connector",
        agent="claude-code",
        issues_created=[{"repo": "o/r", "number": 1, "title": "t", "category": "c", "severity": "low"}],
        issues_commented=[{"repo": "o/r", "number": 1}],
        issues_closed=[{"repo": "o/r", "number": 1, "reason": "duplicate"}],
    )
    assert receipt["total_issues_processed"] == 1


def test_create_receipt_explicit_run_id_and_timestamp():
    """Explicit run_id and timestamp are honored."""
    receipt = create_receipt(
        source="manual",
        agent="devin",
        run_id="issueops-custom-123",
        timestamp="2026-01-01T00:00:00Z",
    )
    assert receipt["run_id"] == "issueops-custom-123"
    assert receipt["timestamp"] == "2026-01-01T00:00:00Z"


def test_create_receipt_invalid_source():
    """Invalid source raises IssueOpsReceiptError."""
    with pytest.raises(IssueOpsReceiptError, match="source must be one of"):
        create_receipt(source="bogus", agent="devin")


def test_create_receipt_empty_agent():
    """Empty agent raises IssueOpsReceiptError."""
    with pytest.raises(IssueOpsReceiptError, match="agent must be a non-empty"):
        create_receipt(source="manual", agent="")


def test_create_receipt_invalid_severity():
    """Invalid severity in issues_created raises IssueOpsReceiptError."""
    with pytest.raises(IssueOpsReceiptError, match="failed validation"):
        create_receipt(
            source="manual",
            agent="devin",
            issues_created=[
                {"repo": "o/r", "number": 1, "title": "t", "category": "c", "severity": "bogus"}
            ],
        )


def test_create_receipt_missing_created_subfield():
    """Missing required subfield in issues_created raises."""
    with pytest.raises(IssueOpsReceiptError, match="failed validation"):
        create_receipt(
            source="manual",
            agent="devin",
            issues_created=[
                {"repo": "o/r", "number": 1, "title": "t", "category": "c"}  # no severity
            ],
        )


# =============================================================================
# content_hash
# =============================================================================


def test_content_hash_is_sha256_hex():
    """content_hash must be a 64-char hex string."""
    receipt = create_receipt(source="manual", agent="devin")
    h = receipt["content_hash"]
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_content_hash_deterministic():
    """Same receipt content produces the same hash."""
    r1 = create_receipt(
        source="manual", agent="devin", run_id="issueops-x", timestamp="2026-01-01T00:00:00Z"
    )
    # Recompute without the hash field
    r2 = dict(r1)
    del r2["content_hash"]
    r2 = create_receipt(
        source="manual", agent="devin", run_id="issueops-x", timestamp="2026-01-01T00:00:00Z"
    )
    assert r1["content_hash"] == r2["content_hash"]


def test_content_hash_changes_on_content_change():
    """Different content produces a different hash."""
    r1 = create_receipt(
        source="manual", agent="devin", run_id="issueops-x", timestamp="2026-01-01T00:00:00Z"
    )
    r2 = create_receipt(
        source="manual", agent="codex", run_id="issueops-x", timestamp="2026-01-01T00:00:00Z"
    )
    assert r1["content_hash"] != r2["content_hash"]


# =============================================================================
# validate_receipt
# =============================================================================


def test_validate_receipt_valid():
    """A well-formed receipt validates cleanly."""
    receipt = create_receipt(source="manual", agent="devin")
    is_valid, errors = validate_receipt(receipt)
    assert is_valid
    assert errors == []


def test_validate_receipt_missing_required():
    """A receipt missing a required field fails validation."""
    receipt = {"run_id": "issueops-x", "timestamp": "2026-01-01T00:00:00Z"}
    is_valid, errors = validate_receipt(receipt)
    assert not is_valid
    assert any("source" in e for e in errors)


def test_validate_receipt_invalid_source():
    """A receipt with an invalid source fails validation."""
    receipt = {
        "run_id": "issueops-x",
        "timestamp": "2026-01-01T00:00:00Z",
        "source": "bogus",
        "issues_created": [],
        "issues_closed": [],
        "issues_commented": [],
        "total_issues_processed": 0,
        "agent": "devin",
        "evidence_refs": [],
    }
    is_valid, errors = validate_receipt(receipt)
    assert not is_valid


# =============================================================================
# append_receipt / read_receipts
# =============================================================================


def test_append_receipt_writes_jsonl(tmp_path):
    """append_receipt writes a single JSONL line to the log."""
    log = tmp_path / "receipts.jsonl"
    receipt = create_receipt(source="manual", agent="devin")
    path = append_receipt(receipt, log_path=log)
    assert path == log.resolve() or path == log
    assert log.exists()
    content = log.read_text(encoding="utf-8").strip()
    assert content  # non-empty
    parsed = json.loads(content)
    assert parsed["run_id"] == receipt["run_id"]


def test_append_receipt_creates_parent_dirs(tmp_path):
    """append_receipt creates missing parent directories."""
    log = tmp_path / "nested" / "dir" / "receipts.jsonl"
    receipt = create_receipt(source="manual", agent="devin")
    append_receipt(receipt, log_path=log)
    assert log.exists()


def test_append_receipt_appends_multiple(tmp_path):
    """Multiple appends produce multiple lines."""
    log = tmp_path / "receipts.jsonl"
    for i in range(3):
        append_receipt(create_receipt(source="manual", agent="devin"), log_path=log)
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


def test_append_receipt_invalid_raises(tmp_path):
    """append_receipt rejects an invalid receipt."""
    log = tmp_path / "receipts.jsonl"
    with pytest.raises(IssueOpsReceiptError, match="cannot append invalid receipt"):
        append_receipt({"run_id": "x"}, log_path=log)


def test_read_receipts_empty(tmp_path):
    """read_receipts returns [] when the log does not exist."""
    log = tmp_path / "nofile.jsonl"
    assert read_receipts(log_path=log) == []


def test_read_receipts_newest_first(tmp_path):
    """read_receipts returns newest receipts first."""
    log = tmp_path / "receipts.jsonl"
    ids = []
    for i in range(3):
        r = create_receipt(
            source="manual", agent="devin", run_id=f"issueops-{i}", timestamp=f"2026-01-0{i+1}T00:00:00Z"
        )
        ids.append(r["run_id"])
        append_receipt(r, log_path=log)
    receipts = read_receipts(log_path=log, limit=10)
    # newest first => last appended is first
    assert receipts[0]["run_id"] == ids[-1]
    assert receipts[-1]["run_id"] == ids[0]


def test_read_receipts_respects_limit(tmp_path):
    """read_receipts honors the limit parameter."""
    log = tmp_path / "receipts.jsonl"
    for i in range(5):
        append_receipt(create_receipt(source="manual", agent="devin"), log_path=log)
    assert len(read_receipts(log_path=log, limit=3)) == 3


def test_read_receipts_skips_unparseable(tmp_path):
    """read_receipts skips lines that are not valid JSON."""
    log = tmp_path / "receipts.jsonl"
    log.write_text("not json\n", encoding="utf-8")
    # Should not raise, just return []
    assert read_receipts(log_path=log) == []


# =============================================================================
# CLI
# =============================================================================


def test_cli_create_dry_run(tmp_path, capsys):
    """CLI create --dry-run prints the receipt without writing."""
    rc = main(
        [
            "create",
            "--source", "manual",
            "--agent", "devin",
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["source"] == "manual"
    assert parsed["agent"] == "devin"


def test_cli_create_writes_to_log(tmp_path, capsys, monkeypatch):
    """CLI create appends to the log file."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    rc = main(
        [
            "create",
            "--source", "arbiter-audit",
            "--agent", "devin",
            "--evidence-refs", "https://example.com/report",
        ]
    )
    assert rc == 0
    assert log.exists()
    line = log.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["source"] == "arbiter-audit"
    assert parsed["evidence_refs"] == ["https://example.com/report"]


def test_cli_create_with_issues_json(tmp_path, capsys, monkeypatch):
    """CLI create accepts JSON arrays for issues_created/closed/commented."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    rc = main(
        [
            "create",
            "--source", "arbiter-audit",
            "--agent", "devin",
            "--issues-created", json.dumps([
                {"repo": "o/r", "number": 1, "title": "t", "category": "c", "severity": "high"}
            ]),
            "--issues-closed", json.dumps([
                {"repo": "o/r", "number": 2, "reason": "resolved"}
            ]),
            "--issues-commented", json.dumps([
                {"repo": "o/r", "number": 1}
            ]),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "2 issues" in out


def test_cli_create_invalid_source(capsys):
    """CLI create with invalid source exits non-zero."""
    with pytest.raises(SystemExit):
        main(["create", "--source", "bogus", "--agent", "devin"])


def test_cli_create_invalid_issues_json(tmp_path, capsys, monkeypatch):
    """CLI create with malformed JSON for issues exits non-zero."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    rc = main(
        [
            "create",
            "--source", "manual",
            "--agent", "devin",
            "--issues-created", "{not json}",
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "invalid JSON" in err


def test_cli_list_empty(tmp_path, capsys, monkeypatch):
    """CLI list on an empty log prints 'No receipts found.'"""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    rc = main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No receipts found" in out


def test_cli_list_with_receipts(tmp_path, capsys, monkeypatch):
    """CLI list shows appended receipts."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    main(["create", "--source", "manual", "--agent", "devin"])
    capsys.readouterr()  # clear
    rc = main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "issueops-" in out
    assert "1 receipts" in out


def test_cli_validate_no_log(tmp_path, capsys, monkeypatch):
    """CLI validate with no log file exits 0."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    rc = main(["validate"])
    assert rc == 0


def test_cli_validate_clean(tmp_path, capsys, monkeypatch):
    """CLI validate on a clean log exits 0."""
    log = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("ISSUEOPS_RECEIPT_LOG", str(log))
    main(["create", "--source", "manual", "--agent", "devin"])
    capsys.readouterr()
    rc = main(["validate"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 valid" in out


def test_cli_no_command_prints_help(capsys):
    """CLI with no subcommand prints help and exits 0."""
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Available commands" in out or "usage" in out.lower()


# =============================================================================
# Extended schema fields (Issue #1023)
# =============================================================================


class TestExtendedSchemaFields:
    """Tests for extended IssueOps receipt fields from #1023."""

    def test_receipt_with_skipped_duplicates(self):
        """Receipt should accept skipped_duplicate_candidates."""
        receipt = create_receipt(
            source="chatgpt-connector",
            agent="devin",
            skipped_duplicate_candidates=[
                {
                    "repo": "hummbl-dev/arbiter",
                    "proposed_title": "fix: missing AGENTS.md",
                    "duplicate_of": 42,
                    "match_reason": "title-similarity",
                }
            ],
            run_disposition="skipped-all",
        )
        assert receipt["skipped_duplicate_candidates"][0]["duplicate_of"] == 42
        assert receipt["run_disposition"] == "skipped-all"
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_receipt_with_read_only_candidates(self):
        """Receipt should accept read_only_candidates outside write boundary."""
        receipt = create_receipt(
            source="arbiter-audit",
            agent="devin",
            read_only_candidates=[
                {
                    "repo": "hummbl-dev/some-fork",
                    "proposed_title": "fix: missing LICENSE",
                    "category": "governance",
                    "severity": "high",
                    "reason": "outside-write-boundary",
                }
            ],
            write_boundary=["hummbl-dev/arbiter", "hummbl-io/hummbl-governance"],
            run_disposition="no-op",
        )
        assert len(receipt["read_only_candidates"]) == 1
        assert receipt["write_boundary"] == ["hummbl-dev/arbiter", "hummbl-io/hummbl-governance"]
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_receipt_with_access_limits(self):
        """Receipt should accept access_limits."""
        receipt = create_receipt(
            source="scheduled",
            agent="devin",
            access_limits=[
                {
                    "repo": "hummbl-dev/private-repo",
                    "limit_type": "permission-denied",
                    "details": "Token lacks issues:write scope",
                }
            ],
            run_disposition="partial",
        )
        assert receipt["access_limits"][0]["limit_type"] == "permission-denied"
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_receipt_with_quality_scores(self):
        """Receipt should accept quality_scores."""
        receipt = create_receipt(
            source="manual",
            agent="devin",
            issues_created=[
                {"repo": "hummbl-dev/arbiter", "number": 1, "title": "test", "category": "gov", "severity": "high"}
            ],
            quality_scores={
                "avg_quality_score": 85.5,
                "min_quality_score": 70.0,
                "max_quality_score": 95.0,
                "rubric_version": "v1.0",
            },
            run_disposition="created",
        )
        assert receipt["quality_scores"]["avg_quality_score"] == 85.5
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_receipt_with_backpressure_notes(self):
        """Receipt should accept backpressure_notes."""
        receipt = create_receipt(
            source="scheduled",
            agent="devin",
            backpressure_notes="Throttled to 5 issues/min after rate limit",
            run_disposition="partial",
        )
        assert "Throttled" in receipt["backpressure_notes"]
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_no_op_run_produces_valid_receipt(self):
        """A run with no issues created should still produce a valid receipt."""
        receipt = create_receipt(
            source="chatgpt-connector",
            agent="devin",
            run_disposition="no-op",
            skipped_duplicate_candidates=[],
            read_only_candidates=[],
        )
        assert receipt["total_issues_processed"] == 0
        assert receipt["run_disposition"] == "no-op"
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"

    def test_mixed_run_with_all_fields(self):
        """A run with created, skipped, and read-only candidates should validate."""
        receipt = create_receipt(
            source="arbiter-audit",
            agent="devin",
            issues_created=[
                {"repo": "hummbl-dev/arbiter", "number": 10, "title": "fix A", "category": "security", "severity": "high"}
            ],
            issues_commented=[
                {"repo": "hummbl-io/hummbl-governance", "number": 5}
            ],
            skipped_duplicate_candidates=[
                {"repo": "hummbl-dev/arbiter", "proposed_title": "fix B", "duplicate_of": 8}
            ],
            read_only_candidates=[
                {"repo": "hummbl-dev/some-fork", "proposed_title": "fix C", "category": "governance", "severity": "low"}
            ],
            access_limits=[
                {"repo": "hummbl-dev/private", "limit_type": "read-only", "details": "No write access"}
            ],
            write_boundary=["hummbl-dev/arbiter", "hummbl-io/hummbl-governance"],
            quality_scores={"avg_quality_score": 90.0, "rubric_version": "v1.0"},
            run_disposition="partial",
            backpressure_notes="Rate limited after 3 issues",
        )
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"
        assert receipt["run_disposition"] == "partial"

    def test_backward_compatible_no_new_fields(self):
        """Receipts without new fields should still validate (backward compat)."""
        receipt = create_receipt(
            source="manual",
            agent="devin",
            issues_created=[
                {"repo": "hummbl-dev/arbiter", "number": 1, "title": "test", "category": "gov", "severity": "low"}
            ],
        )
        is_valid, errors = validate_receipt(receipt)
        assert is_valid, f"Validation errors: {errors}"
        # New fields should not be present
        assert "skipped_duplicate_candidates" not in receipt
        assert "read_only_candidates" not in receipt
        assert "run_disposition" not in receipt

    def test_extended_receipt_append_and_read(self, tmp_path):
        """Extended receipts should survive append+read roundtrip."""
        log = tmp_path / "extended_receipts.jsonl"
        receipt = create_receipt(
            source="chatgpt-connector",
            agent="devin",
            skipped_duplicate_candidates=[
                {"repo": "hummbl-dev/arbiter", "proposed_title": "test", "duplicate_of": 99}
            ],
            run_disposition="skipped-all",
        )
        append_receipt(receipt, log)
        receipts = read_receipts(log)
        assert len(receipts) == 1
        assert receipts[0]["skipped_duplicate_candidates"][0]["duplicate_of"] == 99
        assert receipts[0]["run_disposition"] == "skipped-all"
