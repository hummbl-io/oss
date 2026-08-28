"""IDP-Kernel integration — agent identity verification via hummbl-governance.

This module bridges the IDP delegation system with the hummbl-governance
IdentityEngine, providing canonical identity verification for all
delegation operations.

Usage::

    from idp_spec.identity_kernel import verify_agent_identity

    # Before issuing a DCT, verify the agent is registered
    identity = verify_agent_identity("briefing_service")
    if not identity:
        raise IDP_E_DCT_VIOLATION("Agent not in canonical registry")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _kernel_state_dir() -> Path:
    """Return the Kernel state directory."""
    env_dir = os.environ.get("HUMMBL_KERNEL_STATE_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".local" / "share" / "hummbl-governance" / "kernel"


def verify_agent_identity(agent_id: str) -> dict[str, Any] | None:
    """Verify an agent's identity using the hummbl-governance IdentityEngine.

    Args:
        agent_id: The canonical agent identifier (e.g., "briefing_service")

    Returns:
        Identity dict if registered, None otherwise.
    """
    try:
        from hummbl_governance.kernel import Kernel

        kernel = Kernel.boot(state_dir=_kernel_state_dir())
        identity = kernel.identity.lookup(agent_id)
        if identity is None:
            logger.warning("Agent %s not found in canonical identity registry", agent_id)
            return None
        return {
            "agent_id": identity.agent_id,
            "trust_tier": identity.trust_tier,
            "status": identity.status,
            "registered_at": identity.registered_at,
        }
    except (ImportError, OSError, KeyError, AttributeError, TypeError):
        logger.debug("hummbl-governance IdentityEngine unavailable; skipping verification")
        return None


def register_agent_if_missing(
    agent_id: str,
    trust_tier: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Register an agent in the canonical identity registry if not present.

    Args:
        agent_id: Canonical agent identifier.
        trust_tier: Initial trust tier (1-3).
        metadata: Optional metadata dict.

    Returns:
        True if registered (or already present), False on failure.
    """
    try:
        from hummbl_governance.kernel import Kernel

        kernel = Kernel.boot(state_dir=_kernel_state_dir())
        existing = kernel.identity.lookup(agent_id)
        if existing is not None:
            return True
        kernel.identity.register(
            agent_id=agent_id,
            trust_tier=trust_tier,
            metadata=metadata or {},
        )
        logger.info("Registered agent %s in canonical identity registry", agent_id)
        return True
    except (ImportError, OSError, KeyError, AttributeError, TypeError):
        logger.debug("hummbl-governance IdentityEngine unavailable; skipping registration")
        return False
