"""Regression test: is_valid_sender() must reject unknown senders.

Phase 1 P0 fix (lane=fix/cline/hummbl-governance-phase-1-quality).

Prior bug: canonicalize() returns None for unknown senders, and the
old implementation compared `self.canonicalize(sender) != sender`,
which evaluates to True whenever canonicalize returns None (since
None != "any-string" is always True). This meant every unknown
sender was incorrectly reported as valid.
"""
from __future__ import annotations

from hummbl_governance.identity import AgentRegistry


class TestUnknownSenderRejection:
    """Verify is_valid_sender() correctly rejects unrecognized senders."""

    def test_unknown_sender_is_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register_agent("orchestrator", trust="high")

        assert registry.is_valid_sender("totally-unknown-agent") is False

    def test_unknown_sender_with_special_chars_is_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register_agent("orchestrator", trust="high")

        assert registry.is_valid_sender("../../etc/passwd") is False
        assert registry.is_valid_sender("<script>alert(1)</script>") is False
        assert registry.is_valid_sender("") is False

    def test_known_agent_is_accepted(self) -> None:
        registry = AgentRegistry()
        registry.register_agent("orchestrator", trust="high")

        assert registry.is_valid_sender("orchestrator") is True

    def test_known_alias_is_accepted(self) -> None:
        registry = AgentRegistry()
        registry.register_agent("orchestrator", trust="high")
        registry.add_alias("orch-1", "orchestrator")

        assert registry.is_valid_sender("orch-1") is True

    def test_known_service_is_accepted(self) -> None:
        registry = AgentRegistry(services={"cron-service"})

        assert registry.is_valid_sender("cron-service") is True

    def test_empty_registry_rejects_everything(self) -> None:
        registry = AgentRegistry()

        assert registry.is_valid_sender("anything") is False
        assert registry.is_valid_sender("orchestrator") is False

    def test_deprecated_identity_is_not_valid_sender(self) -> None:
        # Deprecated identities are tracked separately and should not
        # be treated as valid senders unless also registered.
        registry = AgentRegistry(deprecated={"old-bot"})

        assert registry.is_valid_sender("old-bot") is False
        assert registry.is_deprecated("old-bot") is True
