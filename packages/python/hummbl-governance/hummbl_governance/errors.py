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
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""HUMMBL unified error taxonomy.

Three layers:
  FailureMode  — contract/artifact-level governance failure modes (FM1–FM30)
  HummblError  — runtime governance violation codes (HG_E_*, execution level)
  FM_TO_ERRORS — mapping from FM codes to HummblError values

IDP_E_* aliases are provided for backward compatibility with hummbl-governance code
that currently uses the IDP_E_* naming convention.
"""

from __future__ import annotations

from enum import Enum


class FailureMode(str, Enum):
    """Contract and artifact-level governance failure modes (FM1–FM42).

    FM1–FM30: contract/artifact-level governance failures.
    FM31–FM42: interaction-level systemic risk failures (ESRH taxonomy,
    arXiv:2512.02682). These describe emergent risks in multi-agent
    interaction — semantic drift, covert channels, alignment faking,
    collusion, polarization, and feedback degradation.

    These describe categories of structural failure in governance contracts,
    schemas, and execution artifacts — not runtime violations.
    """

    SPECIFICATION_AMBIGUITY = "FM1"
    UNBOUNDED_SCOPE = "FM2"
    IMPLICIT_ASSUMPTIONS = "FM3"
    INVALID_STATE_TRANSITION = "FM4"
    HIDDEN_COUPLING = "FM5"
    INCOMPLETE_VALIDATION = "FM6"
    INCONSISTENT_CONSTRAINTS = "FM7"
    DATA_SHAPE_MISMATCH = "FM8"
    TYPE_SYSTEM_VIOLATION = "FM9"
    BOUNDARY_CONDITION_FAILURE = "FM10"
    RESOURCE_EXHAUSTION = "FM11"
    TEMPORAL_ORDERING_VIOLATION = "FM12"
    NON_DETERMINISTIC_BEHAVIOR = "FM13"
    VERSION_INCOMPATIBILITY = "FM14"
    SCHEMA_NON_COMPLIANCE = "FM15"
    INVALID_REFERENCE = "FM16"
    AUTHORIZATION_FAILURE = "FM17"
    POLICY_VIOLATION = "FM18"
    OBSERVABILITY_FAILURE = "FM19"
    AVAILABILITY_LOSS = "FM20"
    LATENCY_BREACH = "FM21"
    CONFIGURATION_DRIFT = "FM22"
    DEPENDENCY_FAILURE = "FM23"
    STATE_CORRUPTION = "FM24"
    GOVERNANCE_BYPASS = "FM25"
    ESCALATION_SUPPRESSION = "FM26"
    TERMINATION_FAILURE = "FM27"
    AUDIT_TRAIL_LOSS = "FM28"
    RECOVERY_FAILURE = "FM29"
    UNRECOVERABLE_SYSTEM_STATE = "FM30"
    # ESRH interaction-level systemic risks (arXiv:2512.02682)
    SEMANTIC_DRIFT_PROPAGATION = "FM31"
    COVERT_CHANNEL_FORMATION = "FM32"
    ALIGNMENT_FAKING = "FM33"
    SYCOPHANTIC_CONVERGENCE = "FM34"
    FALSE_CONSENSUS_COLLAPSE = "FM35"
    AGENT_COLLUSION = "FM36"
    NETWORK_POLARIZATION = "FM37"
    MODEL_DATA_FEEDBACK_DEGRADATION = "FM38"
    CASCADING_ERROR_PROPAGATION = "FM39"
    PROMPT_INFECTION_VECTOR = "FM40"
    CROSS_AGENT_DATA_LEAKAGE = "FM41"
    EMERGENT_CONFLICT_ESCALATION = "FM42"


class HummblError(str, Enum):
    """Runtime governance violation codes (execution level).

    These are raised when a running system violates a governance invariant —
    delegation bounds, capability constraints, audit requirements, etc.

    All codes use the HG_E_ prefix. IDP_E_* aliases below provide backward
    compatibility with existing hummbl-governance code.
    """

    # --- Delegation / DCT ---
    DCT_VIOLATION = "HG_E_DCT_VIOLATION"
    TOKEN_EXPIRED = "HG_E_TOKEN_EXPIRED"  # nosec B105 — error code enum, not a password
    TOKEN_INVALID = "HG_E_TOKEN_INVALID"  # nosec B105 — error code enum, not a password
    BINDING_MISMATCH = "HG_E_BINDING_MISMATCH"
    DEPTH_EXCEEDED = "HG_E_DEPTH_EXCEEDED"
    CAPABILITY_ESCALATION = "HG_E_CAPABILITY_ESCALATION"
    REPLAN_LIMIT = "HG_E_REPLAN_LIMIT"

    # --- Audit / governance bus ---
    AUDIT_IMMUTABLE = "HG_E_AUDIT_IMMUTABLE"
    AUDIT_INCOMPLETE = "HG_E_AUDIT_INCOMPLETE"
    AMENDMENT_TARGET_MISSING = "HG_E_AMENDMENT_TARGET_MISSING"
    VERIFICATION_REF_INVALID = "HG_E_VERIFICATION_REF_INVALID"
    EVIDENCE_REQUIRED = "HG_E_EVIDENCE_REQUIRED"
    CHAIN_BROKEN = "HG_E_CHAIN_BROKEN"

    # --- State machine ---
    INVALID_STATE_TRANSITION = "HG_E_INVALID_STATE_TRANSITION"


# ---------------------------------------------------------------------------
# FM → runtime error mapping
# Shows which FailureModes correspond to which HummblErrors at runtime.
# ---------------------------------------------------------------------------

FM_TO_ERRORS: dict[str, list[HummblError]] = {
    FailureMode.INVALID_STATE_TRANSITION.value: [HummblError.INVALID_STATE_TRANSITION],
    FailureMode.AUTHORIZATION_FAILURE.value: [
        HummblError.DCT_VIOLATION,
        HummblError.TOKEN_INVALID,
    ],
    FailureMode.POLICY_VIOLATION.value: [HummblError.CAPABILITY_ESCALATION],
    FailureMode.GOVERNANCE_BYPASS.value: [HummblError.DCT_VIOLATION],
    FailureMode.AUDIT_TRAIL_LOSS.value: [
        HummblError.AUDIT_IMMUTABLE,
        HummblError.AUDIT_INCOMPLETE,
    ],
    FailureMode.ESCALATION_SUPPRESSION.value: [HummblError.CHAIN_BROKEN],
    FailureMode.INVALID_REFERENCE.value: [HummblError.VERIFICATION_REF_INVALID],
    FailureMode.INCOMPLETE_VALIDATION.value: [HummblError.EVIDENCE_REQUIRED],
}


def fm_to_errors(fm_code: str) -> list[HummblError]:
    """Return runtime errors associated with a failure mode code.

    Args:
        fm_code: A failure mode code, e.g. "FM4" or "FM28".

    Returns:
        List of associated HummblError values, or empty list if none mapped.
    """
    return FM_TO_ERRORS.get(fm_code, [])


# ---------------------------------------------------------------------------
# IDP_E_* backward-compatibility aliases
# hummbl-governance code uses these names; they resolve to the same enum members.
# ---------------------------------------------------------------------------

IDP_E_DCT_VIOLATION = HummblError.DCT_VIOLATION
IDP_E_TOKEN_EXPIRED = HummblError.TOKEN_EXPIRED
IDP_E_TOKEN_INVALID = HummblError.TOKEN_INVALID
IDP_E_BINDING_MISMATCH = HummblError.BINDING_MISMATCH
IDP_E_DEPTH_EXCEEDED = HummblError.DEPTH_EXCEEDED
IDP_E_CAPABILITY_ESCALATION = HummblError.CAPABILITY_ESCALATION
IDP_E_REPLAN_LIMIT = HummblError.REPLAN_LIMIT
IDP_E_AUDIT_IMMUTABLE = HummblError.AUDIT_IMMUTABLE
IDP_E_AUDIT_INCOMPLETE = HummblError.AUDIT_INCOMPLETE
IDP_E_AMENDMENT_TARGET_MISSING = HummblError.AMENDMENT_TARGET_MISSING
IDP_E_VERIFICATION_REF_INVALID = HummblError.VERIFICATION_REF_INVALID
IDP_E_EVIDENCE_REQUIRED = HummblError.EVIDENCE_REQUIRED
IDP_E_CHAIN_BROKEN = HummblError.CHAIN_BROKEN
IDP_E_INVALID_STATE_TRANSITION = HummblError.INVALID_STATE_TRANSITION
