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

"""Corpus adapter — bridge hummbl-governance receipts to unified-frameworks.

Usage::

    from hummbl_governance.corpus_adapter import CorpusAdapter
    from hummbl_governance.kernel import ReceiptEngine

    engine = ReceiptEngine(state_dir)
    adapter = CorpusAdapter(corpus_dir=Path("./corpus"))

    receipt = engine.create(agent_id="devin", action_type="BUS_POST")
    adapter.ingest_receipt(receipt)  # kernel_version defaults to hummbl_governance.__version__

Best-effort: if unified-frameworks is not installed, receipts are queued
locally for later ingestion.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_governance import __version__ as _KERNEL_VERSION

logger = logging.getLogger(__name__)

# Lazy import of unified-frameworks corpus ingest (best-effort)
try:
    from corpus.ingest import CorpusIngestor

    _HAS_CORPUS = True
except ImportError:
    _HAS_CORPUS = False


def _receipt_to_kernel_output(receipt: Any, kernel_version: str = _KERNEL_VERSION) -> dict[str, Any]:
    """Transform a hummbl-governance Receipt into a kernel_output envelope."""
    return {
        "kernel_name": "hummbl-governance",
        "kernel_version": kernel_version,
        "engine_name": "ReceiptEngine",
        "invariant_id": "K1",
        "output_type": "receipt",
        "timestamp": receipt.timestamp,
        "payload": {
            "receipt_id": receipt.receipt_id,
            "agent_id": receipt.agent_id,
            "sequence_id": receipt.sequence_id,
            "action_type": receipt.action_type,
            "law_checks": receipt.law_checks,
            "violations": receipt.violations,
            "evidence_grade": receipt.evidence_grade,
        },
        "receipt_ref": receipt.receipt_id,
        "confidence": 0.95 if not receipt.violations else 0.7,
    }


class CorpusAdapter:
    """Adapter that submits hummbl-governance receipts to the unified corpus.

    If the corpus ingestion API is unavailable, receipts are queued locally
    in ``state_dir / corpus_queue`` as JSONL for later batch ingestion.
    """

    def __init__(
        self,
        corpus_dir: Path | None = None,
        state_dir: Path | None = None,
    ) -> None:
        self.corpus_dir = corpus_dir
        self.state_dir = state_dir or Path(
            os.environ.get("HUMMBL_KERNEL_STATE_DIR", ".kernel")
        )
        self._ingestor: Any = None
        if _HAS_CORPUS and corpus_dir is not None:
            self._ingestor = CorpusIngestor(corpus_dir=corpus_dir)

    def ingest_receipt(self, receipt: Any, kernel_version: str = _KERNEL_VERSION) -> str | None:
        """Submit a receipt to the corpus.

        Args:
            receipt: A Receipt dataclass instance.
            kernel_version: Version of hummbl-governance that produced it.

        Returns:
            The corpus packet_id if ingested, None on failure.
        """
        kernel_output = _receipt_to_kernel_output(receipt, kernel_version)

        if self._ingestor is not None:
            try:
                packet_id = self._ingestor.ingest_kernel_output(kernel_output)
                logger.debug("Receipt %s ingested to corpus as %s", receipt.receipt_id, packet_id)
                return packet_id
            except Exception:
                logger.warning("Corpus ingestion failed; queuing locally", exc_info=True)

        # Fallback: queue locally
        return self._queue_locally(kernel_output)

    def _queue_locally(self, kernel_output: dict[str, Any]) -> str | None:
        """Write kernel_output to local queue for later ingestion."""
        queue_dir = self.state_dir / "corpus_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_file = queue_dir / "pending.jsonl"

        entry = {
            "queued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kernel_output": kernel_output,
        }
        with open(queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.debug("Receipt %s queued locally at %s", kernel_output.get("receipt_ref"), queue_file)
        return kernel_output.get("receipt_ref")

    def flush_queue(self) -> list[str]:
        """Flush locally queued receipts to corpus if now available.

        Returns:
            List of packet_ids successfully ingested.
        """
        if self._ingestor is None:
            logger.debug("No corpus ingestor available; cannot flush queue")
            return []

        queue_file = self.state_dir / "corpus_queue" / "pending.jsonl"
        if not queue_file.exists():
            return []

        ingested: list[str] = []
        new_queue_file = self.state_dir / "corpus_queue" / "pending.new.jsonl"

        with open(queue_file, "r", encoding="utf-8") as f_in, open(
            new_queue_file, "w", encoding="utf-8"
        ) as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    kernel_output = entry["kernel_output"]
                    packet_id = self._ingestor.ingest_kernel_output(kernel_output)
                    if packet_id:
                        ingested.append(packet_id)
                except Exception:
                    # Keep in queue if ingestion fails
                    f_out.write(line + "\n")

        # Atomically replace queue file
        queue_file.unlink()
        new_queue_file.rename(queue_file)

        if ingested:
            logger.info("Flushed %d queued receipts to corpus", len(ingested))
        return ingested
