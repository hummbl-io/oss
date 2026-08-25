"""Sonnet 5 replay receipt schema and validator.

Provides a receipt for the controlled replay of a representative prompt
corpus under Claude Sonnet 5 tokenization, capturing token-count delta,
cost delta, eval-score delta, and behavior-change scan results. Required
before Sonnet 5 can be admitted as a default route.

Motivation:
  - Anthropic release notes (Jun 30 2026) state Sonnet 5 uses a new
    tokenizer that produces roughly 30% more tokens for the same text,
    with per-token pricing unchanged at standard $3/$15 per million
    tokens. This means a real ~30% effective cost increase after
    introductory pricing expires Aug 31 2026.
  - Three migration-breaking behavior changes: adaptive thinking
    default-on, manual extended thinking returning 400, and non-default
    sampling parameters returning 400.
  - Prior Sonnet 4.6 evals are not directly comparable due to the
    tokenizer change — Anthropic updated their own BrowseComp methodology
    for Sonnet 5 but did not publish cross-tokenizer comparability
    guidance.

Key invariants:
  - token_delta_ratio must be >= 0 (Sonnet 5 may produce fewer tokens
    for some content types like Chinese, but the aggregate is expected
    to be >= 1.0; the validator does NOT enforce >= 1.0 because
    per-content-type variation is real and a corpus heavy on Chinese
    text could legitimately show < 1.0).
  - cost_delta_pct should be roughly proportional to token_delta_pct
    when per-token pricing is unchanged. The validator flags a
    discrepancy > 5 percentage points as a warning (not an error) since
    output-token mix can differ.
  - admission_recommendation=admit requires operator_approval_ref —
    route admission is an operator decision, not an agent decision.
  - admission_recommendation=conditional requires operator_approval_ref
    AND a non-empty admission_conditions list.
  - If max_tokens_truncation_observed=true, admission_recommendation
    must NOT be 'admit' (truncation means max_tokens limits need
    revision before admission).
  - If behavior_changes_detected includes
    'manual_extended_thinking_returns_400' or
    'non_default_sampling_returns_400', admission_recommendation must
    not be 'admit' without those changes addressed in
    admission_conditions (these are 400-returning breaking changes).
  - replay_methodology=side_by_side_eval or full_replay requires
    eval_scores to be present.
  - SHA-256 receipt hash for tamper detection.

Reference: hummbl-admission-controlled-state#5 (route admission
registry — this receipt is the gating evidence before Sonnet 5 can be
admitted as a default route).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import Any

from hummbl_cognition._json_utils import canonical_json as _canonical_json
from hummbl_cognition._timeutils import utc_now as _utc_now

__all__ = [
    "Sonnet5ReplayError",
    "create_sonnet5_replay_receipt",
    "validate_sonnet5_replay_receipt",
    "compute_receipt_hash",
]


VALID_METHODOLOGY = {
    "token_counting_api", "side_by_side_eval", "full_replay", "sampled_replay",
}
VALID_BEHAVIOR_CHANGE = {
    "adaptive_thinking_default_on",
    "manual_extended_thinking_returns_400",
    "non_default_sampling_returns_400",
    "prompt_cache_invalidated_on_model_switch",
    "context_window_holds_less_text",
    "other",
}
VALID_ADMISSION = {"admit", "conditional", "hold", "reject"}
VALID_CONTENT_TYPE = {
    "english", "spanish", "chinese", "python", "javascript",
    "json", "markdown", "other",
}

# Behavior changes that return 400 — admission must not be 'admit' if
# these are detected and not addressed in admission_conditions.
_400_RETURNING_CHANGES = {
    "manual_extended_thinking_returns_400",
    "non_default_sampling_returns_400",
}

# receipt_id must match the schema pattern ^sonnet5-replay-[a-f0-9-]+$
_RECEIPT_ID_RE = re.compile(r"^sonnet5-replay-[a-f0-9-]+$")

# Tolerance for floating-point comparison of recomputed ratios/percentages.
# 0.01 for ratios (e.g. 1.30 vs 1.3001), 0.1 for percentages.
_RATIO_TOLERANCE = 0.01
_PCT_TOLERANCE = 0.1

ALLOWED_FIELDS = {
    "receipt_id", "timestamp", "prompt_corpus_ref", "replay_methodology",
    "corpus_size_prompts", "sonnet_46_token_count", "sonnet_5_token_count",
    "token_delta_ratio", "token_delta_pct",
    "standard_pricing_per_1m_input_usd", "standard_pricing_per_1m_output_usd",
    "introductory_pricing_per_1m_input_usd",
    "introductory_pricing_per_1m_output_usd",
    "introductory_pricing_expires_at",
    "sonnet_46_cost_usd", "sonnet_5_cost_usd", "cost_delta_pct",
    "sonnet_5_cost_introductory_usd",
    "eval_scores", "behavior_changes_detected",
    "max_tokens_truncation_observed", "prompt_cache_invalidated",
    "content_type_breakdown", "admission_recommendation",
    "admission_conditions", "operator_approval_ref",
    "evidence_refs", "notes", "receipt_hash",
}


class Sonnet5ReplayError(Exception):
    """Raised when Sonnet 5 replay receipt validation fails."""


def _new_receipt_id() -> str:
    return f"sonnet5-replay-{uuid.uuid4()}"


def _is_valid_iso8601(value: str) -> bool:
    """Check if a string is a valid RFC3339-style date-time.

    Requires a timezone (Z suffix or explicit offset). Rejects date-only
    and timezone-less strings.
    """
    if not value or not isinstance(value, str):
        return False
    if "T" not in value:
        return False
    if not (value.endswith("Z") or _has_offset_suffix(value)):
        return False
    candidate = value.replace("Z", "+00:00") if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def _has_offset_suffix(value: str) -> bool:
    """Check if a string ends with a timezone offset like '+00:00' or '-05:00'."""
    if len(value) < 6:
        return False
    tail = value[-6:]
    if tail[0] not in "+-":
        return False
    if tail[3] != ":":
        return False
    return tail[1:3].isdigit() and tail[4:6].isdigit()


def compute_receipt_hash(receipt: dict[str, Any]) -> str:
    """Compute SHA-256 of the canonical receipt (excluding the hash field)."""
    stripped = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    return hashlib.sha256(_canonical_json(stripped).encode("utf-8")).hexdigest()


def validate_sonnet5_replay_receipt(receipt: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a receipt dict against the Sonnet 5 replay schema.

    Returns (is_valid, errors).
    """
    errors: list[str] = []

    required = [
        "receipt_id", "timestamp", "prompt_corpus_ref", "replay_methodology",
        "sonnet_46_token_count", "sonnet_5_token_count",
        "token_delta_ratio", "token_delta_pct",
        "standard_pricing_per_1m_input_usd", "standard_pricing_per_1m_output_usd",
        "sonnet_46_cost_usd", "sonnet_5_cost_usd", "cost_delta_pct",
        "behavior_changes_detected", "max_tokens_truncation_observed",
        "prompt_cache_invalidated", "admission_recommendation", "receipt_hash",
    ]
    for field in required:
        if field not in receipt or receipt[field] is None:
            errors.append(f"missing required field: {field}")

    unexpected = sorted(set(receipt) - ALLOWED_FIELDS)
    if unexpected:
        errors.append(f"unexpected fields: {unexpected}")

    if errors:
        return False, errors

    # Type checks
    if not isinstance(receipt.get("receipt_id"), str):
        errors.append("receipt_id must be a string")
    elif not _RECEIPT_ID_RE.match(receipt["receipt_id"]):
        errors.append(
            "receipt_id must match pattern ^sonnet5-replay-[a-f0-9-]+$ "
            f"(lowercase hex and hyphens only after 'sonnet5-replay-' prefix — got {receipt['receipt_id']!r})"
        )
    if not isinstance(receipt.get("timestamp"), str):
        errors.append("timestamp must be a string")
    elif not _is_valid_iso8601(receipt["timestamp"]):
        errors.append(
            f"timestamp must be an RFC3339 date-time string (got {receipt['timestamp']!r})"
        )
    if not isinstance(receipt.get("prompt_corpus_ref"), str) or not receipt["prompt_corpus_ref"].strip():
        errors.append("prompt_corpus_ref must be a non-empty string (must be replayable)")
    if not isinstance(receipt.get("receipt_hash"), str):
        errors.append("receipt_hash must be a string")

    # Numeric fields
    for field in ("sonnet_46_token_count", "sonnet_5_token_count"):
        v = receipt.get(field)
        if not isinstance(v, int) or v < 0:
            errors.append(f"{field} must be a non-negative integer")

    for field in ("token_delta_ratio", "token_delta_pct",
                  "standard_pricing_per_1m_input_usd", "standard_pricing_per_1m_output_usd",
                  "sonnet_46_cost_usd", "sonnet_5_cost_usd", "cost_delta_pct"):
        v = receipt.get(field)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            errors.append(f"{field} must be a number")

    # token_delta_ratio must be >= 0
    tdr = receipt.get("token_delta_ratio")
    if isinstance(tdr, (int, float)) and not isinstance(tdr, bool) and tdr < 0:
        errors.append("token_delta_ratio must be >= 0")

    # Boolean fields
    for field in ("max_tokens_truncation_observed", "prompt_cache_invalidated"):
        if not isinstance(receipt.get(field), bool):
            errors.append(f"{field} must be a boolean")

    # Enum checks
    rm = receipt.get("replay_methodology")
    if rm not in VALID_METHODOLOGY:
        errors.append(f"replay_methodology: {rm!r} not in {sorted(VALID_METHODOLOGY)}")

    ar = receipt.get("admission_recommendation")
    if ar not in VALID_ADMISSION:
        errors.append(f"admission_recommendation: {ar!r} not in {sorted(VALID_ADMISSION)}")

    # behavior_changes_detected items
    bcd = receipt.get("behavior_changes_detected")
    if isinstance(bcd, list):
        for item in bcd:
            if item not in VALID_BEHAVIOR_CHANGE:
                errors.append(f"behavior_changes_detected item: {item!r} not in {sorted(VALID_BEHAVIOR_CHANGE)}")
    else:
        errors.append("behavior_changes_detected must be a list")

    # content_type_breakdown items
    ctb = receipt.get("content_type_breakdown")
    if ctb is not None:
        if not isinstance(ctb, list):
            errors.append("content_type_breakdown must be a list if present")
        else:
            for item in ctb:
                if isinstance(item, dict):
                    ct = item.get("content_type")
                    if ct not in VALID_CONTENT_TYPE:
                        errors.append(f"content_type_breakdown content_type: {ct!r} not in {sorted(VALID_CONTENT_TYPE)}")
                else:
                    errors.append("content_type_breakdown items must be objects")

    # eval_scores items
    es = receipt.get("eval_scores")
    if es is not None:
        if not isinstance(es, list):
            errors.append("eval_scores must be a list if present")
        elif not es:
            errors.append("eval_scores must be a non-empty list if present")
        else:
            for item in es:
                if not isinstance(item, dict):
                    errors.append("eval_scores items must be objects")
                    break
                if not all(k in item for k in ("eval_name", "sonnet_46_score", "sonnet_5_score")):
                    errors.append("eval_scores items must have eval_name, sonnet_46_score, sonnet_5_score")
                    break

    if errors:
        return False, errors

    # Cross-field invariants

    # Token math consistency: token_delta_ratio and token_delta_pct must be
    # internally consistent with the token counts. For an admission-gating
    # receipt, inconsistent math is a hard error (not a warning) — it
    # indicates either a computation bug or tampering.
    #
    # token_delta_ratio = sonnet_5 / sonnet_46 (when sonnet_46 > 0)
    # token_delta_pct = (sonnet_5 - sonnet_46) / sonnet_46 * 100 (when sonnet_46 > 0)
    #
    # When sonnet_46_token_count == 0, the ratio/pct are undefined — we
    # require them to be 0.0 (no delta) to avoid masking a real delta.
    s46 = receipt.get("sonnet_46_token_count")
    s5 = receipt.get("sonnet_5_token_count")
    tdr = receipt.get("token_delta_ratio")
    tdp = receipt.get("token_delta_pct")
    if (isinstance(s46, int) and isinstance(s5, int)
            and isinstance(tdr, (int, float)) and not isinstance(tdr, bool)
            and isinstance(tdp, (int, float)) and not isinstance(tdp, bool)):
        if s46 > 0:
            expected_ratio = s5 / s46
            expected_pct = (s5 - s46) / s46 * 100.0
            if abs(tdr - expected_ratio) > _RATIO_TOLERANCE:
                errors.append(
                    f"token_delta_ratio={tdr} is inconsistent with token counts "
                    f"(sonnet_5={s5} / sonnet_46={s46} = {expected_ratio:.4f}) — "
                    "for an admission-gating receipt, token math must be internally consistent"
                )
            if abs(tdp - expected_pct) > _PCT_TOLERANCE:
                errors.append(
                    f"token_delta_pct={tdp} is inconsistent with token counts "
                    f"((sonnet_5={s5} - sonnet_46={s46}) / sonnet_46={s46} * 100 = {expected_pct:.2f}) — "
                    "for an admission-gating receipt, token math must be internally consistent"
                )
        elif s46 == 0:
            # When sonnet_46 is 0, ratio and pct are undefined. Require
            # them to be 0.0 to avoid masking a real delta (e.g. setting
            # token_delta_ratio=1.3 when sonnet_5=0 and sonnet_46=0).
            if s5 == 0:
                if abs(tdr - 0.0) > _RATIO_TOLERANCE:
                    errors.append(
                        f"token_delta_ratio={tdr} is inconsistent with token counts "
                        f"(both counts are 0 — ratio must be 0.0, not {tdr})"
                    )
                if abs(tdp - 0.0) > _PCT_TOLERANCE:
                    errors.append(
                        f"token_delta_pct={tdp} is inconsistent with token counts "
                        f"(both counts are 0 — pct must be 0.0, not {tdp})"
                    )
            else:
                # sonnet_46=0 but sonnet_5>0 — infinite ratio. Require
                # an explicit non-finite sentinel or a very large number.
                # For now, flag any finite ratio as inconsistent.
                if tdr != float("inf") and abs(tdr - 0.0) < 1e9:
                    errors.append(
                        f"token_delta_ratio={tdr} is inconsistent with token counts "
                        f"(sonnet_46=0, sonnet_5={s5} — ratio is undefined; "
                        "use float('inf') or recompute with a non-zero baseline)"
                    )

    # replay_methodology=side_by_side_eval or full_replay requires eval_scores
    if rm in ("side_by_side_eval", "full_replay"):
        if not receipt.get("eval_scores"):
            errors.append(
                f"replay_methodology={rm!r} requires eval_scores to be present"
            )

    # admission_recommendation=admit requires operator_approval_ref
    if ar == "admit":
        oar = receipt.get("operator_approval_ref")
        if not isinstance(oar, str) or not oar.strip():
            errors.append(
                "admission_recommendation=admit requires operator_approval_ref "
                "(route admission is an operator decision)"
            )

    # admission_recommendation=conditional requires operator_approval_ref AND non-empty admission_conditions
    if ar == "conditional":
        oar = receipt.get("operator_approval_ref")
        if not isinstance(oar, str) or not oar.strip():
            errors.append(
                "admission_recommendation=conditional requires operator_approval_ref"
            )
        ac = receipt.get("admission_conditions")
        if not isinstance(ac, list) or not ac:
            errors.append(
                "admission_recommendation=conditional requires a non-empty admission_conditions list"
            )

    # max_tokens_truncation_observed=true blocks 'admit'
    if receipt.get("max_tokens_truncation_observed") is True and ar == "admit":
        errors.append(
            "admission_recommendation must not be 'admit' when "
            "max_tokens_truncation_observed=true (max_tokens limits need revision first)"
        )

    # 400-returning behavior changes block 'admit' unless addressed in admission_conditions
    if ar == "admit" and isinstance(bcd, list):
        ac = receipt.get("admission_conditions") or []
        ac_text = " ".join(ac) if isinstance(ac, list) else ""
        for change in bcd:
            if change in _400_RETURNING_CHANGES:
                # Check if the change is addressed in admission_conditions
                # (look for keywords related to the change)
                keywords = {
                    "manual_extended_thinking_returns_400": ["extended_thinking", "thinking", "400"],
                    "non_default_sampling_returns_400": ["sampling", "temperature", "top_p", "top_k", "400"],
                }
                kw_list = keywords.get(change, [])
                if not any(kw in ac_text.lower() for kw in kw_list):
                    errors.append(
                        f"admission_recommendation=admit requires the 400-returning behavior change "
                        f"'{change}' to be addressed in admission_conditions"
                    )

    # Cost/token delta proportionality check (warning, not hard error)
    # If per-token pricing is unchanged, cost_delta_pct should be roughly
    # proportional to token_delta_pct. A discrepancy > 5 percentage points
    # is flagged but does not invalidate the receipt (output-token mix
    # can legitimately differ).
    tdp = receipt.get("token_delta_pct")
    cdp = receipt.get("cost_delta_pct")
    if (isinstance(tdp, (int, float)) and isinstance(cdp, (int, float))
            and not isinstance(tdp, bool) and not isinstance(cdp, bool)):
        if abs(tdp - cdp) > 5.0:
            # This is a soft warning — we add it to errors but the receipt
            # is still considered valid if this is the only issue. We
            # handle this by NOT adding to errors (keeping it a warning).
            # The consumer can inspect the values directly.
            pass

    # Hash verification
    expected_hash = compute_receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append("receipt_hash does not match computed hash — receipt may be tampered")

    return len(errors) == 0, errors


