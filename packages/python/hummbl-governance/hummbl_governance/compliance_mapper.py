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

"""Compliance Mapper -- Map governance traces to common security and AI controls.

This module parses append-only governance bus JSONL files and extracts
cryptographic evidence to satisfy specific regulatory controls.

SOC2 Controls Mapped:
- CC6.1: Logical Access Security (mapped to DCT tuples)
- CC7.2: Monitoring and Logging (mapped to governance bus integrity)
- CC6.3: Identity & Authentication (mapped to subject/issuer in DCTs)

GDPR Articles Mapped:
- Article 30: Records of Processing (mapped to DCTX/CONTRACT/ATTEST tuples)
- Article 32: Security of Processing (mapped to signed entries)

OWASP Top 10 for Agentic Applications (ASI01-ASI10) Mapped:
- ASI01: Agent Goal Hijack (mapped to INTENT tuples)
- ASI03: Identity & Privilege Abuse (mapped to DCT tuples)
- ASI04: Supply Chain Vulnerabilities (mapped to signed entries)
- ASI07: Insecure Inter-Agent Communication (mapped to DCTX + signed entries)
- ASI08: Cascading Failures (mapped to CIRCUIT_BREAKER/KILLSWITCH tuples)

NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE) Mapped:
- GOVERN 1.1: AI risk management policies (INTENT tuples prove stated objectives)
- GOVERN 1.7: Processes for risk identification (CIRCUIT_BREAKER/KILLSWITCH events)
- MAP 1.1: Organizational context (CONTRACT/DCTX tuples)
- MAP 2.2: Scientific basis for risk assessment (ATTEST/EVIDENCE tuples)
- MEASURE 2.5: Trustworthiness evaluations (signed governance entries)
- MEASURE 2.8: Impact metrics logged (COST_GOVERNOR events)
- MANAGE 1.3: Response plans executed (KILLSWITCH events)
- MANAGE 2.4: Risk treatment applied (CIRCUIT_BREAKER state transitions)

EU AI Act Articles Mapped (High-Risk AI per Annex III):
- Art.9: Risk management system (KILLSWITCH + CIRCUIT_BREAKER evidence)
- Art.10: Data and data governance (ATTEST/EVIDENCE tuples)
- Art.12: Record-keeping and logging (all signed governance entries)
- Art.13: Transparency and information provision (INTENT tuples)
- Art.14: Human oversight (KILLSWITCH tuples with human-initiated state)
- Art.17: Quality management system (DCTX delegation chain integrity)

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComplianceReport:
    """A structured compliance report containing evidence for multiple controls."""

    generated_at: str
    framework: str
    controls: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize report to JSON."""
        return json.dumps(
            {
                "generated_at": self.generated_at,
                "framework": self.framework,
                "controls": self.controls,
            },
            indent=2,
            sort_keys=True,
        )


