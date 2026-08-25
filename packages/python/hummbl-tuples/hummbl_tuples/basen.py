from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .base import BaseNTuple


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelCandidateTuple(BaseNTuple):
    """A candidate mental model proposed for a transformation.

    Schema: model_candidate.schema.json
    Required tuple_data: transformation_id, mental_model_id, candidate_rank, proposed_by
    """

    transformation_id: str = ""
    mental_model_id: str = ""
    candidate_rank: int = 1
    proposed_by: str = ""
    selection_rationale: Optional[str] = None
    confidence: Optional[float] = None
    tuple_type: str = "MODEL_CANDIDATE"


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelSelectedTuple(BaseNTuple):
    """The mental model selected for a transformation.

    Schema: model_selected.schema.json
    Required tuple_data: transformation_id, mental_model_id, selected_by, selection_rationale
    """

    transformation_id: str = ""
    mental_model_id: str = ""
    selected_by: str = ""
    selection_rationale: str = ""
    candidate_count: Optional[int] = None
    confidence: Optional[float] = None
    tuple_type: str = "MODEL_SELECTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class TransformationCandidateTuple(BaseNTuple):
    """A candidate transformation proposed for a problem.

    Schema: transformation_candidate.schema.json
    Required tuple_data: transformation_id, candidate_rank, proposed_by, selection_rationale
    """

    transformation_id: str = ""
    candidate_rank: int = 1
    proposed_by: str = ""
    selection_rationale: str = ""
    confidence: Optional[float] = None
    tuple_type: str = "TRANSFORMATION_CANDIDATE"


@dataclass(frozen=True, slots=True, kw_only=True)
class TransformationSelectedTuple(BaseNTuple):
    """The transformation selected for a problem.

    Schema: transformation_selected.schema.json
    Required tuple_data: transformation_id, selected_by, selection_rationale
    """

    transformation_id: str = ""
    selected_by: str = ""
    selection_rationale: str = ""
    candidate_count: Optional[int] = None
    confidence: Optional[float] = None
    tuple_type: str = "TRANSFORMATION_SELECTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class HitlOverrideTuple(BaseNTuple):
    """A human-in-the-loop override of a prior tuple decision.

    Schema: hitl_override.schema.json
    Required tuple_data: overridden_tuple_id, override_type, human_actor, override_reason
    """

    overridden_tuple_id: str = ""
    override_type: str = ""
    human_actor: str = ""
    override_reason: str = ""
    replacement_transformation_id: Optional[str] = None
    replacement_mental_model_id: Optional[str] = None
    tuple_type: str = "HITL_OVERRIDE"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningPathTuple(BaseNTuple):
    """A reasoning path constructed from a sequence of transformation steps.

    Schema: reasoning_path.schema.json
    Required tuple_data: path_id, constructed_by, path_steps
    path_steps items: {step_index: int, transformation_id: str, mental_model_id: str}
    """

    path_id: str = ""
    constructed_by: str = ""
    path_steps: List[Dict[str, object]] = field(default_factory=list)
    path_depth: Optional[int] = None
    tuple_type: str = "REASONING_PATH"


@dataclass(frozen=True, slots=True, kw_only=True)
class PathComparisonTuple(BaseNTuple):
    """Comparison of two reasoning paths.

    Schema: path_comparison.schema.json
    Required tuple_data: path_a_id, path_b_id, comparison_basis, preferred_path, decided_by
    """

    path_a_id: str = ""
    path_b_id: str = ""
    comparison_basis: str = ""
    preferred_path: str = ""
    decided_by: str = ""
    notes: Optional[str] = None
    tuple_type: str = "PATH_COMPARISON"


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceEvidenceTuple(BaseNTuple):
    """Evidence supporting or refuting a claim along a reasoning path.

    Schema: trace_evidence_tuple.schema.json
    Required tuple_data: path_id, claim, evidence_status, metric_bundle
    """

    path_id: str = ""
    claim: str = ""
    evidence_status: str = ""
    metric_bundle: Dict[str, object] = field(default_factory=dict)
    notes: Optional[str] = None
    tuple_type: str = "TRACE_EVIDENCE"
