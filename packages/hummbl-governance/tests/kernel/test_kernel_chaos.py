#!/usr/bin/env python3
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
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Chaos engineering tests for the HUMMBL Governance Kernel.

Randomly corrupt state files mid-run and verify graceful recovery.
These tests prove the Kernel is resilient to disk corruption, crashes,
and unexpected mutations.

Usage:
    python -m pytest hummbl_governance/kernel/test_kernel_chaos.py -v
"""

from __future__ import annotations

import json
import os
import random
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hummbl_governance.kernel import (
    IdentityEngine,
    Kernel,
    KernelPanic,
    Receipt,
    ReceiptEngine,
    SequenceEngine,
)


class TestChaosReceiptEngine:
    """Corrupt receipt files and verify fail-closed panic (K1)."""

    def test_random_line_corruption(self) -> None:
        """Corrupt lines in a receipt file; verify fail-closed panic (K1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            # Create 100 receipts
            for i in range(100):
                receipt = engine.create(agent_id="chaos", action_type=f"STEP-{i}")
                engine.store(receipt)

            # Corrupt ~10% of lines
            receipt_file = engine.receipts_dir / "chaos.jsonl"
            lines = receipt_file.read_text().strip().split("\n")
            for i in range(len(lines)):
                if random.random() < 0.10:
                    lines[i] = lines[i][: len(lines[i]) // 2] + "CORRUPTED!!!"
            receipt_file.write_text("\n".join(lines) + "\n")

            # Fail-closed (K1): any corrupted receipt line must raise
            # KernelPanic rather than silently dropping the record.
            with pytest.raises(KernelPanic):
                engine.list_for_agent("chaos")

    def test_random_byte_corruption(self) -> None:
        """Randomly flip bytes in receipt file; verify fail-closed panic (K1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            for i in range(50):
                receipt = engine.create(agent_id="byte-chaos", action_type=f"STEP-{i}")
                engine.store(receipt)

            receipt_file = engine.receipts_dir / "byte-chaos.jsonl"
            data = bytearray(receipt_file.read_bytes())
            # Flip ~1% of bytes randomly
            for _ in range(len(data) // 100):
                idx = random.randint(0, len(data) - 1)
                data[idx] ^= 0xFF
            receipt_file.write_bytes(bytes(data))

            # Fail-closed (K1): corrupted receipt lines must raise
            # KernelPanic rather than silently dropping records.
            with pytest.raises(KernelPanic):
                engine.list_for_agent("byte-chaos")

    def test_truncate_mid_file(self) -> None:
        """Truncate file to 50%; verify fail-closed panic (K1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            for i in range(50):
                receipt = engine.create(agent_id="trunc", action_type=f"STEP-{i}")
                engine.store(receipt)

            receipt_file = engine.receipts_dir / "trunc.jsonl"
            content = receipt_file.read_text()
            receipt_file.write_text(content[: len(content) // 2])

            # Fail-closed (K1): truncated receipt line must raise
            # KernelPanic rather than silently dropping records.
            with pytest.raises(KernelPanic):
                engine.list_for_agent("trunc")

    def test_delete_receipt_file_mid_run(self) -> None:
        """Delete receipt file after creation; verify clean empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            for i in range(10):
                receipt = engine.create(agent_id="deleted", action_type=f"STEP-{i}")
                engine.store(receipt)

            receipt_file = engine.receipts_dir / "deleted.jsonl"
            os.remove(receipt_file)

            loaded = engine.list_for_agent("deleted")
            assert loaded == []

    def test_chain_breaks_after_corruption(self) -> None:
        """Replace a middle receipt with one that has a wrong hash; verify chain detects break."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ReceiptEngine(Path(tmpdir))
            receipts = []
            for i in range(20):
                receipt = engine.create(agent_id="chain-break", action_type=f"STEP-{i}")
                engine.store(receipt)
                receipts.append(receipt)

            # Replace line 10 with a valid Receipt that has a wrong prev_receipt_hash
            # (not corrupted JSON — that would now trigger KernelPanic per K1 fail-closed)
            receipt_file = engine.receipts_dir / "chain-break.jsonl"
            lines = receipt_file.read_text().strip().split("\n")
            fake = Receipt(
                receipt_id="fake-id",
                agent_id="chain-break",
                sequence_id=999,
                prev_receipt_hash="wronghash",
                timestamp=datetime.now(timezone.utc).isoformat(),
                action_type="FAKE",
            )
            lines[10] = json.dumps(asdict(fake))
            receipt_file.write_text("\n".join(lines) + "\n")

            # Chain should be broken (but list_for_agent should not panic —
            # the line is valid JSON and a valid Receipt, just has a wrong hash)
            valid, _ = engine.verify_chain("chain-break")
            assert valid is False


class TestChaosIdentityEngine:
    """Corrupt identity registry and verify recovery."""

    def test_registry_corruption_recovery(self) -> None:
        """Corrupt identity registry lines; verify fail-closed panic (K3)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for i in range(50):
                engine.register(f"agent-{i:02d}")

            registry_file = engine.registry_file
            lines = registry_file.read_text().strip().split("\n")
            for i in range(len(lines)):
                if random.random() < 0.20:
                    lines[i] = "not valid json {{"
            registry_file.write_text("\n".join(lines) + "\n")

            # Fail-closed (K3): any corrupted identity line must raise
            # KernelPanic rather than silently dropping the record.
            with pytest.raises(KernelPanic):
                IdentityEngine(Path(tmpdir))

    def test_role_claims_corruption(self) -> None:
        """Corrupt role claims file; verify fail-closed panic (K7)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            for i in range(20):
                engine.register(f"agent-{i}")
                engine.claim_role(f"agent-{i}", "AI-PE")

            claims_file = engine.role_claims_file
            lines = claims_file.read_text().strip().split("\n")
            for i in range(len(lines)):
                if random.random() < 0.30:
                    lines[i] = "truncated..."
            claims_file.write_text("\n".join(lines) + "\n")

            # Fail-closed (K7): any corrupted role claim must raise
            # KernelPanic rather than silently dropping the claim.
            with pytest.raises(KernelPanic):
                IdentityEngine(Path(tmpdir))

    def test_empty_registry_boot(self) -> None:
        """Boot with empty identity registry file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = Path(tmpdir) / "identity_registry.jsonl"
            registry.write_text("")
            engine = IdentityEngine(Path(tmpdir))
            assert len(engine._identities) == 0

    def test_permission_denied_graceful(self) -> None:
        """Make state dir read-only; verify KernelPanics gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = IdentityEngine(Path(tmpdir))
            engine.register("test")
            # Make file read-only
            os.chmod(engine.registry_file, 0o444)
            try:
                # This should fail gracefully
                with pytest.raises((PermissionError, OSError)):
                    engine.register("test2")
            finally:
                os.chmod(engine.registry_file, 0o644)


class TestChaosSequenceEngine:
    """Corrupt sequence counters and verify recovery."""

    def test_counters_corruption(self) -> None:
        """Corrupt counters JSON; verify engine fails closed (K4 panic)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            engine.next("agent-a")
            engine.next("agent-a")
            engine.next("agent-b")

            # Corrupt counters file
            engine.counters_file.write_text("not json")

            # Fail-closed (K4): corrupted counters must raise KernelPanic
            # rather than silently resetting Lamport counters to zero.
            with pytest.raises(KernelPanic):
                SequenceEngine(Path(tmpdir))

    def test_counters_partial_corruption(self) -> None:
        """Counters file with valid JSON but wrong types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SequenceEngine(Path(tmpdir))
            engine.next("agent")

            # Write string instead of int
            engine.counters_file.write_text('{"agent": "not_a_number"}')

            engine2 = SequenceEngine(Path(tmpdir))
            assert engine2.current("agent") == 0


class TestChaosKernelIntegration:
    """Chaos tests at the full Kernel level."""

    def test_kernel_boot_with_corrupt_state(self) -> None:
        """Boot Kernel with corrupt state; verify fail-closed panic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-seed corrupt state
            state_dir = Path(tmpdir)
            (state_dir / "identity_registry.jsonl").write_text(
                'bad json\n{"agent_id": "good", "trust_tier": "TRUSTED"}\n'
            )
            (state_dir / "sequence_counters.json").write_text('{"bad": "json"}')
            (state_dir / "receipts").mkdir(exist_ok=True)

            # Fail-closed (K3/K4): corrupted identity registry and
            # sequence counters must raise KernelPanic on boot rather
            # than silently dropping security-critical records.
            with pytest.raises(KernelPanic):
                Kernel.boot(state_dir=state_dir)

    def test_kernel_survives_missing_atlas(self) -> None:
        """Boot with missing atlas; verify degraded but functional."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override atlas_dir to a non-existent path
            from hummbl_governance.kernel.law_engine import LawEngine
            # Manually construct kernel with no atlas
            kernel = Kernel(state_dir=Path(tmpdir))
            # Replace law engine with empty atlas
            kernel.law = LawEngine(atlas_dir=Path(tmpdir) / "nonexistent_atlas")
            kernel._boot_sequence()
            assert kernel.booted is True
            assert len(kernel.law.laws) == 0  # No atlas loaded
            health = kernel.health()
            assert health["healthy"] is True  # Degraded mode still healthy

    def test_random_corruption_mid_session(self) -> None:
        """Create receipts, corrupt some, verify fail-closed panic (K1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel = Kernel.boot(state_dir=Path(tmpdir))
            kernel.identity.register("chaos-agent")

            # Phase 1: Create receipts
            for i in range(20):
                receipt = kernel.create_receipt("chaos-agent", f"PHASE1-{i}")
                kernel.store_receipt(receipt)

            # Phase 2: Corrupt some receipts
            receipt_file = kernel.receipt.receipts_dir / "chaos-agent.jsonl"
            lines = receipt_file.read_text().strip().split("\n")
            corrupted = False
            for i in range(len(lines)):
                if random.random() < 0.20:
                    lines[i] = "CORRUPT"
                    corrupted = True
            if not corrupted:
                lines[0] = "CORRUPT"
            receipt_file.write_text("\n".join(lines) + "\n")

            # Fail-closed (K1): any attempt to read corrupted receipts must
            # raise KernelPanic. This includes create_receipt which calls
            # last_for_agent → list_for_agent internally.
            with pytest.raises(KernelPanic):
                kernel.receipt.list_for_agent("chaos-agent")
