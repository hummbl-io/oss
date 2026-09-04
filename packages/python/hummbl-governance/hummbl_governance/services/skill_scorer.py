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
# See the License for the specific language and permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Skill health scorer -- usage telemetry, chain participation, exploration bonus.

Scores installed skills on five usage-health components (0-40 points total):

- **Frequency** (12): Recency-weighted invocation count (log-diminishing).
- **Success** (8): Wilson score lower bound for success rate.
- **Recency** (8): Days since last invocation (exponential decay).
- **Chain** (6): References from/to other skills in SKILL.md chain sections.
- **Exploration** (6): UCB1 bonus for under-explored skills.

Telemetry TSV format (tab-separated)::

    skill_name\\tinvocation_count\\tlast_invoked\\tsession_count\\tsuccess_count

Usage::

    from hummbl_governance.services.skill_scorer import SkillScorer

    scorer = SkillScorer(telemetry_path="~/hummbl_governance/_state/telemetry/skill-usage.tsv")
    scores = scorer.score_all()
    print(scorer.generate_report(scores))
"""

from __future__ import annotations

import csv
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FREQUENCY = 12.0
_MAX_SUCCESS = 8.0
_MAX_RECENCY = 8.0
_MAX_CHAIN = 6.0
_MAX_EXPLORATION = 6.0
_MAX_TOTAL = 40.0

# Recency decay: half-life of 14 days
_RECENCY_HALFLIFE_DAYS = 14.0

# Frequency: log2-based diminishing returns. 1 invocation = 4 pts, 10 = 12 pts.
_FREQ_BASE = 4.0
_FREQ_LOG_SCALE = 8.0 / math.log2(10)  # so 10 invocations -> 12 pts

# Wilson score z-value for 95% confidence
_Z_95 = 1.96

# UCB1 exploration constant
_UCB1_C = math.sqrt(2.0)

# Skills directory for chain analysis
_DEFAULT_SKILLS_DIR = os.path.join(os.path.expanduser("~"), ".agents", "skills")

# Regex for chain references in SKILL.md
_CHAIN_PATTERN = re.compile(r"`\[?([\w-]+)\]?`")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SkillUsageData:
    """Raw telemetry data for a single skill."""

    name: str
    invocation_count: int = 0
    last_invoked: Optional[str] = None
    session_count: int = 0
    success_count: int = 0


@dataclass
class SkillScore:
    """Composite usage score for a single skill."""

    name: str
    frequency: float = 0.0
    success: float = 0.0
    recency: float = 0.0
    chain: float = 0.0
    exploration: float = 0.0
    total: float = 0.0
    invocation_count: int = 0
    last_invoked: Optional[str] = None

    def __post_init__(self) -> None:
        self.total = round(
            self.frequency
            + self.success
            + self.recency
            + self.chain
            + self.exploration,
            1,
        )


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


def _wilson_score_lower(successes: int, total: int, z: float = _Z_95) -> float:
    """Wilson score lower bound for a binomial proportion.

    Returns the lower bound of the confidence interval for the true
    success rate, which penalizes small sample sizes.
    """
    if total == 0:
        return 0.0
    p = successes / total
    denominator = 1.0 + z * z / total
    center = p + z * z / (2 * total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    return max(0.0, (center - margin) / denominator)


def _score_frequency(count: int) -> float:
    """Log-diminishing frequency score: 1 invocation = 4 pts, 10 = 12 pts."""
    if count <= 0:
        return 0.0
    score = _FREQ_BASE + _FREQ_LOG_SCALE * math.log2(count)
    return min(score, _MAX_FREQUENCY)


def _score_success(successes: int, total: int) -> float:
    """Wilson score lower bound scaled to 8 points."""
    if total == 0:
        return 0.0
    wilson = _wilson_score_lower(successes, total)
    return round(wilson * _MAX_SUCCESS, 2)


def _score_recency(last_invoked: Optional[str], now: Optional[datetime] = None) -> float:
    """Exponential decay based on days since last invocation.

    Half-life of 14 days: 0 days = 8 pts, 14 days = 4 pts, 28 days = 2 pts.
    """
    if not last_invoked:
        return 0.0
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        # Parse ISO timestamp
        ts = last_invoked
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta_days = (now - dt).total_seconds() / 86400.0
        if delta_days < 0:
            delta_days = 0.0
        decay = math.pow(0.5, delta_days / _RECENCY_HALFLIFE_DAYS)
        return round(decay * _MAX_RECENCY, 2)
    except (ValueError, TypeError):
        return 0.0


def _score_chain(skill_name: str, chain_map: dict[str, set[str]]) -> float:
    """Chain participation score based on references from/to other skills."""
    refs = chain_map.get(skill_name, set())
    # Each reference contributes, up to max
    if not refs:
        return 0.0
    score = min(len(refs) * 1.5, _MAX_CHAIN)
    return round(score, 2)


def _score_exploration(invocation_count: int, total_pulls: int) -> float:
    """UCB1 exploration bonus for under-explored skills."""
    if total_pulls == 0:
        return _MAX_EXPLORATION
    if invocation_count == 0:
        # Unexplored skills get maximum exploration bonus
        return _MAX_EXPLORATION
    # UCB1 exploration term: C * sqrt(ln(N) / n)
    exploration = _UCB1_C * math.sqrt(math.log(total_pulls) / invocation_count)
    return round(min(exploration * 2.0, _MAX_EXPLORATION), 2)


# ---------------------------------------------------------------------------
# Chain map builder
# ---------------------------------------------------------------------------


def build_chain_map(skills_dir: str = _DEFAULT_SKILLS_DIR) -> dict[str, set[str]]:
    """Build a map of skill_name -> set of skills that reference it.

    Parses SKILL.md files for chain references in Skill Chains sections only.
    """
    chain_map: dict[str, set[str]] = {}

    if not os.path.isdir(skills_dir):
        return chain_map

    # Known skill names for validation (from directory names)
    known_skills: set[str] = set()
    for entry in os.listdir(skills_dir):
        if os.path.isfile(os.path.join(skills_dir, entry, "SKILL.md")):
            known_skills.add(entry)

    for entry in known_skills:
        skill_path = os.path.join(skills_dir, entry, "SKILL.md")
        try:
            with open(skill_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        # Extract only the Skill Chains section
        chain_section = _extract_chain_section(content)
        if not chain_section:
            continue

        # Find skill chain references (backtick-quoted names)
        refs = _CHAIN_PATTERN.findall(chain_section)
        for ref in refs:
            ref_clean = ref.strip().strip("`[]/")
            # Only count references to known skills (filters out flags, args, etc.)
            if ref_clean and ref_clean in known_skills and ref_clean != entry:
                chain_map.setdefault(ref_clean, set()).add(entry)

    return chain_map


def _extract_chain_section(content: str) -> str:
    """Extract the Skill Chains section from a SKILL.md file."""
    # Find the Skill Chains heading
    markers = ["## Skill Chains", "### Skill Chains", "## Skill Chain", "### Skill Chain"]
    start = -1
    for marker in markers:
        idx = content.find(marker)
        if idx >= 0:
            start = idx
            break
    if start < 0:
        return ""
    # Find the next ## heading after the chain section
    rest = content[start:]
    next_heading = re.search(r"\n##[^#]", rest[1:])
    if next_heading:
        return rest[: next_heading.start() + 1]
    return rest


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------


class SkillScorer:
    """Score skills on usage health dimensions from telemetry data.

    Parameters
    ----------
    telemetry_path : str or None
        Path to the telemetry TSV file. If None, all usage scores are 0.
    skills_dir : str
        Path to the skills directory for chain analysis.
    """

    def __init__(
        self,
        telemetry_path: Optional[str] = None,
        skills_dir: str = _DEFAULT_SKILLS_DIR,
    ) -> None:
        self.telemetry_path = telemetry_path
        self.skills_dir = skills_dir
        self._usage_data: dict[str, SkillUsageData] = {}
        self._chain_map: dict[str, set[str]] = {}
        self._total_invocations = 0
        self._load_telemetry()
        self._load_chain_map()

    def _load_telemetry(self) -> None:
        """Load telemetry data from TSV file."""
        if not self.telemetry_path or not os.path.isfile(self.telemetry_path):
            return

        try:
            with open(self.telemetry_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    name = row.get("skill_name", "").strip()
                    if not name:
                        continue
                    try:
                        count = int(row.get("invocation_count", 0))
                        sessions = int(row.get("session_count", 0))
                        successes = int(row.get("success_count", 0))
                    except ValueError:
                        count = sessions = successes = 0
                    last = row.get("last_invoked", "").strip() or None
                    self._usage_data[name] = SkillUsageData(
                        name=name,
                        invocation_count=count,
                        last_invoked=last,
                        session_count=sessions,
                        success_count=successes,
                    )
                    self._total_invocations += count
        except OSError:
            pass

    def _load_chain_map(self) -> None:
        """Build chain reference map from SKILL.md files."""
        self._chain_map = build_chain_map(self.skills_dir)

    def score_skill(self, name: str) -> SkillScore:
        """Score a single skill."""
        data = self._usage_data.get(name, SkillUsageData(name=name))

        freq = _score_frequency(data.invocation_count)
        success = _score_success(data.success_count, data.invocation_count)
        recency = _score_recency(data.last_invoked)
        chain = _score_chain(name, self._chain_map)
        exploration = _score_exploration(data.invocation_count, self._total_invocations)

        return SkillScore(
            name=name,
            frequency=freq,
            success=success,
            recency=recency,
            chain=chain,
            exploration=exploration,
            invocation_count=data.invocation_count,
            last_invoked=data.last_invoked,
        )

    def score_all(self) -> dict[str, SkillScore]:
        """Score all skills: those with telemetry plus those in the chain map."""
        all_names = set(self._usage_data.keys()) | set(self._chain_map.keys())
        # Also include skills from the filesystem
        if os.path.isdir(self.skills_dir):
            for entry in os.listdir(self.skills_dir):
                if os.path.isfile(os.path.join(self.skills_dir, entry, "SKILL.md")):
                    all_names.add(entry)
        return {name: self.score_skill(name) for name in sorted(all_names)}

    def generate_report(self, scores: dict[str, SkillScore]) -> str:
        """Generate a human-readable report from scores."""
        lines = []
        lines.append(f"Skill Usage Scorer | {len(scores)} skills | {self._total_invocations} invocations")
        lines.append("=" * 68)
        lines.append("")

        # Sort by total descending
        ranked = sorted(scores.values(), key=lambda s: s.total, reverse=True)

        # Top 20
        lines.append("TOP 20 (by usage health score)")
        lines.append(
            f"  {'#':>3s}  {'Skill':30s} {'Total':>6s} {'Freq':>5s}"
            f"  {'Succ':>5s} {'Recy':>5s} {'Chn':>5s} {'Expl':>5s} {'Inv':>5s}"
        )
        for i, s in enumerate(ranked[:20], 1):
            lines.append(
                f"  {i:3d}  {s.name:30s} {s.total:6.1f} {s.frequency:5.1f} {s.success:5.1f} "
                f"{s.recency:5.1f} {s.chain:5.1f} {s.exploration:5.1f} {s.invocation_count:5d}"
            )

        lines.append("")

        # Skills with invocations > 0
        used = [s for s in ranked if s.invocation_count > 0]
        lines.append(f"Skills with invocations: {len(used)}")
        lines.append(f"Skills with 0 invocations: {len(ranked) - len(used)}")
        lines.append(f"Total invocations: {self._total_invocations}")
        lines.append("")

        # Telemetry source
        if self.telemetry_path and os.path.isfile(self.telemetry_path):
            lines.append(f"Telemetry source: {self.telemetry_path}")
        else:
            lines.append("Telemetry source: NONE (all usage scores are 0)")

        if self._chain_map:
            lines.append(f"Chain map: {len(self._chain_map)} skills referenced by others")
        else:
            lines.append("Chain map: empty (no SKILL.md chain references found)")

        return "\n".join(lines)
