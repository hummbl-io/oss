"""Tests for the push/pull work queue (work_queue.py).

Component 3 of PROPOSAL-012: Autonomous Agent Orchestration.
The bus IS the work queue.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hummbl_bus.work_queue import (
    TaskSpec,
    TaskItem,
    push_task,
    pull_tasks,
    claim_task,
    complete_task,
    generate_task_id,
    _parse_task_request_line,
    _extract_field,
    _tier_leq,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task_spec(
    task_id: str = "task-abc123",
    lane: str = "ops/codex/test",
    task_name: str = "run-tests",
    priority: str = "P2",
    tier: str = "T1",
) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        lane=lane,
        task_name=task_name,
        priority=priority,
        required_model_tier=tier,
        estimated_duration="5m",
        description="Run the test suite",
        host="test-host",
        requester="codex",
    )


# ---------------------------------------------------------------------------
# TaskSpec tests
# ---------------------------------------------------------------------------

class TestTaskSpec:
    """Tests for TaskSpec dataclass and to_bus_body()."""

    def test_to_bus_body_contains_all_fields(self) -> None:
        spec = _make_task_spec()
        body = spec.to_bus_body()
        assert "event=task_request" in body
        assert "task_id=task-abc123" in body
        assert "lane=ops/codex/test" in body
        assert "task=run-tests" in body
        assert "priority=P2" in body
        assert "model_tier=T1" in body
        assert "host=test-host" in body
        assert "requester=codex" in body

    def test_to_bus_body_escapes_newlines(self) -> None:
        spec = TaskSpec(
            task_id="t1",
            lane="ops/test",
            task_name="test",
            priority="P2",
            required_model_tier="T0",
            estimated_duration="1m",
            description="line1\nline2\rline3",
            host="h",
            requester="r",
        )
        body = spec.to_bus_body()
        assert "\n" not in body.split("desc=")[1]
        assert "\\n" in body

    def test_task_spec_is_frozen(self) -> None:
        spec = _make_task_spec()
        with pytest.raises(Exception):
            spec.task_id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Field extraction tests
# ---------------------------------------------------------------------------

class TestExtractField:
    """Tests for _extract_field()."""

    def test_extracts_simple_field(self) -> None:
        assert _extract_field("task_id=abc; lane=ops", "task_id") == "abc"

    def test_extracts_last_field(self) -> None:
        assert _extract_field("a=1; b=2; task_id=xyz", "task_id") == "xyz"

    def test_returns_none_for_missing(self) -> None:
        assert _extract_field("a=1; b=2", "task_id") is None

    def test_extracts_value_with_spaces(self) -> None:
        assert _extract_field("desc=hello world; x=1", "desc") == "hello world"

    def test_extracts_trailing_field(self) -> None:
        assert _extract_field("x=1; task_id=final", "task_id") == "final"


# ---------------------------------------------------------------------------
# Task request parsing tests
# ---------------------------------------------------------------------------

class TestParseTaskRequestLine:
    """Tests for _parse_task_request_line()."""

    def test_parses_valid_line(self) -> None:
        body = (
            "event=task_request; task_id=t1; lane=ops/test; task=run; "
            "priority=P1; model_tier=T2; estimated_duration=10m; "
            "host=h1; requester=codex; desc=test task"
        )
        item = _parse_task_request_line("2026-01-01T00:00:00Z", "codex", body)
        assert item is not None
        assert item.task_id == "t1"
        assert item.lane == "ops/test"
        assert item.task_name == "run"
        assert item.priority == "P1"
        assert item.required_model_tier == "T2"

    def test_returns_none_without_task_id(self) -> None:
        body = "event=task_request; lane=ops/test"
        item = _parse_task_request_line("ts", "codex", body)
        assert item is None

    def test_defaults_for_missing_fields(self) -> None:
        body = "task_id=t1"
        item = _parse_task_request_line("ts", "codex", body)
        assert item is not None
        assert item.priority == "P3"
        assert item.required_model_tier == "T1"
        assert item.requester == "codex"

    def test_requester_defaults_to_sender(self) -> None:
        body = "task_id=t1"
        item = _parse_task_request_line("ts", "gemini", body)
        assert item is not None
        assert item.requester == "gemini"


# ---------------------------------------------------------------------------
# Tier comparison tests
# ---------------------------------------------------------------------------

class TestTierLeq:
    """Tests for _tier_leq()."""

    def test_t0_le_t0(self) -> None:
        assert _tier_leq("T0", "T0") is True

    def test_t0_le_t1(self) -> None:
        assert _tier_leq("T0", "T1") is True

    def test_t0_le_t2(self) -> None:
        assert _tier_leq("T0", "T2") is True

    def test_t2_not_le_t0(self) -> None:
        assert _tier_leq("T2", "T0") is False

    def test_t1_not_le_t0(self) -> None:
        assert _tier_leq("T1", "T0") is False

    def test_case_insensitive(self) -> None:
        assert _tier_leq("t0", "T1") is True

    def test_free_variants(self) -> None:
        assert _tier_leq("T0-FREE", "T1") is True
        assert _tier_leq("T1-LOW", "T2") is True


# ---------------------------------------------------------------------------
# Task ID generation tests
# ---------------------------------------------------------------------------

class TestGenerateTaskId:
    """Tests for generate_task_id()."""

    def test_default_prefix(self) -> None:
        tid = generate_task_id()
        assert tid.startswith("task-")

    def test_custom_prefix(self) -> None:
        tid = generate_task_id("audit")
        assert tid.startswith("audit-")

    def test_sanitizes_prefix(self) -> None:
        tid = generate_task_id("ops/codex test")
        assert tid.startswith("ops-codex-test-")

    def test_empty_prefix_becomes_task(self) -> None:
        tid = generate_task_id("!!!")
        assert tid.startswith("task-")

    def test_generates_unique_ids(self) -> None:
        ids = {generate_task_id() for _ in range(10)}
        assert len(ids) == 10


# ---------------------------------------------------------------------------
# Integration tests (push/pull/claim/complete on a real bus file)
# ---------------------------------------------------------------------------

class TestPushPullClaimComplete:
    """Integration tests using a temporary bus file."""

    def test_push_and_pull(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        spec = _make_task_spec(task_id="t1", priority="P2")
        push_task(bus, "codex", spec)
        tasks = pull_tasks(bus, agent_id="gemini")
        assert len(tasks) == 1
        assert tasks[0].task_id == "t1"

    def test_pull_empty_bus(self, tmp_path: Path) -> None:
        bus = tmp_path / "nonexistent.tsv"
        tasks = pull_tasks(bus, agent_id="gemini")
        assert tasks == []

    def test_completed_tasks_excluded(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        push_task(bus, "codex", _make_task_spec(task_id="t1"))
        complete_task(bus, "gemini", "t1", outcome="done")
        tasks = pull_tasks(bus, agent_id="codex")
        assert len(tasks) == 0

    def test_exclude_requester(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        push_task(bus, "codex", _make_task_spec(task_id="t1"))
        tasks = pull_tasks(bus, agent_id="codex", exclude_requester="codex")
        assert len(tasks) == 0

    def test_max_model_tier_filter(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        push_task(bus, "codex", _make_task_spec(task_id="t1", tier="T2"))
        push_task(bus, "codex", _make_task_spec(task_id="t2", tier="T0"))
        tasks = pull_tasks(bus, agent_id="gemini", max_model_tier="T1")
        assert len(tasks) == 1
        assert tasks[0].task_id == "t2"

    def test_allowed_lanes_filter(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        push_task(bus, "codex", _make_task_spec(task_id="t1", lane="ops/codex/test"))
        push_task(bus, "codex", _make_task_spec(task_id="t2", lane="audit/sub"))
        tasks = pull_tasks(bus, agent_id="gemini", allowed_lanes=["audit/"])
        assert len(tasks) == 1
        assert tasks[0].task_id == "t2"

    def test_priority_sorting(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        push_task(bus, "codex", _make_task_spec(task_id="p2", priority="P2"))
        push_task(bus, "codex", _make_task_spec(task_id="p0", priority="P0"))
        push_task(bus, "codex", _make_task_spec(task_id="p1", priority="P1"))
        tasks = pull_tasks(bus, agent_id="gemini")
        assert [t.task_id for t in tasks] == ["p0", "p1", "p2"]

    def test_claim_task_posts_receipt(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        claim_task(bus, "gemini", "t1", lane="ops/test", host="worker-1")
        text = bus.read_text(encoding="utf-8")
        assert "RECEIPT" in text
        assert "claimed_by=gemini" in text
        assert "task_id=t1" in text

    def test_complete_task_posts_completion(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        complete_task(bus, "gemini", "t1", outcome="success", lane="ops/test")
        text = bus.read_text(encoding="utf-8")
        assert "TASK_COMPLETE" in text
        assert "outcome=success" in text

    def test_complete_task_with_artifact(self, tmp_path: Path) -> None:
        bus = tmp_path / "messages.tsv"
        complete_task(bus, "gemini", "t1", outcome="done", artifact="report.md")
        text = bus.read_text(encoding="utf-8")
        assert "artifact=report.md" in text

    def test_full_lifecycle(self, tmp_path: Path) -> None:
        """Push → pull → claim → complete."""
        bus = tmp_path / "messages.tsv"
        spec = _make_task_spec(task_id="lifecycle-1", priority="P1")
        push_task(bus, "codex", spec)

        tasks = pull_tasks(bus, agent_id="gemini")
        assert len(tasks) == 1
        assert tasks[0].task_id == "lifecycle-1"

        claim_task(bus, "gemini", "lifecycle-1", lane=spec.lane)
        complete_task(bus, "gemini", "lifecycle-1", outcome="done")

        # After completion, task should not appear in pull
        remaining = pull_tasks(bus, agent_id="codex")
        assert len(remaining) == 0
