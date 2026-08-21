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

"""Tests for hummbl_governance.kill_switch."""

import json
import tempfile
from pathlib import Path

import pytest

from hummbl_governance.kill_switch import (
    KillSwitch,
    KillSwitchMode,
    KillSwitchEngagedError,
    KillSwitchTamperError,
)


class TestKillSwitchModes:
    def test_starts_disengaged(self):
        ks = KillSwitch()
        assert ks.mode == KillSwitchMode.DISENGAGED
        assert not ks.engaged

    def test_engage_halt_noncritical(self):
        ks = KillSwitch()
        event = ks.engage(KillSwitchMode.HALT_NONCRITICAL, "test", "tester")
        assert ks.mode == KillSwitchMode.HALT_NONCRITICAL
        assert ks.engaged
        assert event.mode == KillSwitchMode.HALT_NONCRITICAL

    def test_engage_halt_all(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "budget", "governor")
        assert ks.mode == KillSwitchMode.HALT_ALL

    def test_engage_emergency(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.EMERGENCY, "critical failure", "system")
        assert ks.mode == KillSwitchMode.EMERGENCY

    def test_disengage(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        event = ks.disengage("tester")
        assert ks.mode == KillSwitchMode.DISENGAGED
        assert not ks.engaged
        assert event.mode == KillSwitchMode.DISENGAGED

    def test_engage_disengaged_raises(self):
        ks = KillSwitch()
        with pytest.raises(ValueError, match="Use disengage"):
            ks.engage(KillSwitchMode.DISENGAGED, "test", "tester")

    def test_disengage_custom_reason(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        event = ks.disengage("admin", reason="Manual override")
        assert "Manual override" in event.reason


class TestTaskChecking:
    def test_disengaged_allows_all(self):
        ks = KillSwitch()
        result = ks.check_task_allowed("anything")
        assert result["allowed"] is True

    def test_halt_noncritical_blocks_regular(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_NONCRITICAL, "test", "tester")
        result = ks.check_task_allowed("data_export")
        assert result["allowed"] is False
        assert result["action"] == "queue"

    def test_halt_noncritical_allows_critical(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_NONCRITICAL, "test", "tester")
        result = ks.check_task_allowed("safety_monitoring")
        assert result["allowed"] is True

    def test_halt_all_allows_critical(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        result = ks.check_task_allowed("audit_logging")
        assert result["allowed"] is True
        assert result["note"] == "critical only"

    def test_halt_all_blocks_regular(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        result = ks.check_task_allowed("data_export")
        assert result["allowed"] is False
        assert result["action"] == "block"

    def test_emergency_blocks_everything(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.EMERGENCY, "critical", "system")
        result = ks.check_task_allowed("safety_monitoring")
        assert result["allowed"] is False

    def test_custom_critical_tasks(self):
        ks = KillSwitch(critical_tasks=frozenset(["my_critical_task"]))
        ks.engage(KillSwitchMode.HALT_NONCRITICAL, "test", "tester")
        assert ks.check_task_allowed("my_critical_task")["allowed"] is True
        assert ks.check_task_allowed("safety_monitoring")["allowed"] is False

    def test_check_or_raise(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        with pytest.raises(KillSwitchEngagedError):
            ks.check_or_raise("data_export")

    def test_check_or_raise_passes(self):
        ks = KillSwitch()
        ks.check_or_raise("anything")


class TestHistory:
    def test_history_records_events(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        ks.disengage("tester")
        assert len(ks.get_history()) == 2

    def test_history_engaged_only(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        ks.disengage("tester")
        engaged = ks.get_history(engaged_only=True)
        assert len(engaged) == 1
        assert engaged[0].mode == KillSwitchMode.HALT_ALL

    def test_history_limit(self):
        ks = KillSwitch()
        for i in range(5):
            ks.engage(KillSwitchMode.HALT_ALL, f"test-{i}", "tester")
            ks.disengage("tester")
        assert len(ks.get_history(limit=3)) == 3

    def test_get_status(self):
        ks = KillSwitch()
        status = ks.get_status()
        assert status["mode"] == "DISENGAGED"
        assert status["engaged"] is False
        assert status["engagement_count"] == 0

    def test_get_status_after_engage(self):
        ks = KillSwitch()
        ks.engage(KillSwitchMode.HALT_ALL, "budget exceeded", "governor")
        status = ks.get_status()
        assert status["mode"] == "HALT_ALL"
        assert status["engaged"] is True
        assert status["engagement_count"] == 1
        assert status["last_engagement"]["reason"] == "budget exceeded"


class TestSubscribers:
    def test_subscriber_called(self):
        events = []
        ks = KillSwitch()
        ks.subscribe(lambda e: events.append(e))
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        assert len(events) == 1

    def test_subscriber_error_swallowed(self):
        ks = KillSwitch()
        ks.subscribe(lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
        ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
        assert ks.engaged


class TestPersistence:
    def test_persist_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            secret = b"test-secret"
            ks = KillSwitch(state_dir=state_dir, signing_secret=secret)
            ks.engage(KillSwitchMode.HALT_ALL, "persist test", "tester")
            loaded = KillSwitch.load_from_file(state_dir, signing_secret=secret)
            assert loaded.mode == KillSwitchMode.HALT_ALL

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = KillSwitch.load_from_file(Path(tmpdir), require_hmac=False)
            assert loaded.mode == KillSwitchMode.DISENGAGED

    def test_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            secret = b"test-secret"
            ks = KillSwitch(state_dir=state_dir, signing_secret=secret)
            ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
            state_file = state_dir / "kill_switch_state.json"
            data = json.loads(state_file.read_text())
            data["reason"] = "tampered"
            state_file.write_text(json.dumps(data))
            with pytest.raises(KillSwitchTamperError):
                KillSwitch.load_from_file(state_dir, signing_secret=secret)

    def test_persist_disengaged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            ks = KillSwitch(state_dir=state_dir, require_hmac=False)
            ks.engage(KillSwitchMode.HALT_ALL, "test", "tester")
            ks.disengage("tester")
            loaded = KillSwitch.load_from_file(state_dir, require_hmac=False)
            assert loaded.mode == KillSwitchMode.DISENGAGED


class TestConcurrencyToctou:
    """Concurrency tests for the TOCTOU fix in check_task_allowed (issue #317).

    The fix moved the ``is_critical = task_type in self._critical_tasks`` read
    inside ``with self._lock:`` so that ``(mode, is_critical)`` is a single
    atomic snapshot. These tests verify that a regression moving the read back
    outside the lock would be caught.

    ``_critical_tasks`` is an immutable ``frozenset`` set once at init with no
    mutation API, so the TOCTOU surface is the ``_mode`` field (mutated by
    ``engage``/``disengage`` under the lock). The invariant under test: every
    ``check_task_allowed`` result is consistent with exactly one observed mode.
    """

    def test_check_task_allowed_atomic_snapshot_under_concurrent_mode_mutation(self):
        """A concurrent engage/disengage must not produce an inconsistent decision.

        If ``is_critical`` were read outside the lock, a mode change between the
        ``is_critical`` read and the ``_mode`` read could allow a non-critical
        task through HALT_ALL (or block a critical task under DISENGAGED). This
        test asserts every result is consistent with the mode observed in the
        same locked critical section.
        """
        import threading

        ks = KillSwitch()
        critical_task = next(iter(ks.DEFAULT_CRITICAL_TASKS))
        non_critical_task = "definitely_not_critical_xyz"
        stop = threading.Event()
        errors: list[str] = []

        def mutator():
            while not stop.is_set():
                ks.engage(KillSwitchMode.HALT_ALL, "concurrent test", "mutator")
                ks.disengage("mutator")

        def checker():
            while not stop.is_set():
                for task_type in (critical_task, non_critical_task):
                    result = ks.check_task_allowed(task_type)
                    allowed = result["allowed"]
                    # Re-read mode AFTER the check; if the snapshot was atomic,
                    # the result must be consistent with EITHER the mode at
                    # check time OR this later read (mode only moves between
                    # DISENGAGED and HALT_ALL here). The forbidden outcome is:
                    # non-critical task allowed while mode is HALT_ALL, OR
                    # critical task blocked while mode is DISENGAGED.
                    mode_after = ks.mode
                    if mode_after == KillSwitchMode.HALT_ALL:
                        if not allowed and task_type == critical_task:
                            # Critical task blocked under HALT_ALL is allowed
                            # by the spec only if the snapshot saw HALT_ALL;
                            # but if mode was DISENGAGED at snapshot, it should
                            # have been allowed. A block here means the snapshot
                            # saw HALT_ALL (correct). This is fine.
                            pass
                        if allowed and task_type == non_critical_task:
                            errors.append(
                                f"non-critical allowed under HALT_ALL: {result}"
                            )
                    elif mode_after == KillSwitchMode.DISENGAGED:
                        if not allowed:
                            errors.append(
                                f"task blocked under DISENGAGED: {result}"
                            )

        threads = [threading.Thread(target=mutator) for _ in range(2)]
        threads += [threading.Thread(target=checker) for _ in range(4)]
        for t in threads:
            t.start()
        stop.wait(2.0)
        stop.set()
        for t in threads:
            t.join(timeout=5.0)
        assert not errors, f"TOCTOU invariant violated: {errors}"

    def test_critical_tasks_is_frozenset_and_immutable(self):
        """``_critical_tasks`` must be a frozenset so it cannot be mutated in place.

        This verifies issue #318's requirement that there are no mutation paths:
        a frozenset has no ``add``/``remove``/``discard`` methods, so the only
        way to change it is reassignment (which does not exist in the codebase).
        """
        ks = KillSwitch()
        assert isinstance(ks._critical_tasks, frozenset)
        assert not hasattr(ks._critical_tasks, "add")
        assert not hasattr(ks._critical_tasks, "remove")
        assert not hasattr(ks._critical_tasks, "discard")

    def test_no_public_mutation_api_for_critical_tasks(self):
        """There must be no add_critical_task/remove_critical_task methods.

        If such methods existed without holding ``self._lock``, the TOCTOU would
        relocate from ``_mode`` to ``_critical_tasks``. Their absence means the
        only write is the single init-time assignment (already under no
        concurrency since __init__ runs before the object is shared).
        """
        ks = KillSwitch()
        assert not hasattr(ks, "add_critical_task")
        assert not hasattr(ks, "remove_critical_task")
        assert not hasattr(ks, "set_critical_tasks")
