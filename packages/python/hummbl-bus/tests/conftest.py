from __future__ import annotations

import pytest
from hummbl_bus.bus_policy import reset_bus_policy


@pytest.fixture(autouse=True)
def _reset_bus_policy(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BUS_SECURITY_POLICY", "permissive")
    monkeypatch.delenv("BUS_SIGNING_SECRET", raising=False)
    reset_bus_policy()
    yield
    reset_bus_policy()
