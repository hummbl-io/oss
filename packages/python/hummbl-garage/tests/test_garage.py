"""Tests for hummbl-garage."""

import json
import pytest

from hummbl_garage import (
    Garage,
    AgentPerformanceIndex,
    WatchFace,
    RuinGallery,
    FailureRecord,
)


class TestGarage:
    def test_livery_presets(self):
        g = Garage()
        presets = g.livery_presets()
        assert len(presets) == 6
        ids = [p.id for p in presets]
        assert "martini" in ids
        assert "gulf" in ids
        assert "john_player_special" in ids

    def test_find_livery(self):
        g = Garage()
        p = g.find_livery("gulf")
        assert p is not None
        assert p.name == "Gulf"
        assert p.primary == "#1E3A8A"

    def test_find_livery_not_found(self):
        g = Garage()
        assert g.find_livery("nonexistent") is None

    def test_cockpit_presets(self):
        g = Garage()
        assert len(g.cockpit_presets()) == 3
        ids = [c.id for c in g.cockpit_presets()]
        assert "leclerc" in ids
        assert "vettel" in ids
        assert "tesla" in ids

    def test_manettino_modes(self):
        g = Garage()
        modes = g.manettino_modes()
        assert len(modes) == 3
        ids = [m.id for m in modes]
        assert "cautious" in ids
        assert "balanced" in ids
        assert "aggressive" in ids

    def test_watch_dial_finishes(self):
        g = Garage()
        finishes = g.watch_dial_finishes()
        assert len(finishes) == 5
        tiers = [f.trust_tier for f in finishes]
        assert "PROBATIONARY" in tiers
        assert "TRUSTED" in tiers
        assert "OWNER" in tiers

    def test_find_dial_finish(self):
        g = Garage()
        d = g.find_dial_finish("TRUSTED")
        assert d is not None
        assert d.id == "enamel"

    def test_find_dial_finish_probationary(self):
        g = Garage()
        d = g.find_dial_finish("PROBATIONARY")
        assert d is not None
        assert d.id == "flat"

    def test_watch_hand_colors(self):
        g = Garage()
        colors = g.watch_hand_colors()
        assert len(colors) == 5
        states = [c.state for c in colors]
        assert "working" in states
        assert "blocked" in states

    def test_watch_complications(self):
        g = Garage()
        assert len(g.watch_complications()) == 4

    def test_failure_states(self):
        g = Garage()
        states = g.failure_states()
        assert len(states) == 3
        ids = [s.id for s in states]
        assert "degraded" in ids
        assert "broken" in ids
        assert "dead" in ids

    def test_find_failure_state(self):
        g = Garage()
        s = g.find_failure_state("broken")
        assert s is not None
        assert s.name == "Broken"
        assert s.color == "#D4AF37"  # kintsugi gold

    def test_api_classes(self):
        g = Garage()
        classes = g.api_classes()
        assert len(classes) == 7
        ids = [c.id for c in classes]
        assert "D" in ids
        assert "R" in ids

    def test_classify_api(self):
        g = Garage()
        assert g.classify_api(150).id == "D"
        assert g.classify_api(350).id == "C"
        assert g.classify_api(550).id == "B"
        assert g.classify_api(750).id == "A"
        assert g.classify_api(850).id == "S1"
        assert g.classify_api(920).id == "S2"
        assert g.classify_api(970).id == "R"

    def test_classify_api_out_of_range(self):
        g = Garage()
        assert g.classify_api(50) is None
        assert g.classify_api(1000) is None

    def test_api_subratings(self):
        g = Garage()
        subs = g.api_subratings()
        assert len(subs) == 6
        ids = [s.id for s in subs]
        assert "reasoning_speed" in ids
        assert "safety" in ids

    def test_upgrade_priority(self):
        g = Garage()
        priority = g.upgrade_priority()
        assert priority[0] == "context"
        assert priority[-1] == "observability"
        assert len(priority) == 6


