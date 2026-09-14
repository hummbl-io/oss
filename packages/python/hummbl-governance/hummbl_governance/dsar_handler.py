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

"""DSAR Handler (P55) — GDPR Art. 15 / AI Act Art. 26(11) workflow.

End-to-end Data Subject Access Request workflow. Compiles Art. 15-structured
responses from governance evidence (AuditLog, HumanReviewGate, ContestationHandler).
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

from hummbl_governance._types import DSARRecord

logger = logging.getLogger(__name__)

_RECEIPT_KEY = b"hummbl-governance-receipt-key-v1"


def _sign_dsar(dsar_id: str, status: str, timestamp_received: str) -> str:
    msg = f"{dsar_id}:{status}:{timestamp_received}".encode()
    return hmac.new(_RECEIPT_KEY, msg, hashlib.sha256).hexdigest()


class DSARHandler:
    BOUNDARY_NOTE = (
        "This export covers technical governance metadata processed by "
        "hummbl-governance primitives. Actual personal data resides in your "
        "organisation's application systems. HUMMBL is not a supervisory "
        "authority and this export does not constitute legal advice."
    )

    def __init__(
        self,
        storage_path: Path,
        audit_log: Any | None = None,
        gate_store_path: Path | None = None,
        contestation_store_path: Path | None = None,
    ):
        self._storage_path = storage_path
        self._audit_log = audit_log
        self._gate_store_path = gate_store_path
        self._contestation_store_path = contestation_store_path
        
        self._lock = threading.RLock()
        self._in_memory: dict[str, DSARRecord] = {}

        if self._storage_path:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_store()

    def receive(
        self,
        data_subject_id: str,
        requester_ref: str,
        request_notes: str = "",
    ) -> DSARRecord:
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=30)
        
        dsar_id = str(uuid.uuid4())
        
        record = DSARRecord(
            dsar_id=dsar_id,
            data_subject_id=data_subject_id,
            requester_ref=requester_ref,
            status="received",
            deadline_iso=deadline.strftime("%Y-%m-%dT%H:%M:%SZ"),
            extended=False,
            extension_reason=None,
            request_notes=request_notes,
            timestamp_received=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            timestamp_completed=None,
            response_path=None,
            receipt_hmac=_sign_dsar(dsar_id, "received", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        )

        with self._lock:
            self._in_memory[dsar_id] = record
            self._persist(record)

        return record

    def extend(self, dsar_id: str, reason: str) -> DSARRecord:
        with self._lock:
            record = self.get(dsar_id)
            if record.extended:
                raise ValueError("DSAR already extended. Only one 60-day extension is permitted.")
            if record.status in ("complete", "refused"):
                raise ValueError(f"Cannot extend {record.status} DSAR.")
            
            # Deadline is 90 days total from receipt
            received = datetime.strptime(record.timestamp_received, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            new_deadline = received + timedelta(days=90)
            
            record.deadline_iso = new_deadline.strftime("%Y-%m-%dT%H:%M:%SZ")
            record.extended = True
            record.extension_reason = reason
            record.status = "extended"
            record.receipt_hmac = _sign_dsar(record.dsar_id, record.status, record.timestamp_received)
            
            self._persist(record)
        return record

    def compile_response(
        self,
        dsar_id: str,
        output_path: Path,
        format: str = "json",
    ) -> DSARRecord:
        with self._lock:
            record = self.get(dsar_id)
            if record.status in ("complete", "refused"):
                raise ValueError(f"Cannot compile response for {record.status} DSAR.")

            data_subject_id = record.data_subject_id
            
            gate_entries = self._grep_jsonl(self._gate_store_path, data_subject_id)
            contestation_entries = self._grep_jsonl(self._contestation_store_path, data_subject_id)
            audit_entries = self._grep_audit_log(data_subject_id)

            response_data = {
                "dsar_id": dsar_id,
                "data_subject_id": data_subject_id,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "art15_disclosure": {
                    "confirmation_of_processing": True,
                    "purposes": ["governance", "agent-oversight"],
                    "categories": ["governance-metadata"],
                    "recipients": [],
                    "retention_period": "per governance.yml",
                    "rights_information": "Right to rectification, erasure, restriction, portability, objection."
                },
                "records": [
                    {"source": "audit_log", "entries": audit_entries},
                    {"source": "gate_receipts", "entries": gate_entries},
                    {"source": "contestation_records", "entries": contestation_entries}
                ],
                "boundary_note": self.BOUNDARY_NOTE
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=2)

            record.status = "in_review"
            record.response_path = str(output_path)
            record.receipt_hmac = _sign_dsar(record.dsar_id, record.status, record.timestamp_received)
            self._persist(record)
            
        return record

    def close(
        self,
        dsar_id: str,
        outcome: str,
        notes: str = "",
    ) -> DSARRecord:
        if outcome not in ("complete", "refused"):
            raise ValueError(f"outcome must be 'complete' or 'refused', got {outcome}")

        with self._lock:
            record = self.get(dsar_id)
            if record.status in ("complete", "refused"):
                raise ValueError(f"DSAR is already {record.status}")
                
            record.status = outcome
            if notes:
                record.request_notes = f"{record.request_notes}\nClosure notes: {notes}".strip()
            record.timestamp_completed = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            record.receipt_hmac = _sign_dsar(record.dsar_id, record.status, record.timestamp_received)
            self._persist(record)
            
        return record

    def get(self, dsar_id: str) -> DSARRecord:
        with self._lock:
            if dsar_id not in self._in_memory:
                raise KeyError(f"DSAR {dsar_id} not found.")
            return self._in_memory[dsar_id]

    def list_overdue(self) -> list[DSARRecord]:
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._lock:
            return [
                r for r in self._in_memory.values()
                if r.status not in ("complete", "refused") and r.deadline_iso < now_iso
            ]

    def generate_ai_act_notice(self, dsar_id: str) -> str:
        record = self.get(dsar_id)
        return (
            f"[{record.dsar_id}] You have been subject to a high-risk AI system "
            "governed by hummbl-governance. This system is subject to the EU AI Act "
            "Article 26(11) notification requirement. Please consult the "
            "accompanying documentation for more information."
        )

    def _grep_jsonl(self, path: Path | None, data_subject_id: str) -> list[dict]:
        results = []
        if path and path.exists():
            search_str = f'"data_subject_id":"{data_subject_id}"'
            # Also try with space just in case
            search_str2 = f'"data_subject_id": "{data_subject_id}"'
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        if search_str in line or search_str2 in line:
                            try:
                                results.append(json.loads(line.strip()))
                            except json.JSONDecodeError:
                                pass
            except OSError as e:
                logger.warning(f"Failed to read {path}: {e}")
        return results

    def _grep_audit_log(self, data_subject_id: str) -> list[dict]:
        results = []
        if self._audit_log:
            # We attempt to find the underlying jsonl file from AuditLog.
            # If log exposes it, we grep it.
            if hasattr(self._audit_log, "_log_dir") and self._audit_log._log_dir:
                log_dir = Path(self._audit_log._log_dir)
                for file_path in log_dir.glob("audit_*.jsonl"):
                    results.extend(self._grep_jsonl(file_path, data_subject_id))
        return results

    def _persist(self, record: DSARRecord) -> None:
        if not self._storage_path:
            return
        line = json.dumps(record.to_dict(), separators=(",", ":")) + "\n"
        try:
            with open(self._storage_path, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            logger.error(f"DSAR store write failed: {exc}")

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
                        record = DSARRecord.from_dict(data)
                        self._in_memory[record.dsar_id] = record
                    except (json.JSONDecodeError, KeyError) as exc:
                        logger.warning(f"Skipping malformed DSAR record: {exc}")
        except OSError as exc:
            logger.warning(f"Could not load DSAR store {self._storage_path}: {exc}")
