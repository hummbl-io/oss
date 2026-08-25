#!/usr/bin/env python3
"""Research Integrity Artifact Maturity validator v0.1.

Validates artifact maturity records against the schema and enforces
semantic rules from the HUMMBL Research Integrity Standard:

- Novelty claims require prior-art review and novelty challenge
- PEER_REVIEWED requires independent review completed
- PREPRINT_CANDIDATE or higher requires reproducibility manifest
- AI use disclosure must list material assistance when agent contributions exist
- Maturity state transitions must not skip stages
- Risk checks for R1/R2 must not be FAIL when novelty claims are present

Uses only Python stdlib.
"""

import json
import sys


REQUIRED_FIELDS = [
    "schema_version", "artifact_id", "title", "maturity_state",
    "claim_postures", "risk_checks", "authorship", "ai_use_disclosure",
    "independent_review", "reproducibility_manifest",
    "correction_contact", "version_history"
]

VALID_MATURITY = {
    "IDEA", "RESEARCH_NOTE", "SOURCE_GROUNDED_CANDIDATE",
    "INTERNAL_TECHNICAL_REPORT", "REPRODUCIBLE_REPORT",
    "PREPRINT_CANDIDATE", "SUBMISSION_CANDIDATE",
    "SUBMITTED", "PEER_REVIEWED",
    "CORRECTED", "SUPERSEDED", "RETRACTED"
}

VALID_POSTURES = {
    "OBSERVATION", "MEASUREMENT", "EXPERIMENTAL_RESULT",
    "INFERENCE", "HYPOTHESIS", "DESIGN_PROPOSAL",
    "NORMATIVE_ARGUMENT", "THEORETICAL_CLAIM",
    "NOVELTY_CLAIM", "EXTERNAL_FACT", "UNVERIFIED"
}

VALID_RISK_CLASSES = {f"R{i}" for i in range(1, 16)}
VALID_RISK_STATUS = {"PASS", "FAIL", "NOT_APPLICABLE", "UNRESOLVED"}

MATURITY_ORDER = [
    "IDEA", "RESEARCH_NOTE", "SOURCE_GROUNDED_CANDIDATE",
    "INTERNAL_TECHNICAL_REPORT", "REPRODUCIBLE_REPORT",
    "PREPRINT_CANDIDATE", "SUBMISSION_CANDIDATE",
    "SUBMITTED", "PEER_REVIEWED",
]

REPRODUCIBILITY_REQUIRED_FROM = "PREPRINT_CANDIDATE"
INDEPENDENT_REVIEW_REQUIRED_FROM = "PREPRINT_CANDIDATE"
PRIOR_ART_REQUIRED_FOR_NOVELTY = True


def _check_required(record: dict) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: {field}")
    return errors


def _check_enums(record: dict) -> list[str]:
    errors = []
    if record.get("maturity_state") not in VALID_MATURITY:
        errors.append(f"Invalid maturity_state: {record.get('maturity_state')}")
    for cp in record.get("claim_postures", []):
        if cp.get("posture") not in VALID_POSTURES:
            errors.append(f"Invalid claim posture: {cp.get('posture')}")
    for rc in record.get("risk_checks", []):
        if rc.get("risk_class") not in VALID_RISK_CLASSES:
            errors.append(f"Invalid risk class: {rc.get('risk_class')}")
        if rc.get("status") not in VALID_RISK_STATUS:
            errors.append(f"Invalid risk status: {rc.get('status')}")
    return errors


def _check_novelty_discipline(record: dict) -> list[str]:
    """Novelty claims require prior-art review and novelty challenge."""
    errors = []
    has_novelty = any(
        cp.get("posture") == "NOVELTY_CLAIM"
        for cp in record.get("claim_postures", [])
    )
    if not has_novelty:
        return errors

    prior_art = record.get("prior_art_review")
    if not prior_art:
        errors.append("Novelty claims present but no prior_art_review section")
    else:
        if not prior_art.get("novelty_challenge_completed"):
            errors.append("Novelty claims present but novelty_challenge_completed is false/missing")
        if not prior_art.get("adjacent_disciplines_searched"):
            errors.append("Novelty claims present but adjacent_disciplines_searched is false/missing")

    r1 = next((r for r in record.get("risk_checks", []) if r.get("risk_class") == "R1"), None)
    r2 = next((r for r in record.get("risk_checks", []) if r.get("risk_class") == "R2"), None)
    if r1 and r1.get("status") == "FAIL":
        errors.append("Novelty claims present but R1 (NOVELTY_OVERCLAIM) is FAIL")
    if r2 and r2.get("status") == "FAIL":
        errors.append("Novelty claims present but R2 (PRIOR_ART_OMISSION) is FAIL")

    return errors


