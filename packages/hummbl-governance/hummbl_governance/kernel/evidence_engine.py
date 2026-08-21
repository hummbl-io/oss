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

"""Evidence Engine — K5 invariant enforcement.

Every claim in a receipt is graded using the MTSMU evidence rubric
or marked SPECULATIVE. All-C claims are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvidenceGrade:
    """MTSMU evidence grade per dimension."""

    credibility: str = "C"  # A, B, C
    recency: str = "C"
    methodology: str = "C"
    reproducibility: str = "C"
    relevance: str = "C"

    def average(self) -> str:
        """Compute overall grade from dimensions."""
        scores = {"A": 3, "B": 2, "C": 1}
        total = sum(
            scores.get(getattr(self, dim), 1)
            for dim in ["credibility", "recency", "methodology", "reproducibility", "relevance"]
        )
        avg = total / 5
        if avg >= 2.5:
            return "A"
        if avg >= 1.5:
            return "B"
        return "C"

    def is_acceptable(self) -> bool:
        """Check if grade is acceptable (not all C)."""
        return self.average() != "C" or any(
            getattr(self, dim) != "C"
            for dim in ["credibility", "recency", "methodology", "reproducibility", "relevance"]
        )


class EvidenceEngine:
    """Engine for grading evidence quality using MTSMU rubric."""

    def grade(
        self,
        claim: str,
        sources: list[str],
        methodology: str = "",
    ) -> EvidenceGrade:
        """Grade a claim using the MTSMU evidence rubric.

        This is a rule-based heuristic. Future versions may use
        more sophisticated analysis.
        """
        # Credibility
        credibility = "C"
        if any(src.startswith("http") or "/" in src for src in sources):
            credibility = "B"  # Has path or URL
        if any("experiment" in src or "trial" in src.lower() for src in sources):
            credibility = "A"  # Empirical source

        # Recency (simplified: no date info = C)
        recency = "C"

        # Methodology
        meth_score = "C"
        if methodology:
            if "reproducible" in methodology.lower() or "monte carlo" in methodology.lower():
                meth_score = "A"
            elif "test" in methodology.lower() or "review" in methodology.lower():
                meth_score = "B"
        methodology_grade = meth_score

        # Reproducibility
        repro = "C"
        if "reproducible" in methodology.lower() or "open source" in methodology.lower():
            repro = "A"
        elif sources:
            repro = "B"

        # Relevance
        relevance = "B"
        if claim and len(claim) > 20:
            relevance = "A"

        return EvidenceGrade(
            credibility=credibility,
            recency=recency,
            methodology=methodology_grade,
            reproducibility=repro,
            relevance=relevance,
        )

    def canonicalize(self, claim: str) -> str:
        """Generate a canonical ID for a claim.

        Used to deduplicate and track claims across receipts.
        """
        import hashlib
        return hashlib.sha256(claim.lower().strip().encode()).hexdigest()[:16]

    def validate_receipt_claims(self, payload: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate all claims in a receipt payload.

        Returns (acceptable, [reasons]).
        """
        reasons: list[str] = []
        claims = payload.get("claims", [])
        if not claims:
            # No explicit claims = acceptable (payload may be raw data)
            return True, reasons

        for claim in claims:
            grade = self.grade(
                claim.get("text", ""),
                claim.get("sources", []),
                claim.get("methodology", ""),
            )
            if not grade.is_acceptable():
                reasons.append(
                    f"Claim '{claim.get('text', '')[:50]}...' has unacceptable evidence grade (all C)"
                )

        return len(reasons) == 0, reasons
