"""Peptide domain knowledge — thresholds, grading rules, and vendor trust.

This module encodes the empirical standards used by Peptide Checker to
evaluate peptide quality. These rules are consumed by PeptideQualityProtocol
to generate auditable reasoning traces.

Sources:
    - Finnrick community testing database
    - USP <1> Injections monograph (endotoxin / heavy metal limits)
    - Peptide synthesis literature (common degradation pathways)
    - Consumer guide compiled from ClinicalTrials.gov, ChEMBL, CMS data
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Per-peptide quality thresholds
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeptideSpec:
    """Quality thresholds and chemistry data for a single peptide."""

    name: str
    molecular_weight: float          # daltons
    mw_tolerance: float = 0.5        # daltons
    min_purity: float = 98.0         # pass threshold (%)
    warning_purity: float = 95.0     # warning threshold (%)
    known_degradation: tuple[str, ...] = ()
    storage_temp_max_c: float = -20  # max storage temp (Celsius)
    reconstituted_shelf_days: int = 28
    never_freeze: bool = False
    max_endotoxin_eu_per_mg: float = 5.0   # USP limit for injection
    max_heavy_metals_ppm: float = 10.0     # conservative limit


PEPTIDE_SPECS: dict[str, PeptideSpec] = {
    "BPC-157": PeptideSpec(
        name="BPC-157",
        molecular_weight=1419.53,
        mw_tolerance=0.5,
        min_purity=98.0,
        warning_purity=95.0,
        known_degradation=(
            "aspartimide isomers",
            "deamidation",
            "oxidation",
        ),
        storage_temp_max_c=-20,
        reconstituted_shelf_days=28,
    ),
    "semaglutide": PeptideSpec(
        name="semaglutide",
        molecular_weight=4113.58,
        mw_tolerance=1.0,
        min_purity=99.0,
        warning_purity=97.0,
        known_degradation=(
            "D-amino acid isomers",
            "oxidized fragments",
            "aggregates",
        ),
        storage_temp_max_c=8,
        reconstituted_shelf_days=56,
        never_freeze=True,
    ),
    "tirzepatide": PeptideSpec(
        name="tirzepatide",
        molecular_weight=4813.45,
        mw_tolerance=1.0,
        min_purity=99.0,
        warning_purity=97.0,
        known_degradation=(
            "deamidation",
            "oxidation",
            "aggregates",
        ),
        storage_temp_max_c=8,
        reconstituted_shelf_days=42,
        never_freeze=True,
    ),
    "ipamorelin": PeptideSpec(
        name="ipamorelin",
        molecular_weight=711.87,
        mw_tolerance=0.3,
        min_purity=98.0,
        warning_purity=95.0,
        known_degradation=(
            "deamidation",
            "oxidation",
        ),
        storage_temp_max_c=-20,
        reconstituted_shelf_days=21,
    ),
    "CJC-1295": PeptideSpec(
        name="CJC-1295",
        molecular_weight=3367.97,
        mw_tolerance=0.8,
        min_purity=98.0,
        warning_purity=95.0,
        known_degradation=(
            "deamidation",
            "DAC hydrolysis",
            "oxidation",
        ),
        storage_temp_max_c=-20,
        reconstituted_shelf_days=21,
    ),
}


def get_spec(peptide_name: str) -> Optional[PeptideSpec]:
    """Look up a peptide spec by name (case-insensitive)."""
    key = peptide_name.strip()
    if key in PEPTIDE_SPECS:
        return PEPTIDE_SPECS[key]
    # Try case-insensitive match
    lower = key.lower()
    for k, v in PEPTIDE_SPECS.items():
        if k.lower() == lower:
            return v
    return None


# ---------------------------------------------------------------------------
# Vendor trust grading rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VendorTrustTier:
    """Criteria for a vendor trust grade."""
    grade: str
    min_tests: int
    min_avg_score: float         # Finnrick 0-10 scale
    max_failures: int            # tests below warning threshold
    label: str = ""

VENDOR_TRUST_TIERS: dict[str, VendorTrustTier] = {
    "A": VendorTrustTier(
        grade="A",
        min_tests=5,
        min_avg_score=7.5,
        max_failures=0,
        label="Trusted — consistent high quality",
    ),
    "B": VendorTrustTier(
        grade="B",
        min_tests=3,
        min_avg_score=6.5,
        max_failures=1,
        label="Good — minor inconsistencies",
    ),
    "C": VendorTrustTier(
        grade="C",
        min_tests=3,
        min_avg_score=5.5,
        max_failures=2,
        label="Acceptable — notable variability",
    ),
    "D": VendorTrustTier(
        grade="D",
        min_tests=1,
        min_avg_score=4.0,
        max_failures=3,
        label="Poor — frequent quality issues",
    ),
    "E": VendorTrustTier(
        grade="E",
        min_tests=0,
        min_avg_score=0.0,
        max_failures=999,
        label="Avoid — do not use",
    ),
}


# ---------------------------------------------------------------------------
# Grade-to-recommendation mapping
# ---------------------------------------------------------------------------

GRADE_RECOMMENDATIONS: dict[str, str] = {
    "A": "Safe to use — high confidence in product quality.",
    "B": "Proceed with caution — generally acceptable but verify CoA.",
    "C": "Caution — variable quality; request third-party testing.",
    "D": "Do not use — significant quality concerns.",
    "E": "Do not use — failed testing or known bad actor.",
    "U": "Unknown — insufficient data to assess; treat as high risk.",
}


# ---------------------------------------------------------------------------
# Finnrick score to letter grade conversion
# ---------------------------------------------------------------------------

def score_to_grade(score_avg: Optional[float], test_count: Optional[int]) -> str:
    """Convert a Finnrick average score to a letter grade.

    This mirrors the Finnrick grading bands observed in the database:
        A: score >= 7.5 and test_count >= 5
        B: score >= 6.5 and test_count >= 3
        C: score >= 5.5
        D: score >= 4.0
        E: score < 4.0 or explicitly flagged
        U: no score available
    """
    if score_avg is None:
        return "U"
    tc = test_count or 0
    if score_avg >= 7.5 and tc >= 5:
        return "A"
    if score_avg >= 6.5 and tc >= 3:
        return "B"
    if score_avg >= 5.5:
        return "C"
    if score_avg >= 4.0:
        return "D"
    return "E"


# ---------------------------------------------------------------------------
# Purity assessment helpers
# ---------------------------------------------------------------------------

def assess_purity(
    purity_pct: Optional[float],
    spec: PeptideSpec,
) -> tuple[str, str]:
    """Assess purity against peptide-specific thresholds.

    Returns:
        (status, explanation) where status is 'pass', 'warning', or 'fail'.
    """
    if purity_pct is None:
        return ("unknown", "No purity data available.")
    if purity_pct >= spec.min_purity:
        return (
            "pass",
            f"Purity {purity_pct:.1f}% meets minimum threshold "
            f"of {spec.min_purity:.1f}%.",
        )
    if purity_pct >= spec.warning_purity:
        return (
            "warning",
            f"Purity {purity_pct:.1f}% is below ideal ({spec.min_purity:.1f}%) "
            f"but above failure threshold ({spec.warning_purity:.1f}%).",
        )
    return (
        "fail",
        f"Purity {purity_pct:.1f}% is below failure threshold "
        f"of {spec.warning_purity:.1f}%.",
    )


def assess_contaminants(
    endotoxin: Optional[float],
    heavy_metals: Optional[float],
    spec: PeptideSpec,
) -> list[tuple[str, str]]:
    """Check endotoxin and heavy metals against safety limits.

    Returns a list of (status, explanation) tuples.
    """
    results: list[tuple[str, str]] = []
    if endotoxin is not None:
        if endotoxin <= spec.max_endotoxin_eu_per_mg:
            results.append((
                "pass",
                f"Endotoxin {endotoxin:.2f} EU/mg within limit "
                f"({spec.max_endotoxin_eu_per_mg:.1f} EU/mg).",
            ))
        else:
            results.append((
                "fail",
                f"Endotoxin {endotoxin:.2f} EU/mg EXCEEDS limit "
                f"({spec.max_endotoxin_eu_per_mg:.1f} EU/mg). "
                f"Unsafe for injection.",
            ))
    if heavy_metals is not None:
        if heavy_metals <= spec.max_heavy_metals_ppm:
            results.append((
                "pass",
                f"Heavy metals {heavy_metals:.1f} ppm within limit "
                f"({spec.max_heavy_metals_ppm:.1f} ppm).",
            ))
        else:
            results.append((
                "fail",
                f"Heavy metals {heavy_metals:.1f} ppm EXCEEDS limit "
                f"({spec.max_heavy_metals_ppm:.1f} ppm).",
            ))
    return results
