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

"""Tests for records_of_processing module (P57 RecordsOfProcessing).

Covers:
- generate() for controller and processor roles
- Boundary disclaimer always present
- HMAC receipt fingerprint present and non-empty
- JSON export produces valid JSON
- Markdown export writes a file
- SME exemption logic (under/over 250 employees)
- check_sme_exemption conditions_met list
- generate() with all optional args None (no primitives)
- Invalid role raises ValueError
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_governance.records_of_processing import RecordsOfProcessing
from hummbl_governance._types import Art30Record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rop(**kwargs) -> RecordsOfProcessing:
    """Return a RecordsOfProcessing with no primitives unless overridden."""
    return RecordsOfProcessing(**kwargs)


def _basic_generate(rop: RecordsOfProcessing, role: str = "controller") -> Art30Record:
    return rop.generate(
        role=role,
        controller_name="ACME Corp",
        controller_contact="privacy@acme.example",
        dpo_contact="dpo@acme.example",
        processing_purposes=["analytics", "fraud-prevention"],
        data_subject_categories=["customers"],
        personal_data_categories=["name", "email"],
        recipient_categories=["payment-processor"],
        retention_periods={"name": "2 years", "email": "2 years"},
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestRecordsOfProcessing:

    def test_generate_controller_record_has_required_fields(self):
        """Art. 30 record has all mandatory fields with correct types."""
        rop = _make_rop()
        rec = _basic_generate(rop, role="controller")

        assert isinstance(rec.record_id, str) and len(rec.record_id) > 0
        assert isinstance(rec.generated_at, str) and "T" in rec.generated_at
        assert rec.role == "controller"
        assert rec.controller_name == "ACME Corp"
        assert rec.controller_contact == "privacy@acme.example"
        assert rec.dpo_contact == "dpo@acme.example"
        assert isinstance(rec.processing_purposes, list)
        assert isinstance(rec.data_subject_categories, list)
        assert isinstance(rec.personal_data_categories, list)
        assert isinstance(rec.recipient_categories, list)
        assert isinstance(rec.third_country_transfers, list)
        assert isinstance(rec.retention_periods, dict)
        assert isinstance(rec.security_measures_summary, str)
        assert isinstance(rec.primitive_sources, list)
        assert isinstance(rec.receipt_hmac, str)
        assert isinstance(rec.sme_exempt, bool)

    def test_generate_processor_record_role_set_correctly(self):
        """Processor role is stored verbatim in the record."""
        rop = _make_rop()
        rec = _basic_generate(rop, role="processor")
        assert rec.role == "processor"

    def test_boundary_disclaimer_always_present(self):
        """Boundary disclaimer is always set to the class-level constant."""
        rop = _make_rop()
        rec = _basic_generate(rop)
        assert rec.boundary_disclaimer == RecordsOfProcessing.BOUNDARY_DISCLAIMER
        assert len(rec.boundary_disclaimer) > 50

    def test_receipt_hmac_present(self):
        """Receipt HMAC is a 64-character hex string (SHA-256)."""
        rop = _make_rop()
        rec = _basic_generate(rop)
        assert len(rec.receipt_hmac) == 64
        assert all(c in "0123456789abcdef" for c in rec.receipt_hmac)

    def test_export_json_writes_valid_json(self):
        """export(..., format='json') writes a file that is valid JSON."""
        rop = _make_rop()
        rec = _basic_generate(rop)
        tmp = tempfile.mkdtemp()
        out = Path(tmp) / "record.json"
        rop.export(rec, out, format="json")
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["record_id"] == rec.record_id
        assert data["role"] == "controller"
        assert "receipt_hmac" in data
        assert "boundary_disclaimer" in data

    def test_export_markdown_writes_file(self):
        """export(..., format='markdown') writes a non-empty markdown file."""
        rop = _make_rop()
        rec = _basic_generate(rop)
        tmp = tempfile.mkdtemp()
        out = Path(tmp) / "record.md"
        rop.export(rec, out, format="markdown")
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "GDPR Article 30" in content
        assert rec.record_id in content
        assert "HMAC" in content

    def test_sme_exempt_under_250_employees(self):
        """check_sme_exemption returns exempt=True for <250 employees with no AuditLog."""
        rop = _make_rop()
        result = rop.check_sme_exemption(employee_count=50)
        assert result["exempt"] is True
        assert "50" in result["reason"]

    def test_sme_not_exempt_over_250_employees(self):
        """check_sme_exemption returns exempt=False for >=250 employees."""
        rop = _make_rop()
        result = rop.check_sme_exemption(employee_count=500)
        assert result["exempt"] is False
        assert "500" in result["reason"] or "250" in result["reason"]

    def test_check_sme_conditions_met_list(self):
        """conditions_met is empty when exempt, non-empty when not."""
        rop = _make_rop()
        # Under 250, no AuditLog => fully exempt
        res_exempt = rop.check_sme_exemption(employee_count=10)
        assert res_exempt["conditions_met"] == []

        # Over 250 => at least one blocking condition
        res_blocked = rop.check_sme_exemption(employee_count=1000)
        assert len(res_blocked["conditions_met"]) >= 1
        assert any("1000" in c or "250" in c for c in res_blocked["conditions_met"])

    def test_generate_with_no_primitives_works(self):
        """generate() succeeds with all optional args None and no primitives."""
        rop = RecordsOfProcessing()
        rec = rop.generate(
            role="controller",
            controller_name="Minimal Corp",
            controller_contact="info@minimal.example",
        )
        assert rec.controller_name == "Minimal Corp"
        assert rec.processing_purposes == []
        assert rec.data_subject_categories == []
        assert rec.personal_data_categories == []
        assert rec.recipient_categories == []
        assert rec.third_country_transfers == []
        assert rec.retention_periods == {}
        assert rec.primitive_sources == []
        assert rec.receipt_hmac != ""

    def test_invalid_role_raises_value_error(self):
        """generate() with an invalid role raises ValueError."""
        rop = _make_rop()
        with pytest.raises(ValueError, match="Invalid role"):
            rop.generate(
                role="administrator",
                controller_name="Bad Corp",
                controller_contact="bad@corp.example",
            )
