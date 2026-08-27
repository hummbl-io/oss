#!/usr/bin/env python3
"""Generate multi-actor epistemic event fixtures (valid and invalid)."""

import json
import os

EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples",
    "multi_actor",
)
INVALID_DIR = os.path.join(EXAMPLES_DIR, "invalid")


def base_event(
    tuple_type: str,
    eid: str,
    actor: str,
    principal: str,
    control_mode: str,
    actor_regime: str,
    authored_by: str,
    represented_principal: str,
    owner: str,
    receipted_by: str,
    extra: dict = None,
) -> dict:
    """Build a base event with the common envelope."""
    td = {
        "authored_by": authored_by,
        "represented_principal": represented_principal,
        "owner": owner,
        "receipted_by": receipted_by,
        "actor_regime": actor_regime,
        "evidence_links": [],
        "receipt_link": f"receipt-{eid}",
        "visibility_class": "private",
        "epistemic_permission": "observe",
        "durable_write_permission": "none",
        "action_permission": "none",
        "approval_requirement": "required",
        "authority_source": "user-001",
        "scope": "bounded",
        "expiry": "2026-12-31",
        "revocation_state": "active",
    }
    if extra:
        td.update(extra)
    return {
        "tuple_type": tuple_type,
        "id": eid,
        "time": "2026-07-11T10:00:00Z",
        "actor": actor,
        "principal": principal,
        "control_mode": control_mode,
        "tuple_data": td,
    }


