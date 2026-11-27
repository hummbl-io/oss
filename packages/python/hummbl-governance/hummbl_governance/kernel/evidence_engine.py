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

    # Primary verifiable source prefixes / institutional domains eligible for
    # Grade A credibility when paired with non-empty methodology.
    _PRIMARY_PREFIXES = ("doi:", "arxiv:", "sha256:", "commit:", "receipt:", "pypi:")
    _PRIMARY_DOMAINS = (
        "https://doi.org/",
        "https://arxiv.org/",
        "https://nist.gov/",
        "https://www.nist.gov/",
        "https://nvlpubs.nist.gov/",
    )

    def _is_primary_source(self, src: str) -> bool:
        s = src.strip().lower()
        if any(s.startswith(p) for p in self._PRIMARY_PREFIXES):
            return True
        if any(s.startswith(d) for d in self._PRIMARY_DOMAINS):
            return True
        if s.startswith("https://github.com/") and "/commit/" in s:
            return True
        return False

    def grade(
        self,
        claim: str,
        sources: list[str],
        methodology: str = "",
    ) -> EvidenceGrade:
        """Grade a claim using the MTSMU evidence rubric.

        Closes hummbl-io/oss#517 Finding 3:
        - Arbitrary URLs containing keywords like 'experiment' no longer receive
          Grade A credibility; Grade A requires a structured/verifiable primary
          source identifier paired with non-empty methodology.
        - Empty or unsourced claims default to relevance='C', making all-C
          rejection reachable and active.
        """
        nonempty_sources = [s.strip() for s in sources if isinstance(s, str) and s.strip()]
        clean_claim = claim.strip() if isinstance(claim, str) else ""
        clean_methodology = methodology.strip() if isinstance(methodology, str) else ""

        # Credibility
        credibility = "C"
        if any(src.startswith("http") or "/" in src or ":" in src for src in nonempty_sources):
            credibility = "B"  # Has path, URL, or structured identifier
        if clean_methodology and any(self._is_primary_source(src) for src in nonempty_sources):
            credibility = "A"  # Verifiable primary source + stated methodology

        # Recency (simplified: no date info = C)
        recency = "C"

        # Methodology
        meth_score = "C"
        if clean_methodology:
            lower_meth = clean_methodology.lower()
            if "reproducible" in lower_meth or "monte carlo" in lower_meth:
                meth_score = "A"
            elif "test" in lower_meth or "review" in lower_meth:
                meth_score = "B"
        methodology_grade = meth_score

        # Reproducibility
        repro = "C"
        if "reproducible" in clean_methodology.lower() or "open source" in clean_methodology.lower():
            repro = "A"
        elif nonempty_sources:
            repro = "B"

        # Relevance (fail-closed default: C when empty or completely unsourced)
        relevance = "C"
        if clean_claim and (nonempty_sources or clean_methodology):
            relevance = "A" if (len(clean_claim) > 20 and nonempty_sources) else "B"

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
