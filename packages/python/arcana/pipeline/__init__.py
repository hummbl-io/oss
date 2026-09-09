"""Compatibility package for ARCANA runtime entry points.

This package provides legacy `pipeline.*` import paths expected by
`cli.py` and local scripts while reusing the canonical implementations
in the repository root modules.
"""

from .models import (  # noqa: F401
    VALID_OVERSIGHT_MODES,
    VALID_REVIEW_STATUSES,
    AgentPerspective,
    ARCANAArticle,
    GovernanceReceipt,
    make_article_id,
    now_utc,
)

_API_EXPORTS = {
    "AgentGenerationRequest",
    "APIClient",
    "GenerationResult",
    "SynthesisRequest",
    "StubAPIClient",
    "build_article_from_results",
    "get_system_prompt",
}


def __getattr__(name: str):
    if name in _API_EXPORTS:
        from . import api_client
        return getattr(api_client, name)
    raise AttributeError(name)


__all__ = [
    "VALID_OVERSIGHT_MODES",
    "VALID_REVIEW_STATUSES",
    "APIClient",
    "ARCANAArticle",
    "AgentGenerationRequest",
    "AgentPerspective",
    "GenerationResult",
    "GovernanceReceipt",
    "StubAPIClient",
    "SynthesisRequest",
    "build_article_from_results",
    "get_system_prompt",
    "make_article_id",
    "now_utc",
]