VALID_FIXTURES = [
    # 1. Agent inference followed by user rejection
    (
        "01a-agent-inference.json",
        "AGENT_INFERENCE",
        "agent-a",
        "user-001",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent",
        "agent-a",
        "user-001",
        "user-001",
        "receipt-001",
        {
            "inference_content": "User appears to prefer morning meetings",
            "target_model": "umf-001",
            "inference_basis": ["obs-001", "obs-002"],
            "epistemic_permission": "infer",
        },
    ),
    (
        "01b-user-rejection.json",
        "USER_REJECTION",
        "user-001",
        "user-001",
        "USER_DIRECT",
        "user_only",
        "user-001",
        "user-001",
        "user-001",
        "receipt-002",
        {
            "rejected_claim": "User appears to prefer morning meetings",
            "rejected_fragment_ref": "umf-001",
            "rejection_reason": "I don't prefer morning meetings; the data was from a week with early deadlines",
            "epistemic_permission": "challenge",
        },
    ),
    # 2. Agent inference followed by user ratification but no action authority
    (
        "02a-agent-inference.json",
        "AGENT_INFERENCE",
        "agent-b",
        "user-002",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent",
        "agent-b",
        "user-002",
        "user-002",
        "receipt-003",
        {
            "inference_content": "Code review bottleneck is slowing merges",
            "target_model": "umf-002",
            "inference_basis": ["metrics-001"],
            "epistemic_permission": "infer",
        },
    ),
    (
        "02b-user-ratification.json",
        "USER_RATIFICATION",
        "user-002",
        "user-002",
        "USER_DIRECT",
        "user_only",
        "user-002",
        "user-002",
        "user-002",
        "receipt-004",
        {
            "ratified_claim": "Code review bottleneck is slowing merges",
            "ratified_fragment_ref": "umf-002",
            "ratification_reason": "Confirmed by merge rate data",
            "epistemic_permission": "claim",
            "action_permission": "none",
        },
    ),
    # 3. Two correlated agents supporting one claim
    (
        "03-correlated-agents.json",
        "AGENT_INFERENCE",
        "agent-c1",
        "user-003",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent_team",
        "agent-c1",
        "user-003",
        "user-003",
        "receipt-005",
        {
            "inference_content": "Latency increased after deploy v2.3",
            "target_model": "umf-003",
            "inference_basis": ["metrics-002"],
            "epistemic_permission": "infer",
            "model_provider": "same-provider",
            "source_lineage": ["shared-source"],
            "independence_class": "correlated",
        },
    ),
    # 4. Independent corroboration with distinct lineages
    (
        "04-independent-corroboration.json",
        "AGENT_INFERENCE",
        "agent-d1",
        "user-004",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent_team",
        "agent-d1",
        "user-004",
        "user-004",
        "receipt-006",
        {
            "inference_content": "Customer satisfaction improved after redesign",
            "target_model": "umf-004",
            "inference_basis": ["survey-001", "nps-001"],
            "epistemic_permission": "infer",
            "model_provider": "provider-a",
            "source_lineage": ["survey-data"],
            "retrieval_lineage": ["direct-1"],
            "evaluator_lineage": "evaluator-x",
            "independence_class": "independent",
        },
    ),
    # 5. Persistent minority dissent after bounded action acceptance
    (
        "05a-agent-dissent.json",
        "AGENT_DISSENT",
        "agent-e2",
        "user-005",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent_team",
        "agent-e2",
        "user-005",
        "user-005",
        "receipt-007",
        {
            "dissented_claim": "Redesign improved satisfaction",
            "dissent_reason": "Survey sample was biased toward existing users",
            "dissent_evidence": ["methodology-review-001"],
            "resolution_posture": "unresolved",
            "epistemic_permission": "challenge",
        },
    ),
    (
        "05b-action-authorized.json",
        "ACTION_AUTHORIZED",
        "user-005",
        "user-005",
        "USER_DIRECT",
        "user_only",
        "user-005",
        "user-005",
        "user-005",
        "receipt-008",
        {
            "authorized_action": "Proceed with redesign rollout",
            "authorized_by": "user-005",
            "authorization_reason": "Bounded action accepted despite dissent",
            "authorization_scope": "rollout-phase-1",
            "authorization_expiry": "2026-09-01",
            "action_permission": "authorize_action",
        },
    ),
    # 6. Model fork and later merge proposal
    (
        "06a-model-fork.json",
        "MODEL_FORK",
        "user-006",
        "user-006",
        "USER_DIRECT",
        "user_only",
        "user-006",
        "user-006",
        "user-006",
        "receipt-009",
        {
            "source_model": "umf-006",
            "forked_model": "umf-006-fork-a",
            "fork_reason": "Exploring alternative hypothesis",
            "durable_write_permission": "write_fragment",
        },
    ),
    (
        "06b-merge-proposal.json",
        "MODEL_MERGE_PROPOSAL",
        "agent-f1",
        "user-006",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent",
        "agent-f1",
        "user-006",
        "user-006",
        "receipt-010",
        {
            "source_model_a": "umf-006",
            "source_model_b": "umf-006-fork-a",
            "proposed_merged_model": "umf-006-merged",
            "merge_rationale": "Both branches converged on same conclusion",
            "unresolved_dissent_acknowledged": True,
            "durable_write_permission": "write_fragment",
        },
    ),
    # 7. Coalition formation and timed dissolution
    (
        "07a-coalition-formed.json",
        "COALITION_FORMED",
        "user-007",
        "user-007",
        "USER_DIRECT",
        "organization_plus_agents",
        "user-007",
        "user-007",
        "org-007",
        "receipt-011",
        {
            "coalition_id": "coal-001",
            "coalition_purpose": "Investigate latency regression",
            "coalition_members": ["agent-g1", "agent-g2", "user-007"],
            "coalition_authority": "investigation-only",
            "coalition_resources": ["metrics-access"],
            "coalition_expiry": "2026-08-01",
            "decision_rules": "consensus-with-dissent",
            "dissent_policy": "dissent-preserved",
            "action_permission": "none",
        },
    ),
    (
        "07b-coalition-dissolved.json",
        "COALITION_DISSOLVED",
        "user-007",
        "user-007",
        "USER_DIRECT",
        "organization_plus_agents",
        "user-007",
        "user-007",
        "org-007",
        "receipt-012",
        {
            "coalition_id": "coal-001",
            "dissolution_reason": "Investigation complete, expiry reached",
            "dissolution_receipt": "receipt-012",
            "action_permission": "none",
        },
    ),
    # 8. Agent version change invalidating stale calibration
    (
        "08a-agent-version-changed.json",
        "AGENT_VERSION_CHANGED",
        "agent-h1",
        "user-008",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent",
        "agent-h1",
        "user-008",
        "user-008",
        "receipt-013",
        {
            "agent_id": "agent-h1",
            "previous_version": "v1.2",
            "new_version": "v2.0",
            "change_reason": "Model upgrade",
            "durable_write_permission": "none",
        },
    ),
    (
        "08b-calibration-updated.json",
        "AGENT_CALIBRATION_UPDATED",
        "user-008",
        "user-008",
        "USER_DIRECT",
        "user_plus_agent",
        "user-008",
        "user-008",
        "user-008",
        "receipt-014",
        {
            "agent_id": "agent-h1",
            "calibration_domain": "code-review",
            "calibration_task": "merge-prediction",
            "calibration_version": "v2.0-cal-001",
            "evaluated_predictions": ["pred-001", "pred-002"],
            "abstention_behavior": "abstains on >3 file changes",
            "correction_behavior": "self-corrects on outcome mismatch",
        },
    ),
    # 9. Delegation granted and used
    (
        "09a-delegation-granted.json",
        "DELEGATION_GRANTED",
        "user-009",
        "user-009",
        "USER_DIRECT",
        "user_plus_agent",
        "user-009",
        "user-009",
        "user-009",
        "receipt-015",
        {
            "delegation_id": "deleg-001",
            "delegated_to": "agent-i1",
            "delegated_by": "user-009",
            "delegation_scope": "read-only-metrics",
            "delegation_expiry": "2026-09-01",
            "action_permission": "none",
        },
    ),
    (
        "09b-agent-observation.json",
        "AGENT_OBSERVATION",
        "agent-i1",
        "user-009",
        "AI_AUTONOMOUS",
        "bounded_agent_only",
        "agent-i1",
        "user-009",
        "user-009",
        "receipt-016",
        {
            "observation_content": "CPU usage at 80%",
            "target_model": "umf-009",
            "delegation_id": "deleg-001",
            "epistemic_permission": "observe",
            "approval_requirement": "not_required",
        },
    ),
]

