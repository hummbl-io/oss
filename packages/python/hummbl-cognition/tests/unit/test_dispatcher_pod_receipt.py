"""Tests for dispatcher_pod_receipt module."""

import pytest
from hummbl_cognition.dispatcher_pod_receipt import (
    VALID_OPERATIONS,
    VALID_STATUSES,
    _validate_receipt_structure,
    append_receipt,
    create_claim_receipt,
    create_receipt,
    get_pod_chain,
    is_pod_claimed,
    read_receipts,
    validate_chain,
)


class TestCreateClaimReceipt:
    """Tests for create_claim_receipt."""

    def test_basic_claim(self):
        receipt = create_claim_receipt(
            pod_id="pod-test-001",
            agent="devin",
            correlation_id="corr-001",
        )
        assert receipt.pod_id == "pod-test-001"
        assert receipt.operation == "claim"
        assert receipt.agent == "devin"
        assert receipt.parent_receipt_hash is None
        assert receipt.content_hash != ""

    def test_claim_with_optional_fields(self):
        receipt = create_claim_receipt(
            pod_id="pod-test-002",
            agent="codex",
            correlation_id="corr-002",
            lane_id="lane-1",
            tracker_id="tracker-1",
            issue_id="issue-100",
            notes="test claim",
        )
        assert receipt.lane_id == "lane-1"
        assert receipt.tracker_id == "tracker-1"
        assert receipt.issue_id == "issue-100"
        assert receipt.notes == "test claim"

    def test_claim_to_dict(self):
        receipt = create_claim_receipt(
            pod_id="pod-test-003",
            agent="devin",
            correlation_id="corr-003",
        )
        d = receipt.to_dict()
        assert d["pod_id"] == "pod-test-003"
        assert d["operation"] == "claim"
        assert d["parent_receipt_hash"] is None


class TestCreateReceipt:
    """Tests for create_receipt (non-claim)."""

    def test_release_receipt(self):
        receipt = create_receipt(
            pod_id="pod-test-004",
            operation="release",
            agent="devin",
            correlation_id="corr-004",
            parent_receipt_hash="abc123",
            status="complete",
        )
        assert receipt.operation == "release"
        assert receipt.parent_receipt_hash == "abc123"
        assert receipt.status == "complete"

    def test_launch_receipt(self):
        receipt = create_receipt(
            pod_id="pod-test-005",
            operation="launch",
            agent="devin",
            correlation_id="corr-005",
            parent_receipt_hash="abc123",
            worktree_path="/tmp/worktree",
            worktree_head="abc123def456",
            runtime="github-actions",
            process_id=12345,
        )
        assert receipt.operation == "launch"
        assert receipt.worktree_path == "/tmp/worktree"
        assert receipt.process_id == 12345

    def test_claim_via_create_receipt_raises(self):
        with pytest.raises(ValueError, match="Use create_claim_receipt"):
            create_receipt(
                pod_id="pod-test-006",
                operation="claim",
                agent="devin",
                correlation_id="corr-006",
                parent_receipt_hash="abc123",
            )


