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

"""Tests for StrideMapper."""

from hummbl_governance.stride_mapper import (
    Interaction,
    RiskLevel,
    StrideCategory,
    StrideMapper,
)


class TestStrideMapperBasic:
    """Basic interaction analysis."""

    def setup_method(self):
        self.mapper = StrideMapper()

    def test_unauthenticated_cross_boundary(self):
        interaction = Interaction(
            source="worker", target="database", action="write",
            trust_boundary=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        categories = {f.category for f in findings}
        assert StrideCategory.SPOOFING in categories
        assert StrideCategory.ELEVATION_OF_PRIVILEGE in categories

    def test_authenticated_reduces_spoofing(self):
        interaction = Interaction(
            source="worker", target="api", action="read",
            trust_boundary=True, authenticated=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        categories = {f.category for f in findings}
        assert StrideCategory.SPOOFING not in categories

    def test_audit_trail_reduces_tampering_repudiation(self):
        interaction = Interaction(
            source="worker", target="store", action="write",
            has_audit_trail=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        categories = {f.category for f in findings}
        assert StrideCategory.TAMPERING not in categories
        assert StrideCategory.REPUDIATION not in categories

    def test_delegation_token_reduces_disclosure_and_eop(self):
        interaction = Interaction(
            source="worker", target="secrets", action="read",
            trust_boundary=True, has_delegation_token=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        categories = {f.category for f in findings}
        assert StrideCategory.INFORMATION_DISCLOSURE not in categories
        # read action doesn't trigger EoP even without token

    def test_rate_limit_reduces_dos(self):
        interaction = Interaction(
            source="worker", target="api", action="query",
            has_rate_limit=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        categories = {f.category for f in findings}
        assert StrideCategory.DENIAL_OF_SERVICE not in categories

    def test_fully_mitigated_interaction(self):
        """An interaction with all mitigations should produce no findings."""
        interaction = Interaction(
            source="orchestrator", target="worker", action="read",
            trust_boundary=False,
            authenticated=True,
            has_audit_trail=True,
            has_delegation_token=True,
            has_rate_limit=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        assert len(findings) == 0


class TestStrideMapperRiskLevels:
    """Risk level assignment."""

    def setup_method(self):
        self.mapper = StrideMapper()

    def test_cross_boundary_spoofing_is_high(self):
        interaction = Interaction(
            source="external", target="api", action="write",
            trust_boundary=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        spoofing = [f for f in findings if f.category == StrideCategory.SPOOFING]
        assert spoofing[0].risk_level == RiskLevel.HIGH

    def test_internal_spoofing_is_medium(self):
        interaction = Interaction(
            source="worker", target="cache", action="read",
            trust_boundary=False,
        )
        findings = self.mapper.analyze_interaction(interaction)
        spoofing = [f for f in findings if f.category == StrideCategory.SPOOFING]
        assert spoofing[0].risk_level == RiskLevel.MEDIUM

    def test_cross_boundary_mutation_without_token_is_critical(self):
        interaction = Interaction(
            source="agent", target="database", action="delete",
            trust_boundary=True,
        )
        findings = self.mapper.analyze_interaction(interaction)
        eop = [f for f in findings if f.category == StrideCategory.ELEVATION_OF_PRIVILEGE]
        assert len(eop) == 1
        assert eop[0].risk_level == RiskLevel.CRITICAL


class TestStrideReport:
    """Report generation."""

    def setup_method(self):
        self.mapper = StrideMapper()

    def test_report_counts(self):
        interactions = [
            Interaction(source="a", target="b", action="read", trust_boundary=True),
            Interaction(source="c", target="d", action="write", trust_boundary=False),
        ]
        report = self.mapper.generate_report(interactions)
        assert report.interactions_analyzed == 2
        assert len(report.findings) > 0
        assert report.generated_at.endswith("Z")

    def test_report_to_dict(self):
        interactions = [
            Interaction(source="a", target="b", action="read"),
        ]
        report = self.mapper.generate_report(interactions)
        d = report.to_dict()
        assert "findings_count" in d
        assert "by_category" in d
        assert isinstance(d["findings"], list)

    def test_empty_interactions(self):
        report = self.mapper.generate_report([])
        assert report.interactions_analyzed == 0
        assert len(report.findings) == 0


class TestThreatFindingMitigations:
    """Each finding should reference a real governance module."""

    def test_all_findings_have_mitigations(self):
        mapper = StrideMapper()
        interaction = Interaction(
            source="untrusted", target="critical", action="execute",
            trust_boundary=True,
        )
        findings = mapper.analyze_interaction(interaction)
        for f in findings:
            assert f.mitigation_module, f"No module for {f.category}"
            assert f.mitigation_class, f"No class for {f.category}"
            assert f.mitigation_mechanism, f"No mechanism for {f.category}"
