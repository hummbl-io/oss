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

"""Tests for hummbl_governance.health_probe module.

Covers ProbeResult, HealthProbe (abstract), HealthCollector, and HealthReport
with 20+ tests using concrete mock probe implementations.
"""

from __future__ import annotations

import time
import unittest

from hummbl_governance.health_probe import (
    HealthCollector,
    HealthProbe,
    HealthReport,
    ProbeResult,
)


# ---------------------------------------------------------------------------
# Concrete probe implementations for testing
# ---------------------------------------------------------------------------


class AlwaysHealthyProbe(HealthProbe):
    """Probe that always reports healthy."""

    @property
    def name(self) -> str:
        return "always_healthy"

    def check(self) -> ProbeResult:
        return ProbeResult(name=self.name, healthy=True, message="OK")


class AlwaysUnhealthyProbe(HealthProbe):
    """Probe that always reports unhealthy."""

    @property
    def name(self) -> str:
        return "always_unhealthy"

    def check(self) -> ProbeResult:
        return ProbeResult(name=self.name, healthy=False, message="down")


class CrashingProbe(HealthProbe):
    """Probe that raises an exception."""

    @property
    def name(self) -> str:
        return "crasher"

    def check(self) -> ProbeResult:
        raise RuntimeError("probe exploded")


class SlowProbe(HealthProbe):
    """Probe that takes measurable time."""

    def __init__(self, delay_seconds: float = 0.05) -> None:
        self._delay = delay_seconds

    @property
    def name(self) -> str:
        return "slow_probe"

    def check(self) -> ProbeResult:
        time.sleep(self._delay)
        return ProbeResult(name=self.name, healthy=True, message="slow but ok")


class MetadataProbe(HealthProbe):
    """Probe that returns metadata."""

    @property
    def name(self) -> str:
        return "metadata_probe"

    def check(self) -> ProbeResult:
        return ProbeResult(
            name=self.name,
            healthy=True,
            message="with metadata",
            metadata={"version": "1.0", "connections": 42},
        )


class SelfTimedProbe(HealthProbe):
    """Probe that sets its own latency_ms."""

    @property
    def name(self) -> str:
        return "self_timed"

    def check(self) -> ProbeResult:
        return ProbeResult(
            name=self.name,
            healthy=True,
            message="I timed myself",
            latency_ms=99.9,
        )


# ---------------------------------------------------------------------------
# TestProbeResult
# ---------------------------------------------------------------------------


class TestProbeResult(unittest.TestCase):
    """Tests for the ProbeResult dataclass."""

    def test_creation_minimal(self) -> None:
        r = ProbeResult(name="test", healthy=True)
        self.assertEqual(r.name, "test")
        self.assertTrue(r.healthy)
        self.assertEqual(r.message, "")
        self.assertEqual(r.latency_ms, 0.0)
        self.assertEqual(r.metadata, {})

    def test_creation_full(self) -> None:
        r = ProbeResult(
            name="db",
            healthy=False,
            message="connection refused",
            latency_ms=12.5,
            timestamp="2026-03-23T10:00:00Z",
            metadata={"host": "localhost"},
        )
        self.assertEqual(r.name, "db")
        self.assertFalse(r.healthy)
        self.assertEqual(r.message, "connection refused")
        self.assertAlmostEqual(r.latency_ms, 12.5)
        self.assertEqual(r.timestamp, "2026-03-23T10:00:00Z")
        self.assertEqual(r.metadata, {"host": "localhost"})

    def test_auto_timestamp(self) -> None:
        r = ProbeResult(name="ts", healthy=True)
        self.assertTrue(r.timestamp.endswith("Z"))
        self.assertGreater(len(r.timestamp), 10)

    def test_explicit_timestamp_preserved(self) -> None:
        r = ProbeResult(name="ts", healthy=True, timestamp="custom")
        self.assertEqual(r.timestamp, "custom")

    def test_frozen(self) -> None:
        r = ProbeResult(name="frozen", healthy=True)
        with self.assertRaises(AttributeError):
            r.healthy = False  # type: ignore[misc]

    def test_metadata_default_factory(self) -> None:
        r1 = ProbeResult(name="a", healthy=True)
        r2 = ProbeResult(name="b", healthy=True)
        # Each gets its own dict instance
        self.assertIsNot(r1.metadata, r2.metadata)


# ---------------------------------------------------------------------------
# TestHealthProbe
# ---------------------------------------------------------------------------


