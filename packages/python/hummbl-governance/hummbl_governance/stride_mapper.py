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

"""STRIDE Threat Mapper -- Map agent interactions to STRIDE threat categories.

Decomposes agent-to-agent and agent-to-tool interactions into the six STRIDE
threat categories, mapping each to the hummbl-governance module that mitigates it.

STRIDE categories (Shostack, 2014):
- Spoofing:                identity.py (AgentRegistry, trust tiers)
- Tampering:               audit_log.py (append-only, HMAC signatures)
- Repudiation:             audit_log.py (immutable entries, amendment chains)
- Information Disclosure:  delegation.py (least-privilege tokens, caveats)
- Denial of Service:       circuit_breaker.py, cost_governor.py, kill_switch.py
- Elevation of Privilege:  delegation.py (time-bound, caveat-constrained tokens)

Usage::

    from hummbl_governance.stride_mapper import StrideMapper, ThreatFinding

    mapper = StrideMapper()
    findings = mapper.analyze_interaction(
        source="worker-1",
        target="database",
        action="write",
        trust_boundary=True,
    )
    for f in findings:
        print(f.category, f.risk_level, f.mitigation_module)

    report = mapper.generate_report(interactions)

Stdlib-only.

Reference:
    Shostack, A. (2014). Threat Modeling: Designing for Security.
    John Wiley & Sons. ISBN: 978-1-118-80999-0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class StrideCategory(Enum):
    """The six STRIDE threat categories."""

    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


class RiskLevel(Enum):
    """Risk severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Mapping from STRIDE category to hummbl-governance mitigation modules
_MITIGATIONS: dict[StrideCategory, dict[str, str]] = {
    StrideCategory.SPOOFING: {
        "module": "identity.py",
        "class": "AgentRegistry",
        "mechanism": "Trust tiers, alias resolution, sender validation",
    },
    StrideCategory.TAMPERING: {
        "module": "audit_log.py",
        "class": "AuditLog",
        "mechanism": "Append-only JSONL, HMAC-SHA256 signatures, entry immutability",
    },
    StrideCategory.REPUDIATION: {
        "module": "audit_log.py",
        "class": "AuditLog",
        "mechanism": "Immutable entries with UUID IDs, amendment chains, HMAC signatures",
    },
    StrideCategory.INFORMATION_DISCLOSURE: {
        "module": "delegation.py",
        "class": "DelegationTokenManager",
        "mechanism": "Least-privilege tokens, resource selectors, caveat constraints",
    },
    StrideCategory.DENIAL_OF_SERVICE: {
        "module": "circuit_breaker.py + cost_governor.py + kill_switch.py",
        "class": "CircuitBreaker + CostGovernor + KillSwitch",
        "mechanism": "Fast-fail on OPEN, budget DENY on hard cap, graduated halt modes",
    },
    StrideCategory.ELEVATION_OF_PRIVILEGE: {
        "module": "delegation.py",
        "class": "DelegationTokenManager",
        "mechanism": "Time-bound tokens, HMAC signature verification, caveat enforcement",
    },
}


@dataclass(frozen=True)
class ThreatFinding:
    """A single STRIDE threat finding for an interaction."""

    category: StrideCategory
    risk_level: RiskLevel
    description: str
    mitigation_module: str
    mitigation_class: str
    mitigation_mechanism: str
    source: str
    target: str
    action: str
    trust_boundary: bool


@dataclass
class Interaction:
    """An agent-to-agent or agent-to-resource interaction to analyze."""

    source: str
    target: str
    action: str
    trust_boundary: bool = False
    authenticated: bool = False
    encrypted: bool = False
    has_delegation_token: bool = False
    has_audit_trail: bool = False
    has_rate_limit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrideReport:
    """Aggregated STRIDE analysis report."""

    generated_at: str
    interactions_analyzed: int
    findings: list[ThreatFinding]
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "generated_at": self.generated_at,
            "interactions_analyzed": self.interactions_analyzed,
            "findings_count": len(self.findings),
            "by_category": self.summary,
            "findings": [
                {
                    "category": f.category.value,
                    "risk_level": f.risk_level.value,
                    "description": f.description,
                    "mitigation_module": f.mitigation_module,
                    "source": f.source,
                    "target": f.target,
                    "action": f.action,
                    "trust_boundary": f.trust_boundary,
                }
                for f in self.findings
            ],
        }


