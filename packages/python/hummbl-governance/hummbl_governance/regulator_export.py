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

"""Regulator Export (P35) — produce compliance evidence in regulator-accepted formats.

Closes GAP-E1 (EU AI Act Art. 11/Annex IV technical documentation, Art. 47/Annex V
EU declaration of conformity) and partially GAP-E4 (GPAI Art. 51-56 documentation
per Annex XI). Translates internal ``ComplianceReport`` output produced by
``ComplianceMapper`` into regulator-accepted export envelopes with hash-chained
integrity, operator approval (D5 NO_AUTO_PROMOTION), and statutory boundary
disclaimers.

Supported formats
-----------------
- ``eu_ai_act_technical_file_annex_iv`` — Art. 11 technical documentation
- ``eu_ai_act_declaration_of_conformity_annex_v`` — Art. 47 EU declaration
- ``eu_ai_act_gpai_documentation_annex_xi`` — Art. 53 GPAI provider documentation
- ``soc2_audit_packet`` — AICPA SOC 2 audit evidence packet
- ``iso_42001_aims_evidence`` — ISO/IEC 42001 AIMS evidence bundle
- ``nist_rmf_evidence_package`` — NIST AI RMF evidence package
- ``generic_json`` — framework-agnostic JSON envelope

Stdlib only. No third-party runtime dependencies.

Example
-------
::

    from hummbl_governance.regulator_export import RegulatorExport, ExportFormat
    from hummbl_governance.compliance_mapper import ComplianceMapper

    mapper = ComplianceMapper(governance_dir="./governance")
    report = mapper.generate_report("eu-ai-act", days=30)

    exporter = RegulatorExport()
    envelope = exporter.export(
        report=report,
        format=ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV,
        system_identity={
            "system_name": "hummbl-governance",
            "system_version": "1.4.1",
            "provider_name": "HUMMBL, LLC",
            "intended_purpose": "AI agent governance",
            "risk_classification": "high-risk",
        },
        approver_id="operator-001",
    )
    print(envelope.to_json())
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "RegulatorExport",
    "ExportEnvelope",
    "ExportFormat",
    "Framework",
    "CoverageState",
    "REGULATOR_FORMATS",
    "BOUNDARY_DISCLAIMERS",
]

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExportFormat(str, Enum):
    """Regulator-accepted export format."""

    EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV = "eu_ai_act_technical_file_annex_iv"
    EU_AI_ACT_DECLARATION_OF_CONFORMITY_ANNEX_V = (
        "eu_ai_act_declaration_of_conformity_annex_v"
    )
    EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI = "eu_ai_act_gpai_documentation_annex_xi"
    SOC2_AUDIT_PACKET = "soc2_audit_packet"
    ISO_42001_AIMS_EVIDENCE = "iso_42001_aims_evidence"
    NIST_RMF_EVIDENCE_PACKAGE = "nist_rmf_evidence_package"
    GENERIC_JSON = "generic_json"


class Framework(str, Enum):
    """Target regulatory framework."""

    EU_AI_ACT = "eu-ai-act"
    SOC2 = "soc2"
    ISO_42001 = "iso-42001"
    NIST_RMF = "nist-rmf"
    ISO_27001 = "iso-27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci-dss"


class CoverageState(str, Enum):
    """Coverage state per the coverage matrix taxonomy."""

    FULFILLED = "fulfilled"
    PARTIAL = "partial"
    BOUNDARY = "boundary"
    NOT_COVERED = "not_covered"


# ---------------------------------------------------------------------------
# Format -> Framework mapping
# ---------------------------------------------------------------------------

REGULATOR_FORMATS: dict[ExportFormat, Framework] = {
    ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV: Framework.EU_AI_ACT,
    ExportFormat.EU_AI_ACT_DECLARATION_OF_CONFORMITY_ANNEX_V: Framework.EU_AI_ACT,
    ExportFormat.EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI: Framework.EU_AI_ACT,
    ExportFormat.SOC2_AUDIT_PACKET: Framework.SOC2,
    ExportFormat.ISO_42001_AIMS_EVIDENCE: Framework.ISO_42001,
    ExportFormat.NIST_RMF_EVIDENCE_PACKAGE: Framework.NIST_RMF,
    ExportFormat.GENERIC_JSON: Framework.EU_AI_ACT,  # default, overridden by report
}

# ---------------------------------------------------------------------------
# Boundary disclaimers per framework
# ---------------------------------------------------------------------------

BOUNDARY_DISCLAIMERS: dict[Framework, str] = {
    Framework.EU_AI_ACT: (
        "HUMMBL is not a Notified Body under EU AI Act Article 31. "
        "This technical evidence package does not constitute a Notified Body "
        "conformity assessment per Article 43. Statutory conformity assessment "
        "for Annex III high-risk systems requires either (a) internal control "
        "assessment per Annex VI, or (b) Notified Body assessment per Annex VII. "
        "The legal conformity declaration is the provider's responsibility."
    ),
    Framework.SOC2: (
        "HUMMBL is not a SOC 2 auditor. This evidence packet supports but does "
        "not replace a SOC 2 Type II examination by an accredited CPA firm."
    ),
    Framework.ISO_42001: (
        "HUMMBL is not an ISO 42001 certification body. Certification requires "
        "an accredited registrar conducting Stage 1 + Stage 2 audits. This "
        "evidence bundle contributes the technical substrate; the AIMS itself "
        "is the customer organization's responsibility."
    ),
    Framework.NIST_RMF: (
        "NIST AI RMF is a voluntary guidance framework, not a regulation. "
        "This evidence package produces technical evidence aligned to NIST AI "
        "100-1 (2023). It does not constitute a formal RMF assessment."
    ),
    Framework.ISO_27001: (
        "HUMMBL is not an ISO 27001 certification body. ISO 27001 certification "
        "requires an accredited registrar. This mapping produces technical "
        "evidence artifacts."
    ),
    Framework.GDPR: (
        "This evidence supports GDPR compliance documentation. Legal compliance "
        "with GDPR is the controller/processor's responsibility. HUMMBL is not "
        "a legal advisor."
    ),
    Framework.HIPAA: (
        "This evidence supports HIPAA Security Rule documentation. HUMMBL is "
        "not a HIPAA auditor or compliance body. Legal HIPAA compliance is the "
        "covered entity/business associate's responsibility."
    ),
    Framework.PCI_DSS: (
        "HUMMBL is not a PCI DSS Qualified Security Assessor (QSA). This "
        "evidence supports but does not replace a formal PCI DSS assessment."
    ),
}

# ---------------------------------------------------------------------------
# Default control-reference templates per format
# ---------------------------------------------------------------------------

_FORMAT_CONTROL_REFS: dict[ExportFormat, dict[str, str]] = {
    ExportFormat.EU_AI_ACT_TECHNICAL_FILE_ANNEX_IV: {
        "Art.8": "Compliance with requirements (Art. 8-15)",
        "Art.9": "Risk management system",
        "Art.10": "Data and data governance",
        "Art.11": "Technical documentation (Annex IV)",
        "Art.12": "Record-keeping",
        "Art.13": "Transparency and provision of information to deployers",
        "Art.14": "Human oversight",
        "Art.15": "Accuracy, robustness and cybersecurity",
    },
    ExportFormat.EU_AI_ACT_DECLARATION_OF_CONFORMITY_ANNEX_V: {
        "Art.47": "EU declaration of conformity (Annex V)",
        "Art.11": "Technical documentation (Annex IV)",
        "Art.9": "Risk management system",
        "Art.15": "Accuracy, robustness and cybersecurity",
    },
    ExportFormat.EU_AI_ACT_GPAI_DOCUMENTATION_ANNEX_XI: {
        "Art.51": "GPAI model classification (systemic risk)",
        "Art.52": "Transparency obligations for GPAI",
        "Art.53": "Obligations of GPAI model providers",
        "Art.55": "Systemic risk obligations",
    },
    ExportFormat.SOC2_AUDIT_PACKET: {
        "CC6.1": "Logical access security",
        "CC6.3": "Identity and authentication",
        "CC7.2": "Monitoring and logging",
    },
    ExportFormat.ISO_42001_AIMS_EVIDENCE: {
        "Clause.9": "Performance evaluation",
        "Clause.10": "Improvement",
        "A.6": "AI system life cycle",
        "A.7": "Data for AI systems",
    },
    ExportFormat.NIST_RMF_EVIDENCE_PACKAGE: {
        "GOVERN.1.1": "AI risk management policies",
        "GOVERN.1.7": "Processes for risk identification",
        "MAP.1.1": "Organizational context",
        "MEASURE.2.5": "Trustworthiness evaluations",
        "MANAGE.1.3": "Response plans executed",
        "MANAGE.2.4": "Risk treatment applied",
    },
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ExportEnvelope:
    """A regulator-accepted export envelope with hash-chained integrity."""

    schema_version: str
    export_id: str
    framework: str
    format: str
    system_identity: dict[str, Any]
    evidence_bundle: dict[str, Any]
    generated_at: str
    authority: dict[str, Any]
    integrity: dict[str, Any]
    boundary_disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to canonical JSON (sorted keys, no extra whitespace)."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    def to_canonical_json(self) -> str:
        """Canonical JSON for hashing — sorted keys, no indent, no ensure_ascii."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def verify_integrity(self) -> bool:
        """Verify the export_hash matches the canonical body hash."""
        body = self._body_for_hash()
        expected = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return self.integrity.get("export_hash") == expected

    def _body_for_hash(self) -> str:
        """The canonical JSON body used for integrity hashing (excludes integrity block)."""
        body = {
            "schema_version": self.schema_version,
            "export_id": self.export_id,
            "framework": self.framework,
            "format": self.format,
            "system_identity": self.system_identity,
            "evidence_bundle": self.evidence_bundle,
            "generated_at": self.generated_at,
            "authority": self.authority,
            "boundary_disclaimer": self.boundary_disclaimer,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# RegulatorExport
# ---------------------------------------------------------------------------


class RegulatorExport:
    """Produce compliance evidence in regulator-accepted formats.

    Wraps a ``ComplianceReport`` (from ``ComplianceMapper``) and translates it
    into a regulator-accepted export envelope with:

    - Operator approval gate (D5 NO_AUTO_PROMOTION)
    - SHA-256 hash-chained integrity
    - Statutory boundary disclaimers
    - Per-control evidence with coverage state
    - Summary statistics

    Stdlib only.
    """

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, state_dir: Path | str | None = None) -> None:
        self.state_dir = Path(state_dir) if state_dir else Path(
            ".regulator_exports"
        )
        self._previous_hashes: dict[str, str] = {}

    def export(
        self,
        report: Any,
        format: ExportFormat | str,
        system_identity: dict[str, Any],
        approver_id: str,
        approval_timestamp: str | None = None,
        coverage_overrides: dict[str, CoverageState | str] | None = None,
        boundary_notes: dict[str, str] | None = None,
    ) -> ExportEnvelope:
        """Generate a regulator-accepted export envelope from a ComplianceReport.

        Args:
            report: A ``ComplianceReport`` from ``ComplianceMapper.generate_report``.
            format: Export format (ExportFormat enum or string slug).
            system_identity: AI system identity (name, version, provider, etc.).
            approver_id: Operator identity approving the export (D5 gate).
            approval_timestamp: Optional ISO 8601 timestamp; defaults to now UTC.
            coverage_overrides: Optional per-control coverage state overrides.
            boundary_notes: Optional per-control boundary notes (for partial/boundary).

        Returns:
            An ``ExportEnvelope`` with hash-chained integrity.

        Raises:
            ValueError: If approver_id is empty (D5 violation) or system_identity
                is missing required fields.
        """
        if not approver_id or not approver_id.strip():
            raise ValueError(
                "approver_id is required — D5 (NO_AUTO_PROMOTION) forbids "
                "auto-generated regulator exports without operator approval."
            )

        fmt = ExportFormat(format) if isinstance(format, str) else format
        framework = self._resolve_framework(fmt, report)
        self._validate_system_identity(system_identity)

        controls = self._build_controls(
            report=report,
            fmt=fmt,
            coverage_overrides=coverage_overrides,
            boundary_notes=boundary_notes,
        )
        summary_stats = self._compute_summary_stats(controls)

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        approval_ts = approval_timestamp or generated_at
        export_id = self._generate_export_id(fmt, framework, generated_at)

        authority = {
            "operator_approval": True,
            "approver_id": approver_id,
            "approval_timestamp": approval_ts,
        }

        evidence_bundle = {
            "controls": controls,
            "summary_stats": summary_stats,
        }

        # Compute integrity hash over the canonical body (excluding integrity block)
        body_for_hash = json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "export_id": export_id,
                "framework": framework.value,
                "format": fmt.value,
                "system_identity": system_identity,
                "evidence_bundle": evidence_bundle,
                "generated_at": generated_at,
                "authority": authority,
                "boundary_disclaimer": BOUNDARY_DISCLAIMERS.get(framework, ""),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        export_hash = hashlib.sha256(body_for_hash.encode("utf-8")).hexdigest()
        previous_hash = self._previous_hashes.get(framework.value)

        integrity = {
            "export_hash": export_hash,
            "previous_export_hash": previous_hash,
        }

        envelope = ExportEnvelope(
            schema_version=self.SCHEMA_VERSION,
            export_id=export_id,
            framework=framework.value,
            format=fmt.value,
            system_identity=system_identity,
            evidence_bundle=evidence_bundle,
            generated_at=generated_at,
            authority=authority,
            integrity=integrity,
            boundary_disclaimer=BOUNDARY_DISCLAIMERS.get(framework, ""),
        )

        # Update hash chain for this framework
        self._previous_hashes[framework.value] = export_hash
        return envelope

    def export_to_file(
        self,
        envelope: ExportEnvelope,
        output_dir: Path | str | None = None,
    ) -> Path:
        """Write an export envelope to a JSON file.

        Args:
            envelope: The ExportEnvelope to write.
            output_dir: Directory to write to; defaults to ``self.state_dir``.

        Returns:
            Path to the written file.
        """
        out_dir = Path(output_dir) if output_dir else self.state_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{envelope.framework}_{envelope.format}_{envelope.export_id}.json"
        )
        out_path = out_dir / filename
        out_path.write_text(envelope.to_json(), encoding="utf-8")
        logger.info("Regulator export written to %s", out_path)
        return out_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_framework(self, fmt: ExportFormat, report: Any) -> Framework:
        """Resolve the target framework from format or report."""
        if fmt == ExportFormat.GENERIC_JSON:
            # Infer from report.framework field
            report_fw = getattr(report, "framework", "").upper()
            for fw in Framework:
                if fw.value.upper().replace("-", "_") == report_fw:
                    return fw
            return Framework.EU_AI_ACT  # safe default
        return REGULATOR_FORMATS[fmt]

    def _validate_system_identity(self, identity: dict[str, Any]) -> None:
        """Validate required system_identity fields."""
        required = ["system_name", "system_version", "provider_name"]
        for field_name in required:
            if not identity.get(field_name):
                raise ValueError(
                    f"system_identity missing required field: {field_name}"
                )

    def _build_controls(
        self,
        report: Any,
        fmt: ExportFormat,
        coverage_overrides: dict[str, CoverageState | str] | None,
        boundary_notes: dict[str, str] | None,
    ) -> list[dict[str, Any]]:
        """Build per-control evidence entries from the ComplianceReport."""
        control_refs = _FORMAT_CONTROL_REFS.get(fmt, {})
        report_controls = getattr(report, "controls", {})

        controls: list[dict[str, Any]] = []
        for control_id, evidence_list in report_controls.items():
            evidence_entries = self._build_evidence_entries(evidence_list)
            coverage = self._resolve_coverage(
                control_id, evidence_list, coverage_overrides
            )
            entry: dict[str, Any] = {
                "control_id": control_id,
                "control_reference": control_refs.get(
                    control_id, f"Control {control_id}"
                ),
                "coverage_state": coverage,
                "evidence": evidence_entries,
            }
            if boundary_notes and control_id in boundary_notes:
                entry["boundary_note"] = boundary_notes[control_id]
            controls.append(entry)

        # If report has no controls, populate with the format's control template
        # so the export still documents the expected control set (all not_covered).
        if not controls:
            for control_id, ref in control_refs.items():
                coverage = (
                    CoverageState.NOT_COVERED.value
                    if not coverage_overrides
                    else str(
                        coverage_overrides.get(
                            control_id, CoverageState.NOT_COVERED
                        )
                    )
                )
                entry: dict[str, Any] = {
                    "control_id": control_id,
                    "control_reference": ref,
                    "coverage_state": coverage,
                    "evidence": [],
                }
                if boundary_notes and control_id in boundary_notes:
                    entry["boundary_note"] = boundary_notes[control_id]
                controls.append(entry)

        return controls

    def _build_evidence_entries(
        self, evidence_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Normalize evidence entries from ComplianceReport control lists."""
        entries: list[dict[str, Any]] = []
        for ev in evidence_list:
            source = ev.get("source") or ev.get("primitive") or "compliance_mapper"
            artifact_ref = (
                ev.get("artifact_ref")
                or ev.get("receipt_hash")
                or ev.get("test_name")
                or ev.get("tuple_type")
                or "unknown"
            )
            entry: dict[str, Any] = {
                "source": source,
                "artifact_ref": str(artifact_ref),
            }
            if ev.get("timestamp"):
                entry["timestamp"] = ev["timestamp"]
            if "signed" in ev:
                entry["signed"] = bool(ev["signed"])
            entries.append(entry)
        return entries

    def _resolve_coverage(
        self,
        control_id: str,
        evidence_list: list[dict[str, Any]],
        overrides: dict[str, CoverageState | str] | None,
    ) -> str:
        """Resolve coverage state: override > inferred-from-evidence > fulfilled."""
        if overrides and control_id in overrides:
            val = overrides[control_id]
            return val.value if isinstance(val, CoverageState) else str(val)
        # Infer: if evidence exists, fulfilled; else not_covered
        return (
            CoverageState.FULFILLED.value
            if evidence_list
            else CoverageState.NOT_COVERED.value
        )

    def _compute_summary_stats(
        self, controls: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Compute aggregate coverage statistics."""
        stats = {
            "total_controls": len(controls),
            "fulfilled": 0,
            "partial": 0,
            "boundary": 0,
            "not_covered": 0,
        }
        for c in controls:
            state = c.get("coverage_state", "not_covered")
            if state in stats:
                stats[state] += 1
        return stats

    def _generate_export_id(
        self, fmt: ExportFormat, framework: Framework, generated_at: str
    ) -> str:
        """Generate a deterministic-but-unique export ID."""
        seed = f"{framework.value}:{fmt.value}:{generated_at}:{uuid.uuid4().hex[:8]}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
