"""Tests for hummbl-intel core modules.

Stdlib-only — no external test dependencies beyond pytest.
"""

from datetime import UTC

from hummbl_intel.fusion import (
    AllSourceProduct,
    CompetingHypothesesAnalysis,
    EstimativeProbability,
    FusedFinding,
    Hypothesis,
    fuse_into_finding,
)
from hummbl_intel.grading import (
    AssertionPolarity,
    ContentCredibility,
    GradedAssertion,
    SourceGrade,
    SourceReliability,
    grade_automated_source,
    grade_human_source,
    grade_research_source,
    grade_uncorroborated,
    upgrade_with_corroboration,
)
from hummbl_intel.managers import (
    CANONICAL_MANAGERS,
    CORONAL_AGENT,
    get_disciplines_for_agent,
    get_manager,
)
from hummbl_intel.posture import (
    CollectionPostureReport,
    DisciplinePosture,
    PostureStatus,
    SurfaceStatus,
    build_default_posture,
)
from hummbl_intel.taxonomy import (
    CANONICAL_SURFACES,
    IntelligenceDiscipline,
    from_bus_prefix,
    get_surface,
    list_disciplines,
)


class TestTaxonomy:
    def test_all_disciplines_present(self):
        disciplines = list_disciplines()
        assert len(disciplines) == 9
        names = {d.name for d in disciplines}
        assert "SIGINT" in names
        assert "HUMINT" in names
        assert "OSINT" in names
        assert "GEOINT" in names
        assert "MASINT" in names
        assert "FININT" in names
        assert "TECHINT" in names
        assert "IMINT" in names
        assert "ALL_SOURCE" in names

    def test_every_discipline_has_canonical_surface(self):
        for disc in list_disciplines():
            surface = get_surface(disc)
            assert surface is not None
            assert surface.discipline == disc

    def test_every_canonical_surface_has_surfaces(self):
        for disc, surface in CANONICAL_SURFACES.items():
            assert len(surface.surfaces) > 0, f"{disc} has no surfaces"
            assert surface.lead_agency, f"{disc} has no lead agency"

    def test_from_bus_prefix_valid(self):
        assert from_bus_prefix("[int=sigint]") == IntelligenceDiscipline.SIGINT
        assert from_bus_prefix("[int=humint]") == IntelligenceDiscipline.HUMINT
        assert from_bus_prefix("[int=osint]") == IntelligenceDiscipline.OSINT

    def test_from_bus_prefix_invalid(self):
        assert from_bus_prefix("not a tag") is None
        assert from_bus_prefix("[int=fake]") is None
        assert from_bus_prefix("") is None

    def test_sigint_surfaces(self):
        surface = get_surface(IntelligenceDiscipline.SIGINT)
        assert "coordination_bus" in surface.surfaces
        assert "codex_steward_loop" in surface.surfaces

    def test_all_source_has_fusion_surfaces(self):
        surface = get_surface(IntelligenceDiscipline.ALL_SOURCE)
        assert "morning_briefing" in surface.surfaces
        assert "cognitive_ledger" in surface.surfaces


