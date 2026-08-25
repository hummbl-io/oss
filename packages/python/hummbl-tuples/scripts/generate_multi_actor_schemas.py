#!/usr/bin/env python3
"""Generate multi-actor epistemic event schemas.

All schemas share a common envelope with attribution and permission fields.
This script generates them programmatically to ensure consistency.
"""

import json
import os

SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "schemas", "extensions", "multi_actor",
)

BASE = "https://hummbl.dev/schemas/tuples/extensions/multi_actor"

ATTRIBUTION_PROPS = {
    "authored_by": {"type": "string", "minLength": 1},
    "represented_principal": {"type": "string", "minLength": 1},
    "owner": {"type": "string", "minLength": 1},
    "approved_by": {"type": "string"},
    "challenged_by": {"type": "string"},
    "executed_by": {"type": "string"},
    "receipted_by": {"type": "string", "minLength": 1},
    "agent_version": {"type": "string"},
    "delegation_id": {"type": "string"},
    "actor_regime": {
        "type": "string",
        "enum": [
            "user_only", "user_plus_agent", "user_plus_agent_team",
            "organization_plus_agents", "bounded_agent_only",
            "agent_society_sandbox",
        ],
    },
}

PERMISSION_PROPS = {
    "epistemic_permission": {
        "type": "string",
        "enum": ["observe", "infer", "claim", "challenge"],
    },
    "durable_write_permission": {
        "type": "string",
        "enum": ["write_fragment", "revise_fragment", "retire_fragment", "none"],
    },
    "action_permission": {
        "type": "string",
        "enum": ["propose_action", "authorize_action", "execute_action", "none"],
    },
    "approval_requirement": {
        "type": "string",
        "enum": ["required", "not_required", "waived"],
    },
    "authority_source": {"type": "string"},
    "scope": {"type": "string"},
    "expiry": {"type": "string"},
    "revocation_state": {
        "type": "string",
        "enum": ["active", "revoked", "expired"],
    },
}

LINEAGE_PROPS = {
    "model_provider": {"type": "string"},
    "source_lineage": {"type": "array", "items": {"type": "string"}},
    "retrieval_lineage": {"type": "array", "items": {"type": "string"}},
    "tool_lineage": {"type": "array", "items": {"type": "string"}},
    "environment_lineage": {"type": "string"},
    "evaluator_lineage": {"type": "string"},
    "independence_class": {
        "type": "string",
        "enum": ["independent", "correlated", "single_lineage", "unknown"],
    },
}

COMMON_TUPLE_DATA = {
    "evidence_links": {"type": "array", "items": {"type": "string"}},
    "receipt_link": {"type": "string", "minLength": 1},
    "visibility_class": {
        "type": "string",
        "enum": ["private", "shared", "public"],
    },
}


def make_schema(tuple_type: str, title: str, description: str,
                extra_data_props: dict = None,
                required_data_fields: list = None) -> dict:
    """Build a schema for a multi-actor epistemic event."""
    data_props = {}
    data_props.update(ATTRIBUTION_PROPS)
    data_props.update(PERMISSION_PROPS)
    data_props.update(LINEAGE_PROPS)
    data_props.update(COMMON_TUPLE_DATA)
    if extra_data_props:
        data_props.update(extra_data_props)

    required = [
        "tuple_type", "id", "time", "actor", "principal",
        "control_mode", "tuple_data",
    ]
    data_required = [
        "authored_by", "represented_principal", "owner",
        "receipted_by", "actor_regime", "receipt_link",
        "visibility_class",
    ]
    if required_data_fields:
        data_required.extend(required_data_fields)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/{tuple_type.lower()}.schema.json",
        "title": title,
        "description": description,
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "tuple_type": {"const": tuple_type},
            "id": {"type": "string", "minLength": 1},
            "time": {"type": "string", "minLength": 1},
            "actor": {"type": "string", "minLength": 1},
            "principal": {"type": "string", "minLength": 1},
            "control_mode": {
                "type": "string",
                "enum": ["USER_DIRECT", "AI_PROPOSE_USER_CONFIRM",
                         "AI_AUTONOMOUS"],
            },
            "tuple_data": {
                "type": "object",
                "additionalProperties": False,
                "required": data_required,
                "properties": data_props,
            },
        },
    }


