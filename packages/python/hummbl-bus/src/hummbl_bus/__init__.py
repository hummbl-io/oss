"""hummbl-bus: Secure append-only TSV coordination bus.

Extracted from hummbl-governance/hummbl_governance/bus/.

Provides TSV-based message bus with injection protection through
base64 encoding of payloads.

Canonical write path: ``post_message()`` (re-exported from bus_writer).
Security policy: ``get_bus_policy()`` (configurable via BUS_SECURITY_POLICY env).
Integrity audit: ``audit_bus()`` (read-only bus scanner).
Autonomy tiers: ``tier_label()``, ``can_execute()`` (from autonomy_ladder).
Inference tiers: ``baseline_tier()``, ``recommended_tier()`` (from inference_tier).
Lane classification: ``classify_message()``, ``is_foreground()`` (from lane_classifier).
Work queue: ``push_task()``, ``pull_tasks()``, ``claim_task()`` (from work_queue).
"""

from importlib import import_module

from .bus_policy import BusSecurityPolicy, get_bus_policy
from .secure_tsv import (
    BusMessage,
    SecureTSVDecoder,
    SecureTSVEncoder,
    TSVInjectionError,
)

_LAZY_BUS_VERIFIER_EXPORTS = {
    "BusAuditReport",
    "audit_bus",
}

_LAZY_BUS_WRITER_EXPORTS = {
    "harden_bus_file_permissions",
    "is_signed_message",
    "post_message",
    "read_verified_messages",
    "verify_bus_message",
}

_LAZY_AUTONOMY_LADDER_EXPORTS = {
    "tier_label",
    "required_tier_for_action",
    "can_execute",
    "validate_action_tier",
    "tier_transition_allowed",
    "actions_permitted_at_tier",
}

_LAZY_INFERENCE_TIER_EXPORTS = {
    "baseline_tier",
    "recommended_tier",
    "escalate_tier",
    "estimate_cost",
    "validate_tier_escalation",
}

_LAZY_LANE_CLASSIFIER_EXPORTS = {
    "classify_message",
    "classify_lane",
    "is_foreground",
    "is_background",
    "classify_message_from_body",
    "expected_model_tier",
    "validate_model_tier_for_task",
}

_LAZY_WORK_QUEUE_EXPORTS = {
    "TaskSpec",
    "TaskItem",
    "push_task",
    "pull_tasks",
    "claim_task",
    "complete_task",
    "generate_task_id",
}


def __getattr__(name: str):
    if name in _LAZY_BUS_VERIFIER_EXPORTS:
        module = import_module(".bus_verifier", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_BUS_WRITER_EXPORTS:
        module = import_module(".bus_writer", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_AUTONOMY_LADDER_EXPORTS:
        module = import_module(".autonomy_ladder", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_INFERENCE_TIER_EXPORTS:
        module = import_module(".inference_tier", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_LANE_CLASSIFIER_EXPORTS:
        module = import_module(".lane_classifier", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    if name in _LAZY_WORK_QUEUE_EXPORTS:
        module = import_module(".work_queue", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BusAuditReport",
    "BusMessage",
    "BusSecurityPolicy",
    "SecureTSVDecoder",
    "SecureTSVEncoder",
    "TSVInjectionError",
    "audit_bus",
    "get_bus_policy",
    "harden_bus_file_permissions",
    "is_signed_message",
    "post_message",
    "read_verified_messages",
    "verify_bus_message",
    # autonomy_ladder
    "tier_label",
    "required_tier_for_action",
    "can_execute",
    "validate_action_tier",
    "tier_transition_allowed",
    "actions_permitted_at_tier",
    # inference_tier
    "baseline_tier",
    "recommended_tier",
    "escalate_tier",
    "estimate_cost",
    "validate_tier_escalation",
    # lane_classifier
    "classify_message",
    "classify_lane",
    "is_foreground",
    "is_background",
    "classify_message_from_body",
    "expected_model_tier",
    "validate_model_tier_for_task",
    # work_queue
    "TaskSpec",
    "TaskItem",
    "push_task",
    "pull_tasks",
    "claim_task",
    "complete_task",
    "generate_task_id",
]
