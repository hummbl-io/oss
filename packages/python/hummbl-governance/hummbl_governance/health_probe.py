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

"""Health Probe -- Generic health checking framework.

Provides a minimal, stdlib-only health probe interface and collector
for aggregating health status across multiple system components.

Usage:
    from hummbl_governance.health_probe import (
        HealthCollector, HealthProbe, HealthReport, ProbeResult,
    )

    class DatabaseProbe(HealthProbe):
        @property
        def name(self) -> str:
            return "database"

        def check(self) -> ProbeResult:
            try:
                db.ping()
                return ProbeResult(name=self.name, healthy=True, message="OK")
            except Exception as e:
                return ProbeResult(name=self.name, healthy=False, message=str(e))

    collector = HealthCollector([DatabaseProbe()])
    report = collector.check_all()
    print(report.overall_healthy, report.probes)

Extracted from hummbl-governance's health.py (930 LOC) -- stripped of all
project-specific probes, CLI, Path constants, env checks, and subprocess
calls. Users implement HealthProbe subclasses for their own services.

Stdlib-only: time, logging, dataclasses, datetime, typing, abc.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """Result of a single health probe check."""

    name: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0.0
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(
                self,
                "timestamp",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )


class HealthProbe(ABC):
    """Abstract base class for health probes.

    Subclasses must implement ``name`` (property) and ``check()`` (method).
    The collector handles latency tracking and exception safety around
    each probe invocation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this probe."""

    @abstractmethod
    def check(self) -> ProbeResult:
        """Execute the health check and return a result.

        Implementations should return a ProbeResult with ``healthy=False``
        on failure rather than raising exceptions, but the collector will
        catch and wrap any unhandled exceptions as unhealthy results.
        """


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Aggregated health report from all probes."""

    overall_healthy: bool
    probes: list[ProbeResult]
    timestamp: str = ""
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(
                self,
                "timestamp",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )


class HealthCollector:
    """Runs multiple probes and aggregates results into a HealthReport.

    Individual probe failures (uncaught exceptions) are caught and
    recorded as unhealthy ProbeResults -- they never crash the collector.
    """

    def __init__(self, probes: list[HealthProbe] | None = None) -> None:
        self._probes: list[HealthProbe] = list(probes) if probes else []

    def register(self, probe: HealthProbe) -> None:
        """Add a probe to the collector."""
        self._probes.append(probe)

    @property
    def probe_names(self) -> list[str]:
        """Return the names of all registered probes."""
        return [p.name for p in self._probes]

    def check_all(self) -> HealthReport:
        """Run all registered probes and return an aggregated report."""
        collector_start = time.monotonic()
        results: list[ProbeResult] = []

        for probe in self._probes:
            result = self._run_probe(probe)
            results.append(result)

        duration_ms = round((time.monotonic() - collector_start) * 1000, 2)
        overall = all(r.healthy for r in results) if results else True

        return HealthReport(
            overall_healthy=overall,
            probes=results,
            duration_ms=duration_ms,
        )

    def check_one(self, name: str) -> ProbeResult:
        """Run a single probe by name.

        Raises ``KeyError`` if no probe with the given name is registered.
        """
        for probe in self._probes:
            if probe.name == name:
                return self._run_probe(probe)
        raise KeyError(f"No probe registered with name: {name!r}")

    def _run_probe(self, probe: HealthProbe) -> ProbeResult:
        """Execute a single probe with latency tracking and exception safety."""
        start = time.monotonic()
        try:
            result = probe.check()
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            logger.warning("Probe %r crashed: %s", probe.name, exc)
            return ProbeResult(
                name=probe.name,
                healthy=False,
                message=f"Probe crashed: {exc}",
                latency_ms=elapsed_ms,
            )

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)

        # Inject latency if the probe didn't set it
        if result.latency_ms == 0.0:
            result = ProbeResult(
                name=result.name,
                healthy=result.healthy,
                message=result.message,
                latency_ms=elapsed_ms,
                timestamp=result.timestamp,
                metadata=result.metadata,
            )

        return result