class TestAgentPerformanceIndex:
    def test_zero_scores(self):
        api = AgentPerformanceIndex()
        assert api.api_score == 100
        assert api.api_class == "D"

    def test_max_scores(self):
        api = AgentPerformanceIndex(
            reasoning_speed=10, tool_accuracy=10, context_efficiency=10,
            latency=10, safety=10, composite=10,
        )
        assert api.api_score == 999
        assert api.api_class == "R"

    def test_mid_scores(self):
        api = AgentPerformanceIndex(
            reasoning_speed=5, tool_accuracy=5, context_efficiency=5,
            latency=5, safety=5, composite=5,
        )
        assert 500 <= api.api_score <= 550
        assert api.api_class == "B"

    def test_high_scores(self):
        api = AgentPerformanceIndex(
            reasoning_speed=8.5, tool_accuracy=9.0, context_efficiency=7.5,
            latency=8.0, safety=9.5, composite=8.0,
        )
        assert api.api_score >= 800
        assert api.api_class in ("S1", "A")

    def test_to_dict(self):
        api = AgentPerformanceIndex(reasoning_speed=7, tool_accuracy=8)
        d = api.to_dict()
        assert d["reasoning_speed"] == 7
        assert d["tool_accuracy"] == 8
        assert "api_score" in d
        assert "api_class" in d

    def test_safety_weighted_higher(self):
        """Safety has 20% weight — high safety should boost score significantly."""
        low_safety = AgentPerformanceIndex(safety=0, reasoning_speed=10, tool_accuracy=10,
                                           context_efficiency=10, latency=10, composite=10)
        high_safety = AgentPerformanceIndex(safety=10, reasoning_speed=10, tool_accuracy=10,
                                            context_efficiency=10, latency=10, composite=10)
        assert high_safety.api_score > low_safety.api_score

    def test_tool_accuracy_weighted_highest(self):
        """Tool accuracy has 25% weight — highest of all sub-ratings."""
        low_tool = AgentPerformanceIndex(tool_accuracy=0, reasoning_speed=10, safety=10,
                                         context_efficiency=10, latency=10, composite=10)
        high_tool = AgentPerformanceIndex(tool_accuracy=10, reasoning_speed=10, safety=10,
                                          context_efficiency=10, latency=10, composite=10)
        # 25% swing = 225 points
        diff = high_tool.api_score - low_tool.api_score
        assert diff >= 200  # approximately 225


class TestWatchFace:
    def test_default_state(self):
        face = WatchFace()
        assert face.state == "idle"
        assert face.hand_color == "#6B7280"

    def test_working_state(self):
        face = WatchFace(state="working")
        assert face.hand_color == "#2563EB"
        assert face.hand_angle == 90

    def test_blocked_state(self):
        face = WatchFace(state="blocked")
        assert face.hand_color == "#DC2626"
        assert face.hand_angle == 270

    def test_dial_finish_by_trust(self):
        face = WatchFace(trust_tier="TRUSTED")
        assert face.dial_finish == "enamel"

        face2 = WatchFace(trust_tier="PROBATIONARY")
        assert face2.dial_finish == "flat"

    def test_to_dict(self):
        face = WatchFace(state="working", trust_tier="MEDIUM-HIGH", token_budget_pct=72.5)
        d = face.to_dict()
        assert d["state"] == "working"
        assert d["hand_color"] == "#2563EB"
        assert d["dial_finish"] == "guilloche"
        assert d["complications"]["token_budget_pct"] == 72.5


class TestRuinGallery:
    def test_empty_gallery(self):
        gallery = RuinGallery()
        assert len(gallery) == 0
        assert gallery.all_records() == []

    def test_record_failure(self):
        gallery = RuinGallery()
        record = gallery.record(
            agent_name="gemini",
            failure_state="broken",
            timestamp="2026-09-02T12:00:00Z",
            error_message="Context overflow",
            recovery_action="Restart with smaller context",
        )
        assert record.agent_name == "gemini"
        assert record.failure_state == "broken"
        assert len(gallery) == 1

    def test_filter_by_agent(self):
        gallery = RuinGallery()
        gallery.record("devin", "degraded", "2026-09-02T10:00:00Z", "Slow response")
        gallery.record("gemini", "broken", "2026-09-02T12:00:00Z", "Context overflow")
        gallery.record("devin", "dead", "2026-09-02T14:00:00Z", "Session killed")

        devin_failures = gallery.by_agent("devin")
        assert len(devin_failures) == 2
        assert all(r.agent_name == "devin" for r in devin_failures)

    def test_filter_by_state(self):
        gallery = RuinGallery()
        gallery.record("devin", "degraded", "2026-09-02T10:00:00Z", "Slow")
        gallery.record("gemini", "broken", "2026-09-02T12:00:00Z", "Overflow")
        gallery.record("codex", "dead", "2026-09-02T14:00:00Z", "Killed")

        assert len(gallery.dead_agents()) == 1
        assert len(gallery.broken_agents()) == 1
        assert len(gallery.degraded_agents()) == 1

    def test_to_dict(self):
        gallery = RuinGallery()
        gallery.record("devin", "degraded", "2026-09-02T10:00:00Z", "Slow")
        records = gallery.to_dict()
        assert len(records) == 1
        assert records[0]["agent_name"] == "devin"
        assert records[0]["failure_state"] == "degraded"

    def test_successor_for_dead(self):
        gallery = RuinGallery()
        record = gallery.record(
            agent_name="codex",
            failure_state="dead",
            timestamp="2026-09-02T14:00:00Z",
            error_message="OOM killed",
            successor="codex-2",
        )
        assert record.successor == "codex-2"
        dead = gallery.dead_agents()
        assert dead[0].successor == "codex-2"


