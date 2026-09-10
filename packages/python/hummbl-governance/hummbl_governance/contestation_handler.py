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

"""Contestation Handler (P54) — GDPR Art. 22(3) / Art. 21 workflow.

Provides an external data-subject-facing workflow to contest automated decisions.
Links back to HumanReviewGate receipts (P53), suspends the contested decision's 
effects via CapabilityFence, tracks resolution, and enforces the 30-day Art. 12 deadline.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hummbl_governance._types import ContestationRecord
# Try to import CapabilityFence if it exists; tests might not have it loaded identically,
# but it's part of hummbl_governance.
try:
    from hummbl_governance.capability_fence import CapabilityFence
except ImportError:
    CapabilityFence = None

logger = logging.getLogger(__name__)

_RECEIPT_KEY = b"hummbl-governance-receipt-key-v1"


def _sign_contestation(contestation_id: str, status: str, timestamp_submitted: str) -> str:
    msg = f"{contestation_id}:{status}:{timestamp_submitted}".encode()
    return hmac.new(_RECEIPT_KEY, msg, hashlib.sha256).hexdigest()


class ContestationHandler:
    def __init__(
        self,
        storage_path: Path,
        capability_fence: Any | None = None,
        audit_log: Any | None = None,
    ):
        self._storage_path = storage_path
        self._capability_fence = capability_fence
        self._audit_log = audit_log
        self._lock = threading.RLock()
        self._in_memory: dict[str, ContestationRecord] = {}

        if self._storage_path:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_store()

    def submit(
        self,
        original_gate_id: str,
        data_subject_id: str,
        grounds: str,
    ) -> ContestationRecord:
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=30)
        
        contestation_id = str(uuid.uuid4())
        
        record = ContestationRecord(
            contestation_id=contestation_id,
            original_gate_id=original_gate_id,
            data_subject_id=data_subject_id,
            grounds=grounds,
            status="open",
            outcome=None,
            resolution_notes="",
            deadline_iso=deadline.strftime("%Y-%m-%dT%H:%M:%SZ"),
            timestamp_submitted=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            timestamp_resolved=None,
            resolver_id=None,
            receipt_hmac=_sign_contestation(contestation_id, "open", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        )

        with self._lock:
            self._in_memory[contestation_id] = record
            self._persist(record)

            if self._capability_fence:
                try:
                    # Scope restriction to the specific gate_id decision path
                    self._capability_fence.restrict(agent_id=original_gate_id, denied_capabilities=["execute_decision"])
                except Exception as e:
                    logger.warning(f"Failed to apply CapabilityFence for gate_id {original_gate_id}: {e}")
            else:
                logger.info(f"No CapabilityFence configured. Manual suspension required for gate_id {original_gate_id}")

        self._emit_audit("contestation_submitted", record)
        return record

    def begin_review(self, contestation_id: str, reviewer_id: str) -> ContestationRecord:
        with self._lock:
            record = self.get(contestation_id)
            if record.status in ("resolved", "withdrawn"):
                raise ValueError(f"Cannot review {record.status} contestation.")
            
            record.status = "under_review"
            record.resolver_id = reviewer_id
            record.receipt_hmac = _sign_contestation(record.contestation_id, record.status, record.timestamp_submitted)
            self._persist(record)
        
        self._emit_audit("contestation_under_review", record)
        return record

    def resolve(
        self,
        contestation_id: str,
        outcome: str,
        resolver_id: str,
        resolution_notes: str = "",
    ) -> ContestationRecord:
        if outcome not in ("upheld", "overturned", "withdrawn"):
            raise ValueError(f"Invalid outcome: {outcome}")

        with self._lock:
            record = self.get(contestation_id)
            if record.status in ("resolved", "withdrawn"):
                raise ValueError(f"Contestation {contestation_id} is already {record.status}")
                
            record.status = "resolved" if outcome != "withdrawn" else "withdrawn"
            record.outcome = outcome
            record.resolver_id = resolver_id
            record.resolution_notes = resolution_notes
            record.timestamp_resolved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            record.receipt_hmac = _sign_contestation(record.contestation_id, record.status, record.timestamp_submitted)
            
            self._persist(record)

            if outcome in ("overturned", "withdrawn") and self._capability_fence:
                try:
                    if hasattr(self._capability_fence, "unrestrict"):
                        self._capability_fence.unrestrict(agent_id=record.original_gate_id)
                    else:
                        logger.info(f"CapabilityFence lacks unrestrict method. Manual un-suspension required for gate_id {record.original_gate_id}")
                except Exception as e:
                    logger.warning(f"Failed to lift CapabilityFence for gate_id {record.original_gate_id}: {e}")

        self._emit_audit("contestation_resolved", record)
        return record

    def get(self, contestation_id: str) -> ContestationRecord:
        with self._lock:
            if contestation_id not in self._in_memory:
                raise KeyError(f"Contestation {contestation_id} not found.")
            return self._in_memory[contestation_id]

    def list_open(self) -> list[ContestationRecord]:
        with self._lock:
            return [r for r in self._in_memory.values() if r.status in ("open", "under_review")]

    def list_overdue(self) -> list[ContestationRecord]:
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._lock:
            return [
                r for r in self._in_memory.values()
                if r.status not in ("resolved", "withdrawn") and r.deadline_iso < now_iso
            ]

    def list_by_subject(self, data_subject_id: str) -> list[ContestationRecord]:
        with self._lock:
            return [r for r in self._in_memory.values() if r.data_subject_id == data_subject_id]

    def _persist(self, record: ContestationRecord) -> None:
        if not self._storage_path:
            return
        line = json.dumps(record.to_dict(), separators=(",", ":")) + "\n"
        try:
            with open(self._storage_path, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            logger.error(f"ContestationHandler store write failed: {exc}")

    def _load_store(self) -> None:
        if not self._storage_path or not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        record = ContestationRecord.from_dict(data)
                        self._in_memory[record.contestation_id] = record
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning(f"Skipping malformed contestation record: {exc}")
        except OSError as exc:
            logger.warning(f"Could not load contestation store {self._storage_path}: {exc}")

    def _emit_audit(self, event_type: str, record: ContestationRecord) -> None:
        if not self._audit_log:
            return
        try:
            self._audit_log.append(
                intent_id=record.contestation_id,
                task_id=record.original_gate_id,
                tuple_type="EVIDENCE",
                tuple_data={
                    "event_type": f"contestation.{event_type}",
                    "contestation_id": record.contestation_id,
                    "data_subject_id": record.data_subject_id,
                    "status": record.status,
                    "outcome": record.outcome,
                },
                signature=record.receipt_hmac,
            )
        except Exception as exc:
            logger.warning(f"AuditLog emit failed for contestation {record.contestation_id}: {exc}")
