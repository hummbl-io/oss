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

"""Base120 domain models.

Operator       — a single reasoning operator from the canonical registry.
ApplyResult    — the structured result of recording an operator application.
OperatorTuple  — VERUM-aligned evidence tuple emitted by ApplyResult.to_tuple().

VERUM alignment (append-only sovereignty):
  id    — operator code, e.g. "P6"
  time  — UTC ISO-8601 timestamp of the application
  state — the recommendation produced by the application
  drift — deviation from certainty: 1.0 - confidence (0.0 = certain, 1.0 = unknown)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, NamedTuple


class OperatorTuple(NamedTuple):
    """VERUM-aligned evidence tuple for an operator application.

    Drop this into any append-only audit log (JSONL, TSV, etc.) as proof
    that a governed reasoning step occurred.

    Fields mirror the 4 VERUM node fields:
      id     → who/what (operator code)
      time   → when     (UTC ISO-8601)
      state  → current condition (recommendation)
      drift  → deviation from setpoint (1.0 - confidence)
    """

    id: str       # operator code, e.g. "P6"
    time: str     # UTC ISO-8601, e.g. "2026-04-14T21:00:00Z"
    state: str    # recommendation text
    drift: float  # 1.0 - confidence


@dataclass(frozen=True, slots=True)
class Operator:
    """A single Base120 reasoning operator from the canonical registry.

    code           e.g. "P6"
    name           e.g. "Point-of-View Anchoring"
    transformation family key: "P" | "IN" | "CO" | "DE" | "RE" | "SY"
    definition     one-sentence definition of the operator
    """

    code: str
    name: str
    transformation: str
    definition: str

    @property
    def family(self) -> str:
        """Alias for transformation — the operator family."""
        return self.transformation


@dataclass(frozen=True, slots=True)
class ApplyResult:
    """The recorded result of applying a Base120 operator to a problem.

    Produced by Engine.record(). Immutable after creation.

    Fields:
        code            operator code, e.g. "P6"
        name            operator name
        problem         original problem statement
        recommendation  output of the reasoning application
        confidence      0.0–1.0 certainty score
        evidence_id     UUID for this application event (audit trail anchor)
        metadata        arbitrary key/value context
    """

    code: str
    name: str
    problem: str
    recommendation: str
    confidence: float
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_tuple(self) -> OperatorTuple:
        """Emit a VERUM-aligned evidence tuple.

        Returns an OperatorTuple with:
          id    = operator code
          time  = current UTC time as ISO-8601
          state = recommendation
          drift = 1.0 - confidence (deviation from certainty)
        """
        ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return OperatorTuple(
            id=self.code,
            time=ts,
            state=self.recommendation,
            drift=round(1.0 - self.confidence, 6),
        )
