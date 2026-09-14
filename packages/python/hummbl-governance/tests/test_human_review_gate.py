# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_governance.human_review_gate (P53 HumanReviewGate)."""

import json
import tempfile
import time
from pathlib import Path

import pytest
from hummbl_governance import ApprovalManager, RiskLevel
from hummbl_governance.human_review_gate import (
    Art22Mode,
    Art22ModeError,
    GateAlreadyDecidedError,
    GateNotFoundError,
    HumanReviewGate,
    HumanReviewGateReceipt,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def mgr():
    return ApprovalManager()


@pytest.fixture()
def gate(mgr, tmp_dir):
    store = tmp_dir / "gate_receipts.jsonl"
    return HumanReviewGate(approval_manager=mgr, store_path=store)


def _open_gate(gate, **kwargs):
    defaults = dict(
        agent_id="test-agent",
        data_subject_id="subj-aaa-111",
        decision_summary="Deny loan application: score below threshold",
        decision_payload={"score": 420, "threshold": 550},
        art22_mode=Art22Mode.CONTRACT,
    )
    defaults.update(kwargs)
    return gate.request_review(**defaults)


# ---------------------------------------------------------------------------
# Art22Mode validation
# ---------------------------------------------------------------------------

class TestArt22Mode:
    def test_valid_modes_accepted(self):
        for mode in (Art22Mode.CONTRACT, Art22Mode.LAW, Art22Mode.CONSENT):
            assert Art22Mode.validate(mode) == mode

    def test_none_mode_raises_art22_mode_error(self):
        with pytest.raises(Art22ModeError):
            Art22Mode.validate(Art22Mode.NONE)

    def test_unknown_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown Art22Mode"):
            Art22Mode.validate("bogus_mode")


# ---------------------------------------------------------------------------
# request_review
# ---------------------------------------------------------------------------

class TestRequestReview:
    def test_returns_pending_receipt(self, gate):
        receipt = _open_gate(gate)
        assert receipt.outcome == "PENDING"

    def test_receipt_has_gate_id(self, gate):
        receipt = _open_gate(gate)
        assert receipt.gate_id
        assert len(receipt.gate_id) == 36  # UUID4

    def test_receipt_data_subject_id(self, gate):
        receipt = _open_gate(gate, data_subject_id="subj-xyz-999")
        assert receipt.data_subject_id == "subj-xyz-999"

    def test_receipt_art22_mode(self, gate):
        receipt = _open_gate(gate, art22_mode=Art22Mode.CONSENT)
        assert receipt.art22_mode == Art22Mode.CONSENT

    def test_receipt_solely_automated_starts_true(self, gate):
        """solely_automated=True until a human explicitly approves."""
        receipt = _open_gate(gate)
        assert receipt.solely_automated is True

    def test_receipt_hmac_present(self, gate):
        receipt = _open_gate(gate)
        assert receipt.receipt_hmac
        assert len(receipt.receipt_hmac) == 64  # SHA-256 hex

    def test_none_mode_raises_before_creating_gate(self, gate):
        with pytest.raises(Art22ModeError):
            _open_gate(gate, art22_mode=Art22Mode.NONE)

    def test_gate_persisted_to_store(self, gate, tmp_dir):
        receipt = _open_gate(gate)
        store = tmp_dir / "gate_receipts.jsonl"
        assert store.exists()
        lines = store.read_text().strip().splitlines()
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data["gate_id"] == receipt.gate_id


# ---------------------------------------------------------------------------
# record_reviewer_decision
# ---------------------------------------------------------------------------

class TestReviewerDecision:
    def test_approved_sets_outcome_approved(self, gate):
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="reviewer-007", outcome="APPROVED"
        )
        assert final.outcome == "APPROVED"

    def test_approved_sets_solely_automated_false(self, gate):
        """Core Art. 22 chain-break: solely_automated=False on APPROVED."""
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="reviewer-007", outcome="APPROVED"
        )
        assert final.solely_automated is False

    def test_denied_keeps_solely_automated_true(self, gate):
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="reviewer-007", outcome="DENIED"
        )
        assert final.outcome == "DENIED"
        assert final.solely_automated is True

    def test_reviewer_id_recorded(self, gate):
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="alice@example.com", outcome="APPROVED"
        )
        assert final.reviewer_id == "alice@example.com"

    def test_reviewer_notes_recorded(self, gate):
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="bob",
            outcome="DENIED", reviewer_notes="Score too low."
        )
        assert final.reviewer_notes == "Score too low."

    def test_timestamp_decided_set(self, gate):
        receipt = _open_gate(gate)
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="r1", outcome="APPROVED"
        )
        assert final.timestamp_decided is not None

    def test_double_decision_raises(self, gate):
        receipt = _open_gate(gate)
        gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="r1", outcome="APPROVED"
        )
        with pytest.raises(GateAlreadyDecidedError):
            gate.record_reviewer_decision(
                receipt.gate_id, reviewer_id="r2", outcome="DENIED"
            )

    def test_invalid_outcome_raises_value_error(self, gate):
        receipt = _open_gate(gate)
        with pytest.raises(ValueError, match="outcome must be"):
            gate.record_reviewer_decision(
                receipt.gate_id, reviewer_id="r1", outcome="MAYBE"
            )

    def test_unknown_gate_id_raises(self, gate):
        with pytest.raises(GateNotFoundError):
            gate.record_reviewer_decision(
                "no-such-gate", reviewer_id="r1", outcome="APPROVED"
            )


