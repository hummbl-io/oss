from __future__ import annotations

import pytest

from hummbl_bus.bus_policy import reset_bus_policy


@pytest.fixture(autouse=True)
def _reset_bus_policy(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BUS_SECURITY_POLICY", "permissive")
    reset_bus_policy()
    yield
    reset_bus_policy()