class TestGrading:
    def test_source_grade_code(self):
        grade = SourceGrade(SourceReliability.B, ContentCredibility.TWO)
        assert grade.to_code() == "B/2"

    def test_human_source_grade(self):
        grade = grade_human_source()
        assert grade.reliability == SourceReliability.A
        assert grade.credibility == ContentCredibility.TWO
        assert grade.is_actionable()

    def test_automated_source_grade(self):
        grade = grade_automated_source()
        assert grade.reliability == SourceReliability.B
        assert grade.credibility == ContentCredibility.THREE
        assert grade.is_actionable()

    def test_uncorroborated_not_actionable(self):
        grade = grade_uncorroborated()
        assert not grade.is_actionable()

    def test_upgrade_with_corroboration_two_sources(self):
        grade = SourceGrade(SourceReliability.B, ContentCredibility.THREE)
        upgraded = upgrade_with_corroboration(grade, 2)
        assert upgraded.credibility == ContentCredibility.TWO

    def test_upgrade_with_corroboration_three_sources(self):
        grade = SourceGrade(SourceReliability.C, ContentCredibility.THREE)
        upgraded = upgrade_with_corroboration(grade, 3)
        assert upgraded.credibility == ContentCredibility.ONE
        assert upgraded.reliability == SourceReliability.B

    def test_upgrade_minimum_sources(self):
        grade = SourceGrade(SourceReliability.B, ContentCredibility.THREE)
        upgraded = upgrade_with_corroboration(grade, 0)
        assert upgraded == grade

    def test_research_source_peer_reviewed(self):
        grade = grade_research_source(peer_reviewed=True)
        assert grade.reliability == SourceReliability.B

    def test_research_source_not_peer_reviewed(self):
        grade = grade_research_source(peer_reviewed=False)
        assert grade.reliability == SourceReliability.C

    def test_contentcredibility_is_intenum(self):
        assert ContentCredibility.ONE.value == 1
        assert ContentCredibility.SIX.value == 6
        assert int(ContentCredibility.THREE) == 3

    def test_contentcredibility_label(self):
        assert ContentCredibility.ONE.label == "confirmed"
        assert ContentCredibility.THREE.label == "possibly_true"

    def test_to_code_uses_intenum_value(self):
        # B/2 — credibility int comes from IntEnum value, not a side dict.
        grade = SourceGrade(SourceReliability.B, ContentCredibility.TWO)
        assert grade.to_code() == "B/2"
        grade6 = SourceGrade(SourceReliability.A, ContentCredibility.SIX)
        assert grade6.to_code() == "A/6"

    def test_graded_assertion_default_polarity_none(self):
        # Default polarity is None ("caller did not declare"), not SUPPORTS.
        # This lets fusion distinguish omission (run heuristic fallback) from
        # explicit support (trust the declaration).
        ga = GradedAssertion(
            content="x",
            source="s",
            grade=grade_automated_source(),
        )
        assert ga.polarity is None

    def test_graded_assertion_to_dict_shape(self):
        ga = GradedAssertion(
            content="deployment was not delayed",
            source="s",
            grade=SourceGrade(SourceReliability.B, ContentCredibility.TWO),
            polarity=AssertionPolarity.CONTRADICTS,
        )
        d = ga.to_dict()
        assert d["polarity"] == "contradicts"
        # credibility stays the prose label (stable serialization shape)
        assert d["credibility"] == "probably_true"
        assert d["code"] == "B/2"

    def test_graded_assertion_to_dict_polarity_none_serializes(self):
        ga = GradedAssertion(
            content="x",
            source="s",
            grade=grade_automated_source(),
        )
        assert ga.to_dict()["polarity"] is None


class TestPosture:
    def test_default_posture_has_all_disciplines(self):
        report = build_default_posture()
        # Should have 8 collection disciplines (excluding ALL_SOURCE)
        assert len(report.disciplines) == 8

    def test_default_posture_all_surfaces_active(self):
        report = build_default_posture()
        for posture in report.disciplines.values():
            assert posture.status in (
                PostureStatus.GREEN,
                PostureStatus.YELLOW,
            ), f"{posture.discipline.name} is {posture.status}"

    def test_surface_stale_detection(self):
        from datetime import datetime, timedelta

        now = datetime.now(UTC)
        fresh = SurfaceStatus(
            name="test",
            last_collection=now,
            stale_threshold_hours=24.0,
        )
        assert not fresh.is_stale(now)

        old = SurfaceStatus(
            name="test",
            last_collection=now - timedelta(hours=48),
            stale_threshold_hours=24.0,
        )
        assert old.is_stale(now)

    def test_discipline_compute_status_all_active(self):
        surf = SurfaceStatus(name="s1", active=True)
        posture = DisciplinePosture(
            discipline=IntelligenceDiscipline.SIGINT,
            surfaces=[surf],
        )
        assert posture.compute_status() == PostureStatus.GREEN

    def test_discipline_compute_status_half_active(self):
        s1 = SurfaceStatus(name="s1", active=True)
        s2 = SurfaceStatus(name="s2", active=False)
        posture = DisciplinePosture(
            discipline=IntelligenceDiscipline.SIGINT,
            surfaces=[s1, s2],
        )
        assert posture.compute_status() == PostureStatus.YELLOW

    def test_discipline_compute_status_none_active(self):
        posture = DisciplinePosture(
            discipline=IntelligenceDiscipline.SIGINT,
            surfaces=[],
        )
        assert posture.compute_status() == PostureStatus.BLACK

    def test_report_aggregate_worst_wins(self):
        report = CollectionPostureReport()
        report.add_discipline(
            DisciplinePosture(
                discipline=IntelligenceDiscipline.SIGINT,
                status=PostureStatus.GREEN,
            )
        )
        report.add_discipline(
            DisciplinePosture(
                discipline=IntelligenceDiscipline.OSINT,
                status=PostureStatus.RED,
            )
        )
        assert report.compute_overall() == PostureStatus.RED

    def test_summary_lines_output(self):
        report = build_default_posture()
        lines = report.to_summary_lines()
        assert len(lines) == 8
        for line in lines:
            assert ":" in line