INVALID_FIXTURES = [
    # Invalid merge that hides unresolved dissent
    (
        "invalid/01-invalid-merge-hides-dissent.json",
        "MODEL_MERGE_PROPOSAL",
        "agent-bad-1",
        "user-bad-1",
        "AI_PROPOSE_USER_CONFIRM",
        "user_plus_agent",
        "agent-bad-1",
        "user-bad-1",
        "user-bad-1",
        "receipt-bad-001",
        {
            "source_model_a": "umf-bad-1",
            "source_model_b": "umf-bad-1-fork",
            "proposed_merged_model": "umf-bad-1-merged",
            "merge_rationale": "Merge without acknowledging dissent",
            "unresolved_dissent_acknowledged": False,
            "durable_write_permission": "write_fragment",
        },
    ),
    # Invalid coalition self-expanding authority
    (
        "invalid/02-invalid-coalition-self-expands.json",
        "COALITION_FORMED",
        "agent-bad-2",
        "user-bad-2",
        "AI_AUTONOMOUS",
        "bounded_agent_only",
        "agent-bad-2",
        "user-bad-2",
        "user-bad-2",
        "receipt-bad-002",
        {
            "coalition_id": "coal-bad-001",
            "coalition_purpose": "Investigate latency",
            "coalition_members": ["agent-bad-2"],
            "coalition_authority": "unrestricted",  # invalid: self-expanded
            "coalition_resources": ["all-systems"],
            "coalition_expiry": "2026-12-31",
            "decision_rules": "agent-decides",
            "dissent_policy": "ignored",
            "action_permission": "execute_action",
        },
    ),  # invalid: coalition can't grant action
    # Authority laundering through another agent
    (
        "invalid/03-authority-laundering.json",
        "ACTION_EXECUTED",
        "agent-bad-3",
        "user-bad-3",
        "AI_AUTONOMOUS",
        "bounded_agent_only",
        "agent-bad-3",
        "user-bad-3",
        "user-bad-3",
        "receipt-bad-003",
        {
            "executed_action": "Deploy to production",
            "authorization_ref": "auth-bad-001",
            "execution_result": "deployed",
            "action_permission": "execute_action",
            "approval_requirement": "not_required",
        },
    ),
    # Revoked delegation used in a later event
    (
        "invalid/04-revoked-delegation-used.json",
        "AGENT_OBSERVATION",
        "agent-bad-4",
        "user-bad-4",
        "AI_AUTONOMOUS",
        "bounded_agent_only",
        "agent-bad-4",
        "user-bad-4",
        "user-bad-4",
        "receipt-bad-004",
        {
            "observation_content": "observed data",
            "target_model": "umf-bad-4",
            "delegation_id": "deleg-revoked-001",
            "epistemic_permission": "observe",
            "revocation_state": "revoked",  # invalid: using revoked delegation
            "approval_requirement": "not_required",
        },
    ),
]


def main():
    os.makedirs(EXAMPLES_DIR, exist_ok=True)
    os.makedirs(INVALID_DIR, exist_ok=True)

    for (
        filename,
        ttype,
        actor,
        principal,
        cmode,
        regime,
        authored,
        repr_princ,
        owner,
        receipted,
        extra,
    ) in VALID_FIXTURES:
        event = base_event(
            ttype,
            filename.replace(".json", "").split("-")[-1],
            actor,
            principal,
            cmode,
            regime,
            authored,
            repr_princ,
            owner,
            receipted,
            extra,
        )
        path = os.path.join(EXAMPLES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Generated: {filename}")

    for (
        filename,
        ttype,
        actor,
        principal,
        cmode,
        regime,
        authored,
        repr_princ,
        owner,
        receipted,
        extra,
    ) in INVALID_FIXTURES:
        eid = filename.replace(".json", "").split("/")[-1]
        event = base_event(
            ttype,
            eid,
            actor,
            principal,
            cmode,
            regime,
            authored,
            repr_princ,
            owner,
            receipted,
            extra,
        )
        path = os.path.join(EXAMPLES_DIR, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Generated: {filename}")


if __name__ == "__main__":
    main()
