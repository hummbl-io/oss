"""Wrapper module exposing canonical API contracts under `pipeline.api_client`."""

from __future__ import annotations

from api_client import (  # type: ignore
    AgentGenerationRequest,
    APIClient,
    GenerationResult,
    StubAPIClient,
    SynthesisRequest,
    build_article_from_results,
    get_system_prompt,
)

__all__ = [
    "APIClient",
    "AgentGenerationRequest",
    "GenerationResult",
    "StubAPIClient",
    "SynthesisRequest",
    "build_article_from_results",
    "get_system_prompt",
]