class TestFusion:
    def test_hypothesis_likelihood_no_evidence(self):
        h = Hypothesis(id="H1", statement="test")
        assert h.likelihood() == EstimativeProbability.EVEN_CHANCE

    def test_fuse_into_finding_no_assertions(self):
        finding = fuse_into_finding("test conclusion", [])
        assert finding.probability == EstimativeProbability.EVEN_CHANCE
        assert finding.confidence == 0.0

    def _two_actionable_assertions(self, polarity_a):
        """Two actionable assertions, one corroborated -> base HIGHLY_LIKELY/0.85."""
        a1 = GradedAssertion(
            content="deployment was not delayed",
            source="codex-steward-loop",
            grade=grade_automated_source(),  # B/3, actionable
            discipline="SIGINT",
            corroboration_count=2,
            polarity=polarity_a,
        )
        a2 = GradedAssertion(
            content="ops confirmed fleet is live",
            source="human",
            grade=grade_human_source(),  # A/2, actionable
            discipline="HUMINT",
            polarity=AssertionPolarity.SUPPORTS,
        )
        return [a1, a2]

    def test_polarity_supports_not_penalized(self):
        # Regression: content starts with "not " but polarity=SUPPORTS must
        # NOT trigger the contradiction penalty. The old string-prefix
        # heuristic would have wrongly degraded this to 0.60.
        finding = fuse_into_finding(
            "Fleet coordination is active",
            self._two_actionable_assertions(AssertionPolarity.SUPPORTS),
        )
        assert finding.confidence == 0.85
        assert finding.probability == EstimativeProbability.HIGHLY_LIKELY

    def test_polarity_contradicts_penalized(self):
        # Explicit CONTRADICTS polarity degrades confidence by 0.25.
        finding = fuse_into_finding(
            "Fleet coordination is active",
            self._two_actionable_assertions(AssertionPolarity.CONTRADICTS),
        )
        assert finding.confidence == 0.60  # max(0.10, 0.85 - 0.25)

    def test_polarity_neutral_not_penalized(self):
        finding = fuse_into_finding(
            "Fleet coordination is active",
            self._two_actionable_assertions(AssertionPolarity.NEUTRAL),
        )
        assert finding.confidence == 0.85

    def _omitted_polarity_pair(self, content_a):
        """Two actionable assertions; a1 omits polarity (None), a2 supports."""
        a1 = GradedAssertion(
            content=content_a,
            source="sigint-bot",
            grade=grade_automated_source(),  # B/3, actionable
            discipline="SIGINT",
            corroboration_count=2,
            polarity=None,
        )
        a2 = GradedAssertion(
            content="ops confirmed fleet is live",
            source="human",
            grade=grade_human_source(),  # A/2, actionable
            discipline="HUMINT",
            polarity=AssertionPolarity.SUPPORTS,
        )
        return [a1, a2]

    def test_polarity_omission_heuristic_fallback_penalizes_and_warns(self):
        # C2: a caller who omits polarity on contradiction-suggesting content
        # is NOT silently let off — the conservative heuristic fallback fires,
        # confidence is penalized, and a warning nudges explicit polarity.
        finding = fuse_into_finding(
            "Fleet coordination is active",
            self._omitted_polarity_pair("not true that the fleet is live"),
        )
        assert finding.confidence == 0.60  # max(0.10, 0.85 - 0.25)
        assert finding.probability == EstimativeProbability.HIGHLY_LIKELY
        assert len(finding.warnings) == 1
        assert "sigint-bot" in finding.warnings[0]
        assert "set polarity explicitly" in finding.warnings[0]

    def test_polarity_omission_no_match_no_penalty_no_warning(self):
        # Omission on clearly-supporting content: heuristic does not fire,
        # no penalty, no warning. The fallback is conservative (prefix-only).
        finding = fuse_into_finding(
            "Fleet coordination is active",
            self._omitted_polarity_pair("fleet telemetry looks healthy"),
        )
        assert finding.confidence == 0.85
        assert finding.warnings == []

    def test_explicit_supports_contradicting_content_warns_only(self):
        # D3: explicit SUPPORTS is trusted (no penalty — the original P1 fix
        # holds), but a polarity/content inconsistency warning is emitted as
        # an audit trail for mislabeled polarity.
        a1 = GradedAssertion(
            content="not true that the fleet is live",
            source="sigint-bot",
            grade=grade_automated_source(),
            discipline="SIGINT",
            corroboration_count=2,
            polarity=AssertionPolarity.SUPPORTS,
        )
        a2 = GradedAssertion(
            content="ops confirmed fleet is live",
            source="human",
            grade=grade_human_source(),
            discipline="HUMINT",
            polarity=AssertionPolarity.SUPPORTS,
        )
        finding = fuse_into_finding("Fleet coordination is active", [a1, a2])
        assert finding.confidence == 0.85  # no penalty — explicit SUPPORTS trusted
        assert len(finding.warnings) == 1
        assert "verify polarity" in finding.warnings[0]

    def test_fused_finding_warnings_default_empty(self):
        finding = FusedFinding(
            conclusion="x",
            probability=EstimativeProbability.EVEN_CHANCE,
        )
        assert finding.warnings == []

    def test_all_source_product_key_judgments(self):
        product = AllSourceProduct(title="Test Briefing")
        f1 = FusedFinding(
            conclusion="high confidence",
            probability=EstimativeProbability.HIGHLY_LIKELY,
            confidence=0.9,
        )
        f2 = FusedFinding(
            conclusion="low confidence",
            probability=EstimativeProbability.UNLIKELY,
            confidence=0.2,
        )
        product.findings = [f2, f1]
        key = product.key_judgments()
        assert key[0].confidence == 0.9

    def test_source_attribution_line(self):
        from hummbl_intel.taxonomy import IntelligenceDiscipline

        finding = FusedFinding(
            conclusion="the bus bridge is operational",
            probability=EstimativeProbability.LIKELY,
            sources=[IntelligenceDiscipline.SIGINT, IntelligenceDiscipline.OSINT],
            confidence=0.8,
        )
        line = finding.to_attribution_line()
        assert "SIGINT" in line or "signals" in line.lower()
        assert "LIKELY" in line

    def test_estimative_probability_ranges(self):
        from hummbl_intel.fusion import WEP_RANGES

        assert WEP_RANGES[EstimativeProbability.ALMOST_CERTAIN] == (0.93, 0.99)
        assert WEP_RANGES[EstimativeProbability.ALMOST_IMPOSSIBLE] == (0.01, 0.04)

    def test_ach_ranking(self):
        h1 = Hypothesis(id="H1", statement="likely true")
        h2 = Hypothesis(id="H2", statement="unlikely true")

        from hummbl_intel.grading import GradedAssertion

        h1.evidence_for.append(
            GradedAssertion(
                content="evidence A",
                source="test",
                grade=SourceGrade(SourceReliability.A, ContentCredibility.TWO),
            )
        )
        h1.evidence_for.append(
            GradedAssertion(
                content="evidence B",
                source="test2",
                grade=SourceGrade(SourceReliability.A, ContentCredibility.TWO),
            )
        )

        ach = CompetingHypothesesAnalysis(
            question="test question",
            hypotheses=[h1, h2],
        )
        ranked = ach.ranked()
        assert ranked[0] is h1