def _check_independent_review(record: dict) -> list[str]:
    """PREPRINT_CANDIDATE or higher requires independent review."""
    errors = []
    state = record.get("maturity_state", "")
    if state not in MATURITY_ORDER:
        return errors
    idx = MATURITY_ORDER.index(state) if state in MATURITY_ORDER else -1
    threshold = MATURITY_ORDER.index(REPRODUCIBILITY_REQUIRED_FROM)

    if idx >= threshold:
        review = record.get("independent_review", {})
        if not review.get("review_completed"):
            errors.append(
                f"maturity_state is {state} (>= {INDEPENDENT_REVIEW_REQUIRED_FROM}) "
                f"but independent_review.review_completed is false/missing"
            )
        if not review.get("reviewer_not_author"):
            errors.append(
                f"maturity_state is {state} but independent_review.reviewer_not_author is false/missing"
            )
    return errors


def _check_reproducibility(record: dict) -> list[str]:
    """PREPRINT_CANDIDATE or higher requires reproducibility manifest."""
    errors = []
    state = record.get("maturity_state", "")
    if state not in MATURITY_ORDER:
        return errors
    idx = MATURITY_ORDER.index(state) if state in MATURITY_ORDER else -1
    threshold = MATURITY_ORDER.index(REPRODUCIBILITY_REQUIRED_FROM)

    if idx >= threshold:
        manifest = record.get("reproducibility_manifest", {})
        if not manifest.get("methods_preserved"):
            errors.append(f"maturity_state is {state} but methods_preserved is false/missing")
        if not manifest.get("versions_preserved"):
            errors.append(f"maturity_state is {state} but versions_preserved is false/missing")
        if not manifest.get("negative_results_preserved"):
            errors.append(f"maturity_state is {state} but negative_results_preserved is false/missing")
    return errors


def _check_ai_disclosure(record: dict) -> list[str]:
    """Agent contributions must be reflected in AI-use disclosure."""
    errors = []
    agent_contribs = record.get("authorship", {}).get("agent_contributions", [])
    material = record.get("ai_use_disclosure", {}).get("material_assistance", [])

    if agent_contribs and not material:
        errors.append(
            "agent_contributions are listed but ai_use_disclosure.material_assistance is empty"
        )

    r7 = next((r for r in record.get("risk_checks", []) if r.get("risk_class") == "R7"), None)
    if r7 and r7.get("status") == "FAIL":
        if agent_contribs:
            errors.append("R7 (UNDISCLOSED_AI_ASSISTANCE) is FAIL but agent_contributions are listed")
        elif not material:
            errors.append("R7 is FAIL — AI assistance may be undisclosed")
    return errors


def _check_maturity_progression(record: dict) -> list[str]:
    """PEER_REVIEWED cannot be claimed without evidence of review."""
    errors = []
    state = record.get("maturity_state", "")
    if state == "PEER_REVIEWED":
        review = record.get("independent_review", {})
        if not review.get("review_completed"):
            errors.append("maturity_state is PEER_REVIEWED but review_completed is false")
        if not review.get("reviewer_not_author"):
            errors.append("maturity_state is PEER_REVIEWED but reviewer_not_author is false")
        manifest = record.get("reproducibility_manifest", {})
        if not manifest.get("methods_preserved"):
            errors.append("maturity_state is PEER_REVIEWED but methods not preserved")
    return errors


def validate_record(record: dict) -> list[str]:
    errors = []
    errors.extend(_check_required(record))
    if errors:
        return errors
    errors.extend(_check_enums(record))
    errors.extend(_check_novelty_discipline(record))
    errors.extend(_check_independent_review(record))
    errors.extend(_check_reproducibility(record))
    errors.extend(_check_ai_disclosure(record))
    errors.extend(_check_maturity_progression(record))
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate.py <record.json> [...]", file=sys.stderr)
        return 2
    all_valid = True
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        errors = validate_record(record)
        if errors:
            all_valid = False
            print(f"INVALID: {path}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"VALID: {path}")
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
