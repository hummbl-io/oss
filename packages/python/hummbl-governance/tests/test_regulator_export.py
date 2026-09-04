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

"""Tests for regulator_export module (P35 RegulatorExport).

Covers:
- Export envelope generation for all 7 formats
- D5 (NO_AUTO_PROMOTION) enforcement — empty approver_id raises
- system_identity validation
- Hash-chained integrity (export_hash verifies)
- Coverage state inference and overrides
- Summary statistics
- File export
- Boundary disclaimers per framework
- Hash chain across multiple exports
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from hummbl_governance.regulator_export import (
    BOUNDARY_DISCLAIMERS,
    REGULATOR_FORMATS,
    CoverageState,
    ExportFormat,
    Framework,
    RegulatorExport,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@dataclass
class FakeReport:
    """Minimal stand-in for ComplianceReport with the .controls and .framework attrs."""

    generated_at: str
    framework: str
    controls: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@pytest.fixture
def fake_report() -> FakeReport:
    return FakeReport(
        generated_at="2026-09-04T00:00:00Z",
        framework="EU_AI_ACT",
        controls={
            "Art.9": [
                {
                    "source": "kill_switch",
                    "artifact_ref": "receipt-abc123",
                    "timestamp": "2026-09-03T12:00:00Z",
                    "signed": True,
                }
            ],
            "Art.12": [
                {
                    "primitive": "audit_log",
                    "receipt_hash": "hash-def456",
                }
            ],
            "Art.14": [],
        },
    )


@pytest.fixture
def system_identity() -> dict[str, Any]:
    return {
        "system_name": "hummbl-governance",
        "system_version": "1.4.1",
        "provider_name": "HUMMBL, LLC",
        "intended_purpose": "AI agent governance",
        "risk_classification": "high-risk",
    }


@pytest.fixture
def exporter(tmp_path: Path) -> RegulatorExport:
    return RegulatorExport(state_dir=tmp_path)


# ---------------------------------------------------------------------------
# D5 enforcement tests
# ---------------------------------------------------------------------------


class TestD5Enforcement:
    """D5 (NO_AUTO_PROMOTION) — operator must approve regulator exports."""

    def test_empty_approver_id_raises(self, fake_report, system_identity, exporter):
        with pytest.raises(ValueError, match="approver_id is required"):
            exporter.export(
                report=fake_report,
                format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
                system_identity=system_identity,
                approver_id="",
            )

    def test_whitespace_approver_id_raises(self, fake_report, system_identity, exporter):
        with pytest.raises(ValueError, match="approver_id is required"):
            exporter.export(
                report=fake_report,
                format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
                system_identity=system_identity,
                approver_id="   ",
            )

    def test_valid_approver_id_succeeds(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="operator-001",
        )
        assert envelope.authority["operator_approval"] is True
        assert envelope.authority["approver_id"] == "operator-001"


# ---------------------------------------------------------------------------
# system_identity validation
# ---------------------------------------------------------------------------


class TestSystemIdentityValidation:
    @pytest.mark.parametrize("missing_field", ["system_name", "system_version", "provider_name"])
    def test_missing_required_field_raises(
        self, fake_report, system_identity, exporter, missing_field
    ):
        bad_identity = {k: v for k, v in system_identity.items() if k != missing_field}
        with pytest.raises(ValueError, match=f"missing required field: {missing_field}"):
            exporter.export(
                report=fake_report,
                format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
                system_identity=bad_identity,
                approver_id="operator-001",
            )

    def test_empty_required_field_raises(self, fake_report, exporter):
        with pytest.raises(ValueError, match="missing required field: system_name"):
            exporter.export(
                report=fake_report,
                format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
                system_identity={
                    "system_name": "",
                    "system_version": "1.0",
                    "provider_name": "Test",
                },
                approver_id="operator-001",
            )


# ---------------------------------------------------------------------------
# Format / framework resolution
# ---------------------------------------------------------------------------


class TestFormatResolution:
    @pytest.mark.parametrize(
        "fmt,expected_fw",
        [
            (ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV, Framework.EU_AI_ACT),
            (ExportFormat.EU_AI_ACT_DECLARATION_OF_CONFORMITY_ANNEX_V, Framework.EU_AI_ACT),
            (ExportFormat.EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI, Framework.EU_AI_ACT),
            (ExportFormat.SOC2_AUDIT_PACKET, Framework.SOC2),
            (ExportFormat.ISO_42001_AIMS_EVIDENCE, Framework.ISO_42001),
            (ExportFormat.NIST_RMF_EVIDENCE_PACKAGE, Framework.NIST_RMF),
        ],
    )
    def test_format_maps_to_framework(
        self, fake_report, system_identity, exporter, fmt, expected_fw
    ):
        envelope = exporter.export(
            report=fake_report,
            format=fmt,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert envelope.framework == expected_fw.value

    def test_string_format_slug_accepted(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format="soc2_audit_packet",
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert envelope.framework == "soc2"
        assert envelope.format == "soc2_audit_packet"

    def test_generic_json_infers_from_report(self, fake_report, system_identity, exporter):
        # fake_report.framework = "EU_AI_ACT" -> Framework.EU_AI_ACT
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.GENERIC_JSON,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert envelope.framework == "eu-ai-act"


# ---------------------------------------------------------------------------
# Integrity / hash chain
# ---------------------------------------------------------------------------


class TestIntegrity:
    def test_export_hash_verifies(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert envelope.verify_integrity() is True

    def test_tampered_envelope_fails_verification(
        self, fake_report, system_identity, exporter
    ):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        # Tamper with the evidence bundle
        envelope.evidence_bundle["controls"][0]["coverage_state"] = "not_covered"
        assert envelope.verify_integrity() is False

    def test_hash_chain_links_exports(self, fake_report, system_identity, exporter):
        env1 = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        env2 = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        # Second export's previous_export_hash should equal first's export_hash
        assert env2.integrity["previous_export_hash"] == env1.integrity["export_hash"]
        # First export has no previous
        assert env1.integrity["previous_export_hash"] is None

    def test_hash_chain_separate_per_framework(
        self, fake_report, system_identity, exporter
    ):
        eu_env = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        soc2_env = exporter.export(
            report=fake_report,
            format=ExportFormat.SOC2_AUDIT_PACKET,
            system_identity=system_identity,
            approver_id="op-1",
        )
        # Different frameworks have independent chains
        assert soc2_env.integrity["previous_export_hash"] is None
        assert eu_env.integrity["previous_export_hash"] is None


# ---------------------------------------------------------------------------
# Coverage state
# ---------------------------------------------------------------------------


class TestCoverageState:
    def test_evidence_present_infers_fulfilled(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        controls = {c["control_id"]: c for c in envelope.evidence_bundle["controls"]}
        assert controls["Art.9"]["coverage_state"] == "fulfilled"
        assert controls["Art.14"]["coverage_state"] == "not_covered"

    def test_coverage_overrides_applied(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
            coverage_overrides={"Art.9": CoverageState.PARTIAL, "Art.14": "boundary"},
        )
        controls = {c["control_id"]: c for c in envelope.evidence_bundle["controls"]}
        assert controls["Art.9"]["coverage_state"] == "partial"
        assert controls["Art.14"]["coverage_state"] == "boundary"

    def test_boundary_notes_applied(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
            boundary_notes={"Art.14": "Customer-org must configure human oversight policy."},
        )
        controls = {c["control_id"]: c for c in envelope.evidence_bundle["controls"]}
        assert controls["Art.14"]["boundary_note"] == "Customer-org must configure human oversight policy."


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


class TestSummaryStats:
    def test_summary_stats_correct(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        stats = envelope.evidence_bundle["summary_stats"]
        # fake_report has 3 controls: 2 with evidence (fulfilled), 1 empty (not_covered)
        assert stats["total_controls"] == 3
        assert stats["fulfilled"] == 2
        assert stats["not_covered"] == 1
        assert stats["partial"] == 0
        assert stats["boundary"] == 0

    def test_empty_report_populates_template_controls(self, system_identity, exporter):
        empty_report = FakeReport(
            generated_at="2026-09-04T00:00:00Z",
            framework="EU_AI_ACT",
            controls={},
        )
        envelope = exporter.export(
            report=empty_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        # Annex IV template has 8 controls
        controls = envelope.evidence_bundle["controls"]
        assert len(controls) == 8
        assert all(c["coverage_state"] == "not_covered" for c in controls)
        assert envelope.evidence_bundle["summary_stats"]["not_covered"] == 8


# ---------------------------------------------------------------------------
# Boundary disclaimers
# ---------------------------------------------------------------------------


class TestBoundaryDisclaimers:
    @pytest.mark.parametrize(
        "fmt,expected_fw",
        [
            (ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV, Framework.EU_AI_ACT),
            (ExportFormat.SOC2_AUDIT_PACKET, Framework.SOC2),
            (ExportFormat.ISO_42001_AIMS_EVIDENCE, Framework.ISO_42001),
            (ExportFormat.NIST_RMF_EVIDENCE_PACKAGE, Framework.NIST_RMF),
        ],
    )
    def test_disclaimer_present_per_framework(
        self, fake_report, system_identity, exporter, fmt, expected_fw
    ):
        envelope = exporter.export(
            report=fake_report,
            format=fmt,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert envelope.boundary_disclaimer == BOUNDARY_DISCLAIMERS[expected_fw]

    def test_eu_ai_act_disclaimer_mentions_notified_body(
        self, fake_report, system_identity, exporter
    ):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert "Notified Body" in envelope.boundary_disclaimer
        assert "Article 31" in envelope.boundary_disclaimer


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_to_json_roundtrip(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        json_str = envelope.to_json()
        parsed = json.loads(json_str)
        assert parsed["export_id"] == envelope.export_id
        assert parsed["framework"] == "eu-ai-act"
        assert parsed["format"] == "eu_ai_act_technical_file_annex_iv"
        assert parsed["schema_version"] == "1.0.0"

    def test_to_dict_returns_all_fields(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        d = envelope.to_dict()
        required_keys = {
            "schema_version",
            "export_id",
            "framework",
            "format",
            "system_identity",
            "evidence_bundle",
            "generated_at",
            "authority",
            "integrity",
            "boundary_disclaimer",
        }
        assert required_keys.issubset(d.keys())


# ---------------------------------------------------------------------------
# File export
# ---------------------------------------------------------------------------


class TestFileExport:
    def test_export_to_file_writes_json(self, fake_report, system_identity, exporter, tmp_path):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        out_path = exporter.export_to_file(envelope, output_dir=tmp_path / "exports")
        assert out_path.exists()
        assert out_path.suffix == ".json"
        assert envelope.framework in out_path.name

        # File content is valid JSON matching the envelope
        content = out_path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert parsed["export_id"] == envelope.export_id

    def test_export_to_file_default_dir(self, fake_report, system_identity, tmp_path):
        exporter = RegulatorExport(state_dir=tmp_path / "default_exports")
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.SOC2_AUDIT_PACKET,
            system_identity=system_identity,
            approver_id="op-1",
        )
        out_path = exporter.export_to_file(envelope)
        assert out_path.exists()
        assert (tmp_path / "default_exports").exists()


# ---------------------------------------------------------------------------
# Evidence entry normalization
# ---------------------------------------------------------------------------


class TestEvidenceNormalization:
    def test_evidence_with_source_and_artifact_ref(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        controls = {c["control_id"]: c for c in envelope.evidence_bundle["controls"]}
        art9_evidence = controls["Art.9"]["evidence"][0]
        assert art9_evidence["source"] == "kill_switch"
        assert art9_evidence["artifact_ref"] == "receipt-abc123"
        assert art9_evidence["signed"] is True

    def test_evidence_fallback_fields(self, fake_report, system_identity, exporter):
        """Evidence with 'primitive' and 'receipt_hash' instead of source/artifact_ref."""
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        controls = {c["control_id"]: c for c in envelope.evidence_bundle["controls"]}
        art12_evidence = controls["Art.12"]["evidence"][0]
        assert art12_evidence["source"] == "audit_log"
        assert art12_evidence["artifact_ref"] == "hash-def456"


# ---------------------------------------------------------------------------
# GPAI format (GAP-E4 partial close)
# ---------------------------------------------------------------------------


class TestGPAIFormat:
    def test_gpai_format_has_correct_control_refs(self, system_identity, exporter):
        empty_report = FakeReport(
            generated_at="2026-09-04T00:00:00Z",
            framework="EU_AI_ACT",
            controls={},
        )
        envelope = exporter.export(
            report=empty_report,
            format=ExportFormat.EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI,
            system_identity=system_identity,
            approver_id="op-1",
        )
        control_ids = {c["control_id"] for c in envelope.evidence_bundle["controls"]}
        assert "Art.51" in control_ids
        assert "Art.52" in control_ids
        assert "Art.53" in control_ids
        assert "Art.55" in control_ids

    def test_gpai_disclaimer_present(self, system_identity, exporter):
        empty_report = FakeReport(
            generated_at="2026-09-04T00:00:00Z",
            framework="EU_AI_ACT",
            controls={},
        )
        envelope = exporter.export(
            report=empty_report,
            format=ExportFormat.EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI,
            system_identity=system_identity,
            approver_id="op-1",
        )
        # GPAI uses EU_AI_ACT framework disclaimer
        assert "Notified Body" in envelope.boundary_disclaimer


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------


class TestRegistryCompleteness:
    def test_all_formats_have_framework_mapping(self):
        for fmt in ExportFormat:
            assert fmt in REGULATOR_FORMATS, f"Format {fmt} missing from REGULATOR_FORMATS"

    def test_all_frameworks_have_disclaimers(self):
        for fw in Framework:
            assert fw in BOUNDARY_DISCLAIMERS, f"Framework {fw} missing disclaimer"

    def test_export_id_is_hex_and_16_chars(self, fake_report, system_identity, exporter):
        envelope = exporter.export(
            report=fake_report,
            format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
            system_identity=system_identity,
            approver_id="op-1",
        )
        assert len(envelope.export_id) == 16
        int(envelope.export_id, 16)  # raises if not hex
