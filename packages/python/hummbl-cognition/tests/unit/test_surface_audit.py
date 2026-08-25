"""Tests for surface_audit module."""

import json
from pathlib import Path

import pytest

from hummbl_cognition.surface_audit import (
    DEFAULT_LOG_PATH,
    VALID_SURFACES,
    VALID_AUTHORITY_LEVELS,
    VALID_RESULTS,
    SurfaceAuditError,
    record_action,
    validate_receipt,
    append_receipt,
    read_receipts,
)


class TestRecordAction:
    """Tests for record_action function."""

    def test_valid_receipt(self):
        receipt = record_action(
            surface_id="issues-ui",
            actor="devin",
            authority_level="active",
            action="create-issue",
            result="success",
        )
        assert receipt["surface_id"] == "issues-ui"
        assert receipt["actor"] == "devin"
        assert receipt["action"] == "create-issue"
        assert receipt["result"] == "success"
        assert receipt["action_id"].startswith("surf-")
        assert "content_hash" in receipt
        assert len(receipt["content_hash"]) == 64

    def test_with_optional_fields(self):
        receipt = record_action(
            surface_id="prs-ui",
            actor="codex",
            authority_level="trusted",
            action="merge-pr",
            result="success",
            evidence_ref="https://github.com/test/repo/pull/1",
            repo="hummbl-io/hummbl-governance",
            pr_number=42,
            notes="squash-merged after CI green",
        )
        assert receipt["repo"] == "hummbl-io/hummbl-governance"
        assert receipt["pr_number"] == 42
        assert receipt["evidence_ref"] != ""

    def test_invalid_surface_id(self):
        with pytest.raises(SurfaceAuditError, match="invalid surface_id"):
            record_action(
                surface_id="invalid-surface",
                actor="devin",
                authority_level="active",
                action="test",
                result="success",
            )

    def test_invalid_authority_level(self):
        with pytest.raises(SurfaceAuditError, match="invalid authority_level"):
            record_action(
                surface_id="issues-ui",
                actor="devin",
                authority_level="super-admin",
                action="test",
                result="success",
            )

    def test_invalid_result(self):
        with pytest.raises(SurfaceAuditError, match="invalid result"):
            record_action(
                surface_id="issues-ui",
                actor="devin",
                authority_level="active",
                action="test",
                result="maybe",
            )

    def test_empty_actor(self):
        with pytest.raises(SurfaceAuditError, match="actor"):
            record_action(
                surface_id="issues-ui",
                actor="",
                authority_level="active",
                action="test",
                result="success",
            )

    def test_empty_action(self):
        with pytest.raises(SurfaceAuditError, match="action"):
            record_action(
                surface_id="issues-ui",
                actor="devin",
                authority_level="active",
                action="",
                result="success",
            )

    def test_all_valid_surfaces(self):
        for surface in VALID_SURFACES:
            receipt = record_action(
                surface_id=surface,
                actor="test",
                authority_level="active",
                action="test",
                result="success",
            )
            assert receipt["surface_id"] == surface

    def test_all_valid_authority_levels(self):
        for level in VALID_AUTHORITY_LEVELS:
            receipt = record_action(
                surface_id="gh-cli",
                actor="test",
                authority_level=level,
                action="test",
                result="success",
            )
            assert receipt["authority_level"] == level

    def test_all_valid_results(self):
        for result_val in VALID_RESULTS:
            receipt = record_action(
                surface_id="gh-cli",
                actor="test",
                authority_level="active",
                action="test",
                result=result_val,
            )
            assert receipt["result"] == result_val


class TestValidateReceipt:
    """Tests for validate_receipt function."""

    def test_valid_receipt(self):
        receipt = record_action(
            surface_id="issues-ui",
            actor="devin",
            authority_level="active",
            action="create-issue",
            result="success",
        )
        assert validate_receipt(receipt) is True

    def test_missing_field(self):
        receipt = {"action_id": "test", "timestamp": "2026-01-01T00:00:00Z"}
        with pytest.raises(SurfaceAuditError, match="missing required field"):
            validate_receipt(receipt)

    def test_invalid_surface(self):
        receipt = record_action(
            surface_id="issues-ui",
            actor="devin",
            authority_level="active",
            action="test",
            result="success",
        )
        receipt["surface_id"] = "invalid"
        with pytest.raises(SurfaceAuditError, match="invalid surface_id"):
            validate_receipt(receipt)


class TestAppendAndRead:
    """Tests for append_receipt and read_receipts."""

    def test_append_and_read(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        receipt = record_action(
            surface_id="issues-ui",
            actor="devin",
            authority_level="active",
            action="create-issue",
            result="success",
            repo="hummbl-dev/test",
        )
        append_receipt(receipt, log_path)
        assert log_path.exists()

        receipts = read_receipts(log_path)
        assert len(receipts) == 1
        assert receipts[0]["action_id"] == receipt["action_id"]

    def test_append_multiple_and_read_newest_first(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        for i in range(5):
            receipt = record_action(
                surface_id="issues-ui",
                actor="devin",
                authority_level="active",
                action=f"action-{i}",
                result="success",
            )
            append_receipt(receipt, log_path)

        receipts = read_receipts(log_path)
        assert len(receipts) == 5
        assert receipts[0]["action"] == "action-4"

    def test_read_limit(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        for i in range(10):
            receipt = record_action(
                surface_id="issues-ui",
                actor="devin",
                authority_level="active",
                action=f"action-{i}",
                result="success",
            )
            append_receipt(receipt, log_path)

        receipts = read_receipts(log_path, limit=3)
        assert len(receipts) == 3

    def test_read_nonexistent_log(self, tmp_path):
        receipts = read_receipts(tmp_path / "missing.jsonl")
        assert receipts == []

    def test_append_creates_parent_dir(self, tmp_path):
        log_path = tmp_path / "subdir" / "audit.jsonl"
        receipt = record_action(
            surface_id="issues-ui",
            actor="devin",
            authority_level="active",
            action="test",
            result="success",
        )
        append_receipt(receipt, log_path)
        assert log_path.exists()

    def test_append_invalid_receipt_raises(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        with pytest.raises(SurfaceAuditError):
            append_receipt({"invalid": "receipt"}, log_path)