class TestHealthProbe(unittest.TestCase):
    """Tests for the HealthProbe abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        with self.assertRaises(TypeError):
            HealthProbe()  # type: ignore[abstract]

    def test_must_implement_name(self) -> None:
        class MissingName(HealthProbe):
            def check(self) -> ProbeResult:
                return ProbeResult(name="x", healthy=True)

        with self.assertRaises(TypeError):
            MissingName()  # type: ignore[abstract]

    def test_must_implement_check(self) -> None:
        class MissingCheck(HealthProbe):
            @property
            def name(self) -> str:
                return "missing_check"

        with self.assertRaises(TypeError):
            MissingCheck()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        probe = AlwaysHealthyProbe()
        result = probe.check()
        self.assertEqual(result.name, "always_healthy")
        self.assertTrue(result.healthy)


# ---------------------------------------------------------------------------
# TestHealthCollector
# ---------------------------------------------------------------------------


class TestHealthCollector(unittest.TestCase):
    """Tests for the HealthCollector class."""

    def test_all_healthy(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe()])
        report = collector.check_all()
        self.assertTrue(report.overall_healthy)
        self.assertEqual(len(report.probes), 1)
        self.assertTrue(report.probes[0].healthy)

    def test_one_unhealthy(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe(), AlwaysUnhealthyProbe()])
        report = collector.check_all()
        self.assertFalse(report.overall_healthy)
        self.assertEqual(len(report.probes), 2)

    def test_probe_exception_caught(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe(), CrashingProbe()])
        report = collector.check_all()
        self.assertFalse(report.overall_healthy)
        crasher = [r for r in report.probes if r.name == "crasher"][0]
        self.assertFalse(crasher.healthy)
        self.assertIn("Probe crashed", crasher.message)
        self.assertIn("probe exploded", crasher.message)

    def test_empty_probes(self) -> None:
        collector = HealthCollector([])
        report = collector.check_all()
        self.assertTrue(report.overall_healthy)
        self.assertEqual(len(report.probes), 0)

    def test_no_probes_default(self) -> None:
        collector = HealthCollector()
        report = collector.check_all()
        self.assertTrue(report.overall_healthy)

    def test_check_one_found(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe(), AlwaysUnhealthyProbe()])
        result = collector.check_one("always_unhealthy")
        self.assertEqual(result.name, "always_unhealthy")
        self.assertFalse(result.healthy)

    def test_check_one_not_found(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe()])
        with self.assertRaises(KeyError):
            collector.check_one("nonexistent")

    def test_check_one_exception_caught(self) -> None:
        collector = HealthCollector([CrashingProbe()])
        result = collector.check_one("crasher")
        self.assertFalse(result.healthy)
        self.assertIn("Probe crashed", result.message)

    def test_latency_tracked(self) -> None:
        collector = HealthCollector([SlowProbe(delay_seconds=0.05)])
        report = collector.check_all()
        self.assertEqual(len(report.probes), 1)
        # Should have at least 40ms of latency (sleep is 50ms)
        self.assertGreaterEqual(report.probes[0].latency_ms, 40.0)

    def test_self_timed_probe_latency_preserved(self) -> None:
        collector = HealthCollector([SelfTimedProbe()])
        report = collector.check_all()
        # Probe set its own latency to 99.9 -- collector should preserve it
        self.assertAlmostEqual(report.probes[0].latency_ms, 99.9)

    def test_overall_healthy_all_must_pass(self) -> None:
        probes = [AlwaysHealthyProbe(), AlwaysHealthyProbe()]
        collector = HealthCollector(probes)
        report = collector.check_all()
        self.assertTrue(report.overall_healthy)

        # Now add an unhealthy one
        collector.register(AlwaysUnhealthyProbe())
        report = collector.check_all()
        self.assertFalse(report.overall_healthy)

    def test_register(self) -> None:
        collector = HealthCollector()
        self.assertEqual(len(collector.probe_names), 0)
        collector.register(AlwaysHealthyProbe())
        self.assertEqual(collector.probe_names, ["always_healthy"])

    def test_probe_names(self) -> None:
        collector = HealthCollector([AlwaysHealthyProbe(), CrashingProbe()])
        self.assertEqual(collector.probe_names, ["always_healthy", "crasher"])

    def test_metadata_preserved(self) -> None:
        collector = HealthCollector([MetadataProbe()])
        report = collector.check_all()
        result = report.probes[0]
        self.assertEqual(result.metadata["version"], "1.0")
        self.assertEqual(result.metadata["connections"], 42)

    def test_duration_ms_tracked(self) -> None:
        collector = HealthCollector([SlowProbe(delay_seconds=0.05)])
        report = collector.check_all()
        self.assertGreaterEqual(report.duration_ms, 40.0)

    def test_multiple_probes_order_preserved(self) -> None:
        probes = [AlwaysHealthyProbe(), CrashingProbe(), AlwaysUnhealthyProbe()]
        collector = HealthCollector(probes)
        report = collector.check_all()
        names = [r.name for r in report.probes]
        self.assertEqual(names, ["always_healthy", "crasher", "always_unhealthy"])


# ---------------------------------------------------------------------------
# TestHealthReport
# ---------------------------------------------------------------------------


class TestHealthReport(unittest.TestCase):
    """Tests for the HealthReport dataclass."""

    def test_creation(self) -> None:
        probes = [ProbeResult(name="a", healthy=True)]
        report = HealthReport(overall_healthy=True, probes=probes, duration_ms=5.0)
        self.assertTrue(report.overall_healthy)
        self.assertEqual(len(report.probes), 1)
        self.assertAlmostEqual(report.duration_ms, 5.0)

    def test_auto_timestamp(self) -> None:
        report = HealthReport(overall_healthy=True, probes=[], duration_ms=0.0)
        self.assertTrue(report.timestamp.endswith("Z"))

    def test_explicit_timestamp(self) -> None:
        report = HealthReport(
            overall_healthy=True,
            probes=[],
            timestamp="2026-01-01T00:00:00Z",
            duration_ms=0.0,
        )
        self.assertEqual(report.timestamp, "2026-01-01T00:00:00Z")

    def test_frozen(self) -> None:
        report = HealthReport(overall_healthy=True, probes=[], duration_ms=0.0)
        with self.assertRaises(AttributeError):
            report.overall_healthy = False  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