class TestAppendAndRead:
    """Tests for append_receipt and read_receipts."""

    def test_append_and_read(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        receipt = create_claim_receipt(
            pod_id="pod-test-010",
            agent="devin",
            correlation_id="corr-010",
        )
        append_receipt(receipt, log_path)
        assert log_path.exists()

        receipts = read_receipts(log_path)
        assert len(receipts) == 1
        assert receipts[0]["pod_id"] == "pod-test-010"

    def test_append_creates_parent_dir(self, tmp_path):
        log_path = tmp_path / "subdir" / "pod_receipts.jsonl"
        receipt = create_claim_receipt(
            pod_id="pod-test-011",
            agent="devin",
            correlation_id="corr-011",
        )
        append_receipt(receipt, log_path)
        assert log_path.exists()

    def test_read_nonexistent_log(self, tmp_path):
        receipts = read_receipts(tmp_path / "missing.jsonl")
        assert receipts == []

    def test_append_multiple(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        claim = create_claim_receipt(
            pod_id="pod-test-012",
            agent="devin",
            correlation_id="corr-012",
        )
        append_receipt(claim, log_path)

        release = create_receipt(
            pod_id="pod-test-012",
            operation="release",
            agent="devin",
            correlation_id="corr-012",
            parent_receipt_hash=claim.content_hash,
            status="complete",
        )
        append_receipt(release, log_path)

        receipts = read_receipts(log_path)
        assert len(receipts) == 2


class TestPodChain:
    """Tests for get_pod_chain and validate_chain."""

    def test_get_pod_chain(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        claim = create_claim_receipt(
            pod_id="pod-chain-001",
            agent="devin",
            correlation_id="corr-chain-001",
        )
        append_receipt(claim, log_path)

        launch = create_receipt(
            pod_id="pod-chain-001",
            operation="launch",
            agent="devin",
            correlation_id="corr-chain-001",
            parent_receipt_hash=claim.content_hash,
        )
        append_receipt(launch, log_path)

        release = create_receipt(
            pod_id="pod-chain-001",
            operation="release",
            agent="devin",
            correlation_id="corr-chain-001",
            parent_receipt_hash=launch.content_hash,
            status="complete",
        )
        append_receipt(release, log_path)

        chain = get_pod_chain("pod-chain-001", log_path)
        assert len(chain) == 3
        assert chain[0]["operation"] == "claim"
        assert chain[1]["operation"] == "launch"
        assert chain[2]["operation"] == "release"

    def test_validate_chain_valid(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        claim = create_claim_receipt(
            pod_id="pod-valid-001",
            agent="devin",
            correlation_id="corr-valid-001",
        )
        append_receipt(claim, log_path)

        release = create_receipt(
            pod_id="pod-valid-001",
            operation="release",
            agent="devin",
            correlation_id="corr-valid-001",
            parent_receipt_hash=claim.content_hash,
            status="complete",
        )
        append_receipt(release, log_path)

        errors = validate_chain("pod-valid-001", log_path)
        assert errors == []

    def test_validate_chain_empty(self, tmp_path):
        errors = validate_chain("pod-nonexistent", tmp_path / "missing.jsonl")
        assert len(errors) == 1
        assert "No receipts" in errors[0]

    def test_get_pod_chain_empty(self, tmp_path):
        chain = get_pod_chain("pod-nonexistent", tmp_path / "missing.jsonl")
        assert chain == []


class TestIsPodClaimed:
    """Tests for is_pod_claimed."""

    def test_claimed_not_released(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        claim = create_claim_receipt(
            pod_id="pod-claimed-001",
            agent="devin",
            correlation_id="corr-claimed-001",
        )
        append_receipt(claim, log_path)
        assert is_pod_claimed("pod-claimed-001", log_path) is True

    def test_claimed_and_released(self, tmp_path):
        log_path = tmp_path / "pod_receipts.jsonl"
        claim = create_claim_receipt(
            pod_id="pod-released-001",
            agent="devin",
            correlation_id="corr-released-001",
        )
        append_receipt(claim, log_path)

        release = create_receipt(
            pod_id="pod-released-001",
            operation="release",
            agent="devin",
            correlation_id="corr-released-001",
            parent_receipt_hash=claim.content_hash,
            status="complete",
        )
        append_receipt(release, log_path)
        assert is_pod_claimed("pod-released-001", log_path) is False

    def test_never_claimed(self, tmp_path):
        assert is_pod_claimed("pod-never", tmp_path / "missing.jsonl") is False


class TestValidation:
    """Tests for _validate_receipt_structure."""

    def test_valid_receipt(self):
        receipt = create_claim_receipt(
            pod_id="pod-val-001",
            agent="devin",
            correlation_id="corr-val-001",
        )
        errors = _validate_receipt_structure(receipt.to_dict())
        assert errors == []

    def test_missing_field(self):
        receipt = {"receipt_id": "test", "pod_id": "pod-test"}
        errors = _validate_receipt_structure(receipt)
        assert len(errors) > 0
        assert any("Missing" in e for e in errors)

    def test_invalid_operation(self):
        receipt = create_claim_receipt(
            pod_id="pod-val-002",
            agent="devin",
            correlation_id="corr-val-002",
        )
        d = receipt.to_dict()
        d["operation"] = "invalid-op"
        errors = _validate_receipt_structure(d)
        assert any("Invalid operation" in e for e in errors)

    def test_invalid_pod_id_prefix(self):
        receipt = create_claim_receipt(
            pod_id="pod-val-003",
            agent="devin",
            correlation_id="corr-val-003",
        )
        d = receipt.to_dict()
        d["pod_id"] = "invalid-prefix"
        errors = _validate_receipt_structure(d)
        assert any("pod_id must start" in e for e in errors)

    def test_invalid_status(self):
        receipt = create_claim_receipt(
            pod_id="pod-val-004",
            agent="devin",
            correlation_id="corr-val-004",
        )
        d = receipt.to_dict()
        d["status"] = "invalid-status"
        errors = _validate_receipt_structure(d)
        assert any("Invalid status" in e for e in errors)


class TestValidConstants:
    """Tests for valid operations and statuses."""

    def test_valid_operations_include_claim_and_release(self):
        assert "claim" in VALID_OPERATIONS
        assert "release" in VALID_OPERATIONS
        assert "launch" in VALID_OPERATIONS
        assert "writeback" in VALID_OPERATIONS

    def test_valid_statuses(self):
        assert "complete" in VALID_STATUSES
        assert "failed" in VALID_STATUSES
        assert "blocked" in VALID_STATUSES
        assert "partial" in VALID_STATUSES
