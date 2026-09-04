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

"""Tests for K3-01 ghost-agent receipt vulnerability.

The receipt engine must validate agent_id against the identity registry
before creating a receipt. Without this check, any arbitrary string can
be used as agent_id, allowing ghost-agent receipts that bypass the K3
identity invariant.

Fix: ReceiptEngine accepts an optional identity_engine. When provided,
create() and create_and_store() raise KernelPanic(K3) if the agent_id
is not registered. The Kernel wires this when enforce_identity=True.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hummbl_governance.kernel import ReceiptEngine, IdentityEngine
from hummbl_governance.kernel.invariants import KernelInvariant, KernelPanic


@pytest.fixture
def tmp_state(tmp_path: Path) -> Path:
    """Clean state directory with env-var HMAC key."""
    old = os.environ.get("RECEIPTENGINE_HMAC_KEY")
    os.environ["RECEIPTENGINE_HMAC_KEY"] = "test-key-k3-01"
    yield tmp_path
    if old is not None:
        os.environ["RECEIPTENGINE_HMAC_KEY"] = old
    else:
        del os.environ["RECEIPTENGINE_HMAC_KEY"]


class TestGhostAgentReceiptVulnerability:
    """K3-01: Receipts must not be created for unregistered agents."""

    def test_unregistered_agent_rejected_when_identity_engine_wired(self, tmp_state: Path) -> None:
        """ReceiptEngine with identity_engine must reject ghost agents (K3)."""
        identity = IdentityEngine(tmp_state)
        engine = ReceiptEngine(tmp_state, identity_engine=identity)

        with pytest.raises(KernelPanic) as exc_info:
            engine.create(agent_id="ghost-agent", action_type="STATUS")

        assert exc_info.value.invariant == KernelInvariant.IDENTITY
        assert "ghost-agent" in exc_info.value.detail

    def test_registered_agent_accepted_when_identity_engine_wired(self, tmp_state: Path) -> None:
        """Registered agents can still create receipts."""
        identity = IdentityEngine(tmp_state)
        identity.register(agent_id="devin", trust_tier="MEDIUM-HIGH")
        engine = ReceiptEngine(tmp_state, identity_engine=identity)

        receipt = engine.create(agent_id="devin", action_type="STATUS")
        assert receipt.agent_id == "devin"

    def test_no_identity_engine_allows_any_agent_backward_compat(self, tmp_state: Path) -> None:
        """Without identity_engine, behavior is unchanged (backward compat)."""
        engine = ReceiptEngine(tmp_state)

        # This should NOT raise — backward compatibility for callers
        # that haven't wired identity enforcement yet
        receipt = engine.create(agent_id="any-agent", action_type="STATUS")
        assert receipt.agent_id == "any-agent"

    def test_create_and_store_rejects_ghost_agent(self, tmp_state: Path) -> None:
        """create_and_store must also reject ghost agents."""
        identity = IdentityEngine(tmp_state)
        engine = ReceiptEngine(tmp_state, identity_engine=identity)

        with pytest.raises(KernelPanic) as exc_info:
            engine.create_and_store(agent_id="phantom", action_type="STATUS")

        assert exc_info.value.invariant == KernelInvariant.IDENTITY

    def test_empty_agent_id_still_raises_k1(self, tmp_state: Path) -> None:
        """Empty agent_id must still raise K1 (receipt invariant), not K3."""
        identity = IdentityEngine(tmp_state)
        engine = ReceiptEngine(tmp_state, identity_engine=identity)

        with pytest.raises(KernelPanic) as exc_info:
            engine.create(agent_id="", action_type="STATUS")

        assert exc_info.value.invariant == KernelInvariant.RECEIPT

    def test_kernel_enforce_identity_wires_receipt(self, tmp_state: Path) -> None:
        """Kernel with enforce_identity=True must wire identity_engine into receipt engine."""
        from hummbl_governance.kernel import Kernel

        kernel = Kernel(state_dir=tmp_state, enforce_identity=True)
        assert kernel.receipt._identity_engine is not None
        assert kernel.receipt._identity_engine is kernel.identity

    def test_kernel_default_enforces_identity(self, tmp_state: Path) -> None:
        """Kernel default must enforce identity (K3-01 fix).

        The default was flipped from False to True after the wargame
        found that unregistered ghost agents could create receipts via
        the default Kernel path. Production Kernels must be secure by
        default; callers who need the old behavior must explicitly opt
        out with enforce_identity=False.
        """
        from hummbl_governance.kernel import Kernel

        kernel = Kernel(state_dir=tmp_state)
        assert kernel.receipt._identity_engine is not None
        assert kernel.receipt._identity_engine is kernel.identity

    def test_kernel_explicit_opt_out_disables_identity(self, tmp_state: Path) -> None:
        """Kernel with enforce_identity=False explicitly opts out of K3.

        This is the backward-compat escape hatch for callers that
        cannot yet wire identity enforcement.
        """
        from hummbl_governance.kernel import Kernel

        kernel = Kernel(state_dir=tmp_state, enforce_identity=False)
        assert kernel.receipt._identity_engine is None

    def test_kernel_default_rejects_ghost_agent_receipt(self, tmp_state: Path) -> None:
        """Kernel default path must reject ghost-agent receipts (K3-01).

        This is the end-to-end test of the fix: a Kernel created with
        defaults must reject a receipt for an unregistered agent.
        """
        from hummbl_governance.kernel import Kernel

        kernel = Kernel(state_dir=tmp_state)
        with pytest.raises(KernelPanic) as exc_info:
            kernel.receipt.create(agent_id="ghost-agent-not-registered", action_type="STATUS")

        assert exc_info.value.invariant == KernelInvariant.IDENTITY

    def test_kernel_boot_enforces_identity(self, tmp_state: Path) -> None:
        """Kernel.boot() must enforce identity by default."""
        from hummbl_governance.kernel import Kernel

        kernel = Kernel.boot(state_dir=tmp_state)
        assert kernel.receipt._identity_engine is not None
