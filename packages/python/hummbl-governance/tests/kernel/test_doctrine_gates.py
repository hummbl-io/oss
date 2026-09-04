

class TestKernelStrictLawMode:
    """Test that Kernel.store_receipt(strict_law=True) raises on violations."""

    def test_store_receipt_strict_mode_no_violations(self, tmp_path):
        """Test that strict mode passes when no violations exist."""
        from hummbl_governance.kernel.kernel import Kernel
        from hummbl_governance.kernel.receipt_engine import Receipt

        kernel = Kernel(tmp_path)
        receipt = Receipt(
            receipt_id="test-001",
            agent_id="devin",
            sequence_id=0,
            prev_receipt_hash="",
            timestamp="2026-09-02T12:00:00Z",
            action_type="test",
            payload={},
        )
        # Should not raise — no laws loaded in test env
        receipt_id = kernel.store_receipt(receipt, strict_law=True)
        assert receipt_id is not None

    def test_store_receipt_advisory_mode_default(self, tmp_path):
        """Test that default (advisory) mode does not raise."""
        from hummbl_governance.kernel.kernel import Kernel
        from hummbl_governance.kernel.receipt_engine import Receipt

        kernel = Kernel(tmp_path)
        receipt = Receipt(
            receipt_id="test-002",
            agent_id="devin",
            sequence_id=0,
            prev_receipt_hash="",
            timestamp="2026-09-02T12:00:00Z",
            action_type="test",
            payload={},
        )
        # Default mode — should not raise
        receipt_id = kernel.store_receipt(receipt)
        assert receipt_id is not None