class TestSVG:
    def test_render_watch_face(self):
        from hummbl_garage.svg import render_watch_face_svg
        face = WatchFace(state="working", trust_tier="TRUSTED")
        svg = render_watch_face_svg(face)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "#2563EB" in svg  # working hand color

    def test_render_livery_swatch(self):
        from hummbl_garage.svg import render_livery_swatch_svg
        g = Garage()
        livery = g.find_livery("gulf")
        svg = render_livery_swatch_svg(livery)
        assert svg.startswith("<svg")
        assert "Gulf" in svg

    def test_render_failure_state_degraded(self):
        from hummbl_garage.svg import render_failure_state_svg
        g = Garage()
        state = g.find_failure_state("degraded")
        svg = render_failure_state_svg(state)
        assert svg.startswith("<svg")
        assert "DEGRADED" in svg

    def test_render_failure_state_broken(self):
        from hummbl_garage.svg import render_failure_state_svg
        g = Garage()
        state = g.find_failure_state("broken")
        svg = render_failure_state_svg(state)
        assert svg.startswith("<svg")
        assert "BROKEN" in svg
        assert "#D4AF37" in svg  # kintsugi gold

    def test_render_failure_state_dead(self):
        from hummbl_garage.svg import render_failure_state_svg
        g = Garage()
        state = g.find_failure_state("dead")
        svg = render_failure_state_svg(state)
        assert svg.startswith("<svg")
        assert "AGENT LOST" in svg

    def test_render_api_gauge(self):
        from hummbl_garage.svg import render_api_gauge_svg
        svg = render_api_gauge_svg(750, "A")
        assert svg.startswith("<svg")
        assert "750" in svg
        assert "CLASS A" in svg


