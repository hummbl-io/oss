#!/usr/bin/env python3
"""Validate multi-actor epistemic event tuples.

Stdlib-only validator with adversarial checks specific to multi-actor
events.

Adversarial checks:
1. MODEL_MERGE_PROPOSAL with unresolved_dissent_acknowledged=False — rejected
2. COALITION_FORMED with action_permission != "none" — rejected (coalition can't grant action)
3. COALITION_FORMED with coalition_authority="unrestricted" — rejected (self-expanding)
4. ACTION_EXECUTED with AI_AUTONOMOUS and approval_requirement="not_required" — rejected (authority laundering)
5. Any event with revocation_state="revoked" — rejected (revoked delegation used)
6. self_authorizing_agent regime — rejected (not a valid production regime)

Foundational epistemic invariants (MA-1 through MA-4):
MA-1. AGENT_INFERENCE must declare epistemic_permission — agent inference
      cannot be labeled as user belief (inference ≠ belief).
MA-2. USER_RATIFICATION with action_permission in (authorize_action,
      execute_action) — rejected (ratification ≠ authorization).
MA-3. HANDOFF_EVENT must include preserved_dissent — dissent survives handoff.
MA-4. independence_class must be present — correlated ≠ independent.

Usage:
    python scripts/validate_multi_actor_events.py
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples", "multi_actor")

VALID_REGIMES = {
    "user_only", "user_plus_agent", "user_plus_agent_team",
    "organization_plus_agents", "bounded_agent_only",
    "agent_society_sandbox",
}


def validate_event(event: dict, filename: str) -> list[str]:
    """Validate a single multi-actor event. Returns list of errors."""
    errors = []
    eid = event.get("id", f"<{filename}>")
    ttype = event.get("tuple_type", "")

    td = event.get("tuple_data")
    if not isinstance(td, dict):
        errors.append(f"[{eid}] tuple_data must be an object")
        return errors

    # Check actor_regime
    regime = td.get("actor_regime")
    if regime is not None and regime not in VALID_REGIMES:
        errors.append(
            f"[{eid}] actor_regime '{regime}' not allowed. "
            f"self_authorizing_agent is NOT a production-valid regime."
        )

    # Check receipt_link
    if not td.get("receipt_link"):
        errors.append(f"[{eid}] receipt_link must be non-empty")

    # Check revocation_state
    if td.get("revocation_state") == "revoked":
        errors.append(
            f"[{eid}] revocation_state='revoked' — revoked delegation "
            f"cannot be used in a later event"
        )

    # Type-specific adversarial checks
    if ttype == "MODEL_MERGE_PROPOSAL":
        if td.get("unresolved_dissent_acknowledged") is False:
            errors.append(
                f"[{eid}] MODEL_MERGE_PROPOSAL with "
                f"unresolved_dissent_acknowledged=False — merge cannot "
                f"hide unresolved dissent"
            )

    if ttype == "COALITION_FORMED":
        if td.get("action_permission") != "none":
            errors.append(
                f"[{eid}] COALITION_FORMED with action_permission != "
                f"'none' — coalition cannot grant action authority"
            )
        if td.get("coalition_authority") == "unrestricted":
            errors.append(
                f"[{eid}] COALITION_FORMED with "
                f"coalition_authority='unrestricted' — coalition cannot "
                f"self-expand authority"
            )

    if ttype == "ACTION_EXECUTED":
        if event.get("control_mode") == "AI_AUTONOMOUS":
            if td.get("approval_requirement") == "not_required":
                errors.append(
                    f"[{eid}] ACTION_EXECUTED with AI_AUTONOMOUS and "
                    f"approval_requirement='not_required' — authority "
                    f"laundering through agent"
                )

    # --- Foundational epistemic invariants (MA-1 through MA-4) ---

    # MA-1: Agent inference ≠ user belief. AGENT_INFERENCE must declare
    # epistemic_permission so the inference is explicitly labeled as agent
    # epistemic state, never as user belief.
    if ttype == "AGENT_INFERENCE":
        if "epistemic_permission" not in td:
            errors.append(
                f"[{eid}] AGENT_INFERENCE without epistemic_permission — "
                f"agent inference must not be labeled as user belief"
            )

    # MA-2: Ratification ≠ action authorization. USER_RATIFICATION is an
    # epistemic act (agreeing with a claim), not a delegation of action
    # authority. Ratification cannot carry authorize/execute permission.
    if ttype == "USER_RATIFICATION":
        ap = td.get("action_permission")
        if ap in ("authorize_action", "execute_action"):
            errors.append(
                f"[{eid}] USER_RATIFICATION with action_permission="
                f"'{ap}' — ratification cannot authorize or execute actions"
            )

    # MA-3: Dissent survives handoff. HANDOFF_EVENT must carry
    # preserved_dissent so dissenting views are not silently dropped
    # during actor transitions.
    if ttype == "HANDOFF_EVENT":
        if "preserved_dissent" not in td:
            errors.append(
                f"[{eid}] HANDOFF_EVENT without preserved_dissent — "
                f"dissent must survive handoff"
            )

    # MA-4: Correlated ≠ independent. Every multi-actor event must declare
    # independence_class so correlated agents are not counted as independent
    # validators.
    if "independence_class" not in td:
        errors.append(
            f"[{eid}] missing independence_class — correlated agents "
            f"must not be counted as independent validators"
        )

    return errors


def load_examples(directory: str) -> list[tuple[str, str, dict]]:
    """Load all JSON examples from a directory (recursive).
    Returns (relative_path, filename, data) tuples.
    """
    examples = []
    if not os.path.isdir(directory):
        return examples
    for root, _dirs, files in sorted(os.walk(directory)):
        for name in sorted(files):
            if name.endswith(".json"):
                path = os.path.join(root, name)
                rel = os.path.relpath(path, directory)
                with open(path, encoding="utf-8") as f:
                    examples.append((rel, name, json.load(f)))
    return examples


def main() -> int:
    """Run validation on all examples."""
    total_errors = 0
    valid_count = 0
    invalid_count = 0

    examples = load_examples(EXAMPLES_DIR)
    for rel, name, event in examples:
        is_invalid = "invalid" in rel
        errors = validate_event(event, name)
        if is_invalid:
            if not errors:
                print(f"FAIL: {rel} — expected errors but got none")
                total_errors += 1
            else:
                print(f"PASS: {rel} ({len(errors)} error(s))")
                for e in errors:
                    print(f"  {e}")
                invalid_count += 1
        else:
            if errors:
                print(f"FAIL: {rel}")
                for e in errors:
                    print(f"  {e}")
                total_errors += len(errors)
            else:
                print(f"PASS: {rel}")
                valid_count += 1

    print(f"\n{'=' * 40}")
    print(f"Valid fixtures: {valid_count}, Invalid fixtures: {invalid_count}")
    if total_errors:
        print(f"VALIDATION FAILED: {total_errors} error(s)")
        return 1
    print("All fixtures validated correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