class StrideMapper:
    """Analyzes interactions for STRIDE threats and maps to governance modules."""

    def analyze_interaction(self, interaction: Interaction) -> list[ThreatFinding]:
        """Analyze a single interaction for all six STRIDE threat categories.

        Returns findings only for categories where the interaction has
        insufficient mitigation.
        """
        findings: list[ThreatFinding] = []
        self._check_spoofing(interaction, findings)
        self._check_tampering(interaction, findings)
        self._check_repudiation(interaction, findings)
        self._check_information_disclosure(interaction, findings)
        self._check_denial_of_service(interaction, findings)
        self._check_elevation_of_privilege(interaction, findings)
        return findings

    def _check_spoofing(self, interaction: Interaction, findings: list[ThreatFinding]):
        if not interaction.authenticated:
            risk = RiskLevel.HIGH if interaction.trust_boundary else RiskLevel.MEDIUM
            findings.append(self._finding(
                StrideCategory.SPOOFING, risk,
                interaction.source, interaction.target, interaction.action,
                interaction.trust_boundary,
                f"{'Cross-boundary i' if interaction.trust_boundary else 'I'}nteraction "
                f"without authentication. Source '{interaction.source}' identity is not verified.",
            ))

    def _check_tampering(self, interaction: Interaction, findings: list[ThreatFinding]):
        if interaction.action in ("write", "modify", "delete", "execute") and not interaction.has_audit_trail:
            risk = RiskLevel.HIGH if interaction.trust_boundary else RiskLevel.MEDIUM
            findings.append(self._finding(
                StrideCategory.TAMPERING, risk,
                interaction.source, interaction.target, interaction.action,
                interaction.trust_boundary,
                f"Mutation action '{interaction.action}' from '{interaction.source}' to "
                f"'{interaction.target}' without audit trail. "
                f"Changes cannot be detected or attributed.",
            ))

    def _check_repudiation(self, interaction: Interaction, findings: list[ThreatFinding]):
        if not interaction.has_audit_trail:
            risk = RiskLevel.MEDIUM if interaction.trust_boundary else RiskLevel.LOW
            findings.append(self._finding(
                StrideCategory.REPUDIATION, risk,
                interaction.source, interaction.target, interaction.action,
                interaction.trust_boundary,
                f"Action '{interaction.action}' from '{interaction.source}' has no audit record. "
                f"Source could deny performing this action.",
            ))

    def _check_information_disclosure(self, interaction: Interaction, findings: list[ThreatFinding]):
        if interaction.trust_boundary and not interaction.has_delegation_token:
            risk = RiskLevel.HIGH if interaction.action in ("read", "query", "export") else RiskLevel.MEDIUM
            findings.append(self._finding(
                StrideCategory.INFORMATION_DISCLOSURE, risk,
                interaction.source, interaction.target, interaction.action,
                interaction.trust_boundary,
                f"Cross-boundary access from '{interaction.source}' to '{interaction.target}' "
                f"without delegation token. No least-privilege enforcement on data access.",
            ))

    def _check_denial_of_service(self, interaction: Interaction, findings: list[ThreatFinding]):
        if not interaction.has_rate_limit:
            risk = RiskLevel.HIGH if interaction.trust_boundary else RiskLevel.LOW
            findings.append(self._finding(
                StrideCategory.DENIAL_OF_SERVICE, risk,
                interaction.source, interaction.target, interaction.action,
                interaction.trust_boundary,
                f"Action '{interaction.action}' from '{interaction.source}' to "
                f"'{interaction.target}' has no rate limiting. "
                f"Source could exhaust target resources.",
            ))

    def _check_elevation_of_privilege(self, interaction: Interaction, findings: list[ThreatFinding]):
        if interaction.trust_boundary and interaction.action in ("write", "modify", "delete", "execute", "admin"):
            if not interaction.has_delegation_token:
                findings.append(self._finding(
                    StrideCategory.ELEVATION_OF_PRIVILEGE, RiskLevel.CRITICAL,
                    interaction.source, interaction.target, interaction.action,
                    interaction.trust_boundary,
                    f"Cross-boundary mutation '{interaction.action}' from '{interaction.source}' "
                    f"to '{interaction.target}' without delegation token. "
                    f"Agent may exceed intended privileges.",
                ))

    def generate_report(self, interactions: list[Interaction]) -> StrideReport:
        """Analyze multiple interactions and produce an aggregated report."""
        all_findings: list[ThreatFinding] = []
        for interaction in interactions:
            all_findings.extend(self.analyze_interaction(interaction))

        summary: dict[str, int] = {}
        for cat in StrideCategory:
            count = sum(1 for f in all_findings if f.category == cat)
            if count > 0:
                summary[cat.value] = count

        return StrideReport(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            interactions_analyzed=len(interactions),
            findings=all_findings,
            summary=summary,
        )

    @staticmethod
    def _finding(
        category: StrideCategory,
        risk: RiskLevel,
        src: str,
        tgt: str,
        act: str,
        tb: bool,
        desc: str,
    ) -> ThreatFinding:
        mitigation = _MITIGATIONS[category]
        return ThreatFinding(
            category=category,
            risk_level=risk,
            description=desc,
            mitigation_module=mitigation["module"],
            mitigation_class=mitigation["class"],
            mitigation_mechanism=mitigation["mechanism"],
            source=src,
            target=tgt,
            action=act,
            trust_boundary=tb,
        )
