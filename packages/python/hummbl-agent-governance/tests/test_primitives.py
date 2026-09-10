"""Tests for agent runtime governance primitives."""

import time
import pytest
from agent_governance import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CostGovernor,
    DelegationToken,
    KillSwitch,
    KillSwitchState,
)


def test_kill_switch_stages():
    ks = KillSwitch()
    assert ks.check_execution_allowed(is_read_only=False) is True

    ks.set_state(KillSwitchState.RESTRICTED)
    assert ks.check_execution_allowed(is_read_only=False) is False
    assert ks.check_execution_allowed(is_read_only=True) is True

    ks.set_state(KillSwitchState.ENGAGED)
    assert ks.check_execution_allowed(is_read_only=True) is False


def test_kill_switch_shadow_allows_all():
    """SHADOW mode observes without enforcing — all executions allowed."""
    ks = KillSwitch(state=KillSwitchState.SHADOW)
    assert ks.check_execution_allowed(is_read_only=False) is True
    assert ks.check_execution_allowed(is_read_only=True) is True


def test_circuit_breaker_tripping():
    cb = CircuitBreaker("mock_api", failure_threshold=2, recovery_timeout=0.2)
    
    # 1st failure
    with pytest.raises(ValueError):
        with cb:
            raise ValueError("API error")
    assert cb.is_open is False

    # 2nd failure -> trips circuit
    with pytest.raises(ValueError):
        with cb:
            raise ValueError("API error")
    assert cb.is_open is True

    # Fast-fail
    with pytest.raises(CircuitBreakerOpenError):
        with cb:
            pass

    # Wait for recovery timeout
    time.sleep(0.25)
    with cb:
        pass
    assert cb.is_open is False


def test_delegation_token_lifecycle():
    secret = "production-secret-key-123"
    token = DelegationToken.issue(
        issuer="supervisor",
        delegate="worker",
        scope="read:metrics",
        secret_key=secret,
        ttl_seconds=10.0,
    )
    assert token.verify(secret, required_scope="read:metrics") is True
    assert token.verify(secret, required_scope="write:deploy") is False
    assert token.verify("wrong-key") is False


def test_cost_governor():
    gov = CostGovernor(max_budget_usd=5.0)
    assert gov.is_within_budget(2.0) is True
    gov.record_spend(3.50)
    assert gov.is_within_budget(1.0) is True
    assert gov.is_within_budget(2.0) is False
