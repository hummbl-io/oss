# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Tests for hummbl_governance.cost_governor."""

from datetime import datetime, timezone

import pytest

from hummbl_governance.cost_governor import (
    BudgetStatus,
    CostGovernor,
    UsageRecord,
)


class TestUsageRecord:
    """Test UsageRecord creation."""

    def test_create(self):
        record = UsageRecord.create(
            provider="anthropic",
            model="claude-4",
            tokens_in=1000,
            tokens_out=500,
            cost=0.015,
        )
        assert record.provider == "anthropic"
        assert record.model == "claude-4"
        assert record.cost == 0.015
        assert record.record_id.startswith("usage-")

    def test_create_with_meta(self):
        record = UsageRecord.create(
            provider="openai", model="gpt-4o",
            tokens_in=100, tokens_out=50, cost=0.01,
            meta={"task": "summarize"},
        )
        assert record.meta == {"task": "summarize"}


class TestCostGovernor:
    """Test CostGovernor with in-memory database."""

    def test_record_and_query(self):
        gov = CostGovernor(":memory:")
        gov.record_usage("anthropic", "claude-4", 1000, 500, 0.015)
        assert gov.get_daily_spend() == pytest.approx(0.015)

    def test_multiple_records(self):
        gov = CostGovernor(":memory:")
        gov.record_usage("anthropic", "claude-4", 1000, 500, 10.0)
        gov.record_usage("openai", "gpt-4o", 500, 200, 5.0)
        assert gov.get_daily_spend() == pytest.approx(15.0)

    def test_budget_allow(self):
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=100.0)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 10.0)
        status = gov.check_budget_status()
        assert status.decision == "ALLOW"
        assert status.current_spend == pytest.approx(10.0)

    def test_budget_warn_at_80_percent(self):
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=100.0)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 42.0)
        status = gov.check_budget_status()
        assert status.decision == "WARN"

    def test_budget_warn_over_soft_cap(self):
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=100.0)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 55.0)
        status = gov.check_budget_status()
        assert status.decision == "WARN"

    def test_budget_deny_over_hard_cap(self):
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=100.0)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 110.0)
        status = gov.check_budget_status()
        assert status.decision == "DENY"

    def test_no_hard_cap(self):
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=None)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 200.0)
        status = gov.check_budget_status()
        # Should be WARN, not DENY (no hard cap)
        assert status.decision == "WARN"

    def test_unsafe_path_rejected(self):
        with pytest.raises(ValueError, match="Unsafe"):
            CostGovernor("../../../etc/passwd")


class TestCostGovernorQueries:
    """Test query methods."""

    def test_spend_by_provider(self):
        gov = CostGovernor(":memory:")
        now = datetime.now(timezone.utc)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 10.0, timestamp=now)
        gov.record_usage("openai", "gpt-4o", 500, 200, 5.0, timestamp=now)

        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59)

        result = gov.get_spend_by_provider("anthropic", start, end)
        assert result["total_cost"] == pytest.approx(10.0)
        assert result["request_count"] == 1

    def test_spend_by_model(self):
        gov = CostGovernor(":memory:")
        now = datetime.now(timezone.utc)
        gov.record_usage("anthropic", "claude-4", 1000, 500, 10.0, timestamp=now)
        gov.record_usage("anthropic", "claude-4", 500, 200, 5.0, timestamp=now)

        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59)

        models = gov.get_spend_by_model(start, end)
        assert len(models) == 1
        assert models[0]["total_cost"] == pytest.approx(15.0)
        assert models[0]["request_count"] == 2

    def test_count(self):
        gov = CostGovernor(":memory:")
        gov.record_usage("anthropic", "claude-4", 1000, 500, 10.0)
        gov.record_usage("openai", "gpt-4o", 500, 200, 5.0)
        assert gov.count() == 2


class TestBudgetAlert:
    """Test budget alert callback."""

    def test_alert_callback_called(self):
        alerts = []
        gov = CostGovernor(
            ":memory:", soft_cap=10.0, hard_cap=20.0,
            on_budget_alert=lambda s: alerts.append(s),
        )
        gov.record_usage("anthropic", "claude-4", 1000, 500, 15.0)
        assert len(alerts) == 1
        assert alerts[0].decision == "WARN"

    def test_no_alert_under_threshold(self):
        alerts = []
        gov = CostGovernor(
            ":memory:", soft_cap=100.0, hard_cap=200.0,
            on_budget_alert=lambda s: alerts.append(s),
        )
        gov.record_usage("anthropic", "claude-4", 1000, 500, 1.0)
        assert len(alerts) == 0


