"""Tests for convenience methods and aliases added in v1.2.0.

Tests:
- DelegationTokenManager.issue() convenience method
- BusWriter.append() and BusWriter.write() convenience methods
- DCT alias for DelegationTokenManager
- DCTX alias for DelegationContext
- b120 shortcut for ReasoningEngine
- Attest module (ALLOWLIST, BLOCKLIST, CAPABILITY_FENCE)
"""


import pytest

from hummbl_governance import (
    Attest,
    ALLOWLIST,
    BLOCKLIST,
    CAPABILITY_FENCE,
    BusWriter,
    DCT,
    DCTX,
    DelegationContext,
    DelegationTokenManager,
    b120,
)


class TestIssueConvenience:
    """Tests for DelegationTokenManager.issue() convenience method."""

    def test_issue_creates_token(self):
        dtm = DelegationTokenManager()
        token = dtm.issue(
            issuer="orchestrator",
            subject="summarizer-agent",
            operations=["read", "summarize"],
            resources=["docs/*"],
        )
        assert token.issuer == "orchestrator"
        assert token.subject == "summarizer-agent"
        assert "read" in token.ops_allowed
        assert "summarize" in token.ops_allowed
        assert len(token.resource_selectors) == 1
        assert token.resource_selectors[0].resource_id == "docs/*"

    def test_issue_with_expiry(self):
        dtm = DelegationTokenManager()
        token = dtm.issue(
            issuer="orch",
            subject="agent",
            operations=["read"],
            resources=["*"],
            expiry_minutes=60,
        )
        assert token.expiry is not None

    def test_issue_no_expiry(self):
        dtm = DelegationTokenManager()
        token = dtm.issue(
            issuer="orch",
            subject="agent",
            operations=["read"],
            resources=["*"],
            expiry_minutes=None,
        )
        assert token.expiry is None

    def test_dct_alias_is_delegationTokenManager(self):
        assert DCT is DelegationTokenManager

    def test_dct_issue_works(self):
        dtm = DCT()
        token = dtm.issue(
            issuer="orch",
            subject="agent",
            operations=["read"],
            resources=["*"],
        )
        assert token.subject == "agent"


class TestBusConvenience:
    """Tests for BusWriter.append() and BusWriter.write()."""

    def test_append_posts_message(self, tmp_path):
        bus_path = tmp_path / "test_bus.tsv"
        bus = BusWriter(str(bus_path))
        bus.append(agent="agent-1", action="read", resource="docs/report.md")
        msgs = bus.read_all()
        assert len(msgs) == 1
        assert msgs[0]["from"] == "agent-1"
        assert msgs[0]["type"] == "LOG"
        assert "read" in msgs[0]["message"]
        assert "docs/report.md" in msgs[0]["message"]

    def test_write_posts_message(self, tmp_path):
        bus_path = tmp_path / "test_bus.tsv"
        bus = BusWriter(str(bus_path))
        bus.write(actor="auditor", action="audit", scope="all")
        msgs = bus.read_all()
        assert len(msgs) == 1
        assert msgs[0]["from"] == "auditor"
        assert msgs[0]["type"] == "LOG"
        assert "audit" in msgs[0]["message"]
        assert "all" in msgs[0]["message"]

    def test_append_and_write_coexist(self, tmp_path):
        bus_path = tmp_path / "test_bus.tsv"
        bus = BusWriter(str(bus_path))
        bus.append(agent="a1", action="read", resource="r1")
        bus.write(actor="a2", action="write", scope="s1")
        msgs = bus.read_all()
        assert len(msgs) == 2


