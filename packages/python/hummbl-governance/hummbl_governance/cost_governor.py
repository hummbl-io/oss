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
# SPDX-License-Identifier: Apache-2.0

"""Cost Governor -- Budget tracking with soft/hard caps.

SQLite-backed persistent storage for API usage costs with budget
governance decisions (ALLOW, WARN, DENY).

Usage:
    from hummbl_governance import CostGovernor

    gov = CostGovernor(":memory:")  # or path to SQLite file
    gov.record_usage(provider="anthropic", model="claude-4", tokens_in=1000, tokens_out=500, cost=0.015)
    status = gov.check_budget_status()
    # status.decision in ("ALLOW", "WARN", "DENY")

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from hummbl_governance._types import BudgetStatus, UsageRecord


class CostGovernor:
    """SQLite-backed API cost tracker with budget governance.

    Args:
        db_path: Path to SQLite database file, or ":memory:" for in-memory.
        soft_cap: Daily soft cap in currency units (default 50.0).
        hard_cap: Daily hard cap (default 100.0). None for no hard cap.
        currency: Currency code (default "USD").
        retention_days: Days to retain usage records (default 90).
        on_budget_alert: Optional callback(BudgetStatus) called on WARN/DENY.
    """

    DEFAULT_SOFT_CAP = 50.0
    DEFAULT_HARD_CAP = 100.0
    DEFAULT_CURRENCY = "USD"

    def __init__(
        self,
        db_path: str | Path,
        soft_cap: float = DEFAULT_SOFT_CAP,
        hard_cap: float | None = DEFAULT_HARD_CAP,
        currency: str = DEFAULT_CURRENCY,
        retention_days: int = 90,
        on_budget_alert: Callable[[BudgetStatus], None] | None = None,
    ):
        raw = str(db_path)
        if ".." in raw and raw != ":memory:":
            raise ValueError(f"Unsafe database path rejected: {raw!r}")
        self.db_path = Path(db_path) if raw != ":memory:" else raw
        self.soft_cap = soft_cap
        self.hard_cap = hard_cap
        self.currency = currency
        self.retention_days = retention_days
        self._on_budget_alert = on_budget_alert
        self._is_memory = raw == ":memory:"
        self._shared_conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    record_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    date TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    meta TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_date ON usage(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage(provider)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_model ON usage(model)")
            conn.commit()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections.

        For :memory: databases, reuses a single persistent connection
        since each new connection gets a fresh empty database.
        """
        if self._is_memory:
            if self._shared_conn is None:
                self._shared_conn = sqlite3.connect(":memory:")
                self._shared_conn.row_factory = sqlite3.Row
            yield self._shared_conn
            return

        db_str = str(self.db_path) if isinstance(self.db_path, Path) else self.db_path
        conn = sqlite3.connect(db_str)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def record_usage(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        timestamp: datetime | None = None,
        meta: dict[str, Any] | None = None,
    ) -> UsageRecord:
        """Record an API usage event and check budget.

        Raises:
            ValueError: If cost is negative, NaN, or infinite, or if tokens
                are negative, NaN, or infinite.
        """
        if cost < 0 or math.isnan(cost) or math.isinf(cost):
            raise ValueError(f"cost must be a finite non-negative number, got {cost}")
        if tokens_in < 0 or math.isnan(tokens_in) or math.isinf(tokens_in):
            raise ValueError(f"tokens_in must be a finite non-negative number, got {tokens_in}")
        if tokens_out < 0 or math.isnan(tokens_out) or math.isinf(tokens_out):
            raise ValueError(f"tokens_out must be a finite non-negative number, got {tokens_out}")
        record = UsageRecord.create(
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            timestamp=timestamp,
            meta=meta,
        )

        ts = timestamp or datetime.now(timezone.utc)
        date_str = ts.date().isoformat()

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO usage
                (record_id, timestamp, date, provider, model, tokens_in, tokens_out, cost, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.timestamp,
                    date_str,
                    record.provider,
                    record.model,
                    record.tokens_in,
                    record.tokens_out,
                    record.cost,
                    json.dumps(record.meta),
                ),
            )
            conn.commit()

        self._check_and_alert()
        return record

    def get_daily_spend(self, target_date: date | None = None) -> float:
        """Get total spend for a specific day."""
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()
        date_str = target_date.isoformat()
        with self._conn() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(cost), 0) as total FROM usage WHERE date = ?",
                (date_str,),
            ).fetchone()
        return float(result["total"])

    def get_spend_by_provider(self, provider: str, start: datetime, end: datetime) -> dict[str, Any]:
        """Get spend breakdown for a specific provider."""
        start_iso = start.isoformat().replace("+00:00", "Z")
        end_iso = end.isoformat().replace("+00:00", "Z")
        with self._conn() as conn:
            result = conn.execute(
                """SELECT COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(tokens_in), 0) as total_tokens_in,
                    COALESCE(SUM(tokens_out), 0) as total_tokens_out,
                    COUNT(*) as request_count
                FROM usage WHERE provider = ? AND timestamp >= ? AND timestamp <= ?""",
                (provider, start_iso, end_iso),
            ).fetchone()
        return {
            "provider": provider,
            "total_cost": float(result["total_cost"]),
            "total_tokens_in": int(result["total_tokens_in"]),
            "total_tokens_out": int(result["total_tokens_out"]),
            "request_count": int(result["request_count"]),
            "start": start_iso,
            "end": end_iso,
        }

    def get_spend_by_model(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Get spend breakdown by model."""
        start_iso = start.isoformat().replace("+00:00", "Z")
        end_iso = end.isoformat().replace("+00:00", "Z")
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT provider, model,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(tokens_in), 0) as total_tokens_in,
                    COALESCE(SUM(tokens_out), 0) as total_tokens_out,
                    COUNT(*) as request_count
                FROM usage WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY provider, model ORDER BY total_cost DESC""",
                (start_iso, end_iso),
            ).fetchall()
        return [
            {
                "provider": row["provider"],
                "model": row["model"],
                "total_cost": float(row["total_cost"]),
                "total_tokens_in": int(row["total_tokens_in"]),
                "total_tokens_out": int(row["total_tokens_out"]),
                "request_count": int(row["request_count"]),
            }
            for row in rows
        ]

    def check_budget_status(self) -> BudgetStatus:
        """Compare current spend against soft/hard caps."""
        current_spend = self.get_daily_spend()
        threshold_percent = 0.0 if self.soft_cap <= 0 else current_spend / self.soft_cap * 100

        if self.hard_cap is not None and current_spend >= self.hard_cap:
            decision = "DENY"
            rationale = f"Daily hard cap ({self.currency} {self.hard_cap:.2f}) exceeded"
        elif current_spend >= self.soft_cap:
            decision = "WARN"
            rationale = f"Daily soft cap ({self.currency} {self.soft_cap:.2f}) exceeded"
        elif threshold_percent >= 80:
            decision = "WARN"
            rationale = f"Approaching soft cap ({threshold_percent:.1f}% used)"
        else:
            decision = "ALLOW"
            rationale = f"Within budget ({threshold_percent:.1f}% of soft cap)"

        return BudgetStatus(
            current_spend=current_spend,
            soft_cap=self.soft_cap,
            hard_cap=self.hard_cap,
            currency=self.currency,
            threshold_percent=threshold_percent,
            decision=decision,
            rationale=rationale,
        )

    def _check_and_alert(self) -> None:
        """Check budget and invoke alert callback if needed."""
        if self._on_budget_alert is None:
            return
        status = self.check_budget_status()
        if status.decision != "ALLOW":
            self._on_budget_alert(status)

    def cleanup(self, before: datetime | None = None) -> int:
        """Remove old usage records. Returns count deleted."""
        if before is None:
            before = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                days=self.retention_days
            )
        before_iso = before.isoformat().replace("+00:00", "Z")
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM usage WHERE timestamp < ?", (before_iso,))
            conn.commit()
            return cursor.rowcount

    def count(self, start: datetime | None = None, end: datetime | None = None) -> int:
        """Count usage records in time range."""
        query = "SELECT COUNT(*) FROM usage"
        params: list[str] = []
        if start or end:
            conditions = []
            if start:
                conditions.append("timestamp >= ?")
                params.append(start.isoformat().replace("+00:00", "Z"))
            if end:
                conditions.append("timestamp <= ?")
                params.append(end.isoformat().replace("+00:00", "Z"))
            query += " WHERE " + " AND ".join(conditions)
        with self._conn() as conn:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0
