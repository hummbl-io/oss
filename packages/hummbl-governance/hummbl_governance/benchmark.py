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
# SPDX-License-Identifier: MIT OR Apache-2.0

"""BaseBenchmark -- lifecycle and metrics pattern for benchmark runners.

Adapts the hummbl-governance BaseModule pattern for benchmark execution:
    1. Define a config dataclass (or use BenchmarkConfig)
    2. Implement run_benchmark() -> BenchmarkResult
    3. Optionally override on_setup / on_teardown for lifecycle hooks

The framework handles:
    - Lifecycle management (init → setup → running → teardown → complete)
    - Metrics (execution time, accuracy, throughput, custom metrics)
    - Statistical analysis (bootstrap CI, significance testing)
    - Result aggregation and reporting

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import logging
import math
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from hummbl_governance.statistical_framework import (
    bootstrap_confidence_interval,
    calculate_effect_size,
    ks_test,
    population_stability_index
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class BenchmarkState(Enum):
    """Benchmark lifecycle states."""

    INIT = auto()          # Constructed, not yet setup
    SETUP = auto()         # Preparing to run (loading models, data)
    RUNNING = auto()       # Actively executing benchmark
    TEARDOWN = auto()      # Cleanup in progress
    COMPLETE = auto()      # Successfully completed
    ERROR = auto()         # Unrecoverable error


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    """Base configuration for benchmarks. Subclass for domain-specific config."""

    name: str = "unnamed"
    description: str = ""
    iterations: int = 100                # Number of benchmark iterations
    warmup_iterations: int = 10          # Warmup iterations before measurement
    confidence_level: float = 0.95       # For confidence intervals
    bootstrap_samples: int = 10000       # For bootstrap CI
    random_seed: Optional[int] = None    # For reproducibility
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Result for a single metric with statistical analysis."""

    name: str
    values: List[float]
    mean: float
    median: float
    std: float
    min: float
    max: float
    confidence_interval: Optional[Dict[str, float]] = None
    unit: str = ""


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Complete benchmark result with metrics and metadata."""

    config: BenchmarkConfig
    state: BenchmarkState
    metrics: Dict[str, MetricResult]
    total_duration_seconds: float
    setup_duration_seconds: float = 0.0
    teardown_duration_seconds: float = 0.0
    error_message: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


@dataclass(slots=True)
class _BenchmarkMetrics:
    """Internal mutable metrics tracker."""

    execution_times: List[float] = field(default_factory=list)
    custom_metrics: Dict[str, List[float]] = field(default_factory=dict)
    errors: int = 0
    start_time: float = 0.0
    setup_start: float = 0.0
    teardown_start: float = 0.0


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BaseBenchmark(ABC):
    """Abstract base for all benchmark runners.

    Subclasses MUST implement:
        run_single_iteration() -> Dict[str, float]

    Subclasses MAY override:
        on_setup()  -- called before benchmark loop
        on_teardown()  -- called after benchmark loop
        validate_config()  -- validate configuration before setup
    """

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        self._config = config or BenchmarkConfig()
        self._state = BenchmarkState.INIT
        self._metrics = _BenchmarkMetrics()
        self._lock = threading.Lock()

    # -- Properties ----------------------------------------------------------

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def state(self) -> BenchmarkState:
        return self._state

    @property
    def config(self) -> BenchmarkConfig:
        return self._config

    # -- Lifecycle -----------------------------------------------------------

    def setup(self) -> None:
        """Transition to SETUP. Calls on_setup() hook."""
        with self._lock:
            if self._state in (BenchmarkState.RUNNING, BenchmarkState.TEARDOWN):
                return
            self._metrics.setup_start = time.monotonic()
            try:
                self.validate_config()
                self.on_setup()
                self._state = BenchmarkState.SETUP
                logger.info("Benchmark %s setup complete", self.name)
            except Exception as exc:
                self._state = BenchmarkState.ERROR
                self._metrics.errors += 1
                logger.error("Benchmark %s setup failed: %s", self.name, exc)
                raise

    def run(self) -> BenchmarkResult:
        """Execute the full benchmark lifecycle and return results.

        This is the main entry point for benchmark execution:
        1. Setup (if not already setup)
        2. Warmup iterations
        3. Measured iterations
        4. Teardown
        5. Result aggregation with statistical analysis
        """
        with self._lock:
            if self._state == BenchmarkState.RUNNING:
                raise RuntimeError(f"Benchmark {self.name} is already running")

            # Setup if needed
            if self._state == BenchmarkState.INIT:
                self.setup()

            # Transition to running
            self._state = BenchmarkState.RUNNING
            self._metrics.start_time = time.monotonic()

            try:
                # Warmup iterations (not measured)
                logger.info("Benchmark %s: %d warmup iterations", self.name, self._config.warmup_iterations)
                for i in range(self._config.warmup_iterations):
                    try:
                        self.run_single_iteration()
                    except Exception as exc:
                        logger.warning("Warmup iteration %d failed: %s", i, exc)

                # Measured iterations
                logger.info("Benchmark %s: %d measured iterations", self.name, self._config.iterations)
                for i in range(self._config.iterations):
                    try:
                        iteration_start = time.monotonic()
                        metrics = self.run_single_iteration()
                        iteration_duration = time.monotonic() - iteration_start

                        # Track execution time
                        self._metrics.execution_times.append(iteration_duration)

                        # Track custom metrics
                        for metric_name, metric_value in metrics.items():
                            if metric_name not in self._metrics.custom_metrics:
                                self._metrics.custom_metrics[metric_name] = []
                            self._metrics.custom_metrics[metric_name].append(float(metric_value))

                    except Exception as exc:
                        self._metrics.errors += 1
                        logger.error("Iteration %d failed: %s", i, exc)

                # Teardown
                self._metrics.teardown_start = time.monotonic()
                self.on_teardown()
                self._state = BenchmarkState.COMPLETE

                # Calculate total duration
                total_duration = time.monotonic() - self._metrics.start_time
                setup_duration = self._metrics.setup_start - self._metrics.setup_start
                teardown_duration = time.monotonic() - self._metrics.teardown_start

                # Build result with statistical analysis
                result = self._build_result(
                    total_duration=total_duration,
                    setup_duration=setup_duration,
                    teardown_duration=teardown_duration
                )

                logger.info("Benchmark %s complete: %d iterations, %d errors",
                           self.name, self._config.iterations, self._metrics.errors)

                return result

            except Exception as exc:
                self._state = BenchmarkState.ERROR
                self._metrics.errors += 1
                logger.error("Benchmark %s failed: %s", self.name, exc)

                # Return error result
                return BenchmarkResult(
                    config=self._config,
                    state=BenchmarkState.ERROR,
                    metrics={},
                    total_duration_seconds=time.monotonic() - self._metrics.start_time,
                    error_message=str(exc)
                )

    # -- Hooks ----------------------------------------------------------------

    def validate_config(self) -> None:
        """Validate configuration before setup. Override for custom validation."""
        if self._config.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self._config.warmup_iterations < 0:
            raise ValueError("warmup_iterations must be non-negative")
        if not 0 < self._config.confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if self._config.bootstrap_samples <= 0:
            raise ValueError("bootstrap_samples must be positive")

    def on_setup(self) -> None:
        """Setup hook called before benchmark loop. Override for custom setup."""
        pass

    def on_teardown(self) -> None:
        """Teardown hook called after benchmark loop. Override for custom cleanup."""
        pass

    # -- Abstract method ------------------------------------------------------

    @abstractmethod
    def run_single_iteration(self) -> Dict[str, float]:
        """Execute a single benchmark iteration.

        Returns:
            Dictionary of custom metric names to values (e.g., {"accuracy": 0.95})
        """
        pass

    # -- Result building ------------------------------------------------------

    def _build_result(
        self,
        total_duration: float,
        setup_duration: float,
        teardown_duration: float
    ) -> BenchmarkResult:
        """Build BenchmarkResult with statistical analysis."""
        metrics: Dict[str, MetricResult] = {}

        # Process execution time metric
        if self._metrics.execution_times:
            metrics["execution_time"] = self._build_metric_result(
                "execution_time",
                self._metrics.execution_times,
                unit="seconds"
            )

        # Process custom metrics
        for metric_name, values in self._metrics.custom_metrics.items():
            metrics[metric_name] = self._build_metric_result(
                metric_name,
                values,
                unit=""
            )

        return BenchmarkResult(
            config=self._config,
            state=self._state,
            metrics=metrics,
            total_duration_seconds=total_duration,
            setup_duration_seconds=setup_duration,
            teardown_duration_seconds=teardown_duration
        )

    def _build_metric_result(
        self,
        name: str,
        values: List[float],
        unit: str
    ) -> MetricResult:
        """Build MetricResult with statistical analysis."""
        if not values:
            raise ValueError(f"No values for metric {name}")

        # Basic statistics
        mean_val = sum(values) / len(values)
        sorted_values = sorted(values)
        median_val = sorted_values[len(sorted_values) // 2]
        std_val = math.sqrt(sum((x - mean_val) ** 2 for x in values) / len(values))
        min_val = min(values)
        max_val = max(values)

        # Bootstrap confidence interval
        ci = None
        if len(values) >= 2:
            try:
                ci = bootstrap_confidence_interval(
                    values=values,
                    confidence_level=self._config.confidence_level,
                    n_bootstrap=self._config.bootstrap_samples,
                    random_seed=self._config.random_seed
                )
            except Exception as exc:
                logger.warning("Bootstrap CI failed for %s: %s", name, exc)

        return MetricResult(
            name=name,
            values=values,
            mean=mean_val,
            median=median_val,
            std=std_val,
            min=min_val,
            max=max_val,
            confidence_interval=ci,
            unit=unit
        )


# ---------------------------------------------------------------------------
# Comparison utilities
# ---------------------------------------------------------------------------

def compare_benchmarks(
    result_a: BenchmarkResult,
    result_b: BenchmarkResult,
    metric_name: str = "execution_time"
) -> Dict[str, Any]:
    """Compare two benchmark results for statistical significance.

    Performs:
    - Effect size calculation (Cohen's d)
    - Kolmogorov-Smirnov test for distribution difference
    - Population Stability Index for drift detection

    Args:
        result_a: First benchmark result
        result_b: Second benchmark result
        metric_name: Metric to compare (must exist in both results)

    Returns:
        Dictionary with comparison statistics
    """
    if metric_name not in result_a.metrics or metric_name not in result_b.metrics:
        raise ValueError(f"Metric {metric_name} not found in both results")

    values_a = result_a.metrics[metric_name].values
    values_b = result_b.metrics[metric_name].values

    # Effect size
    effect_size = calculate_effect_size(values_a, values_b)

    # KS test
    ks_result = ks_test(values_a, values_b)

    # PSI (drift detection)
    psi_result = population_stability_index(values_a, values_b)

    return {
        "metric": metric_name,
        "effect_size": effect_size,
        "ks_test": ks_result,
        "psi": psi_result,
        "mean_a": result_a.metrics[metric_name].mean,
        "mean_b": result_b.metrics[metric_name].mean,
        "median_a": result_a.metrics[metric_name].median,
        "median_b": result_b.metrics[metric_name].median,
    }