class TestCLI:
    def test_info(self, capsys):
        from hummbl_garage.__main__ import main
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "HUMMBL Garage" in out
        assert "Livery presets" in out

    def test_api_classify(self, capsys):
        from hummbl_garage.__main__ import main
        rc = main(["api", "750"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Class: A" in out

    def test_api_score(self, capsys):
        from hummbl_garage.__main__ import main
        rc = main(["api-score", "8.5", "9.0", "7.5", "8.0", "9.5", "8.0"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "API Score:" in out
        assert "Class:" in out

    def test_failure(self, capsys):
        from hummbl_garage.__main__ import main
        rc = main(["failure", "broken"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Broken" in out
        assert "kintsugi" in out.lower()


# Goodhart mitigation tests


class TestGoodhartMitigation:
    def test_terminal_value_defined(self):
        from hummbl_garage.goodhart import TERMINAL_VALUE
        assert "routing decisions" in TERMINAL_VALUE
        assert "task completion" in TERMINAL_VALUE

    def test_usage_policy_defined(self):
        from hummbl_garage.goodhart import USAGE_POLICY
        assert "DESCRIPTIVE" in USAGE_POLICY
        assert "not PRESCRIPTIVE" in USAGE_POLICY

    def test_proxy_chain_defined(self):
        from hummbl_garage.goodhart import PROXY_CHAIN
        assert "API score" in PROXY_CHAIN
        assert "terminal value" in PROXY_CHAIN

    def test_goodhart_risk_documented(self):
        from hummbl_garage.goodhart import GOODHART_RISK
        assert "composite" in GOODHART_RISK
        assert "inflated" in GOODHART_RISK


class TestGamingDetector:
    def test_no_alerts_with_insufficient_data(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector(min_tasks=3)
        api = AgentPerformanceIndex(composite=8.0)
        alerts = detector.check_agent("devin", api)
        assert alerts == []

    def test_no_alerts_when_matched(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector(divergence_threshold=2.0, min_tasks=3)
        for i in range(5):
            detector.record_outcome_simple("devin", f"task-{i}", True, 7.0)
        api = AgentPerformanceIndex(composite=7.0)
        alerts = detector.check_agent("devin", api)
        assert alerts == []

    def test_alerts_on_composite_inflation(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector(divergence_threshold=2.0, min_tasks=3)
        for i in range(5):
            detector.record_outcome_simple("devin", f"task-{i}", True, 4.5)
        api = AgentPerformanceIndex(composite=9.5)
        alerts = detector.check_agent("devin", api)
        assert len(alerts) == 1
        assert alerts[0].alert_type == "composite_inflation"
        assert alerts[0].severity == "high"

    def test_alerts_on_subrating_divergence(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector(divergence_threshold=2.0, min_tasks=3)
        for i in range(4):
            detector.record_outcome_simple(
                "devin", f"reasoning-{i}", True, 5.0,
                exercises=["reasoning_speed"],
            )
        api = AgentPerformanceIndex(reasoning_speed=9.0, composite=5.0)
        alerts = detector.check_agent("devin", api)
        reasoning_alerts = [a for a in alerts if a.alert_type == "divergence"]
        assert len(reasoning_alerts) >= 1

    def test_severity_low(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector(divergence_threshold=2.0, min_tasks=3)
        for i in range(5):
            detector.record_outcome_simple("devin", f"task-{i}", True, 6.0)
        api = AgentPerformanceIndex(composite=8.5)
        alerts = detector.check_agent("devin", api)
        assert len(alerts) == 1
        assert alerts[0].severity == "low"

    def test_agent_outcomes_filtering(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector()
        detector.record_outcome_simple("devin", "t1", True, 8.0)
        detector.record_outcome_simple("devin", "t2", True, 7.0)
        detector.record_outcome_simple("codex", "t3", True, 9.0)
        devin_outcomes = detector.agent_outcomes("devin")
        assert len(devin_outcomes) == 2

    def test_clear(self):
        from hummbl_garage.goodhart import GamingDetector
        detector = GamingDetector()
        detector.record_outcome_simple("devin", "t1", True, 8.0)
        assert len(detector.all_outcomes()) == 1
        detector.clear()
        assert len(detector.all_outcomes()) == 0


class TestHeldOutEvaluator:
    def test_add_and_get_task(self):
        from hummbl_garage.goodhart import HeldOutTask, HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        task = HeldOutTask("eval-001", "Debug", {"reasoning_speed": 7}, "hard", "reasoning")
        evaluator.add_task(task)
        assert evaluator.get_task("eval-001") is not None
        assert evaluator.get_task("nonexistent") is None

    def test_task_ids(self):
        from hummbl_garage.goodhart import HeldOutTask, HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        evaluator.add_task(HeldOutTask("t1", "d", {}, "easy", "cat"))
        evaluator.add_task(HeldOutTask("t2", "d", {}, "easy", "cat"))
        ids = evaluator.task_ids()
        assert "t1" in ids and "t2" in ids

    def test_evaluate_records_result(self):
        from hummbl_garage.goodhart import HeldOutTask, HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        evaluator.add_task(HeldOutTask("t1", "d", {"reasoning_speed": 7}, "medium", "reasoning"))
        result = evaluator.evaluate("devin", "t1", 8.5, True)
        assert result["agent_name"] == "devin"
        assert result["human_quality_score"] == 8.5
        assert len(evaluator.all_results()) == 1

    def test_evaluate_unknown_task(self):
        from hummbl_garage.goodhart import HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        result = evaluator.evaluate("devin", "nonexistent", 8.0, True)
        assert "error" in result

    def test_correlation_insufficient_data(self):
        from hummbl_garage.goodhart import HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        api = AgentPerformanceIndex(composite=8.0)
        result = evaluator.correlation_with_api("devin", api)
        assert result["assessment"] == "insufficient_data"

    def test_correlation_correlated(self):
        from hummbl_garage.goodhart import HeldOutTask, HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        for i in range(5):
            evaluator.add_task(HeldOutTask(f"t{i}", "d", {}, "medium", "cat"))
            evaluator.evaluate("devin", f"t{i}", 8.0, True)
        api = AgentPerformanceIndex(composite=8.0)
        result = evaluator.correlation_with_api("devin", api)
        assert result["assessment"] == "correlated"

    def test_correlation_uncorrelated(self):
        from hummbl_garage.goodhart import HeldOutTask, HeldOutEvaluator
        evaluator = HeldOutEvaluator()
        for i in range(5):
            evaluator.add_task(HeldOutTask(f"t{i}", "d", {}, "medium", "cat"))
            evaluator.evaluate("devin", f"t{i}", 3.0, True)
        api = AgentPerformanceIndex(composite=9.0)
        result = evaluator.correlation_with_api("devin", api)
        assert result["assessment"] == "uncorrelated"
        assert result["divergence"] > 2.0