# ---------------------------------------------------------------------------
# Timeout → DENIED (not APPROVED)
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_timeout_resolves_as_timeout_not_approved(self, mgr, tmp_dir):
        """Core GDPR invariant: silence ≠ consent. Timeout must DENY."""
        store = tmp_dir / "gate_receipts.jsonl"
        gate = HumanReviewGate(approval_manager=mgr, store_path=store)
        receipt = _open_gate(gate, timeout_seconds=0.1)
        time.sleep(0.2)
        final = gate.wait_for_gate(receipt.gate_id, timeout=0.3,
                                   poll_interval=0.05)
        assert final.outcome in ("TIMEOUT", "DENIED")
        assert final.solely_automated is True

    def test_wait_returns_approved_when_reviewer_approves(self, mgr, tmp_dir):
        store = tmp_dir / "gate_receipts.jsonl"
        gate = HumanReviewGate(approval_manager=mgr, store_path=store)
        receipt = _open_gate(gate)

        import threading
        def approve_after_delay():
            time.sleep(0.1)
            gate.record_reviewer_decision(
                receipt.gate_id, reviewer_id="auto-reviewer",
                outcome="APPROVED"
            )

        t = threading.Thread(target=approve_after_delay, daemon=True)
        t.start()
        final = gate.wait_for_gate(receipt.gate_id, timeout=5.0,
                                   poll_interval=0.05)
        t.join()
        assert final.outcome == "APPROVED"
        assert final.solely_automated is False


# ---------------------------------------------------------------------------
# HMAC integrity
# ---------------------------------------------------------------------------

class TestHMACIntegrity:
    def test_hmac_changes_on_state_transition(self, gate):
        receipt = _open_gate(gate)
        pending_hmac = receipt.receipt_hmac
        final = gate.record_reviewer_decision(
            receipt.gate_id, reviewer_id="r1", outcome="APPROVED"
        )
        assert final.receipt_hmac != pending_hmac

    def test_hmac_is_64_hex_chars(self, gate):
        receipt = _open_gate(gate)
        assert len(receipt.receipt_hmac) == 64
        int(receipt.receipt_hmac, 16)  # Must be valid hex


# ---------------------------------------------------------------------------
# DSAR searchability
# ---------------------------------------------------------------------------

class TestDSARSearchability:
    def test_list_by_subject_returns_matching_gates(self, gate):
        _open_gate(gate, data_subject_id="subj-A")
        _open_gate(gate, data_subject_id="subj-A")
        _open_gate(gate, data_subject_id="subj-B")
        results = gate.list_by_subject("subj-A")
        assert len(results) == 2
        assert all(r.data_subject_id == "subj-A" for r in results)

    def test_list_by_subject_empty_for_unknown(self, gate):
        assert gate.list_by_subject("no-such-subject") == []

    def test_store_entries_contain_data_subject_id(self, gate, tmp_dir):
        _open_gate(gate, data_subject_id="subj-searchable")
        store = tmp_dir / "gate_receipts.jsonl"
        lines = store.read_text().strip().splitlines()
        data = json.loads(lines[0])
        assert data["data_subject_id"] == "subj-searchable"


# ---------------------------------------------------------------------------
# Persistence / reload
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_gate_survives_reload(self, mgr, tmp_dir):
        store = tmp_dir / "gate_receipts.jsonl"
        gate1 = HumanReviewGate(approval_manager=mgr, store_path=store)
        receipt = _open_gate(gate1)
        gate1.record_reviewer_decision(
            receipt.gate_id, reviewer_id="r1", outcome="APPROVED"
        )

        # Load from disk.
        gate2 = HumanReviewGate(approval_manager=mgr, store_path=store)
        reloaded = gate2.get(receipt.gate_id)
        assert reloaded.outcome == "APPROVED"
        assert reloaded.solely_automated is False

    def test_no_store_still_works(self, mgr):
        gate = HumanReviewGate(approval_manager=mgr, store_path=None)
        receipt = _open_gate(gate)
        assert receipt.outcome == "PENDING"


# ---------------------------------------------------------------------------
# list_pending
# ---------------------------------------------------------------------------

class TestListPending:
    def test_pending_gates_listed(self, gate):
        r1 = _open_gate(gate, data_subject_id="subj-1")
        r2 = _open_gate(gate, data_subject_id="subj-2")
        gate.record_reviewer_decision(r1.gate_id, "r1", "APPROVED")
        pending = gate.list_pending()
        assert any(r.gate_id == r2.gate_id for r in pending)
        assert not any(r.gate_id == r1.gate_id for r in pending)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_returns_receipt(self, gate):
        receipt = _open_gate(gate)
        assert gate.get(receipt.gate_id).gate_id == receipt.gate_id

    def test_get_unknown_raises(self, gate):
        with pytest.raises(GateNotFoundError):
            gate.get("does-not-exist")


# ---------------------------------------------------------------------------
# Receipt serialisation
# ---------------------------------------------------------------------------

class TestReceiptSerialisation:
    def test_to_dict_round_trips(self, gate):
        receipt = _open_gate(gate)
        d = receipt.to_dict()
        reconstructed = HumanReviewGateReceipt.from_dict(d)
        assert reconstructed == receipt

    def test_to_dict_has_all_keys(self, gate):
        receipt = _open_gate(gate)
        d = receipt.to_dict()
        for key in (
            "gate_id", "approval_request_id", "agent_id",
            "data_subject_id", "decision_summary", "art22_mode",
            "reviewer_id", "outcome", "solely_automated",
            "reviewer_notes", "timestamp_requested",
            "timestamp_decided", "receipt_hmac",
        ):
            assert key in d, f"Missing key: {key}"
