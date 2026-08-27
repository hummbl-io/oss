"""Sigil Forge prompt DSL compiler and execution runtime.

QUARANTINED: No production callers. Excluded from arbiter scoring.
Test-only + design doc (docs/design/sigil_forge_reference.md).
Retained as research code; do not wire into production without operator approval.
"""

from __future__ import annotations

from hummbl_cognition.sigil_forge.compiler import DSLCompiler
from hummbl_cognition.sigil_forge.critique import CritiqueResult, parse_critique
from hummbl_cognition.sigil_forge.engine import (
    ExecutionEngine,
    RuntimeState,
)
from hummbl_cognition.sigil_forge.evals import EvalCase, EvalResult, run_eval_cases
from hummbl_cognition.sigil_forge.ir import (
    Condition,
    EdgeSpec,
    ExecutionPlan,
    NodeSpec,
    Program,
)
from hummbl_cognition.sigil_forge.parser import DSLParser, ParseError
from hummbl_cognition.sigil_forge.policy import (
    ActionSpec,
    CapabilityPolicy,
    PolicyViolation,
    RiskLevel,
)
from hummbl_cognition.sigil_forge.preprocessors import (
    AmbiguityDetector,
    DefensiveTextScanner,
    InputNormalizer,
    PromptInjectionDetector,
    scan_text,
)
from hummbl_cognition.sigil_forge.race import (
    RaceCandidate,
    RaceReport,
    RaceResult,
    run_race,
)
from hummbl_cognition.sigil_forge.receipts import (
    ExecutionReceipt,
    ExecutionReceiptWriter,
    build_receipt,
)
from hummbl_cognition.sigil_forge.retrievers import (
    OpenBrainSigilRetriever,
    StaticRetriever,
)
from hummbl_cognition.sigil_forge.rituals import RitualLibrary
from hummbl_cognition.sigil_forge.roles import RolePolicy, RolePolicyViolation

__all__ = [
    "Condition",
    "AmbiguityDetector",
    "ActionSpec",
    "CapabilityPolicy",
    "CritiqueResult",
    "DSLCompiler",
    "DSLParser",
    "DefensiveTextScanner",
    "EdgeSpec",
    "EvalCase",
    "EvalResult",
    "ExecutionEngine",
    "ExecutionPlan",
    "ExecutionReceipt",
    "ExecutionReceiptWriter",
    "InputNormalizer",
    "NodeSpec",
    "OpenBrainSigilRetriever",
    "ParseError",
    "PolicyViolation",
    "PromptInjectionDetector",
    "Program",
    "RaceCandidate",
    "RaceReport",
    "RaceResult",
    "RitualLibrary",
    "RiskLevel",
    "RolePolicy",
    "RolePolicyViolation",
    "RuntimeState",
    "StaticRetriever",
    "build_receipt",
    "parse_critique",
    "run_eval_cases",
    "run_race",
    "scan_text",
]
