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

"""CLI entry point for health_probe.

Outputs JSON with:
    - overall_status: healthy | degraded | unhealthy
    - probes: dict of probe name -> {status, message, latency_ms}

Usage:
    python -m hummbl_governance.services.health
    python -m hummbl_governance.services.health --pretty
    python -m hummbl_governance.services.health --check  # exit 0 healthy, 1 degraded, 2 unhealthy

This is a compatibility shim for skills that call
``python -m hummbl_governance.services.health``. It delegates to
``hummbl_governance.health_probe.HealthCollector`` with zero registered
probes (returns healthy by default). Register probes by importing this
module and calling ``register_default_probes()`` or by subclassing.

Stdlib-only: json, sys, argparse.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from hummbl_governance.health_probe import HealthCollector, HealthReport


def _report_to_dict(report: HealthReport) -> dict[str, Any]:
    """Convert a HealthReport to the dict format skills expect."""
    probes: dict[str, dict[str, Any]] = {}
    for r in report.probes:
        probes[r.name] = {
            "status": "healthy" if r.healthy else "unhealthy",
            "message": r.message,
            "latency_ms": r.latency_ms,
            "timestamp": r.timestamp,
        }
    if report.overall_healthy:
        overall = "healthy"
    elif any(not r.healthy for r in report.probes):
        overall = "unhealthy"
    else:
        overall = "degraded"
    return {
        "overall_status": overall,
        "probes": probes,
        "timestamp": report.timestamp,
        "duration_ms": report.duration_ms,
    }


def _build_default_collector() -> HealthCollector:
    """Build a collector with default probes.

    Currently returns an empty collector (healthy by default). Override
    this function or register probes directly to add real probes.
    """
    return HealthCollector(probes=[])


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        0 if healthy, 1 if degraded, 2 if unhealthy.
    """
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_governance.services.health",
        description="Run health probes and output JSON.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit-code mode: 0 healthy, 1 degraded, 2 unhealthy. No stdout.",
    )
    args = parser.parse_args(argv)

    collector = _build_default_collector()
    report = collector.check_all()
    data = _report_to_dict(report)

    if args.check:
        if data["overall_status"] == "healthy":
            return 0
        if data["overall_status"] == "degraded":
            return 1
        return 2

    indent = 2 if args.pretty else None
    json.dump(data, sys.stdout, indent=indent, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