class TestBudgetStatusSerialization:
    """Test BudgetStatus serialization."""

    def test_to_dict(self):
        status = BudgetStatus(
            current_spend=42.0, soft_cap=50.0, hard_cap=100.0,
            currency="USD", threshold_percent=84.0,
            decision="WARN", rationale="test",
        )
        d = status.to_dict()
        assert d["decision"] == "WARN"
        assert d["current_spend"] == 42.0


class TestCostGovernorFileDB:
    """Test CostGovernor with a real filesystem path (covers Path branch)."""

    def test_creates_parent_dir(self, tmp_path):
        db_path = tmp_path / "subdir" / "costs.db"
        gov = CostGovernor(db_path, soft_cap=10.0, hard_cap=20.0)
        assert db_path.parent.exists()
        gov.record_usage("anthropic", "claude-4", 100, 50, 0.5)
        assert gov.get_daily_spend() == pytest.approx(0.5)

    def test_string_db_path_non_memory(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        gov = CostGovernor(db_path, soft_cap=10.0, hard_cap=20.0)
        gov.record_usage("openai", "gpt-4", 100, 50, 0.3)
        assert gov.get_daily_spend() == pytest.approx(0.3)


class TestCostGovernorCleanup:
    """Test cleanup and count with date-range filtering."""

    def test_cleanup_removes_old_records(self):
        gov = CostGovernor(":memory:", soft_cap=100.0, hard_cap=200.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 1.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 2.0)
        assert gov.count() == 2
        # Cleanup with 'before' set to far future removes everything
        from datetime import timedelta
        future = datetime.now(timezone.utc) + timedelta(days=365)
        deleted = gov.cleanup(before=future)
        assert deleted == 2
        assert gov.count() == 0

    def test_cleanup_default_retention(self):
        gov = CostGovernor(":memory:", soft_cap=100.0, hard_cap=200.0, retention_days=30)
        gov.record_usage("anthropic", "claude-4", 100, 50, 1.0)
        # Default cleanup: should not delete recent records
        deleted = gov.cleanup()
        assert deleted == 0
        assert gov.count() == 1

    def test_count_with_start_filter(self):
        gov = CostGovernor(":memory:", soft_cap=100.0, hard_cap=200.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 1.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 2.0)
        future = datetime.now(timezone.utc).replace(year=2099)
        count = gov.count(start=future)
        assert count == 0

    def test_count_with_end_filter(self):
        gov = CostGovernor(":memory:", soft_cap=100.0, hard_cap=200.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 1.0)
        past = datetime.now(timezone.utc).replace(year=2000)
        count = gov.count(end=past)
        assert count == 0

    def test_count_with_start_and_end_filter(self):
        gov = CostGovernor(":memory:", soft_cap=100.0, hard_cap=200.0)
        gov.record_usage("anthropic", "claude-4", 100, 50, 1.0)
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        start = now - timedelta(minutes=5)
        end = now + timedelta(minutes=5)
        count = gov.count(start=start, end=end)
        assert count == 1

    def test_alert_callback_on_deny(self):
        alerts = []
        gov = CostGovernor(
            ":memory:", soft_cap=1.0, hard_cap=2.0,
            on_budget_alert=lambda s: alerts.append(s),
        )
        gov.record_usage("anthropic", "claude-4", 100, 50, 5.0)
        assert len(alerts) >= 1
        assert alerts[0].decision == "DENY"


class TestInputValidation:
    """Tests for input validation in record_usage."""

    def test_negative_cost_rejected(self):
        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="cost must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", 100, 50, -0.01)

    def test_negative_tokens_rejected(self):
        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="tokens_in must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", -1, 50, 0.01)

    def test_negative_tokens_out_rejected(self):
        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="tokens_out must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", 100, -5, 0.01)

    def test_nan_cost_rejected(self):
        import math

        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="cost must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", 100, 50, math.nan)

    def test_inf_cost_rejected(self):
        import math

        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="cost must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", 100, 50, math.inf)

    def test_nan_tokens_in_rejected(self):
        import math

        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="tokens_in must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", math.nan, 50, 0.01)

    def test_inf_tokens_out_rejected(self):
        import math

        gov = CostGovernor(":memory:")
        with pytest.raises(ValueError, match="tokens_out must be a finite non-negative"):
            gov.record_usage("anthropic", "claude-4", 100, math.inf, 0.01)