class TestManagers:
    def test_all_disciplines_have_manager(self):
        from hummbl_intel.taxonomy import list_disciplines

        for disc in list_disciplines():
            manager = get_manager(disc)
            assert manager is not None, f"No manager for {disc}"
            assert manager.steward_agent, f"No steward for {disc}"

    def test_every_manager_has_duties(self):
        for manager in CANONICAL_MANAGERS:
            assert len(manager.duties) > 0, f"No duties for {manager.discipline}"

    def test_get_disciplines_for_agent(self):
        discs = get_disciplines_for_agent(CORONAL_AGENT)
        assert IntelligenceDiscipline.ALL_SOURCE in discs

    def test_coronal_is_all_source_steward(self):
        manager = get_manager(IntelligenceDiscipline.ALL_SOURCE)
        assert manager is not None
        assert manager.steward_agent == CORONAL_AGENT
        assert "morning briefing" in " ".join(manager.duties).lower()

    def test_human_is_humint_steward(self):
        manager = get_manager(IntelligenceDiscipline.HUMINT)
        assert manager is not None
        assert manager.steward_agent == "human"
        assert manager.escalation_agent == "human"

    def test_manager_summary_table(self):
        from hummbl_intel.managers import manager_summary_table

        table = manager_summary_table()
        assert "SIGINT" in table
        assert CORONAL_AGENT in table
        assert len(table.split("\n")) >= 10


class TestIntegration:
    def test_full_workflow(self):
        """End-to-end: grade sources -> build posture -> fuse into product."""
        # 1. Build posture
        report = build_default_posture()
        report.compute_overall()

        # 2. Grade some evidence
        a1 = grade_human_source()
        a2 = grade_automated_source()

        from hummbl_intel.grading import GradedAssertion

        ga1 = GradedAssertion(
            content="Bus bridge is operational",
            source="codex-steward-loop",
            grade=a2,
            discipline="SIGINT",
        )
        ga2 = GradedAssertion(
            content="Operator confirmed doctrine ratification",
            source="human",
            grade=a1,
            discipline="HUMINT",
        )

        # 3. Fuse into findings
        f1 = fuse_into_finding(
            "Fleet coordination is active",
            [ga1, ga2],
        )

        # 4. Build product
        product = AllSourceProduct(
            title="Test Morning Briefing",
            findings=[f1],
            collection_posture=report,
        )

        assert len(product.findings) == 1
        assert f1.confidence > 0.5
        assert len(product.to_summary()) > 0
