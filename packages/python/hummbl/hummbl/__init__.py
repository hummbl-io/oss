"""HUMMBL — Structured reasoning framework for AI agents.

HUMMBL provides composable reasoning engines, inspectable traces,
and domain-specific protocols. It formalizes how agents think,
not just what they do.
"""

__version__ = "0.1.0"

from hummbl.analyzer import TraceAnalyzer
from hummbl.capture import AutoresearchCapture, ToolUseCapture
from hummbl.hummbl_tuples import (
    AttestTuple,
    ContractTuple,
    DCTTuple,
    DCTXTuple,
    EvidenceTuple,
    SystemTuple,
    TypedTuple,
)
from hummbl.planner import ExperimentPlan, PlannedExperiment, TracePlanner
from hummbl.protocols import (
    ReasoningProtocol,
    ScientificMethod,
    StructuredToolUse,
)
from hummbl.reasoning import (
    ReasoningStep,
    ReasoningTopology,
    ReasoningTrace,
    StepType,
)
from hummbl.scoring import DimensionScore, StructuredToolUseScorer, TraceScore

__all__ = [
    "AttestTuple",
    "AutoresearchCapture",
    "ContractTuple",
    "DCTTuple",
    "DCTXTuple",
    "DimensionScore",
    "EvidenceTuple",
    "ExperimentPlan",
    "PlannedExperiment",
    "ReasoningProtocol",
    "ReasoningStep",
    "ReasoningTopology",
    "ReasoningTrace",
    "ScientificMethod",
    "StepType",
    "StructuredToolUse",
    "StructuredToolUseScorer",
    "SystemTuple",
    "ToolUseCapture",
    "TraceAnalyzer",
    "TracePlanner",
    "TraceScore",
    "TypedTuple",
    "__version__",
]