SCHEMAS = [
    ("AGENT_REGISTERED", "Multi-Actor AGENT_REGISTERED Tuple",
     "Records registration of an agent in the multi-actor system.",
     {"agent_id": {"type": "string", "minLength": 1},
      "agent_role": {"type": "string"},
      "registration_reason": {"type": "string"}},
     ["agent_id", "registration_reason"]),

    ("AGENT_VERSION_CHANGED", "Multi-Actor AGENT_VERSION_CHANGED Tuple",
     "Records a change in agent version, which may invalidate stale calibration.",
     {"agent_id": {"type": "string", "minLength": 1},
      "previous_version": {"type": "string"},
      "new_version": {"type": "string", "minLength": 1},
      "change_reason": {"type": "string"}},
     ["agent_id", "new_version"]),

    ("AGENT_ROLE_ASSIGNED", "Multi-Actor AGENT_ROLE_ASSIGNED Tuple",
     "Records assignment of a role to an agent.",
     {"agent_id": {"type": "string", "minLength": 1},
      "role": {"type": "string", "minLength": 1},
      "assignment_reason": {"type": "string"}},
     ["agent_id", "role"]),

    ("AGENT_ROLE_EXPIRED", "Multi-Actor AGENT_ROLE_EXPIRED Tuple",
     "Records expiration of an agent's role.",
     {"agent_id": {"type": "string", "minLength": 1},
      "expired_role": {"type": "string", "minLength": 1},
      "expiry_reason": {"type": "string"}},
     ["agent_id", "expired_role"]),

    ("DELEGATION_GRANTED", "Multi-Actor DELEGATION_GRANTED Tuple",
     "Records granting of delegation from one actor to another.",
     {"delegation_id": {"type": "string", "minLength": 1},
      "delegated_to": {"type": "string", "minLength": 1},
      "delegated_by": {"type": "string", "minLength": 1},
      "delegation_scope": {"type": "string"},
      "delegation_expiry": {"type": "string"}},
     ["delegation_id", "delegated_to", "delegated_by"]),

    ("DELEGATION_REVOKED", "Multi-Actor DELEGATION_REVOKED Tuple",
     "Records revocation of a delegation.",
     {"delegation_id": {"type": "string", "minLength": 1},
      "revoked_by": {"type": "string", "minLength": 1},
      "revocation_reason": {"type": "string"}},
     ["delegation_id", "revoked_by", "revocation_reason"]),

    ("AGENT_OBSERVATION", "Multi-Actor AGENT_OBSERVATION Tuple",
     "Records an observation by an agent, distinct from user observation.",
     {"observation_content": {"type": "string"},
      "target_model": {"type": "string"}},
     ["observation_content"]),

    ("AGENT_INFERENCE", "Multi-Actor AGENT_INFERENCE Tuple",
     "Records an inference by an agent. Must not be labeled as user belief.",
     {"inference_content": {"type": "string"},
      "target_model": {"type": "string"},
      "inference_basis": {"type": "array", "items": {"type": "string"}}},
     ["inference_content", "inference_basis"]),

    ("AGENT_MODEL_PROPOSAL", "Multi-Actor AGENT_MODEL_PROPOSAL Tuple",
     "Records a model proposal by an agent.",
     {"fragment_ref": {"type": "string", "minLength": 1},
      "target_model": {"type": "string"},
      "proposal_rationale": {"type": "string"}},
     ["fragment_ref"]),

    ("AGENT_CHALLENGE", "Multi-Actor AGENT_CHALLENGE Tuple",
     "Records an agent challenging a claim, model, or state.",
     {"challenged_claim": {"type": "string", "minLength": 1},
      "challenge_reason": {"type": "string"},
      "challenge_evidence": {"type": "array", "items": {"type": "string"}}},
     ["challenged_claim", "challenge_reason"]),

    ("AGENT_DISSENT", "Multi-Actor AGENT_DISSENT Tuple",
     "Records agent dissent. Dissent survives handoff and bounded decisions.",
     {"dissented_claim": {"type": "string", "minLength": 1},
      "dissent_reason": {"type": "string"},
      "dissent_evidence": {"type": "array", "items": {"type": "string"}},
      "resolution_posture": {
          "type": "string",
          "enum": ["unresolved", "partially_resolved", "resolved",
                   "superseded"],
      }},
     ["dissented_claim", "dissent_reason", "resolution_posture"]),

    ("USER_RATIFICATION", "Multi-Actor USER_RATIFICATION Tuple",
     "Records user ratification of a claim, model, or state. Does not imply action authorization.",
     {"ratified_claim": {"type": "string", "minLength": 1},
      "ratified_fragment_ref": {"type": "string"},
      "ratification_reason": {"type": "string"}},
     ["ratified_claim"]),

    ("USER_REJECTION", "Multi-Actor USER_REJECTION Tuple",
     "Records user rejection of a claim, model, or state.",
     {"rejected_claim": {"type": "string", "minLength": 1},
      "rejected_fragment_ref": {"type": "string"},
      "rejection_reason": {"type": "string"}},
     ["rejected_claim", "rejection_reason"]),

    ("ORG_RATIFICATION", "Multi-Actor ORG_RATIFICATION Tuple",
     "Records organization ratification. Does not imply action authorization.",
     {"ratified_claim": {"type": "string", "minLength": 1},
      "ratified_fragment_ref": {"type": "string"},
      "org_authority": {"type": "string"},
      "ratification_reason": {"type": "string"}},
     ["ratified_claim", "org_authority"]),

    ("ORG_REJECTION", "Multi-Actor ORG_REJECTION Tuple",
     "Records organization rejection of a claim, model, or state.",
     {"rejected_claim": {"type": "string", "minLength": 1},
      "rejected_fragment_ref": {"type": "string"},
      "org_authority": {"type": "string"},
      "rejection_reason": {"type": "string"}},
     ["rejected_claim", "rejection_reason"]),

    ("MODEL_MERGE_PROPOSAL", "Multi-Actor MODEL_MERGE_PROPOSAL Tuple",
     "Records a proposal to merge two models. Must not hide unresolved dissent.",
     {"source_model_a": {"type": "string", "minLength": 1},
      "source_model_b": {"type": "string", "minLength": 1},
      "proposed_merged_model": {"type": "string", "minLength": 1},
      "merge_rationale": {"type": "string"},
      "unresolved_dissent_acknowledged": {"type": "boolean"}},
     ["source_model_a", "source_model_b", "proposed_merged_model",
      "unresolved_dissent_acknowledged"]),

    ("MODEL_MERGE_ACCEPTED", "Multi-Actor MODEL_MERGE_ACCEPTED Tuple",
     "Records acceptance of a model merge.",
     {"merge_proposal_ref": {"type": "string", "minLength": 1},
      "merged_model": {"type": "string", "minLength": 1},
      "acceptance_reason": {"type": "string"}},
     ["merge_proposal_ref", "merged_model"]),

    ("MODEL_MERGE_REJECTED", "Multi-Actor MODEL_MERGE_REJECTED Tuple",
     "Records rejection of a model merge.",
     {"merge_proposal_ref": {"type": "string", "minLength": 1},
      "rejection_reason": {"type": "string"}},
     ["merge_proposal_ref", "rejection_reason"]),

    ("MODEL_FORK", "Multi-Actor MODEL_FORK Tuple",
     "Records forking of a model into a new branch.",
     {"source_model": {"type": "string", "minLength": 1},
      "forked_model": {"type": "string", "minLength": 1},
      "fork_reason": {"type": "string"}},
     ["source_model", "forked_model"]),

    ("HANDOFF_EVENT", "Multi-Actor HANDOFF_EVENT Tuple",
     "Records handoff from one actor to another. Dissent survives handoff.",
     {"handed_from": {"type": "string", "minLength": 1},
      "handed_to": {"type": "string", "minLength": 1},
      "handoff_context": {"type": "string"},
      "preserved_dissent": {"type": "array", "items": {"type": "string"}}},
     ["handed_from", "handed_to"]),

    ("TOOL_RESULT_PROPOSED", "Multi-Actor TOOL_RESULT_PROPOSED Tuple",
     "Records a tool result proposed for admission to a model.",
     {"tool_id": {"type": "string", "minLength": 1},
      "tool_result": {"type": "string"},
      "proposed_for_model": {"type": "string"},
      "admission_reason": {"type": "string"}},
     ["tool_id", "tool_result"]),

    ("TOOL_RESULT_ADMITTED", "Multi-Actor TOOL_RESULT_ADMITTED Tuple",
     "Records admission of a tool result into a model.",
     {"tool_result_ref": {"type": "string", "minLength": 1},
      "admitted_to_model": {"type": "string", "minLength": 1},
      "admission_reason": {"type": "string"}},
     ["tool_result_ref", "admitted_to_model"]),

    ("ACTION_PROPOSED", "Multi-Actor ACTION_PROPOSED Tuple",
     "Records proposal of an action. Action authority is separate from ratification.",
     {"proposed_action": {"type": "string", "minLength": 1},
      "target_model": {"type": "string"},
      "proposal_reason": {"type": "string"}},
     ["proposed_action"]),

    ("ACTION_AUTHORIZED", "Multi-Actor ACTION_AUTHORIZED Tuple",
     "Records authorization of an action. Must be a separate event from ratification.",
     {"authorized_action": {"type": "string", "minLength": 1},
      "authorized_by": {"type": "string", "minLength": 1},
      "authorization_reason": {"type": "string"},
      "authorization_scope": {"type": "string"},
      "authorization_expiry": {"type": "string"}},
     ["authorized_action", "authorized_by"]),

    ("ACTION_DENIED", "Multi-Actor ACTION_DENIED Tuple",
     "Records denial of an action.",
     {"denied_action": {"type": "string", "minLength": 1},
      "denied_by": {"type": "string", "minLength": 1},
      "denial_reason": {"type": "string"}},
     ["denied_action", "denied_by", "denial_reason"]),

    ("ACTION_EXECUTED", "Multi-Actor ACTION_EXECUTED Tuple",
     "Records execution of an authorized action.",
     {"executed_action": {"type": "string", "minLength": 1},
      "authorization_ref": {"type": "string", "minLength": 1},
      "execution_result": {"type": "string"}},
     ["executed_action", "authorization_ref"]),

    ("AGENT_CALIBRATION_UPDATED", "Multi-Actor AGENT_CALIBRATION_UPDATED Tuple",
     "Records calibration update for an agent. Domain/task/version specific.",
     {"agent_id": {"type": "string", "minLength": 1},
      "calibration_domain": {"type": "string", "minLength": 1},
      "calibration_task": {"type": "string"},
      "calibration_version": {"type": "string", "minLength": 1},
      "evaluated_predictions": {"type": "array", "items": {"type": "string"}},
      "abstention_behavior": {"type": "string"},
      "correction_behavior": {"type": "string"}},
     ["agent_id", "calibration_domain", "calibration_version"]),

    ("COALITION_FORMED", "Multi-Actor COALITION_FORMED Tuple",
     "Records formation of a coalition. Cannot self-expand mission or authority.",
     {"coalition_id": {"type": "string", "minLength": 1},
      "coalition_purpose": {"type": "string"},
      "coalition_members": {"type": "array", "items": {"type": "string"}},
      "coalition_authority": {"type": "string"},
      "coalition_resources": {"type": "array", "items": {"type": "string"}},
      "coalition_expiry": {"type": "string"},
      "decision_rules": {"type": "string"},
      "dissent_policy": {"type": "string"}},
     ["coalition_id", "coalition_purpose", "coalition_members",
      "coalition_authority", "coalition_expiry"]),

    ("COALITION_MEMBERSHIP_CHANGED", "Multi-Actor COALITION_MEMBERSHIP_CHANGED Tuple",
     "Records a change in coalition membership.",
     {"coalition_id": {"type": "string", "minLength": 1},
      "change_type": {"type": "string", "enum": ["joined", "left", "removed"]},
      "affected_member": {"type": "string", "minLength": 1},
      "change_reason": {"type": "string"}},
     ["coalition_id", "change_type", "affected_member"]),

    ("COALITION_DISSOLVED", "Multi-Actor COALITION_DISSOLVED Tuple",
     "Records dissolution of a coalition.",
     {"coalition_id": {"type": "string", "minLength": 1},
      "dissolution_reason": {"type": "string"},
      "dissolution_receipt": {"type": "string"}},
     ["coalition_id", "dissolution_reason"]),

    ("AGENT_QUARANTINED", "Multi-Actor AGENT_QUARANTINED Tuple",
     "Records quarantine of an agent.",
     {"agent_id": {"type": "string", "minLength": 1},
      "quarantine_reason": {"type": "string"},
      "quarantine_scope": {"type": "string"}},
     ["agent_id", "quarantine_reason"]),

    ("AGENT_REBOUND", "Multi-Actor AGENT_REBOUND Tuple",
     "Records an agent returning from quarantine.",
     {"agent_id": {"type": "string", "minLength": 1},
      "rebound_reason": {"type": "string"},
      "post_quarantine_calibration": {"type": "string"}},
     ["agent_id", "rebound_reason"]),
]


def main():
    os.makedirs(SCHEMA_DIR, exist_ok=True)
    for tuple_type, title, desc, extra, required in SCHEMAS:
        schema = make_schema(tuple_type, title, desc, extra, required)
        filename = f"{tuple_type.lower()}.schema.json"
        path = os.path.join(SCHEMA_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Generated: {filename}")


if __name__ == "__main__":
    main()
