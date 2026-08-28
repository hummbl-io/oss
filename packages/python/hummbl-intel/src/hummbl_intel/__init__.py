"""hummbl-intel — INT taxonomy framework for agent systems.

Categorizes agent intelligence collection into the canonical DoD/ODNI
taxonomy (SIGINT, HUMINT, OSINT, GEOINT, MASINT, FININT, TECHINT, IMINT,
ALL-SOURCE) and provides tools for source grading, collection posture,
and structured all-source fusion.

Stdlib-only. PyPI-publishable.

Key modules:
- taxonomy: INT enum, discipline definitions, canonical collection surfaces
- grading: Source reliability (A-F) and content credibility (1-6) scales
- posture: Per-INT collection health (GREEN/YELLOW/RED)
- fusion: All-source methodology, competing hypotheses, estimative probability
- managers: INT steward role definitions and assignments
"""

from hummbl_intel.taxonomy import (
    CANONICAL_SURFACES,
    INT_LABELS,
    CollectionSurface,
    IntelligenceDiscipline,
    from_bus_prefix,
    get_surface,
    list_disciplines,
)
from hummbl_intel.grading import (
    CREDIBILITY_LABELS,
    RELIABILITY_LABELS,
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
from hummbl_intel.posture import (
    CollectionPostureReport,
    DisciplinePosture,
    PostureStatus,
    SurfaceStatus,
    build_default_posture,
)
from hummbl_intel.fusion import (
    AllSourceProduct,
    CompetingHypothesesAnalysis,
    EstimativeProbability,
    FusedFinding,
    Hypothesis,
    WEP_RANGES,
    fuse_into_finding,
)
from hummbl_intel.managers import (
    CANONICAL_MANAGERS,
    INTManager,
    get_disciplines_for_agent,
    get_manager,
    manager_summary_table,
    to_dict,
)

__version__ = "0.1.0"
__all__ = [
    # taxonomy
    "IntelligenceDiscipline",
    "INT_LABELS",
    "CollectionSurface",
    "CANONICAL_SURFACES",
    "from_bus_prefix",
    "get_surface",
    "list_disciplines",
    # grading
    "SourceReliability",
    "ContentCredibility",
    "RELIABILITY_LABELS",
    "CREDIBILITY_LABELS",
    "SourceGrade",
    "GradedAssertion",
    "grade_human_source",
    "grade_automated_source",
    "grade_research_source",
    "grade_uncorroborated",
    "upgrade_with_corroboration",
    # posture
    "PostureStatus",
    "SurfaceStatus",
    "DisciplinePosture",
    "CollectionPostureReport",
    "build_default_posture",
    # fusion
    "EstimativeProbability",
    "WEP_RANGES",
    "Hypothesis",
    "CompetingHypothesesAnalysis",
    "FusedFinding",
    "AllSourceProduct",
    "fuse_into_finding",
    # managers
    "INTManager",
    "CANONICAL_MANAGERS",
    "get_manager",
    "get_disciplines_for_agent",
    "manager_summary_table",
    "to_dict",
]