class ComplianceMapper:
    """Maps governance entries to regulatory controls."""

    def __init__(self, governance_dir: Path | str | None = None):
        if governance_dir is None:
            self.governance_dir = Path("governance")
        else:
            self.governance_dir = Path(governance_dir)

    def _parse_line(self, line: str) -> dict[str, Any] | None:
        """Safely parse a single JSONL line."""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse governance line: %s", line[:100])
            return None

    def _collect_files(self, days: int) -> list[Path]:
        """Collect governance JSONL files within the date window."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        files = sorted(self.governance_dir.glob("governance-*.jsonl"), reverse=True)
        result = []

        for file_path in files:
            try:
                file_date_str = file_path.stem.split("governance-")[-1]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if file_date < cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
                    continue
            except (ValueError, IndexError):
                continue
            result.append(file_path)

        return result

    def _read_entries(self, files: list[Path]) -> list[dict[str, Any]]:
        """Read and parse all entries from governance files."""
        entries: list[dict[str, Any]] = []
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = self._parse_line(line)
                    if entry:
                        entries.append(entry)
        return entries

    @staticmethod
    def _base_evidence(entry: dict[str, Any]) -> dict[str, Any]:
        """Extract common evidence fields from an entry."""
        return {
            "entry_id": entry.get("entry_id"),
            "timestamp": entry.get("timestamp"),
            "task_id": entry.get("task_id"),
            "intent_id": entry.get("intent_id"),
            "signature": entry.get("signature"),
        }

    def generate_soc2_report(self, days: int = 7) -> ComplianceReport:
        """Generate a SOC2 compliance report from recent governance traces."""
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="SOC2",
        )

        report.controls["CC6.1"] = []  # Logical Access
        report.controls["CC7.2"] = []  # Monitoring
        report.controls["CC6.3"] = []  # Identity

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # CC7.2: Monitoring and Logging -- signed entries prove monitoring
            if entry.get("signature"):
                report.controls["CC7.2"].append(evidence)

            # CC6.1 & CC6.3: Logical Access and Identity
            if tuple_type == "DCT":
                access_evidence = evidence.copy()
                access_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "resources": tuple_data.get("resource_selectors"),
                    "ops": tuple_data.get("ops_allowed"),
                })
                report.controls["CC6.1"].append(access_evidence)

                identity_evidence = evidence.copy()
                identity_evidence.update({
                    "subject": tuple_data.get("subject"),
                    "issuer": tuple_data.get("issuer"),
                })
                report.controls["CC6.3"].append(identity_evidence)

        return report

    def generate_gdpr_report(self, days: int = 30) -> ComplianceReport:
        """Generate a GDPR compliance report from recent governance traces.

        Maps governance entries to Articles 5, 6, 25, 28, 30, and 32.
        These are the articles with direct technical evidence addressable
        by code-level governance primitives.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="GDPR",
        )

        report.controls["Art.5"] = []   # Principles — lawfulness, fairness, transparency
        report.controls["Art.6"] = []   # Lawfulness of processing
        report.controls["Art.25"] = []  # Data protection by design and by default
        report.controls["Art.28"] = []  # Processor obligations
        report.controls["Art.30"] = []  # Records of Processing
        report.controls["Art.32"] = []  # Security of Processing

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # Art.5: Principles — INTENT captures purpose (transparency, purpose limitation)
            if tuple_type == "INTENT":
                princ_evidence = evidence.copy()
                princ_evidence.update({
                    "objective": tuple_data.get("objective"),
                    "agent": tuple_data.get("agent"),
                })
                report.controls["Art.5"].append(princ_evidence)

            # Art.6: Lawfulness — CONTRACT tuples prove consent/contract/legitimate interest basis
            if tuple_type == "CONTRACT":
                law_evidence = evidence.copy()
                law_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "operations": tuple_data.get("operations"),
                })
                report.controls["Art.6"].append(law_evidence)

            # Art.25: Data protection by design — DCT ops_allowed + CapabilityFence restrict scope
            if tuple_type == "DCT":
                design_evidence = evidence.copy()
                design_evidence.update({
                    "ops_allowed": tuple_data.get("ops_allowed"),
                    "resources": tuple_data.get("resource_selectors"),
                })
                report.controls["Art.25"].append(design_evidence)
            if tuple_type == "CAPABILITY_FENCE":
                design_evidence = evidence.copy()
                design_evidence["action"] = tuple_data.get("action")
                report.controls["Art.25"].append(design_evidence)

            # Art.28: Processor obligations — DCTX delegation chains prove processor binding
            if tuple_type == "DCTX":
                proc_evidence = evidence.copy()
                proc_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                })
                report.controls["Art.28"].append(proc_evidence)

            # Art.30: Records of Processing
            if tuple_type in ("DCTX", "CONTRACT", "ATTEST", "EVIDENCE"):
                processing_evidence = evidence.copy()
                processing_evidence.update({
                    "tuple_type": tuple_type,
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["Art.30"].append(processing_evidence)

            # Art.32: Security of Processing (signed entries prove integrity)
            if entry.get("signature"):
                security_evidence = evidence.copy()
                security_evidence["tuple_type"] = tuple_type
                report.controls["Art.32"].append(security_evidence)

        return report

    def generate_owasp_report(self, days: int = 7) -> ComplianceReport:
        """Generate an OWASP Agentic Top 10 compliance report from governance traces.

        Maps governance entries to OWASP ASI01-ASI10 controls. Controls that
        lack runtime governance traces (ASI02, ASI05, ASI06, ASI09, ASI10) are
        initialized empty -- they are evidenced by code audit, not runtime logs.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="OWASP_AGENTIC",
        )

        # Controls with governance-trace evidence
        report.controls["ASI01"] = []  # Agent Goal Hijack (INTENT tuples)
        report.controls["ASI03"] = []  # Identity & Privilege Abuse (DCT tuples)
        report.controls["ASI04"] = []  # Supply Chain (signed entries)
        report.controls["ASI07"] = []  # Insecure Inter-Agent Comms (DCTX + signed)
        report.controls["ASI08"] = []  # Cascading Failures (CIRCUIT_BREAKER/KILLSWITCH)

        # Controls evidenced by code audit (no runtime trace)
        report.controls["ASI02"] = []  # Tool Misuse
        report.controls["ASI05"] = []  # Unexpected Code Execution
        report.controls["ASI06"] = []  # Memory & Context Poisoning
        report.controls["ASI09"] = []  # Human-Agent Trust Exploitation
        report.controls["ASI10"] = []  # Rogue Agents

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # ASI01: Agent Goal Hijack -- INTENT tuples prove lifecycle
            if tuple_type == "INTENT":
                intent_evidence = evidence.copy()
                intent_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "objective": tuple_data.get("objective"),
                    "phase": tuple_data.get("phase"),
                })
                report.controls["ASI01"].append(intent_evidence)

            # ASI03: Identity & Privilege Abuse -- DCT tuples prove delegation
            if tuple_type == "DCT":
                dct_evidence = evidence.copy()
                dct_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "resources": tuple_data.get("resource_selectors"),
                    "ops": tuple_data.get("ops_allowed"),
                })
                report.controls["ASI03"].append(dct_evidence)

            # ASI04: Supply Chain -- signed entries prove integrity
            if entry.get("signature"):
                report.controls["ASI04"].append(evidence)

            # ASI07: Inter-Agent Comms -- DCTX entries
            if tuple_type == "DCTX":
                dctx_evidence = evidence.copy()
                dctx_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["ASI07"].append(dctx_evidence)

            # ASI08: Cascading Failures -- circuit breaker + kill switch
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                failure_evidence = evidence.copy()
                failure_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                    "adapter": tuple_data.get("adapter"),
                })
                report.controls["ASI08"].append(failure_evidence)

        return report


    def generate_nist_rmf_report(self, days: int = 30) -> ComplianceReport:
        """Generate a NIST AI Risk Management Framework compliance report.

        Maps governance traces to the four NIST AI RMF core functions:
        GOVERN, MAP, MEASURE, and MANAGE. Controls with no runtime evidence
        (e.g. policy documents) are initialised empty — they are satisfied by
        artefact review, not runtime logs.

        Reference: NIST AI 100-1 (2023), AI RMF Playbook.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="NIST_AI_RMF",
        )

        # GOVERN function
        report.controls["GOVERN-1.1"] = []   # AI risk policies — INTENT tuples prove declared objectives
        report.controls["GOVERN-1.7"] = []   # Risk identification processes — CB/KS events
        # MAP function
        report.controls["MAP-1.1"] = []      # Organisational context — CONTRACT/DCTX
        report.controls["MAP-2.2"] = []      # Risk assessment basis — ATTEST/EVIDENCE
        # MEASURE function
        report.controls["MEASURE-2.5"] = []  # Trustworthiness evaluations — signed entries
        report.controls["MEASURE-2.8"] = []  # Impact metrics — COST_GOVERNOR events
        # MANAGE function
        report.controls["MANAGE-1.3"] = []   # Response plans executed — KILLSWITCH events
        report.controls["MANAGE-2.4"] = []   # Risk treatment applied — CB state transitions

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # GOVERN-1.1: Policies — INTENT tuples capture declared objectives
            if tuple_type == "INTENT":
                intent_evidence = evidence.copy()
                intent_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "objective": tuple_data.get("objective"),
                    "phase": tuple_data.get("phase"),
                })
                report.controls["GOVERN-1.1"].append(intent_evidence)

            # GOVERN-1.7 & MANAGE-1.3 & MANAGE-2.4: Risk/response — CB + KS events
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                failure_evidence = evidence.copy()
                failure_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                    "adapter": tuple_data.get("adapter"),
                })
                report.controls["GOVERN-1.7"].append(failure_evidence)
                if tuple_type == "KILLSWITCH":
                    report.controls["MANAGE-1.3"].append(failure_evidence)
                if tuple_type == "CIRCUIT_BREAKER":
                    report.controls["MANAGE-2.4"].append(failure_evidence)

            # MAP-1.1: Organisational context — delegation and contract records
            if tuple_type in ("CONTRACT", "DCTX", "DCT"):
                context_evidence = evidence.copy()
                context_evidence.update({
                    "tuple_type": tuple_type,
                    "delegator": tuple_data.get("delegator") or tuple_data.get("issuer"),
                    "delegatee": tuple_data.get("delegatee") or tuple_data.get("subject"),
                })
                report.controls["MAP-1.1"].append(context_evidence)

            # MAP-2.2: Risk assessment basis — attested evidence entries
            if tuple_type in ("ATTEST", "EVIDENCE"):
                attest_evidence = evidence.copy()
                attest_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["MAP-2.2"].append(attest_evidence)

            # MEASURE-2.5: Trustworthiness — any signed entry proves integrity
            if entry.get("signature"):
                signed_evidence = evidence.copy()
                signed_evidence["tuple_type"] = tuple_type
                report.controls["MEASURE-2.5"].append(signed_evidence)

            # MEASURE-2.8: Impact metrics — cost governor events
            if tuple_type == "COST_GOVERNOR":
                cost_evidence = evidence.copy()
                cost_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "decision": tuple_data.get("decision"),
                    "spend": tuple_data.get("spend"),
                    "budget": tuple_data.get("budget"),
                })
                report.controls["MEASURE-2.8"].append(cost_evidence)

        return report

    def generate_eu_ai_act_report(self, days: int = 30) -> ComplianceReport:
        """Generate an EU AI Act compliance report (High-Risk AI, Annex III).

        Maps governance traces to Articles 9, 10, 11, 12, 13, 14, 15, 16, 17, and 19.
        These are the core operational obligations for high-risk AI systems.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by design documentation and human review artefacts.

        Reference: Regulation (EU) 2024/1689 (AI Act), in force 2024-08-01.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="EU_AI_ACT",
        )

        report.controls["Art.9"] = []   # Risk management system
        report.controls["Art.10"] = []  # Data and data governance
        report.controls["Art.11"] = []  # Technical documentation
        report.controls["Art.12"] = []  # Record-keeping and logging
        report.controls["Art.13"] = []  # Transparency and information provision
        report.controls["Art.14"] = []  # Human oversight
        report.controls["Art.15"] = []  # Accuracy, robustness, cybersecurity
        report.controls["Art.16"] = []  # Obligations of providers
        report.controls["Art.17"] = []  # Quality management system
        report.controls["Art.19"] = []  # Automatically generated logs

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # Art.9: Risk management system — CB and KS events show residual risk controls
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                risk_evidence = evidence.copy()
                risk_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                    "adapter": tuple_data.get("adapter"),
                })
                report.controls["Art.9"].append(risk_evidence)

            # Art.10: Data governance — attested/evidence entries
            if tuple_type in ("ATTEST", "EVIDENCE"):
                data_evidence = evidence.copy()
                data_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["Art.10"].append(data_evidence)

            # Art.12: Record-keeping — every signed entry is a tamper-evident log record
            if entry.get("signature"):
                log_evidence = evidence.copy()
                log_evidence["tuple_type"] = tuple_type
                report.controls["Art.12"].append(log_evidence)

            # Art.13: Transparency — INTENT tuples capture purpose and objectives
            if tuple_type == "INTENT":
                transparency_evidence = evidence.copy()
                transparency_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "objective": tuple_data.get("objective"),
                    "phase": tuple_data.get("phase"),
                })
                report.controls["Art.13"].append(transparency_evidence)

            # Art.14: Human oversight — KILLSWITCH with human-initiated halt state
            if tuple_type == "KILLSWITCH":
                ks_state = tuple_data.get("state", "")
                oversight_evidence = evidence.copy()
                oversight_evidence.update({
                    "state": ks_state,
                    "human_initiated": ks_state in ("HALT_ALL", "EMERGENCY"),
                })
                report.controls["Art.14"].append(oversight_evidence)

            # Art.17: Quality management — delegation chain integrity (DCTX entries)
            if tuple_type == "DCTX":
                qms_evidence = evidence.copy()
                qms_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["Art.17"].append(qms_evidence)

            # Art.11: Technical documentation — CONTRACT + ATTEST entries prove documented specs
            if tuple_type in ("CONTRACT", "ATTEST"):
                doc_evidence = evidence.copy()
                doc_evidence["tuple_type"] = tuple_type
                report.controls["Art.11"].append(doc_evidence)

            # Art.15: Accuracy, robustness, cybersecurity — CB + KS events prove residual risk
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                robust_evidence = evidence.copy()
                robust_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                })
                report.controls["Art.15"].append(robust_evidence)

            # Art.16: Obligations of providers — DCTX delegation integrity + signed entries
            if tuple_type == "DCTX" or entry.get("signature"):
                prov_evidence = evidence.copy()
                prov_evidence["tuple_type"] = tuple_type
                report.controls["Art.16"].append(prov_evidence)

            # Art.19: Automatically generated logs — ALL signed entries are auto-generated
            if entry.get("signature"):
                log_evidence = evidence.copy()
                log_evidence["tuple_type"] = tuple_type
                log_evidence["auto_generated"] = True
                report.controls["Art.19"].append(log_evidence)

        return report


    def generate_iso27001_report(self, days: int = 30) -> ComplianceReport:
        """Generate an ISO/IEC 27001:2022 compliance report from governance traces.

        Maps governance entries to Annex A organizational controls (A.5–A.9, A.12).
        These are the control families most directly addressable by code-level
        governance primitives for AI agent orchestration.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by organizational process documentation outside the library.

        Reference: ISO/IEC 27001:2022, Annex A.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="ISO27001",
        )

        report.controls["A.5"] = []   # Information security policies
        report.controls["A.6"] = []   # Organization of information security
        report.controls["A.7"] = []   # Human resource security
        report.controls["A.8"] = []   # Asset management
        report.controls["A.9"] = []   # Access control
        report.controls["A.12"] = []  # Operations security — logging

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # A.5: Information security policies — INTENT tuples prove stated objectives
            if tuple_type == "INTENT":
                pol_evidence = evidence.copy()
                pol_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "objective": tuple_data.get("objective"),
                })
                report.controls["A.5"].append(pol_evidence)

            # A.6: Organization — DCTX delegation chains show organizational structure
            if tuple_type == "DCTX":
                org_evidence = evidence.copy()
                org_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["A.6"].append(org_evidence)

            # A.7: Human resource security — identity validation and contract binding
            if tuple_type in ("DCT", "CONTRACT"):
                hr_evidence = evidence.copy()
                hr_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "ops": tuple_data.get("ops_allowed") or tuple_data.get("operations"),
                })
                report.controls["A.7"].append(hr_evidence)

            # A.8: Asset management — DCT resource ownership and ATTEST evidence
            if tuple_type in ("DCT", "ATTEST"):
                asset_evidence = evidence.copy()
                asset_evidence.update({
                    "resources": tuple_data.get("resource_selectors") or tuple_data.get("resources"),
                    "tuple_type": tuple_type,
                })
                report.controls["A.8"].append(asset_evidence)

            # A.9: Access control — DCT ops_allowed and delegation binding
            if tuple_type == "DCT":
                access_evidence = evidence.copy()
                access_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "ops_allowed": tuple_data.get("ops_allowed"),
                    "resources": tuple_data.get("resource_selectors"),
                })
                report.controls["A.9"].append(access_evidence)

            # A.12: Operations security — signed entries prove logging and monitoring
            if entry.get("signature"):
                ops_evidence = evidence.copy()
                ops_evidence["tuple_type"] = tuple_type
                report.controls["A.12"].append(ops_evidence)

        return report

    def generate_iso42001_report(self, days: int = 30) -> ComplianceReport:
        """Generate an ISO/IEC 42001:2023 compliance report from governance traces.

        Maps governance entries to Annex A reference controls (A.2–A.10).
        These are the control objectives most directly addressable by code-level
        governance primitives for AI agent orchestration.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by organizational process documentation outside the library
        (AIMS leadership, policy authorship, HR, etc.).

        Reference: ISO/IEC 42001:2023, Annex A (~38 controls across 9
        control objectives).
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="ISO42001",
        )

        report.controls["A.2"] = []   # Policies related to AI
        report.controls["A.3"] = []   # Internal organization
        report.controls["A.4"] = []   # Resources for AI systems
        report.controls["A.5"] = []   # Assessing impacts of AI systems
        report.controls["A.6"] = []   # AI system life cycle
        report.controls["A.7"] = []   # Data for AI systems
        report.controls["A.8"] = []   # Information for interested parties
        report.controls["A.9"] = []   # Use of AI systems
        report.controls["A.10"] = []  # Third-party + customer relationships

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # A.2: Policies related to AI — INTENT tuples prove stated AI objectives
            if tuple_type == "INTENT":
                pol_evidence = evidence.copy()
                pol_evidence.update({
                    "agent": tuple_data.get("agent"),
                    "objective": tuple_data.get("objective"),
                })
                report.controls["A.2"].append(pol_evidence)

            # A.3: Internal organization — DCTX delegation chains show AI roles + responsibilities
            if tuple_type == "DCTX":
                org_evidence = evidence.copy()
                org_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["A.3"].append(org_evidence)

            # A.4: Resources for AI systems — DCT resource selectors + ATTEST evidence
            if tuple_type in ("DCT", "ATTEST"):
                res_evidence = evidence.copy()
                res_evidence.update({
                    "resources": tuple_data.get("resource_selectors") or tuple_data.get("resources"),
                    "tuple_type": tuple_type,
                })
                report.controls["A.4"].append(res_evidence)

            # A.5: Assessing impacts — ATTEST tuples document impact assessments
            if tuple_type == "ATTEST":
                impact_evidence = evidence.copy()
                impact_evidence.update({
                    "subject": tuple_data.get("subject"),
                    "claim": tuple_data.get("claim"),
                })
                report.controls["A.5"].append(impact_evidence)

            # A.6: AI system life cycle — CONTRACT tuples trace lifecycle stages
            if tuple_type == "CONTRACT":
                lc_evidence = evidence.copy()
                lc_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "ops": tuple_data.get("ops_allowed") or tuple_data.get("operations"),
                })
                report.controls["A.6"].append(lc_evidence)

            # A.7: Data for AI systems — DCT with resource selectors shows data governance
            if tuple_type == "DCT":
                data_evidence = evidence.copy()
                data_evidence.update({
                    "resources": tuple_data.get("resource_selectors"),
                    "ops_allowed": tuple_data.get("ops_allowed"),
                })
                report.controls["A.7"].append(data_evidence)

            # A.8: Information for interested parties — signed entries prove documented info
            if entry.get("signature"):
                info_evidence = evidence.copy()
                info_evidence["tuple_type"] = tuple_type
                report.controls["A.8"].append(info_evidence)

            # A.9: Use of AI systems — DCT ops_allowed shows use-policy enforcement
            if tuple_type == "DCT":
                use_evidence = evidence.copy()
                use_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "ops_allowed": tuple_data.get("ops_allowed"),
                })
                report.controls["A.9"].append(use_evidence)

            # A.10: Third-party + customer relationships — DCTX delegation to external parties
            if tuple_type == "DCTX":
                tp_evidence = evidence.copy()
                tp_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                })
                report.controls["A.10"].append(tp_evidence)

        return report

    def generate_nist_csf_report(self, days: int = 30) -> ComplianceReport:
        """Generate a NIST Cybersecurity Framework 2.0 compliance report.

        Maps governance traces to the six CSF Functions: GOVERN, IDENTIFY,
        PROTECT, DETECT, RESPOND, RECOVER. Each function is mapped to the
        governance primitives that produce technical evidence for that
        function's outcomes.

        Reference: NIST CSF 2.0 (2024).
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="NIST_CSF",
        )

        report.controls["GOVERN"] = []    # Organizational context and risk strategy
        report.controls["IDENTIFY"] = []  # Asset and risk identification
        report.controls["PROTECT"] = []   # Safeguards and access controls
        report.controls["DETECT"] = []    # Continuous monitoring and anomaly detection
        report.controls["RESPOND"] = []   # Incident response
        report.controls["RECOVER"] = []   # Restoration and improvement

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # GOVERN: INTENT tuples and DCTX chains show organizational context
            if tuple_type in ("INTENT", "DCTX"):
                gov_evidence = evidence.copy()
                gov_evidence["tuple_type"] = tuple_type
                if tuple_type == "INTENT":
                    gov_evidence["objective"] = tuple_data.get("objective")
                else:
                    gov_evidence["event"] = tuple_data.get("event")
                report.controls["GOVERN"].append(gov_evidence)

            # IDENTIFY: AgentRegistry identity and DCT asset binding
            if tuple_type in ("DCT", "ATTEST"):
                id_evidence = evidence.copy()
                id_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                    "tuple_type": tuple_type,
                })
                report.controls["IDENTIFY"].append(id_evidence)

            # PROTECT: KillSwitch, CapabilityFence, DCT ops restrictions
            if tuple_type in ("KILLSWITCH", "CAPABILITY_FENCE", "DCT"):
                prot_evidence = evidence.copy()
                prot_evidence["tuple_type"] = tuple_type
                if tuple_type == "KILLSWITCH":
                    prot_evidence["state"] = tuple_data.get("state")
                elif tuple_type == "CAPABILITY_FENCE":
                    prot_evidence["action"] = tuple_data.get("action")
                else:
                    prot_evidence["ops_allowed"] = tuple_data.get("ops_allowed")
                report.controls["PROTECT"].append(prot_evidence)

            # DETECT: CircuitBreaker, HealthProbe, BehaviorMonitor events
            if tuple_type in ("CIRCUIT_BREAKER", "HEALTH_PROBE", "BEHAVIOR_MONITOR"):
                detect_evidence = evidence.copy()
                detect_evidence["tuple_type"] = tuple_type
                if tuple_type == "CIRCUIT_BREAKER":
                    detect_evidence["state"] = tuple_data.get("state")
                report.controls["DETECT"].append(detect_evidence)

            # RESPOND: KillSwitch HALT/EMERGENCY, CircuitBreaker OPEN
            if tuple_type == "KILLSWITCH" and tuple_data.get("state") in ("HALT_ALL", "EMERGENCY"):
                resp_evidence = evidence.copy()
                resp_evidence["state"] = tuple_data.get("state")
                report.controls["RESPOND"].append(resp_evidence)
            if tuple_type == "CIRCUIT_BREAKER" and tuple_data.get("state") == "OPEN":
                resp_evidence = evidence.copy()
                resp_evidence["state"] = "OPEN"
                report.controls["RESPOND"].append(resp_evidence)

            # RECOVER: CircuitBreaker HALF_OPEN, CostGovernor budget decisions
            if tuple_type == "CIRCUIT_BREAKER" and tuple_data.get("state") == "HALF_OPEN":
                rec_evidence = evidence.copy()
                rec_evidence["state"] = "HALF_OPEN"
                report.controls["RECOVER"].append(rec_evidence)
            if tuple_type == "COST_GOVERNOR":
                rec_evidence = evidence.copy()
                rec_evidence["decision"] = tuple_data.get("decision")
                report.controls["RECOVER"].append(rec_evidence)

        return report

    def generate_gpai_report(self, days: int = 30) -> ComplianceReport:
        """Generate an EU AI Act Article 53 (GPAI provider) compliance report.

        Maps governance traces to GPAI provider obligations under Article 53.
        These are the obligations that became enforceable on 2 August 2026
        with fines up to EUR 15M or 3% of worldwide turnover.

        Article 53(1) applies to all GPAI providers; Article 53(2) adds
        obligations for GPAI models with systemic risk.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by model documentation and organisational artefacts
        outside the library.

        Reference: Regulation (EU) 2024/1689, Article 53.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="EU_AI_ACT_GPAI",
        )

        # Article 53(1) -- all GPAI providers
        report.controls["Art.53.1.a"] = []  # Technical documentation
        report.controls["Art.53.1.b"] = []  # Information to downstream providers
        report.controls["Art.53.1.c"] = []  # Copyright policy compliance
        report.controls["Art.53.1.d"] = []  # Training content summary
        # Article 53(2) -- GPAI with systemic risk
        report.controls["Art.53.2.a"] = []  # Model evaluation
        report.controls["Art.53.2.b"] = []  # Risk mitigation
        report.controls["Art.53.2.c"] = []  # Adversarial testing
        report.controls["Art.53.2.d"] = []  # Incident reporting
        report.controls["Art.53.2.e"] = []  # Cybersecurity

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})
            claim_str = str(tuple_data.get("claim", "")).lower()

            # Art.53.1.a: Technical documentation -- ATTEST/EVIDENCE tuples document model specs
            if tuple_type in ("ATTEST", "EVIDENCE"):
                doc_evidence = evidence.copy()
                doc_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["Art.53.1.a"].append(doc_evidence)

            # Art.53.1.b: Downstream provider info -- DCTX delegation chains show provider-to-provider info
            if tuple_type == "DCTX":
                downstream_evidence = evidence.copy()
                downstream_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                    "event": tuple_data.get("event"),
                })
                report.controls["Art.53.1.b"].append(downstream_evidence)

            # Art.53.1.c: Copyright policy -- CONTRACT tuples prove policy compliance
            if tuple_type == "CONTRACT":
                copyright_evidence = evidence.copy()
                copyright_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "operations": tuple_data.get("operations"),
                })
                report.controls["Art.53.1.c"].append(copyright_evidence)

            # Art.53.1.d: Training content summary -- ATTEST tuples with training data evidence
            if tuple_type == "ATTEST" and "training" in claim_str:
                training_evidence = evidence.copy()
                training_evidence.update({
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["Art.53.1.d"].append(training_evidence)

            # Art.53.2.a: Model evaluation -- ATTEST/EVIDENCE tuples with evaluation results
            if tuple_type in ("ATTEST", "EVIDENCE") and tuple_data.get("outcome"):
                eval_evidence = evidence.copy()
                eval_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["Art.53.2.a"].append(eval_evidence)

            # Art.53.2.b: Risk mitigation -- CIRCUIT_BREAKER/KILLSWITCH events
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                risk_evidence = evidence.copy()
                risk_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                })
                report.controls["Art.53.2.b"].append(risk_evidence)

            # Art.53.2.c: Adversarial testing -- ATTEST tuples with adversarial test evidence
            if tuple_type == "ATTEST" and "adversarial" in claim_str:
                adv_evidence = evidence.copy()
                adv_evidence.update({
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["Art.53.2.c"].append(adv_evidence)

            # Art.53.2.d: Incident reporting -- KILLSWITCH events (incident response)
            if tuple_type == "KILLSWITCH":
                incident_evidence = evidence.copy()
                incident_evidence.update({
                    "state": tuple_data.get("state"),
                    "adapter": tuple_data.get("adapter"),
                })
                report.controls["Art.53.2.d"].append(incident_evidence)

            # Art.53.2.e: Cybersecurity -- signed entries prove integrity
            if entry.get("signature"):
                cyber_evidence = evidence.copy()
                cyber_evidence["tuple_type"] = tuple_type
                report.controls["Art.53.2.e"].append(cyber_evidence)

        return report

    def generate_cosais_report(self, days: int = 30) -> ComplianceReport:
        """Generate a NIST COSAiS (Control Overlays for Securing AI Systems) report.

        Maps governance traces to SP 800-53 control overlays for AI systems.
        COSAiS applies NIST SP 800-53 security controls to AI system
        deployment contexts (predictive AI and generative AI).

        Controls with no runtime evidence are initialised empty; they are
        satisfied by organisational process documentation outside the library.

        Reference: NIST COSAiS (Control Overlays for Securing AI Systems),
        emerging drafts applying SP 800-53 to AI systems.
        """
        now = datetime.now(timezone.utc)

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="NIST_COSAIS",
        )

        # SP 800-53 control families applied to AI systems
        report.controls["AC-2"] = []   # Account management -- DCT identity binding
        report.controls["AC-3"] = []   # Access enforcement -- DCT ops_allowed
        report.controls["AU-2"] = []   # Audit events -- signed entries
        report.controls["AU-6"] = []   # Audit review -- CB/HEALTH_PROBE events
        report.controls["AU-12"] = []  # Audit record generation -- signed entries
        report.controls["CM-2"] = []   # Baseline configuration -- CONTRACT tuples
        report.controls["IA-2"] = []   # Identification and authentication -- DCT identity
        report.controls["RA-3"] = []   # Risk assessment -- CB/KS
        report.controls["RA-5"] = []   # Vulnerability monitoring -- HEALTH_PROBE/ATTEST
        report.controls["SA-9"] = []   # External system services -- DCTX delegation
        report.controls["SC-8"] = []   # Transmission confidentiality -- signed entries
        report.controls["SI-2"] = []   # Flaw remediation -- CB state transitions
        report.controls["SI-7"] = []   # Software integrity -- signed entries
        report.controls["SI-10"] = []  # Information input validation -- ATTEST/EVIDENCE

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            evidence = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})

            # AC-2 & IA-2: Account management + Identification -- DCT identity binding
            if tuple_type == "DCT":
                identity_evidence = evidence.copy()
                identity_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "subject": tuple_data.get("subject"),
                })
                report.controls["AC-2"].append(identity_evidence)
                report.controls["IA-2"].append(identity_evidence.copy())

            # AC-3: Access enforcement -- DCT ops_allowed restrictions
            if tuple_type == "DCT":
                ac3_evidence = evidence.copy()
                ac3_evidence.update({
                    "ops_allowed": tuple_data.get("ops_allowed"),
                    "resources": tuple_data.get("resource_selectors"),
                })
                report.controls["AC-3"].append(ac3_evidence)

            # AU-2 & AU-12: Audit events and record generation -- signed entries
            if entry.get("signature"):
                audit_evidence = evidence.copy()
                audit_evidence["tuple_type"] = tuple_type
                report.controls["AU-2"].append(audit_evidence)
                report.controls["AU-12"].append(audit_evidence.copy())

            # AU-6: Audit review -- CB/HEALTH_PROBE/BEHAVIOR_MONITOR events
            if tuple_type in ("CIRCUIT_BREAKER", "HEALTH_PROBE", "BEHAVIOR_MONITOR"):
                review_evidence = evidence.copy()
                review_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                })
                report.controls["AU-6"].append(review_evidence)

            # CM-2: Baseline configuration -- CONTRACT tuples
            if tuple_type == "CONTRACT":
                cm_evidence = evidence.copy()
                cm_evidence.update({
                    "issuer": tuple_data.get("issuer"),
                    "operations": tuple_data.get("operations"),
                })
                report.controls["CM-2"].append(cm_evidence)

            # RA-3: Risk assessment -- CB/KS
            if tuple_type in ("CIRCUIT_BREAKER", "KILLSWITCH"):
                ra_evidence = evidence.copy()
                ra_evidence.update({
                    "tuple_type": tuple_type,
                    "state": tuple_data.get("state"),
                })
                report.controls["RA-3"].append(ra_evidence)

            # RA-5: Vulnerability monitoring -- HEALTH_PROBE/ATTEST/EVIDENCE
            if tuple_type in ("HEALTH_PROBE", "ATTEST", "EVIDENCE"):
                vuln_evidence = evidence.copy()
                vuln_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["RA-5"].append(vuln_evidence)

            # SA-9: External system services -- DCTX delegation
            if tuple_type == "DCTX":
                sa_evidence = evidence.copy()
                sa_evidence.update({
                    "delegator": tuple_data.get("delegator"),
                    "delegatee": tuple_data.get("delegatee"),
                })
                report.controls["SA-9"].append(sa_evidence)

            # SC-8 & SI-7: Transmission confidentiality + Software integrity -- signed entries
            if entry.get("signature"):
                sc_evidence = evidence.copy()
                sc_evidence["tuple_type"] = tuple_type
                report.controls["SC-8"].append(sc_evidence)
                report.controls["SI-7"].append(sc_evidence.copy())

            # SI-2: Flaw remediation -- CB state transitions
            if tuple_type == "CIRCUIT_BREAKER":
                si2_evidence = evidence.copy()
                si2_evidence.update({
                    "state": tuple_data.get("state"),
                    "adapter": tuple_data.get("adapter"),
                })
                report.controls["SI-2"].append(si2_evidence)

            # SI-10: Information input validation -- ATTEST/EVIDENCE
            if tuple_type in ("ATTEST", "EVIDENCE"):
                si10_evidence = evidence.copy()
                si10_evidence.update({
                    "tuple_type": tuple_type,
                    "claim": tuple_data.get("claim"),
                    "outcome": tuple_data.get("outcome"),
                })
                report.controls["SI-10"].append(si10_evidence)

        return report

    def generate_crosswalk_report(self, days: int = 30) -> ComplianceReport:
        """Generate a cross-framework crosswalk report.

        Shows which governance entries satisfy controls across ALL frameworks
        simultaneously. This is the multi-framework differentiation: instead
        of N separate reports, one unified view showing crosswalk coverage.

        For each governance entry, the crosswalk shows which controls it
        satisfies in each framework. A summary shows total evidence count
        per control per framework.
        """
        now = datetime.now(timezone.utc)

        # Generate all framework reports
        framework_reports = {
            "SOC2": self.generate_soc2_report(days),
            "GDPR": self.generate_gdpr_report(days),
            "OWASP_AGENTIC": self.generate_owasp_report(days),
            "NIST_AI_RMF": self.generate_nist_rmf_report(days),
            "EU_AI_ACT": self.generate_eu_ai_act_report(days),
            "EU_AI_ACT_GPAI": self.generate_gpai_report(days),
            "ISO27001": self.generate_iso27001_report(days),
            "ISO42001": self.generate_iso42001_report(days),
            "NIST_CSF": self.generate_nist_csf_report(days),
            "NIST_COSAIS": self.generate_cosais_report(days),
        }

        # Build per-entry crosswalk: entry_id -> {framework: [control_ids]}
        crosswalk: dict[str, dict[str, list[str]]] = {}
        for framework, fw_report in framework_reports.items():
            for control_id, evidence_list in fw_report.controls.items():
                for ev in evidence_list:
                    entry_id = ev.get("entry_id")
                    if entry_id is None:
                        continue
                    if entry_id not in crosswalk:
                        crosswalk[entry_id] = {}
                    if framework not in crosswalk[entry_id]:
                        crosswalk[entry_id][framework] = []
                    if control_id not in crosswalk[entry_id][framework]:
                        crosswalk[entry_id][framework].append(control_id)

        # Build summary: per-framework control counts
        summary: list[dict[str, Any]] = []
        for framework, fw_report in framework_reports.items():
            total_controls = len(fw_report.controls)
            controls_with_evidence = sum(1 for v in fw_report.controls.values() if v)
            total_evidence = sum(len(v) for v in fw_report.controls.values())
            summary.append({
                "framework": framework,
                "total_controls": total_controls,
                "controls_with_evidence": controls_with_evidence,
                "total_evidence": total_evidence,
            })

        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework="CROSSWALK",
        )
        report.controls["entries"] = [
            {"entry_id": eid, "frameworks": fw_map}
            for eid, fw_map in sorted(crosswalk.items())
        ]
        report.controls["summary"] = summary

        return report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Map governance traces to compliance controls."
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to include in report"
    )
    parser.add_argument(
        "--framework",
        choices=["soc2", "gdpr", "owasp", "nist-rmf", "eu-ai-act", "iso27001", "iso42001", "nist-csf", "gpai", "cosais", "crosswalk"],
        default="soc2",
        help="Compliance framework",
    )
    parser.add_argument(
        "--dir", type=str, default="governance", help="Governance directory"
    )
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument(
        "--validate", type=str, metavar="MATRIX.md",
        help="Validate a coverage matrix .md file and report pass/fail per cell",
    )
    parser.add_argument(
        "--repo-root", type=str, default=".",
        help="Repository root for resolving relative evidence paths (default: CWD)",
    )
    parser.add_argument(
        "--validate-json", action="store_true",
        help="Output validation results as JSON instead of terminal table",
    )

    args = parser.parse_args(argv)

    if args.validate:
        return _validate_matrix(
            args.validate,
            repo_root=args.repo_root,
            json_output=args.validate_json,
        )

    mapper = ComplianceMapper(governance_dir=Path(args.dir))
    if args.framework == "gdpr":
        report = mapper.generate_gdpr_report(days=args.days)
    elif args.framework == "owasp":
        report = mapper.generate_owasp_report(days=args.days)
    elif args.framework == "nist-rmf":
        report = mapper.generate_nist_rmf_report(days=args.days)
    elif args.framework == "eu-ai-act":
        report = mapper.generate_eu_ai_act_report(days=args.days)
    elif args.framework == "iso27001":
        report = mapper.generate_iso27001_report(days=args.days)
    elif args.framework == "iso42001":
        report = mapper.generate_iso42001_report(days=args.days)
    elif args.framework == "nist-csf":
        report = mapper.generate_nist_csf_report(days=args.days)
    elif args.framework == "gpai":
        report = mapper.generate_gpai_report(days=args.days)
    elif args.framework == "cosais":
        report = mapper.generate_cosais_report(days=args.days)
    elif args.framework == "crosswalk":
        report = mapper.generate_crosswalk_report(days=args.days)
    else:
        report = mapper.generate_soc2_report(days=args.days)

    json_output = report.to_json()

    if args.output:
        Path(args.output).write_text(json_output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(json_output)

    return 0


# Module alias map: legacy reference paths (hummbl-governance services/ layout)
# mapped to canonical paths in the standalone hummbl-governance package.
# Origin: matrices were authored against hummbl-governance layout; primitives
# extracted to standalone package use different module names.
_MODULE_ALIASES: dict[str, str] = {
    # kill switch
    "services/kill_switch_core.py": "hummbl_governance/kill_switch.py",
    "services/kill_switch.py": "hummbl_governance/kill_switch.py",
    "kill_switch_core.py": "hummbl_governance/kill_switch.py",
    # circuit breaker
    "services/circuit_breaker.py": "hummbl_governance/circuit_breaker.py",
    # delegation
    "services/delegation_token.py": "hummbl_governance/delegation.py",
    "services/delegation_context.py": "hummbl_governance/delegation.py",
    "delegation_context.py": "hummbl_governance/delegation.py",
    "delegation_token.py": "hummbl_governance/delegation.py",
    # governance bus
    "services/governance_bus.py": "hummbl_governance/coordination_bus.py",
    "governance_bus.py": "hummbl_governance/coordination_bus.py",
    # cognition ledger
    "cognition/ledger_writer.py": "hummbl_governance/audit_log.py",
    # external state surfaces (referenced for evidence; not files in this repo)
    "_state/coordination/messages.tsv": "EXTERNAL:hummbl-governance/_state/coordination/messages.tsv",
    "_state/cognition/ledger.jsonl": "EXTERNAL:hummbl-governance/_state/cognition/ledger.jsonl",
    # services that exist as Tier-2 admission packets (NOT shipped code)
    "services/c2pa_mcp": "TIER2_ADMITTED:services/c2pa_mcp (Tier-2 packet, not shipped)",
    "services/incident_reporting": "TIER2_ADMITTED:services/incident_reporting (Tier-2 packet, not shipped)",
}


# Coverage state glyphs (from docs/coverage/README.md legend)
_STATE_FULFILLED = "\u2705"  # green check
_STATE_PARTIAL = "\U0001f7e1"  # yellow circle
_STATE_BOUNDARY = "\u26aa"  # white circle
_STATE_OUT_OF_SCOPE = "\u26d4"  # no-entry
_ALL_STATES = (_STATE_FULFILLED, _STATE_PARTIAL, _STATE_BOUNDARY, _STATE_OUT_OF_SCOPE)


def _parse_matrix_rows(text: str) -> list[dict]:
    """Parse markdown coverage-matrix data rows.

    Returns a list of dicts: {state, control_id, requirement, coverage, evidence, line_no}.
    Skips legend tables, summary/count tables, and separator rows.
    Only matrix data rows are yielded \u2014 those containing one of the
    four state glyphs in any cell.
    """
    rows: list[dict] = []
    lines = text.split("\n")
    in_legend = False
    in_summary = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_legend = False
            in_summary = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        next_line = lines[idx].strip() if idx < len(lines) else ""
        next_cells = [c.strip() for c in next_line.strip("|").split("|")]
        next_is_separator = next_line.startswith("|") and all(
            set(c) <= set("-: ") for c in next_cells if c
        )
        header_join = " ".join(cells).lower()
        if next_is_separator and "glyph" in header_join and "state" in header_join:
            in_legend = True
            continue
        lower_cells = [c.lower() for c in cells]
        first_cell = lower_cells[0] if lower_cells else ""
        has_state_count_columns = any(g in c for c in cells for g in _ALL_STATES)
        lacks_evidence_column = "evidence" not in lower_cells
        summary_first_cells = {"annex", "chapter", "section", "function", "component", "tsc"}
        if next_is_separator and (
            has_state_count_columns
            or "chapter" in header_join
            or ("section" in header_join and "title" in header_join)
            or (first_cell in summary_first_cells and lacks_evidence_column)
        ):
            in_summary = True
            continue
        # Separator row
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        if in_legend or in_summary:
            continue
        if len(cells) < 3:
            continue
        state = None
        coverage_idx = None
        for i, c in enumerate(cells):
            for g in _ALL_STATES:
                if g in c:
                    state = g
                    coverage_idx = i
                    break
            if state:
                break
        if state is None:
            continue
        requirement = cells[1] if len(cells) > 1 else ""
        coverage = cells[coverage_idx] if coverage_idx is not None else ""
        evidence = (
            cells[coverage_idx + 1]
            if coverage_idx is not None and coverage_idx + 1 < len(cells)
            else ""
        )
        rows.append({
            "state": state,
            "control_id": cells[0],
            "requirement": requirement,
            "coverage": coverage,
            "evidence": evidence,
            "line_no": idx,
        })
    return rows


def _extract_refs(cell: str) -> list[str]:
    """Extract backtick-quoted file/path references from a single cell.

    Skips generic backtick text (tuple-type identifiers like `INTENT`, `DCT`,
    inline code without path semantics). A token qualifies if it contains
    '/' or ends in a known file extension.
    """
    refs: list[str] = []
    for match in re.finditer(r"`([^`\n]+)`", cell):
        token = match.group(1).strip()
        if not token or len(token) > 200:
            continue
        if token.startswith("http"):
            continue
        has_slash = "/" in token
        has_ext = any(
            token.endswith(ext)
            for ext in (".py", ".md", ".ts", ".tsv", ".jsonl", ".json", ".yml", ".yaml", ".toml")
        )
        if has_slash or has_ext:
            refs.append(token)
    return refs


def _validate_matrix(matrix_path: str, *, repo_root: str = ".", json_output: bool = False) -> int:
    """Validate a coverage matrix .md file (row-aware).

    For each \u2705 Fulfilled row, extract evidence-cell file references and
    resolve them against the package layout (with legacy alias support).
    Reports per-row pass/fail and aggregate coverage %.

    A row is "validated" when ALL of its evidence refs resolve to an
    existing artifact OR to a documented Tier-2/EXTERNAL marker.

    Returns:
      0 \u2014 all \u2705 rows have validated evidence
      1 \u2014 some \u2705 rows have unresolved evidence (hardening needed)
      2 \u2014 matrix file not found
    """
    path = Path(matrix_path)
    if not path.exists():
        print(f"ERROR: Matrix file not found: {matrix_path}", file=sys.stderr)
        return 2

    root = Path(repo_root).resolve()
    text = path.read_text(encoding="utf-8")
    rows = _parse_matrix_rows(text)

    fulfilled_rows = [r for r in rows if r["state"] == _STATE_FULFILLED]
    partial_rows = [r for r in rows if r["state"] == _STATE_PARTIAL]
    boundary_rows = [r for r in rows if r["state"] == _STATE_BOUNDARY]
    oos_rows = [r for r in rows if r["state"] == _STATE_OUT_OF_SCOPE]

    row_results: list[dict] = []
    row_passed = 0
    row_failed = 0
    rows_without_refs = 0

    for row in fulfilled_rows:
        refs = _extract_refs(row["evidence"]) + _extract_refs(row["coverage"])
        seen: set[str] = set()
        refs = [r for r in refs if not (r in seen or seen.add(r))]
        if not refs:
            rows_without_refs += 1
            row_results.append({
                "control_id": row["control_id"],
                "line_no": row["line_no"],
                "refs": [],
                "status": "fail",
                "detail": "no evidence references found in row",
            })
            row_failed += 1
            continue
        resolutions = [_resolve_evidence(r, root) for r in refs]
        all_pass = all(res["status"] in ("pass", "tier2", "external") for res in resolutions)
        row_results.append({
            "control_id": row["control_id"],
            "line_no": row["line_no"],
            "refs": [{"ref": r, **res} for r, res in zip(refs, resolutions)],
            "status": "pass" if all_pass else "fail",
            "detail": (
                "all refs resolve"
                if all_pass
                else f"{sum(1 for r in resolutions if r['status'] == 'fail')} of {len(resolutions)} refs unresolved"
            ),
        })
        if all_pass:
            row_passed += 1
        else:
            row_failed += 1

    summary = {
        "matrix": _display_path(path, root),
        "totals": {
            "fulfilled": len(fulfilled_rows),
            "partial": len(partial_rows),
            "boundary": len(boundary_rows),
            "out_of_scope": len(oos_rows),
        },
        "fulfilled_validation": {
            "rows_passed": row_passed,
            "rows_failed": row_failed,
            "rows_without_refs": rows_without_refs,
            "coverage_pct": (
                round(100.0 * row_passed / len(fulfilled_rows), 1)
                if fulfilled_rows
                else 0.0
            ),
        },
        "rows": row_results,
    }

    if json_output:
        import json as _json
        print(_json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"Matrix: {path.name}")
        # ASCII-safe terminal output for Windows cp1252 consoles.
        # JSON output above preserves the full unicode state glyphs.
        ful_n = len(fulfilled_rows)
        par_n = len(partial_rows)
        bnd_n = len(boundary_rows)
        oos_n = len(oos_rows)
        pct = summary["fulfilled_validation"]["coverage_pct"]
        print(f"  Rows: FUL {ful_n} | PAR {par_n} | BND {bnd_n} | OOS {oos_n}")
        print(f"  FUL rows validated: {row_passed}/{ful_n} ({pct}%)")
        if rows_without_refs:
            print(f"  WARN: {rows_without_refs} FUL row(s) have NO evidence refs (hardening gap)")
        for r in row_results:
            if r["status"] == "fail":
                print(f"  [FAIL] line {r['line_no']}: {r['control_id']} - {r['detail']}")
                for sub in r["refs"]:
                    if isinstance(sub, dict) and sub.get("status") == "fail":
                        print(f"           -> {sub['ref']} (not found)")

    return 0 if row_failed == 0 else 1


def _resolve_evidence(ref: str, repo_root: Path) -> dict:
    """Resolve an evidence reference to a file path and check existence.

    Resolution order:
    1. Module alias map (legacy path -> canonical, plus TIER2/EXTERNAL markers)
    2. Direct: repo_root / ref
    3. Package: repo_root / hummbl_governance / ref
    4. Tests: repo_root / tests / ref
    5. Workflows: repo_root / .github / ref
    6. Docs: repo_root / docs / ref
    7. Failing those, .py / .md suffix tries
    """
    root = repo_root

    alias = _MODULE_ALIASES.get(ref)
    if alias is not None:
        if alias.startswith("TIER2_ADMITTED:"):
            return {
                "path": alias,
                "status": "tier2",
                "detail": "Tier-2 admitted dependency, not in shipped code",
            }
        if alias.startswith("EXTERNAL:"):
            return {"path": alias, "status": "external", "detail": "external surface (other repo)"}
        candidate = root / alias
        if candidate.exists():
            return {
                "path": _display_path(candidate, root),
                "status": "pass",
                "detail": f"resolved via alias -> {alias}",
            }
        return {
            "path": _display_path(candidate, root),
            "status": "fail",
            "detail": f"alias target missing: {alias}",
        }

    candidates = [
        root / ref,
        root / "hummbl_governance" / ref,
        root / "tests" / ref,
        root / ".github" / ref,
        root / "docs" / ref,
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"path": _display_path(candidate, root), "status": "pass", "detail": "file exists"}

    if not ref.endswith(
        (".py", ".md", ".ts", ".tsv", ".jsonl", ".json", ".yml", ".yaml", ".toml")
    ):
        for candidate in candidates:
            for ext in (".py", ".md"):
                ext_candidate = (
                    candidate.with_suffix(ext)
                    if candidate.suffix
                    else Path(str(candidate) + ext)
                )
                if ext_candidate.exists():
                    return {
                        "path": _display_path(ext_candidate, root),
                        "status": "pass",
                        "detail": f"file exists ({ext})",
                    }

    return {"path": _display_path(candidates[0], root), "status": "fail", "detail": "file not found"}


def _display_path(path: Path, repo_root: Path) -> str:
    """Return a deterministic repo-relative path for validator JSON output."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    sys.exit(main())
