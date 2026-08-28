"""Atlas readers — extract contradictions from evidence cuts and claimed state.

Two input sources:
  1. Markdown ledger files (hummbl-atlas-*.md) — contain contradiction fields
     in structured prose: "Contradiction:", "Verdict:", "Confidence:", etc.
  2. JSON inventory files — contain claimed state (counts, manifests, rosters)

The reader extracts Contradiction objects from both, then the scanner diffs
claimed vs observed to surface mismatches.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

from .contradiction import Contradiction


# ─────────────────────────────────────────────────────────────
# Markdown ledger parser
# ─────────────────────────────────────────────────────────────

# Atlas ledger entries follow a structured format with labeled fields.
# We extract the key fields by regex on the field labels.

_FIELD_PATTERNS = {
    "scope": re.compile(r"(?:\*\*Scope:\*\*|Scope:)\s*(.+)", re.I),
    "observation": re.compile(r"(?:\*\*Direct observation:\*\*|Direct observation:)\s*(.+)", re.I),
    "contradiction": re.compile(r"(?:\*\*Contradiction:\*\*|Contradiction:)\s*(.+)", re.I),
    "verdict": re.compile(r"(?:\*\*Verdict:\*\*|Verdict:)\s*(.+)", re.I),
    "confidence": re.compile(r"(?:\*\*Confidence:\*\*|Confidence:)\s*(.+)", re.I),
    "volatility": re.compile(r"(?:\*\*Volatility:\*\*|Volatility:)\s*(.+)", re.I),
}

_CLAIM_ID = re.compile(r"##\s+(AR-[A-Z]+-\d+)", re.I)


def _parse_confidence(text: str) -> float:
    """Parse confidence text like 'High for metadata' to a float."""
    text_lower = text.lower()
    if "high" in text_lower:
        return 0.9
    if "medium" in text_lower:
        return 0.6
    if "low" in text_lower:
        return 0.3
    # Try to extract a number
    match = re.search(r"(\d+\.?\d*)", text)
    if match:
        val = float(match.group(1))
        if val > 1:
            val = val / 100
        return val
    return 0.5


def _parse_volatility(text: str) -> str:
    """Parse volatility text to a canonical level.

    Priority order: high > medium > low. Compound terms like "Medium-high"
    resolve to "high" because the higher qualifier dominates — a surface
    with medium-high volatility changes fast enough to be treated as high
    for cadence purposes. This is intentional, not a bug.
    """
    text_lower = text.lower()
    if "high" in text_lower:
        return "high"
    if "medium" in text_lower:
        return "medium"
    if "low" in text_lower:
        return "low"
    return "medium"


def _infer_severity(scope: str, contradiction: str, verdict: str) -> str:
    """Infer P0-P3 from the nature of the contradiction."""
    combined = (scope + " " + contradiction + " " + verdict).lower()
    if any(w in combined for w in ["safety-critical", "kill switch", "emergency", "security-critical"]):
        return "P0"
    if any(w in combined for w in ["canonical", "identity", "migration", "release", "deployment"]):
        return "P1"
    if any(w in combined for w in ["documentation", "stale", "drift", "count", "manifest"]):
        return "P2"
    return "P3"


def parse_ledger_markdown(path: Path) -> list[Contradiction]:
    """Parse a single Atlas ledger markdown file into Contradiction objects.

    Only entries that contain a 'Contradiction:' field produce a Contradiction.
    Entries without contradictions are observations, not contradictions.
    """
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="ignore")

    # Split into claim blocks by ## headers
    blocks = re.split(r"\n(?=##\s+)", text)
    contradictions = []

    for block in blocks:
        # Must have a contradiction field to be a contradiction
        contradiction_match = _FIELD_PATTERNS["contradiction"].search(block)
        if not contradiction_match:
            continue

        # Skip "No contradiction" or "None" entries
        contradiction_text = contradiction_match.group(1).strip()
        if contradiction_text.lower() in ("none", "none.", "n/a", "n/a."):
            continue

        scope_match = _FIELD_PATTERNS["scope"].search(block)
        observation_match = _FIELD_PATTERNS["observation"].search(block)
        verdict_match = _FIELD_PATTERNS["verdict"].search(block)
        confidence_match = _FIELD_PATTERNS["confidence"].search(block)
        volatility_match = _FIELD_PATTERNS["volatility"].search(block)

        scope = scope_match.group(1).strip() if scope_match else path.stem
        observation = observation_match.group(1).strip() if observation_match else ""
        verdict = verdict_match.group(1).strip() if verdict_match else ""
        confidence = _parse_confidence(confidence_match.group(1)) if confidence_match else 0.5
        volatility = _parse_volatility(volatility_match.group(1)) if volatility_match else "medium"
        severity = _infer_severity(scope, contradiction_text, verdict)

        contradictions.append(Contradiction(
            scope=scope,
            claim=contradiction_text,  # The contradiction IS the claim that's wrong
            observation=observation,
            severity=severity,
            confidence=confidence,
            volatility=volatility,
            evidence_source=str(path),
            claim_source=str(path),
        ))

    return contradictions


def scan_ledger_directory(directory: Path, pattern: str = "hummbl-atlas-*.md") -> list[Contradiction]:
    """Scan a directory of Atlas ledger markdown files."""
    all_contradictions = []
    for md_path in sorted(directory.glob(pattern)):
        all_contradictions.extend(parse_ledger_markdown(md_path))
    return all_contradictions


# ─────────────────────────────────────────────────────────────
# JSON inventory parser — claimed state
# ─────────────────────────────────────────────────────────────

def load_json_inventory(path: Path) -> dict:
    """Load a JSON inventory file (Atlas census, skill manifest, etc.)."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_claimed_counts(inventory: dict) -> dict[str, int]:
    """Extract numeric claims from a JSON inventory.

    Looks for common count fields in Atlas-style inventories:
      - stats.* (source_atoms, families, lenses, etc.)
      - counts.* (repos, skills, agents, etc.)
      - top-level numeric fields
    """
    claimed = {}

    # Nested stats block (Intel Atlas style)
    if "stats" in inventory and isinstance(inventory["stats"], dict):
        for key, val in inventory["stats"].items():
            if isinstance(val, (int, float)):
                claimed[key] = int(val)

    # Nested counts block
    if "counts" in inventory and isinstance(inventory["counts"], dict):
        for key, val in inventory["counts"].items():
            if isinstance(val, (int, float)):
                claimed[key] = int(val)

    # Top-level numeric fields
    for key, val in inventory.items():
        if isinstance(val, (int, float)) and key not in ("version",):
            claimed[key] = int(val)

    return claimed