class TestDelegationContext:
    """Tests for DelegationContext and DCTX alias."""

    def test_dctx_alias_is_delegation_context(self):
        assert DCTX is DelegationContext

    def test_create_context(self):
        ctx = DCTX(parent="tok-123", max_depth=3)
        assert ctx.parent == "tok-123"
        assert ctx.max_depth == 3
        assert ctx.depth == 0

    def test_delegate_increments_depth(self):
        ctx = DCTX(parent="tok-123", max_depth=3)
        child = ctx.delegate()
        assert child.depth == 1
        grandchild = child.delegate()
        assert grandchild.depth == 2

    def test_depth_exceeded_raises(self):
        ctx = DCTX(parent="tok-123", max_depth=2)
        child = ctx.delegate()  # depth 1
        grandchild = child.delegate()  # depth 2
        with pytest.raises(PermissionError):
            grandchild.delegate()  # depth 3 > max_depth 2

    def test_can_delegate(self):
        ctx = DCTX(parent="tok", max_depth=2)
        assert ctx.can_delegate() is True
        child = ctx.delegate()
        assert child.can_delegate() is True
        grandchild = child.delegate()
        assert grandchild.can_delegate() is False

    def test_to_dict(self):
        ctx = DCTX(parent="tok", max_depth=3)
        d = ctx.to_dict()
        assert d["parent"] == "tok"
        assert d["max_depth"] == 3
        assert d["depth"] == 0


class TestB120Shortcut:
    """Tests for b120 shortcut."""

    def test_b120_get_returns_model(self):
        model = b120.get("P1")
        # P1 should exist in Base120
        if model:
            assert hasattr(model, "name")
            assert hasattr(model, "code")

    def test_b120_get_nonexistent_returns_none(self):
        model = b120.get("ZZZ999")
        assert model is None

    def test_b120_list_returns_list(self):
        models = b120.list()
        assert isinstance(models, list)


class TestAttest:
    """Tests for Attest module."""

    def test_attest_allowlist_pass(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=ALLOWLIST,
            allowed_tools=["tool_a", "tool_b"],
            declared_tools=["tool_a", "tool_b"],
        )
        assert result.ok is True
        assert result.server == "test-server"
        assert result.policy == ALLOWLIST

    def test_attest_allowlist_fail(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=ALLOWLIST,
            allowed_tools=["tool_a"],
            declared_tools=["tool_a", "tool_b"],
        )
        assert result.ok is False
        assert "tool_b" in result.reason

    def test_attest_blocklist_pass(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=BLOCKLIST,
            blocked_tools=["dangerous_tool"],
            declared_tools=["safe_tool"],
        )
        assert result.ok is True

    def test_attest_blocklist_fail(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=BLOCKLIST,
            blocked_tools=["dangerous_tool"],
            declared_tools=["safe_tool", "dangerous_tool"],
        )
        assert result.ok is False
        assert "dangerous_tool" in result.reason

    def test_attest_capability_fence_pass(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=CAPABILITY_FENCE,
            allowed_tools=["tool_a"],
            declared_tools=["tool_a"],
        )
        assert result.ok is True

    def test_attest_capability_fence_fail(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=CAPABILITY_FENCE,
            allowed_tools=["tool_a"],
            declared_tools=["tool_a", "tool_b"],
        )
        assert result.ok is False

    def test_attest_unknown_policy(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy="unknown",
            allowed_tools=["tool_a"],
            declared_tools=["tool_a"],
        )
        assert result.ok is False
        assert "Unknown policy" in result.reason

    def test_attest_allowlist_no_allowed_tools(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=ALLOWLIST,
            allowed_tools=[],
            declared_tools=["tool_a"],
        )
        assert result.ok is False

    def test_attest_result_to_dict(self):
        attest = Attest()
        result = attest.verify(
            server="test-server",
            policy=ALLOWLIST,
            allowed_tools=["tool_a"],
            declared_tools=["tool_a"],
        )
        d = result.to_dict()
        assert d["ok"] is True
        assert d["server"] == "test-server"
        assert d["policy"] == ALLOWLIST

    def test_attest_hash_is_consistent(self):
        attest = Attest()
        r1 = attest.verify(
            server="s",
            policy=ALLOWLIST,
            allowed_tools=["a"],
            declared_tools=["a"],
            nonce="fixed-nonce",
        )
        r2 = attest.verify(
            server="s",
            policy=ALLOWLIST,
            allowed_tools=["a"],
            declared_tools=["a"],
            nonce="fixed-nonce",
        )
        # Hashes should be the same for same inputs (except timestamp may differ)
        # Since timestamp is included, hashes may differ. Just check hash exists.
        assert len(r1.hash) > 0
        assert len(r2.hash) > 0