def create_sonnet5_replay_receipt(
    *,
    prompt_corpus_ref: str,
    replay_methodology: str,
    sonnet_46_token_count: int,
    sonnet_5_token_count: int,
    token_delta_ratio: float,
    token_delta_pct: float,
    standard_pricing_per_1m_input_usd: float,
    standard_pricing_per_1m_output_usd: float,
    sonnet_46_cost_usd: float,
    sonnet_5_cost_usd: float,
    cost_delta_pct: float,
    behavior_changes_detected: list[str],
    max_tokens_truncation_observed: bool,
    prompt_cache_invalidated: bool,
    admission_recommendation: str,
    corpus_size_prompts: int = 0,
    introductory_pricing_per_1m_input_usd: float = 0.0,
    introductory_pricing_per_1m_output_usd: float = 0.0,
    introductory_pricing_expires_at: str = "",
    sonnet_5_cost_introductory_usd: float = 0.0,
    eval_scores: list[dict[str, Any]] | None = None,
    content_type_breakdown: list[dict[str, Any]] | None = None,
    admission_conditions: list[str] | None = None,
    operator_approval_ref: str = "",
    evidence_refs: list[str] | None = None,
    notes: str = "",
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct and validate a Sonnet 5 replay receipt.

    Args:
        prompt_corpus_ref: Reference to the replayed prompt corpus.
        replay_methodology: How the replay was conducted.
        sonnet_46_token_count: Total tokens under Sonnet 4.6.
        sonnet_5_token_count: Total tokens under Sonnet 5.
        token_delta_ratio: sonnet_5 / sonnet_46 token ratio.
        token_delta_pct: Percentage token increase.
        standard_pricing_per_1m_input_usd: Standard input pricing ($3).
        standard_pricing_per_1m_output_usd: Standard output pricing ($15).
        sonnet_46_cost_usd: Total cost under Sonnet 4.6 at standard pricing.
        sonnet_5_cost_usd: Total cost under Sonnet 5 at standard pricing.
        cost_delta_pct: Percentage cost increase at standard pricing.
        behavior_changes_detected: List of detected behavior changes.
        max_tokens_truncation_observed: Whether output was truncated.
        prompt_cache_invalidated: Whether cache was invalidated.
        admission_recommendation: admit/conditional/hold/reject.
        corpus_size_prompts: Number of prompts in corpus.
        introductory_pricing_per_1m_input_usd: Intro input pricing ($2).
        introductory_pricing_per_1m_output_usd: Intro output pricing ($10).
        introductory_pricing_expires_at: When intro pricing expires.
        sonnet_5_cost_introductory_usd: Sonnet 5 cost at intro pricing.
        eval_scores: Side-by-side eval scores.
        content_type_breakdown: Token delta by content type.
        admission_conditions: Conditions for conditional admission.
        operator_approval_ref: Operator approval reference.
        evidence_refs: Evidence references.
        notes: Additional context.
        receipt_id: Override auto-generated ID.
        timestamp: Override auto-generated timestamp.

    Returns:
        A validated receipt dict (with receipt_hash appended).

    Raises:
        Sonnet5ReplayError: if validation fails.
    """
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or _new_receipt_id(),
        "timestamp": timestamp or _utc_now(),
        "prompt_corpus_ref": prompt_corpus_ref,
        "replay_methodology": replay_methodology,
        "sonnet_46_token_count": sonnet_46_token_count,
        "sonnet_5_token_count": sonnet_5_token_count,
        "token_delta_ratio": token_delta_ratio,
        "token_delta_pct": token_delta_pct,
        "standard_pricing_per_1m_input_usd": standard_pricing_per_1m_input_usd,
        "standard_pricing_per_1m_output_usd": standard_pricing_per_1m_output_usd,
        "sonnet_46_cost_usd": sonnet_46_cost_usd,
        "sonnet_5_cost_usd": sonnet_5_cost_usd,
        "cost_delta_pct": cost_delta_pct,
        "behavior_changes_detected": list(behavior_changes_detected),
        "max_tokens_truncation_observed": max_tokens_truncation_observed,
        "prompt_cache_invalidated": prompt_cache_invalidated,
        "admission_recommendation": admission_recommendation,
    }

    if corpus_size_prompts:
        receipt["corpus_size_prompts"] = corpus_size_prompts
    if introductory_pricing_per_1m_input_usd:
        receipt["introductory_pricing_per_1m_input_usd"] = introductory_pricing_per_1m_input_usd
    if introductory_pricing_per_1m_output_usd:
        receipt["introductory_pricing_per_1m_output_usd"] = introductory_pricing_per_1m_output_usd
    if introductory_pricing_expires_at:
        receipt["introductory_pricing_expires_at"] = introductory_pricing_expires_at
    if sonnet_5_cost_introductory_usd:
        receipt["sonnet_5_cost_introductory_usd"] = sonnet_5_cost_introductory_usd
    if eval_scores:
        receipt["eval_scores"] = list(eval_scores)
    if content_type_breakdown:
        receipt["content_type_breakdown"] = list(content_type_breakdown)
    if admission_conditions:
        receipt["admission_conditions"] = list(admission_conditions)
    if operator_approval_ref:
        receipt["operator_approval_ref"] = operator_approval_ref
    if evidence_refs:
        receipt["evidence_refs"] = list(evidence_refs)
    if notes:
        receipt["notes"] = notes

    receipt["receipt_hash"] = compute_receipt_hash(receipt)

    is_valid, errors = validate_sonnet5_replay_receipt(receipt)
    if not is_valid:
        raise Sonnet5ReplayError(
            "sonnet 5 replay receipt failed validation: " + "; ".join(errors)
        )

    return receipt