# ─────────────────────────────────────────────────────────────
# Claimed-vs-observed diff
# ─────────────────────────────────────────────────────────────

def diff_counts(
    claimed: dict[str, int],
    observed: dict[str, int],
    evidence_source: str = "",
    claim_source: str = "",
) -> list[Contradiction]:
    """Diff claimed counts against observed counts.

    Produces a Contradiction for each count that differs.
    This is the skill-count (547/360/126) pattern generalized.
    """
    contradictions = []
    all_keys = set(claimed) | set(observed)

    for key in sorted(all_keys):
        claim_val = claimed.get(key)
        obs_val = observed.get(key)

        if claim_val is None:
            # Observed but not claimed — system has something it doesn't document
            contradictions.append(Contradiction(
                scope=f"count:{key}",
                claim=f"not declared",
                observation=f"observed: {obs_val}",
                severity="P2",
                confidence=0.8,
                volatility="medium",
                evidence_source=evidence_source,
                claim_source=claim_source,
            ))
        elif obs_val is None:
            # Claimed but not observed — system claims something that doesn't exist
            contradictions.append(Contradiction(
                scope=f"count:{key}",
                claim=f"declared: {claim_val}",
                observation=f"not observed",
                severity="P2",
                confidence=0.7,
                volatility="medium",
                evidence_source=evidence_source,
                claim_source=claim_source,
            ))
        elif claim_val != obs_val:
            # Mismatch — the core contradiction type
            severity = "P1" if abs(claim_val - obs_val) > claim_val * 0.2 else "P2"
            contradictions.append(Contradiction(
                scope=f"count:{key}",
                claim=f"declared: {claim_val}",
                observation=f"observed: {obs_val}",
                severity=severity,
                confidence=0.85,
                volatility="medium",
                evidence_source=evidence_source,
                claim_source=claim_source,
            ))

    return contradictions


# ─────────────────────────────────────────────────────────────
# Freshness checker — Atlas scoring standard v0.1
# ─────────────────────────────────────────────────────────────

# Freshness windows from the Atlas scoring standard (in days)
FRESHNESS_WINDOWS: dict[str, int] = {
    "metadata": 30,      # Repository metadata and branch state
    "dependency": 14,    # Dependency/package/release evidence
    "security": 7,       # Security settings and publishing bindings
}


@dataclass
class FreshnessResult:
    """Result of a freshness check on an Atlas evidence cut."""
    path: str
    category: str
    age_days: float
    max_age_days: int
    is_stale: bool
    last_modified: float  # Unix timestamp

    def to_dict(self) -> dict:
        return asdict(self)


def check_freshness(
    path: Path,
    category: str = "metadata",
    now: float | None = None,
) -> FreshnessResult:
    """Check if an Atlas evidence cut is stale per the scoring standard.

    Categories and their max age (from Atlas Scoring Standard v0.1):
      - metadata: 30 days (repository metadata, branch state)
      - dependency: 14 days (dependency/package/release evidence)
      - security: 7 days (security settings, publishing bindings)

    Args:
        path: Path to the evidence cut file
        category: Freshness category (metadata/dependency/security)
        now: Override current time for testing (Unix timestamp)

    Returns:
        FreshnessResult with age, staleness, and metadata
    """
    if now is None:
        now = time.time()

    max_age_days = FRESHNESS_WINDOWS.get(category, 30)
    mtime = path.stat().st_mtime if path.exists() else 0.0
    age_seconds = now - mtime
    age_days = age_seconds / 86400.0

    return FreshnessResult(
        path=str(path),
        category=category,
        age_days=age_days,
        max_age_days=max_age_days,
        is_stale=age_days > max_age_days,
        last_modified=mtime,
    )


def scan_freshness(
    directory: Path,
    pattern: str = "hummbl-atlas-*.md",
    category: str = "metadata",
    now: float | None = None,
) -> list[FreshnessResult]:
    """Check freshness of all Atlas evidence cuts in a directory.

    Returns results sorted by age (oldest first).
    """
    if now is None:
        now = time.time()

    results = []
    for md_path in sorted(directory.glob(pattern)):
        results.append(check_freshness(md_path, category, now))

    return sorted(results, key=lambda r: -r.age_days)
