"""Governance primitives for ARCANA CLI review workflows."""

from __future__ import annotations

from dataclasses import replace

from .models import GovernanceReceipt, now_utc


def validate_receipt(receipt: GovernanceReceipt) -> bool:
    """Validate receipt shape and invariants.

    Returns:
        True if the receipt can be reconstructed without validation errors.
    """
    try:
        # Rebuilding guarantees dataclass validation rules are executed.
        GovernanceReceipt(
            article_id=receipt.article_id,
            topic=receipt.topic,
            generated_at=receipt.generated_at,
            agents_used=list(receipt.agents_used),
            model=receipt.model,
            human_review_status=receipt.human_review_status,
            human_reviewer=receipt.human_reviewer,
            reviewed_at=receipt.reviewed_at,
            confidence_score=float(receipt.confidence_score),
            content_warnings=list(receipt.content_warnings),
            oversight_mode=receipt.oversight_mode,
            version=receipt.version,
        )
        return True
    except Exception:
        return False


def generate_receipt(
    article,
    mode: str,
    *,
    model: str,
    confidence_score: float = 0.75,
) -> GovernanceReceipt:
    """Create a receipt for a freshly generated article."""
    existing = getattr(article, "receipt", None)
    if existing is None:
        raise ValueError("article is missing an existing receipt")
    return GovernanceReceipt(
        article_id=existing.article_id,
        topic=existing.topic,
        generated_at=now_utc(),
        agents_used=getattr(existing, "agents_used", []),
        model=model,
        human_review_status="pending",
        human_reviewer=None,
        reviewed_at=None,
        confidence_score=confidence_score,
        content_warnings=[],
        oversight_mode=mode,
        version="1.0",
    )


def approve_receipt(receipt: GovernanceReceipt, *, reviewer: str = "cli-user") -> GovernanceReceipt:
    """Return a receipt copy marked approved."""
    return replace(
        receipt,
        human_review_status="approved",
        human_reviewer=reviewer or "cli-user",
        reviewed_at=now_utc(),
    )


def reject_receipt(
    receipt: GovernanceReceipt,
    *,
    reviewer: str,
    reason: str,
) -> GovernanceReceipt:
    """Return a receipt copy marked rejected and annotate reviewer reason."""
    warnings = list(receipt.content_warnings)
    warnings.append(f"REJECT_REASON: {reason.strip()}")
    return replace(
        receipt,
        human_review_status="rejected",
        human_reviewer=reviewer or "cli-user",
        reviewed_at=now_utc(),
        content_warnings=warnings,
    )
