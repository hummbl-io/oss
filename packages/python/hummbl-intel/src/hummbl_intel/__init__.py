"""hummbl-intel — INT taxonomy framework for agent systems.

Categorizes agent intelligence collection into the canonical DoD/ODNI
taxonomy (SIGINT, HUMINT, OSINT, GEOINT, MASINT, FININT, TECHINT, IMINT,
ALL-SOURCE) and provides tools for source grading, collection posture,
and structured all-source fusion.

Stdlib-only. PyPI-publishable. Imported by founder-mode as a dependency.

Key modules:
- taxonomy: INT enum, discipline definitions, canonical collection surfaces
- grading: Source reliability (A-F) and content credibility (1-6) scales
- posture: Per-INT collection health (GREEN/YELLOW/RED)
- fusion: All-source methodology, competing hypotheses, estimative probability
- managers: INT steward role definitions and assignments
"""

from hummbl_intel.fusion import (
    WEP_RANGES,
    AllSourceProduct,
    CompetingHypothesesAnalysis,
    EstimativeProbability,
    FusedFinding,
    Hypothesis,
    fuse_into_finding,
)
from hummbl_intel.grading import (
    ASSERTION_POLARITY_LABELS,
    CREDIBILITY_LABELS,
    RELIABILITY_LABELS,
    AssertionPolarity,
    ContentCredibility,
    GradedAssertion,
    SourceGrade,
    SourceReliability,
    grade_automated_source,
    grade_human_source,
    grade_research_source,
    grade_uncorroborated,
    upgrade_with_corroboration,
)
from hummbl_intel.managers import (
    CANONICAL_MANAGERS,
    CORONAL_AGENT,
    INTManager,
    get_disciplines_for_agent,
    get_manager,
    manager_summary_table,
    to_dict,
)
from hummbl_intel.posture import (
    CollectionPostureReport,
    DisciplinePosture,
    PostureStatus,
    SurfaceStatus,
    build_default_posture,
)
from hummbl_intel.taxonomy import (
    CANONICAL_SURFACES,
    INT_LABELS,
    CollectionSurface,
    IntelligenceDiscipline,
    from_bus_prefix,
    get_surface,
    list_disciplines,
)

__version__ = "0.1.0"
__all__ = [
    "ASSERTION_POLARITY_LABELS",
    "CANONICAL_MANAGERS",
    "CANONICAL_SURFACES",
    "CORONAL_AGENT",
    "CREDIBILITY_LABELS",
    "INT_LABELS",
    "RELIABILITY_LABELS",
    "WEP_RANGES",
    "AllSourceProduct",
    "AssertionPolarity",
    "CollectionPostureReport",
    "CollectionSurface",
    "CompetingHypothesesAnalysis",
    "ContentCredibility",
    "DisciplinePosture",
    # fusion
    "EstimativeProbability",
    "FusedFinding",
    "GradedAssertion",
    "Hypothesis",
    # managers
    "INTManager",
    # taxonomy
    "IntelligenceDiscipline",
    # posture
    "PostureStatus",
    "SourceGrade",
    # grading
    "SourceReliability",
    "SurfaceStatus",
    "build_default_posture",
    "from_bus_prefix",
    "fuse_into_finding",
    "get_disciplines_for_agent",
    "get_manager",
    "get_surface",
    "grade_automated_source",
    "grade_human_source",
    "grade_research_source",
    "grade_uncorroborated",
    "list_disciplines",
    "manager_summary_table",
    "to_dict",
    "upgrade_with_corroboration",
]
