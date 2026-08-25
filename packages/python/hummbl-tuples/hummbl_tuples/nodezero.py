from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import NodezeroTuple, NodezeroExperimentTuple


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseProfileIssuedTuple(NodezeroTuple):
    """Records the base profile issued for an experiment run.

    Schema: base_profile_issued.schema.json
    Required tuple_data: issued_by, base_profile
    """

    issued_by: str = "nodezero"
    base_profile: str = ""
    description: Optional[str] = None
    tuple_type: str = "BASE_PROFILE_ISSUED"


@dataclass(frozen=True, slots=True, kw_only=True)
class ControlModeSetTuple(NodezeroTuple):
    """Records the control mode assigned to an experiment run.

    Schema: control_mode_set.schema.json
    Required tuple_data: issued_by, control_mode
    """

    issued_by: str = "nodezero"
    control_mode: str = ""
    rationale: Optional[str] = None
    tuple_type: str = "CONTROL_MODE_SET"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRunAssignedTuple(NodezeroExperimentTuple):
    """Records assignment of an experiment run to an agent or human.

    Schema: experiment_run_assigned.schema.json
    Required tuple_data: issued_by, assignee, control_mode
    """

    issued_by: str = "nodezero"
    assignee: str = ""
    control_mode: str = ""
    base_profile: Optional[str] = None
    notes: Optional[str] = None
    tuple_type: str = "EXPERIMENT_RUN_ASSIGNED"


@dataclass(frozen=True, slots=True, kw_only=True)
class RegistryVersionPinnedTuple(NodezeroTuple):
    """Records the pinned registry versions for an experiment run.

    Schema: registry_version_pinned.schema.json
    Required tuple_data: issued_by, transformation_registry_version, mental_model_registry_version
    """

    issued_by: str = "nodezero"
    transformation_registry_version: str = ""
    mental_model_registry_version: str = ""
    evaluation_rubric_version: Optional[str] = None
    tuple_type: str = "REGISTRY_VERSION_PINNED"
