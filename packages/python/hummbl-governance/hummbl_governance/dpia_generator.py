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

"""DPIA Generator (P58) -- GDPR Art. 35 / AI Act Art. 27 FRIA.

P-ID:    P58
Family:  RM-2
Layer:   Infrastructure
Legal:   GDPR Art. 35; AI Act Art. 27 (FRIA as addendum)

Assembles a GDPR Art. 35 Data Protection Impact Assessment (DPIA) document
from evidence gathered by existing hummbl-governance primitives.
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

from hummbl_governance._types import DPIADocument, DPIASection

logger = logging.getLogger(__name__)

_HMAC_KEY = b"hummbl-governance-receipt-key-v1"

_ART35_SECTION_TITLES = [
    "Systematic Description of Processing",
    "Necessity and Proportionality Assessment",
    "Risk Assessment",
    "Measures Envisaged",
]

_DEFAULT_MEASURES: list[str] = [
    "HMAC-SHA256 signed receipts",
    "Append-only audit log",
    "Capability-fenced operations",
    "Kill switch (graduated halt)",
    "Human review gate (Art. 22 compliance)",
]

_FRIA_PREAMBLE = (
    "This FRIA is generated as an addendum to the DPIA per AI Act Art. 27. "
    "It complements but does not replace the DPIA."
)

_FRIA_RIGHTS = [
    "Non-discrimination (Art. 21 EU Charter)",
    "Privacy (Art. 7 EU Charter)",
    "Data protection (Art. 8 EU Charter / GDPR)",
    "Freedom of expression and information (Art. 11 EU Charter)",
    "Access to justice and effective remedy (Art. 47 EU Charter)",
]


def _compute_hmac(dpia_id: str, generated_at: str, system_name: str) -> str:
    msg = f"{dpia_id}:{generated_at}:{system_name}"
    return hmac.new(_HMAC_KEY, msg.encode(), hashlib.sha256).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _risk_level_key(level_str: str) -> str:
    mapping = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium",
               "LOW": "low", "INFO": "info"}
    return mapping.get(level_str.upper(), "info")


class DPIAGenerator:
    """Assembles a GDPR Art. 35 DPIA from existing primitive evidence.

    Thread-safe via RLock.
    """

    BOUNDARY_DISCLAIMER: str = (
        "This DPIA template is generated from technical governance evidence. "
        "The risk assessment and necessity/proportionality assessment must be "
        "completed and signed off by the controller organisation's DPO or "
        "qualified legal team. HUMMBL is not a supervisory authority."
    )

    def __init__(
        self,
        stride_mapper: Any = None,
        failure_modes: Any = None,
        compliance_mapper: Any = None,
        review_gate_store: "str | Path | None" = None,
        governance_dir: "str | Path | None" = None,
    ) -> None:
        self._lock = threading.RLock()
        self._stride_mapper = stride_mapper
        self._failure_modes = failure_modes
        self._compliance_mapper = compliance_mapper
        self._review_gate_store: Path | None = (
            Path(review_gate_store) if review_gate_store is not None else None
        )
        self._governance_dir: Path | None = (
            Path(governance_dir) if governance_dir is not None else None
        )

    def detect_art35_triggers(self, days: int = 90) -> list[str]:
        """Detect which Art. 35(3) conditions are triggered.

        Checks the review gate JSONL store for solely_automated=True entries.

        Returns:
            List of triggered condition strings.
        """
        with self._lock:
            triggers: list[str] = []
            triggers.extend(self._check_solely_automated())
            return triggers

    def generate(
        self,
        system_name: str,
        system_description: str,
        processing_purposes: list[str],
        data_categories: list[str],
        days: int = 90,
        include_fria: bool = False,
        output_format: str = "both",
    ) -> DPIADocument:
        """Generate a DPIADocument from available evidence."""
        with self._lock:
            dpia_id = str(uuid.uuid4())
            generated_at = _now_iso()

            art35_triggers = self.detect_art35_triggers(days=days)
            risk_summary = self._build_risk_summary()

            sections = [
                self._build_section_description(
                    system_name, system_description,
                    processing_purposes, data_categories,
                ),
                self._build_section_necessity(processing_purposes, data_categories),
                self._build_section_risk_assessment(risk_summary),
                self._build_section_measures(),
            ]

            measures_summary = list(_DEFAULT_MEASURES)
            if self._compliance_mapper is not None:
                measures_summary.append("Compliance mapping (GDPR, EU AI Act)")

            fria_addendum: "str | None" = None
            if include_fria:
                fria_addendum = self._build_fria(system_description, data_categories)

            receipt_hmac = _compute_hmac(dpia_id, generated_at, system_name)

            return DPIADocument(
                dpia_id=dpia_id,
                generated_at=generated_at,
                system_name=system_name,
                art35_triggers=art35_triggers,
                sections=sections,
                fria_addendum=fria_addendum,
                risk_summary=risk_summary,
                measures_summary=measures_summary,
                boundary_disclaimer=self.BOUNDARY_DISCLAIMER,
                receipt_hmac=receipt_hmac,
            )

    def export(
        self,
        doc: DPIADocument,
        output_path: "str | Path",
        format: str = "markdown",
    ) -> None:
        """Write a DPIADocument to a file.

        Args:
            format: 'markdown' or 'json'.
        """
        output_path = Path(output_path)
        if format == "markdown":
            output_path.write_text(doc.to_markdown(), encoding="utf-8")
        elif format == "json":
            output_path.write_text(
                json.dumps(doc.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            raise ValueError(
                f"Unknown export format {format!r}. Use 'markdown' or 'json'."
            )
        logger.info("DPIA exported to %s (format=%s)", output_path, format)

    def _check_solely_automated(self) -> list[str]:
        if self._review_gate_store is None:
            return []
        try:
            path = self._review_gate_store
            found = False
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("solely_automated") is True:
                        found = True
                        break
            if found:
                return [
                    "solely_automated_decisions -- Art. 35(3)(a): automated "
                    "processing producing legal or similarly significant effects "
                    "(GDPR Art. 22) detected in review gate store."
                ]
        except FileNotFoundError:
            logger.debug(
                "Review gate store not found at %s; skipping trigger check.",
                self._review_gate_store,
            )
        return []

    def _build_section_description(
        self,
        system_name: str,
        system_description: str,
        processing_purposes: list[str],
        data_categories: list[str],
    ) -> DPIASection:
        purposes_text = (
            ", ".join(processing_purposes) if processing_purposes
            else "[TO BE COMPLETED BY DPO]"
        )
        categories_text = (
            ", ".join(data_categories) if data_categories
            else "[TO BE COMPLETED BY DPO]"
        )
        content = (
            f"**System:** {system_name}\n\n"
            f"**Description:** {system_description}\n\n"
            f"**Processing purposes:** {purposes_text}\n\n"
            f"**Personal data categories:** {categories_text}\n\n"
            "**Data flows:** [TO BE COMPLETED BY DPO]\n\n"
            "**Retention periods:** [TO BE COMPLETED BY DPO]\n\n"
            "**Legal basis:** [TO BE COMPLETED BY DPO]"
        )
        refs = ["stride_mapper", "compliance_mapper"] if self._stride_mapper else []
        return DPIASection(
            title=_ART35_SECTION_TITLES[0],
            content=content,
            evidence_refs=refs,
        )

    def _build_section_necessity(
        self,
        processing_purposes: list[str],
        data_categories: list[str],
    ) -> DPIASection:
        purposes_text = (
            ", ".join(processing_purposes) if processing_purposes
            else "[purposes not specified]"
        )
        categories_text = (
            ", ".join(data_categories) if data_categories
            else "[categories not specified]"
        )
        compliance_evidence: list[str] = []
        if self._compliance_mapper is not None:
            compliance_evidence.append("compliance_mapper (GDPR Art. 30 evidence)")
        content = (
            f"Processing for purposes [{purposes_text}] using data categories "
            f"[{categories_text}].\n\n"
            "**Necessity test:** [TO BE COMPLETED BY DPO]\n\n"
            "**Proportionality assessment:** [TO BE COMPLETED BY DPO]\n\n"
            "**Data minimisation measures implemented:**\n"
            "- Capability-fenced operations limit data access to declared scopes.\n"
            "- Delegation tokens enforce least-privilege on agent data access.\n"
            "- Audit log records all data access events with cryptographic integrity."
        )
        return DPIASection(
            title=_ART35_SECTION_TITLES[1],
            content=content,
            evidence_refs=compliance_evidence,
        )

    def _build_section_risk_assessment(self, risk_summary: dict[str, int]) -> DPIASection:
        refs: list[str] = []
        if self._stride_mapper is not None:
            refs.append("stride_mapper (STRIDE findings)")
        if self._failure_modes is not None:
            refs.append("failure_modes (FM registry)")

        summary_lines = [
            f"- {level.capitalize()}: {count}"
            for level, count in risk_summary.items()
        ]
        summary_text = "\n".join(summary_lines) if summary_lines else "- No findings"

        content = (
            "STRIDE threat model findings derived from hummbl-governance "
            "StrideMapper (where available).\n\n"
            f"**Severity breakdown:**\n{summary_text}\n\n"
            "**Residual risks and mitigations:** [TO BE COMPLETED BY DPO]\n\n"
            "**Data subject impact:** [TO BE COMPLETED BY DPO]"
        )
        return DPIASection(
            title=_ART35_SECTION_TITLES[2],
            content=content,
            evidence_refs=refs,
        )

    def _build_section_measures(self) -> DPIASection:
        measures_lines = "\n".join(f"- {m}" for m in _DEFAULT_MEASURES)
        content = (
            "The following technical and organisational measures are "
            "implemented in the hummbl-governance layer:\n\n"
            f"{measures_lines}\n\n"
            "**Additional organisational measures:** [TO BE COMPLETED BY DPO]\n\n"
            "**Review schedule:** [TO BE COMPLETED BY DPO]"
        )
        return DPIASection(
            title=_ART35_SECTION_TITLES[3],
            content=content,
            evidence_refs=list(_DEFAULT_MEASURES),
        )

    def _build_fria(self, system_description: str, data_categories: list[str]) -> str:
        categories_text = (
            ", ".join(data_categories) if data_categories else "unspecified"
        )
        special_cats = {
            "health", "biometric", "genetic", "racial", "ethnic",
            "religion", "political", "trade_union", "sexual",
        }
        has_special = any(
            any(sc in cat.lower() for sc in special_cats)
            for cat in data_categories
        )

        lines: list[str] = [
            _FRIA_PREAMBLE,
            "",
            f"**System assessed:** {system_description}",
            f"**Personal data categories in scope:** {categories_text}",
            "",
            "### Fundamental Rights Assessment (AI Act Art. 27)",
            "",
        ]

        for right in _FRIA_RIGHTS:
            if "non-discrimination" in right.lower():
                risk = (
                    "HIGH -- special-category data processed; discrimination risk elevated."
                    if has_special
                    else "MEDIUM -- automated decision-making may embed bias; fairness testing recommended."
                )
            elif "privacy" in right.lower():
                risk = (
                    "HIGH -- special-category data processed."
                    if has_special
                    else "MEDIUM -- personal data processed; data minimisation measures in place."
                )
            elif "data protection" in right.lower():
                risk = (
                    "MEDIUM -- technical controls (HMAC receipts, audit log, capability fence) address Art. 8 requirements."
                )
            elif "freedom of expression" in right.lower():
                risk = "LOW -- system does not restrict expression; output validation prevents injected content."
            elif "access to justice" in right.lower():
                risk = (
                    "MEDIUM -- human review gate ensures contestability per GDPR Art. 22; "
                    "DPO must confirm complaint mechanism is accessible."
                )
            else:
                risk = "LOW -- no specific risk identified; DPO to confirm."

            lines.append(f"**{right}**")
            lines.append(f"Risk level: {risk}")
            lines.append("")

        lines.append(
            "[TO BE COMPLETED BY DPO -- confirm FRIA findings, document "
            "mitigations for HIGH/MEDIUM rights risks, and sign off.]"
        )
        return "\n".join(lines)

    def _build_risk_summary(self) -> dict[str, int]:
        base: dict[str, int] = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
        }
        if self._stride_mapper is None:
            return base
        try:
            if hasattr(self._stride_mapper, "_last_report"):
                report = self._stride_mapper._last_report
                if report is not None and hasattr(report, "findings"):
                    for finding in report.findings:
                        key = _risk_level_key(finding.risk_level.value)
                        base[key] = base.get(key, 0) + 1
        except Exception:
            logger.debug("Could not extract findings from stride_mapper.")
        return base
