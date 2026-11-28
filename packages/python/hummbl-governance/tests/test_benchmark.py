# Copyright 2024-2026 HUMMBL
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

"""Unit tests for BaseBenchmark lifecycle, locking, and setup timing."""

from __future__ import annotations

import time
from typing import Dict

from hummbl_governance.benchmark import (
    BaseBenchmark,
    BenchmarkConfig,
    BenchmarkState,
)


class _SleepySetupBenchmark(BaseBenchmark):
    """Minimal concrete benchmark with measurable setup work."""

    def __init__(self, config: BenchmarkConfig, setup_sleep: float = 0.02) -> None:
        super().__init__(config)
        self._setup_sleep = setup_sleep
        self.setup_calls = 0
        self.teardown_calls = 0
        self.iteration_calls = 0

    def on_setup(self) -> None:
        self.setup_calls += 1
        time.sleep(self._setup_sleep)

    def on_teardown(self) -> None:
        self.teardown_calls += 1

    def run_single_iteration(self) -> Dict[str, float]:
        self.iteration_calls += 1
        return {"score": float(self.iteration_calls)}


def test_run_calls_setup_without_deadlock_and_measures_setup_duration() -> None:
    """run() must invoke setup() re-entrantly without deadlocking and record setup_duration."""
    bench = _SleepySetupBenchmark(
        BenchmarkConfig(
            name="reentrant-setup",
            iterations=3,
            warmup_iterations=1,
            bootstrap_samples=200,
        ),
        setup_sleep=0.02,
    )

    result = bench.run()

    assert result.state == BenchmarkState.COMPLETE
    assert bench.setup_calls == 1
    assert bench.teardown_calls == 1
    assert bench.iteration_calls == 4  # 1 warmup + 3 measured
    assert result.setup_duration_seconds >= 0.015
    assert result.total_duration_seconds >= 0.0
    assert result.teardown_duration_seconds >= 0.0
    assert "score" in result.metrics
    assert len(result.metrics["score"].values) == 3
    assert result.metrics["score"].confidence_interval is not None


def test_explicit_setup_before_run_preserves_setup_duration() -> None:
    """Calling setup() explicitly before run() should also report non-zero setup_duration."""
    bench = _SleepySetupBenchmark(
        BenchmarkConfig(
            name="explicit-setup",
            iterations=2,
            warmup_iterations=0,
            bootstrap_samples=200,
        ),
        setup_sleep=0.02,
    )

    bench.setup()
    assert bench.state == BenchmarkState.SETUP

    result = bench.run()

    assert result.state == BenchmarkState.COMPLETE
    assert bench.setup_calls == 1
    assert result.setup_duration_seconds >= 0.015
