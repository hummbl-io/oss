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

"""Tests for ReceiptEngine → CorpusAdapter auto-ingest wire."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

from hummbl_governance.kernel import Kernel, Receipt, ReceiptEngine
from hummbl_governance.corpus_adapter import CorpusAdapter


class TestReceiptCorpusWire:
    def test_store_with_corpus_adapter(self, tmp_path: Path) -> None:
        engine = ReceiptEngine(tmp_path)
        receipt = engine.create(agent_id="devin", action_type="TEST")

        # Create a mock adapter
        mock_adapter = MagicMock(spec=CorpusAdapter)
        engine.corpus_adapter = mock_adapter

        engine.store(receipt)

        # Verify corpus adapter was called
        mock_adapter.ingest_receipt.assert_called_once_with(receipt)

    def test_store_with_failing_adapter(self, tmp_path: Path) -> None:
        engine = ReceiptEngine(tmp_path)
        receipt = engine.create(agent_id="devin", action_type="TEST")

        # Create a mock adapter that raises
        mock_adapter = MagicMock(spec=CorpusAdapter)
        mock_adapter.ingest_receipt.side_effect = RuntimeError("corpus down")
        engine.corpus_adapter = mock_adapter

        # Should NOT raise — best-effort ingestion
        result = engine.store(receipt)
        assert result == receipt.receipt_id

        # Local storage should still have happened
        receipt_file = tmp_path / "receipts" / "devin.jsonl"
        assert receipt_file.exists()

    def test_create_and_store(self, tmp_path: Path) -> None:
        engine = ReceiptEngine(tmp_path)

        mock_adapter = MagicMock(spec=CorpusAdapter)
        engine.corpus_adapter = mock_adapter

        receipt = engine.create_and_store(
            agent_id="devin",
            action_type="BUS_POST",
            payload={"bus_path": "messages.tsv"},
        )

        assert isinstance(receipt, Receipt)
        assert receipt.agent_id == "devin"
        assert receipt.action_type == "BUS_POST"

        # Verify local storage
        receipt_file = tmp_path / "receipts" / "devin.jsonl"
        assert receipt_file.exists()

        # Verify corpus ingestion
        mock_adapter.ingest_receipt.assert_called_once_with(receipt)

    def test_create_and_store_without_adapter(self, tmp_path: Path) -> None:
        engine = ReceiptEngine(tmp_path)
        receipt = engine.create_and_store(
            agent_id="devin",
            action_type="BUS_POST",
        )
        assert isinstance(receipt, Receipt)
        receipt_file = tmp_path / "receipts" / "devin.jsonl"
        assert receipt_file.exists()

    def test_kernel_wires_corpus_adapter_via_env(self, tmp_path: Path) -> None:
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        # Set env var
        os.environ["HUMMBL_CORPUS_DIR"] = str(corpus_dir)
        try:
            kernel = Kernel(state_dir=tmp_path / "kernel")
            assert kernel.receipt.corpus_adapter is not None
            assert isinstance(kernel.receipt.corpus_adapter, CorpusAdapter)
        finally:
            del os.environ["HUMMBL_CORPUS_DIR"]

    def test_kernel_without_env_has_no_adapter(self, tmp_path: Path) -> None:
        # Ensure env var is not set
        os.environ.pop("HUMMBL_CORPUS_DIR", None)

        kernel = Kernel(state_dir=tmp_path / "kernel")
        assert kernel.receipt.corpus_adapter is None
