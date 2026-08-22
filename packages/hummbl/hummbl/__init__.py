"""HUMMBL — Structured reasoning framework for AI agents.

HUMMBL provides composable reasoning engines, inspectable traces,
and domain-specific protocols. It formalizes how agents think,
not just what they do.
"""

__version__ = "0.1.0"

from hummbl.reasoning import (
    ReasoningTopology,
    StepType,
    ReasoningStep,
    ReasoningTrace,
)
from hummbl.protocols import (
    ReasoningProtocol,
    ScientificMethod,
    QualityAssessment,
    StructuredToolUse,
)
from hummbl.peptide_protocol import PeptideQualityProtocol
from hummbl.peptide_rules import (
    PEPTIDE_SPECS,
    VENDOR_TRUST_TIERS,
    GRADE_RECOMMENDATIONS,
    PeptideSpec,
)
from hummbl.capture import AutoresearchCapture, ToolUseCapture
from hummbl.scoring import DimensionScore, TraceScore, StructuredToolUseScorer
from hummbl.analyzer import TraceAnalyzer
from hummbl.planner import TracePlanner, ExperimentPlan, PlannedExperiment
from hummbl.hummbl_tuples import (
    TypedTuple,
    ContractTuple,
    DCTTuple,
    DCTXTuple,
    EvidenceTuple,
    AttestTuple,
    SystemTuple,
)
