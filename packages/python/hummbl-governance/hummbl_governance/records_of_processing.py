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

"""Records of Processing (P57) -- GDPR Art. 30 record assembler.

P-ID  : P57
Family: AC-6
Layer : Infrastructure
Legal : GDPR Art. 30(1)/(2), AI Act Art. 12

Assembles an Article 30-formatted Record of Processing Activities (RoPA)
by querying existing governance primitives (AuditLog, ComplianceMapper).
This module is a **stateless assembler/formatter** -- it owns no new data
store. All inputs from primitives are optional; missing sources are
gracefully skipped and noted in ``primitive_sources``.

Thread-safety: RLock guards the generate/export methods.
Stdlib-only. Zero third-party runtime dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_governance._types import Art30Record

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HMAC_KEY = b"hummbl-governance-receipt-key-v1"

_SECURITY_MEASURES_SUMMARY = (
    "HMAC-SHA256 signed receipts, append-only audit log, "
    "capability-fenced operations, cryptographic integrity verification"
)

_VALID_ROLES = {"controller", "processor"}

# Tuple types that indicate active / non-occasional processing
_ACTIVE_TUPLE_TYPES = {"DCTX", "CONTRACT", "ATTEST", "DCT"}

# GDPR Art. 9 special-category indicator keywords (heuristic scan)
_SPECIAL_CATEGORY_KEYWORDS = {
    "health",
    "medical",
    "biometric",
    "genetic",
    "racial",
    "ethnic",
    "political",
    "religious",
    "sexual",
    "union",
    "criminal",
    "special",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _compute_hmac(record_id: str, generated_at: str, role: str, controller_name: str) -> str:
    """Compute HMAC-SHA256 over canonical record fields."""
    msg = f"{record_id}:{generated_at}:{role}:{controller_name}"
    return hmac.new(_HMAC_KEY, msg.encode("utf-8"), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class RecordsOfProcessing:
    """GDPR Art. 30 Records of Processing Activities assembler.

    Assembles a structured RoPA from technical governance evidence
    provided by AuditLog and ComplianceMapper primitives.  Both
    primitives are **optional** -- the assembler degrades gracefully
    when they are unavailable or return no data.

    Args:
        audit_log:         An ``AuditLog`` instance (optional).
        compliance_mapper: A ``ComplianceMapper`` instance (optional).
        governance_dir:    Fallback path used to instantiate an internal
                           ComplianceMapper if *compliance_mapper* is None
                           but a directory is known (optional).

    Thread-safety: All public methods are guarded by an ``RLock``.
    """

    BOUNDARY_DISCLAIMER = (
        "This record is generated from technical governance evidence. "
        "Lawful-basis determination, DPO information, and recipient details "
        "must be supplied and verified by the controller organisation. "
        "HUMMBL is not a supervisory authority and this record does not "
        "constitute a legal opinion or regulatory determination of compliance."
    )

    def __init__(
        self,
        audit_log: Any = None,
        compliance_mapper: Any = None,
        governance_dir: Any = None,
    ) -> None:
        self._audit_log = audit_log
        self._compliance_mapper = compliance_mapper
        self._governance_dir = governance_dir
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _derive_purposes_from_audit(self, days: int) -> list:
        """Heuristically derive processing purposes from AuditLog entries."""
        if self._audit_log is None:
            return []
        try:
            seen: set = set()
            for entry in self._audit_log._query(lambda _: True):
                tt = entry.tuple_type or ""
                if tt == "CONTRACT":
                    td = entry.tuple_data or {}
                    purpose = td.get("purpose") or td.get("name") or td.get("description")
                    if purpose and isinstance(purpose, str):
                        seen.add(purpose)
                elif tt == "DCTX":
                    td = entry.tuple_data or {}
                    ops = td.get("ops_allowed") or []
                    for op in ops:
                        if isinstance(op, str):
                            seen.add(op)
            return sorted(seen)
        except Exception as exc:
            logger.warning("Could not derive purposes from AuditLog: %s", exc)
            return []

    def _detect_special_categories(self, days: int) -> bool:
        """Return True if special-category data keywords appear in AuditLog."""
        if self._audit_log is None:
            return False
        try:
            for entry in self._audit_log._query(lambda _: True):
                td_str = json.dumps(entry.tuple_data or {}).lower()
                for kw in _SPECIAL_CATEGORY_KEYWORDS:
                    if kw in td_str:
                        return True
        except Exception:
            pass
        return False

    def _count_active_entries(self, days: int) -> int:
        """Count ACTIVE_TUPLE_TYPE entries in AuditLog."""
        if self._audit_log is None:
            return 0
        try:
            count = 0
            for entry in self._audit_log._query(
                lambda e: e.tuple_type in _ACTIVE_TUPLE_TYPES
            ):
                count += 1
            return count
        except Exception:
            return 0

    def _primitive_sources(
        self, audit_used: bool, mapper_used: bool
    ) -> list:
        sources = []
        if audit_used:
            sources.append("AuditLog")
        if mapper_used:
            sources.append("ComplianceMapper")
        return sources

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        role: str,
        controller_name: str,
        controller_contact: str,
        dpo_contact: str = "",
        processing_purposes: list = None,
        data_subject_categories: list = None,
        personal_data_categories: list = None,
        recipient_categories: list = None,
        third_country_transfers: list = None,
        retention_periods: dict = None,
        days: int = 90,
    ) -> Art30Record:
        """Generate an Art. 30 Record of Processing Activities.

        Args:
            role:                     ``'controller'`` or ``'processor'``.
            controller_name:          Name of the data controller.
            controller_contact:       Controller contact (name / address / email).
            dpo_contact:              Data Protection Officer contact (optional).
            processing_purposes:      Explicit list of purposes. When ``None``,
                                      derived from AuditLog if available.
            data_subject_categories:  Categories of data subjects.
            personal_data_categories: Categories of personal data processed.
            recipient_categories:     Categories of recipients.
            third_country_transfers:  Third-country transfer records (list[dict]).
            retention_periods:        Mapping of data category to retention period.
            days:                     Lookback window when querying primitives.

        Returns:
            A frozen :class:`Art30Record`.

        Raises:
            ValueError: If ``role`` is not ``'controller'`` or ``'processor'``.
        """
        if role not in _VALID_ROLES:
            raise ValueError(
                f"Invalid role {role!r}. Must be 'controller' or 'processor'."
            )

        with self._lock:
            audit_used = self._audit_log is not None
            mapper_used = self._compliance_mapper is not None

            # --- Derive processing purposes ---
            if processing_purposes is None:
                processing_purposes = self._derive_purposes_from_audit(days)

            # --- Defaults for optional lists/dicts ---
            data_subject_categories = list(data_subject_categories or [])
            personal_data_categories = list(personal_data_categories or [])
            recipient_categories = list(recipient_categories or [])
            third_country_transfers = list(third_country_transfers or [])
            retention_periods = dict(retention_periods or {})

            # --- Build record ---
            record_id = str(uuid.uuid4())
            generated_at = datetime.now(timezone.utc).isoformat().replace(
                "+00:00", "Z"
            )
            receipt_hmac = _compute_hmac(
                record_id, generated_at, role, controller_name
            )

            return Art30Record(
                record_id=record_id,
                generated_at=generated_at,
                role=role,
                controller_name=controller_name,
                controller_contact=controller_contact,
                dpo_contact=dpo_contact,
                processing_purposes=processing_purposes,
                data_subject_categories=data_subject_categories,
                personal_data_categories=personal_data_categories,
                recipient_categories=recipient_categories,
                third_country_transfers=third_country_transfers,
                retention_periods=retention_periods,
                security_measures_summary=_SECURITY_MEASURES_SUMMARY,
                primitive_sources=self._primitive_sources(audit_used, mapper_used),
                boundary_disclaimer=self.BOUNDARY_DISCLAIMER,
                receipt_hmac=receipt_hmac,
                sme_exempt=False,
            )

    def export(
        self,
        record: Art30Record,
        output_path: Any,
        format: str = "json",
    ) -> None:
        """Export an :class:`Art30Record` to a file.

        Args:
            record:      The record to export.
            output_path: Destination file path.
            format:      ``'json'`` or ``'markdown'``.

        Raises:
            ValueError: If *format* is unsupported.
        """
        with self._lock:
            output_path = Path(output_path)
            fmt = format.lower()
            if fmt == "json":
                self._export_json(record, output_path)
            elif fmt in {"markdown", "md"}:
                self._export_markdown(record, output_path)
            else:
                raise ValueError(
                    f"Unsupported export format {format!r}. Use 'json' or 'markdown'."
                )

    def _export_json(self, record: Art30Record, path: Path) -> None:
        data = {
            "record_id": record.record_id,
            "generated_at": record.generated_at,
            "role": record.role,
            "controller_name": record.controller_name,
            "controller_contact": record.controller_contact,
            "dpo_contact": record.dpo_contact,
            "processing_purposes": record.processing_purposes,
            "data_subject_categories": record.data_subject_categories,
            "personal_data_categories": record.personal_data_categories,
            "recipient_categories": record.recipient_categories,
            "third_country_transfers": record.third_country_transfers,
            "retention_periods": record.retention_periods,
            "security_measures_summary": record.security_measures_summary,
            "primitive_sources": record.primitive_sources,
            "boundary_disclaimer": record.boundary_disclaimer,
            "receipt_hmac": record.receipt_hmac,
            "sme_exempt": record.sme_exempt,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _export_markdown(self, record: Art30Record, path: Path) -> None:
        lines = [
            "# GDPR Article 30 Record of Processing Activities",
            "",
            f"> Generated: {record.generated_at}  ",
            f"> Record ID: `{record.record_id}`",
            "",
            "## Controller Information",
            "",
            "| Field | Value |",
            "| ----- | ----- |",
            f"| Role | {record.role} |",
            f"| Controller Name | {record.controller_name} |",
            f"| Controller Contact | {record.controller_contact} |",
            f"| DPO Contact | {record.dpo_contact or 'not set'} |",
            "",
            "## Processing Details",
            "",
            "| Art. 30 Field | Value |",
            "| ------------- | ----- |",
            f"| Purposes | {', '.join(record.processing_purposes) or 'not set'} |",
            f"| Data Subject Categories | {', '.join(record.data_subject_categories) or 'not set'} |",
            f"| Personal Data Categories | {', '.join(record.personal_data_categories) or 'not set'} |",
            f"| Recipient Categories | {', '.join(record.recipient_categories) or 'not set'} |",
            f"| Third Country Transfers | {len(record.third_country_transfers)} record(s) |",
            "",
            "## Retention Periods",
            "",
            "| Data Category | Retention Period |",
            "| ------------- | ---------------- |",
        ]
        if record.retention_periods:
            for cat, period in record.retention_periods.items():
                lines.append(f"| {cat} | {period} |")
        else:
            lines.append("| not set | not set |")

        lines += [
            "",
            "## Technical Safeguards",
            "",
            f"> {record.security_measures_summary}",
            "",
            "## Governance Provenance",
            "",
            "| Field | Value |",
            "| ----- | ----- |",
            f"| Primitive Sources | {', '.join(record.primitive_sources) or 'none'} |",
            f"| Receipt HMAC | `{record.receipt_hmac}` |",
            f"| SME Exempt | {record.sme_exempt} |",
            "",
            "---",
            "",
            f"*{record.boundary_disclaimer}*",
        ]

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")

    def check_sme_exemption(
        self, employee_count: int, days: int = 90
    ) -> dict:
        """Evaluate whether the organisation qualifies for the Art. 30(5) SME exemption.

        Under GDPR Art. 30(5) organisations with fewer than 250 employees
        are exempt from the record-keeping obligation *unless*:

        - They process data likely to result in a risk to data subjects, OR
        - The processing is not occasional, OR
        - Special-category data (Art. 9) or criminal-conviction data (Art. 10) is processed.

        Args:
            employee_count: Number of employees in the organisation.
            days:           Lookback window for AuditLog queries.

        Returns:
            A dict with keys:
            - ``exempt`` (bool): True if the exemption applies.
            - ``reason`` (str): Human-readable explanation.
            - ``conditions_met`` (list[str]): Blocking conditions (empty if fully exempt).
        """
        with self._lock:
            conditions_met: list = []

            under_250 = employee_count < 250
            if not under_250:
                conditions_met.append(
                    f"Organisation has {employee_count} employees (>= 250 threshold)"
                )

            has_special = self._detect_special_categories(days)
            if has_special:
                conditions_met.append(
                    "Special-category personal data detected (GDPR Art. 9)"
                )

            active_count = self._count_active_entries(days)
            is_non_occasional = active_count > 0
            if is_non_occasional:
                conditions_met.append(
                    f"Non-occasional processing detected ({active_count} active entries)"
                )

            exempt = under_250 and not has_special and not is_non_occasional

            if exempt:
                reason = (
                    f"Organisation qualifies for the Art. 30(5) SME exemption: "
                    f"fewer than 250 employees ({employee_count}), no special-category data "
                    f"detected, and no non-occasional processing evidence found."
                )
            else:
                blocking = "; ".join(conditions_met)
                reason = (
                    f"Organisation does NOT qualify for the Art. 30(5) SME exemption. "
                    f"Blocking conditions: {blocking}."
                )

            return {
                "exempt": exempt,
                "reason": reason,
                "conditions_met": conditions_met,
            }
