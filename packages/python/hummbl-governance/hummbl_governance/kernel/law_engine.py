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

"""Law Engine — K2 invariant enforcement.

Every receipt is evaluated against at least one scaling law.
The Kernel loads the Scaling Law Atlas at boot.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class ScalingLaw:
    """A scaling law record."""

    law_id: str
    name: str
    status: str = "candidate.accepted"  # candidate.accepted, empirically.tested, ratified, deprecated
    statement: str = ""
    falsification_criterion: str = ""
    experiment_receipts: list[str] = field(default_factory=list)
    boundary_conditions: list[str] = field(default_factory=list)
    related_modules: list[str] = field(default_factory=list)


@dataclass
class Violation:
    """A scaling law violation."""

    law_id: str
    severity: str  # CRITICAL, WARNING, INFO
    agent_id: str
    timestamp: str
    message: str
    detail: str
    actual_value: Any = None
    threshold_value: Any = None


class LawEngine:
    """Engine for loading scaling laws and evaluating receipts against them."""

    def __init__(self, atlas_dir: Path | None = None) -> None:
        if atlas_dir is None:
            # Resolution order:
            # 1. HUMMBL_KERNEL_ATLAS_DIR environment variable
            # 2. Package data directory (bundled with hummbl-governance)
            # 3. Relative path from repo root
            # 4. Home directory (legacy external atlas)
            # 5. Empty (degraded mode — no laws loaded)
            env_dir = os.environ.get("HUMMBL_KERNEL_ATLAS_DIR")
            if env_dir:
                atlas_dir = Path(env_dir)
            else:
                # Package data directory — bundled atlas shipped with the library
                pkg_atlas = Path(__file__).resolve().parents[1] / "data" / "atlas"
                candidates = [
                    pkg_atlas,
                    Path("_internal/research/2026-06-17-scaling-law-atlas/records"),
                    Path.home() / "_internal" / "research" / "2026-06-17-scaling-law-atlas" / "records",
                ]
                for candidate in candidates:
                    if candidate.exists():
                        atlas_dir = candidate
                        break
                else:
                    atlas_dir = Path("/dev/null")  # nonexistent → degraded mode
        self.atlas_dir = atlas_dir
        self.laws: dict[str, ScalingLaw] = {}
        self._load_atlas()

    def _load_atlas(self) -> None:
        """Load all scaling law records from the atlas directory."""
        if not self.atlas_dir.exists():
            return
        for file in self.atlas_dir.glob("SL-*.yaml"):
            try:
                import yaml
                data = yaml.safe_load(file.read_text())
            except ImportError:
                # Fallback: parse YAML-ish manually for stdlib-only operation
                data = self._parse_yamlish(file.read_text())
            if data:
                # YAML uses 'id' and 'title'; map to our schema
                law_id = data.get("id") or data.get("record_id") or data.get("law_id", file.stem)
                name = data.get("title") or data.get("name", "")
                status = data.get("status", "candidate.accepted")
                statement = data.get("candidate_law_statement", "") or data.get("description", "")
                falsification = data.get("falsification_criterion", "")
                if not falsification and "failure_envelope" in data:
                    falsification = str(data["failure_envelope"])[:200]
                self.laws[law_id] = ScalingLaw(
                    law_id=law_id,
                    name=name,
                    status=status,
                    statement=statement,
                    falsification_criterion=falsification,
                    experiment_receipts=data.get("experiment_receipts", []),
                    boundary_conditions=data.get("boundary_conditions", []),
                    related_modules=data.get("related_modules", []),
                )

    def _parse_yamlish(self, text: str) -> dict[str, Any]:
        """Minimal YAML subset parser for scaling law record files.

        Supports the YAML subset used by SL-*.yaml atlas:
        - key: value pairs (quoted strings, booleans, nulls)
        - key: (empty) followed by an indented block list -- e.g.
          boundary_conditions, related_modules, experiment_receipts
        - Inline lists: [a, b, c]

        This is a fallback for stdlib-only operation when PyYAML is
        not available. Merges the original block-list parser with
        inline-list and scalar-literal support so no atlas fields are
        dropped (Codex review finding: the two prior parsers were
        never merged, silently dropping block-list fields).
        """
        result: dict[str, Any] = {}
        current_key = ""
        current_list: list[str] = []

        def _flush() -> None:
            if current_key and current_list:
                result[current_key] = list(current_list)

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Block list item: "- value" (continuation of current_key)
            if stripped.startswith("-"):
                item = stripped[1:].strip().strip(chr(34)).strip("'")
                current_list.append(item)
                continue

            # key: value  OR  key: (empty, block list follows)
            if ":" in stripped:
                colon_idx = stripped.index(":")
                key = stripped[:colon_idx].strip()
                raw_value = stripped[colon_idx + 1:].strip()
                if not key:
                    continue

                # Starting a new key -- flush any pending block list
                # from the previous key first.
                _flush()
                current_list = []
                current_key = key

                if not raw_value:
                    # Empty value: either a block list follows on
                    # subsequent lines, or the key is genuinely empty.
                    # Default to None; overwritten if items follow.
                    result[current_key] = None
                elif raw_value.lower() == "true":
                    result[current_key] = True
                elif raw_value.lower() == "false":
                    result[current_key] = False
                elif raw_value.lower() in ("null", "~"):
                    result[current_key] = None
                elif raw_value.startswith("[") and raw_value.endswith("]"):
                    result[current_key] = [
                        v.strip().strip("'").strip(chr(34))
                        for v in raw_value[1:-1].split(",")
                        if v.strip()
                    ]
                else:
                    result[current_key] = raw_value.strip(chr(34)).strip("'")

        # Flush the final pending block list
        _flush()
        return result

    def evaluate(self, receipt: dict[str, Any]) -> list[Violation]:
        """Evaluate a receipt against all loaded scaling laws.

        Returns list of violations.
        """
        violations: list[Violation] = []
        agent_id = receipt.get("agent_id", "unknown")
        timestamp = receipt.get("timestamp", "")
        payload = receipt.get("payload", {})

        for law in self.laws.values():
            v = self._check_law(law, agent_id, timestamp, payload)
            if v:
                violations.append(v)

        return violations

    def _check_law(
        self, law: ScalingLaw, agent_id: str, timestamp: str, payload: dict[str, Any]
    ) -> Violation | None:
        """Check a single law against receipt payload.

        This is a simplified rule-based checker. Full implementation
        would compile law checks into evaluable functions.
        """
        # SL-07: Delegation depth
        if law.law_id == "SL-07":
            depth_match = re.search(r"depth[=:]\s*(\d+)", str(payload))
            if depth_match:
                depth = int(depth_match.group(1))
                if depth > 3:
                    return Violation(
                        law_id="SL-07",
                        severity="CRITICAL" if depth > 3 else "WARNING",
                        agent_id=agent_id,
                        timestamp=timestamp,
                        message=str(payload)[:200],
                        detail=f"Delegation depth {depth} exceeds max 3",
                        actual_value=depth,
                        threshold_value=3,
                    )

        # SL-10: Constraint refresh
        if law.law_id == "SL-10":
            msg = str(payload)
            # Only trigger if we see a step count that exceeds threshold
            steps_match = re.search(r"step[=:]\s*(\d+)", msg)
            if steps_match:
                steps = int(steps_match.group(1))
                # Violation if steps > 10 AND no positive refresh marker
                # Positive markers: "constraint.refresh applied", "constraint.refresh=true", "refreshed"
                # "without constraint.refresh" is a NEGATIVE marker, not positive
                positive_refresh = (
                    "constraint.refresh applied" in msg.lower()
                    or "constraint.refresh=true" in msg.lower()
                    or "refreshed" in msg.lower()
                )
                if steps > 10 and not positive_refresh:
                    return Violation(
                        law_id="SL-10",
                        severity="WARNING",
                        agent_id=agent_id,
                        timestamp=timestamp,
                        message=msg[:200],
                        detail=f"Agent has {steps} messages without constraint refresh",
                        actual_value=steps,
                        threshold_value=10,
                    )

        # SL-11: Temporal ordering
        if law.law_id == "SL-11":
            msg = str(payload)
            if "sequence_id" not in msg.lower() and "step" not in msg.lower():
                # Only check for message types that need ordering
                action_type = payload.get("action_type", "")
                if action_type in ("STATUS", "SITREP", "PROPOSAL"):
                    return Violation(
                        law_id="SL-11",
                        severity="WARNING",
                        agent_id=agent_id,
                        timestamp=timestamp,
                        message=msg[:200],
                        detail="Message missing sequence_id; reconstructability will degrade",
                    )

        # SL-03: Coordination overhead
        if law.law_id == "SL-03":
            # Would need time-window aggregation — simplified
            pass

        # SL-15: Drift calibration
        if law.law_id == "SL-15":
            msg = str(payload)
            interactions_match = re.search(r"interactions[=:]\s*(\d+)", msg)
            if interactions_match:
                interactions = int(interactions_match.group(1))
                # Violation if interactions > 500 AND no positive calibration marker
                # Positive markers: "calibration complete", "calibrated=true", "calibrated"
                # "without calibration" is a NEGATIVE marker, not positive
                positive_calibration = (
                    "calibration complete" in msg.lower()
                    or "calibrated=true" in msg.lower()
                    or "calibrated" in msg.lower()
                )
                if interactions > 500 and not positive_calibration:
                    return Violation(
                        law_id="SL-15",
                        severity="WARNING",
                        agent_id=agent_id,
                        timestamp=timestamp,
                        message=msg[:200],
                        detail=f"Agent has {interactions} interactions without calibration",
                        actual_value=interactions,
                        threshold_value=500,
                    )

        return None

    
    def list_laws(self) -> list[ScalingLaw]:
        """List all loaded scaling laws."""
        return list(self.laws.values())

    def get_law(self, law_id: str) -> ScalingLaw | None:
        """Get a specific scaling law by ID."""
        return self.laws.get(law_id)
