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

"""Google Calendar Adapter -- stub implementation.

This is a STUB. It returns empty results for all calendar queries so that
skills that import it do not crash. A real implementation would use the
Google Calendar API (or a local ICS reader) to fetch calendar entries.

Skills that use this adapter:
    gm, runway, weekly-plan, mission-status, mission-declare, mission-abort,
    evening-touchdown, daily-standup

To implement for real:
    1. Add Google Calendar API credentials (or local ICS file path).
    2. Replace get_calendar_entries() with a real fetch.
    3. Replace get_entries_for_range() with a real range query.

Stdlib-only: datetime, dataclasses, typing, logging.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CalendarEntry:
    """A single calendar entry."""

    title: str
    start_time: str
    end_time: str = ""
    location: str = ""
    description: str = ""
    attendees: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GoogleCalendarAdapter:
    """Stub Google Calendar adapter.

    All methods return empty results. Replace with a real implementation
    when calendar integration is needed.
    """

    def __init__(self, *, calendar_id: str = "primary", **kwargs: Any) -> None:
        self._calendar_id = calendar_id
        logger.debug("GoogleCalendarAdapter stub initialized (calendar_id=%s)", calendar_id)

    def get_calendar_entries(self, *, max_results: int = 10) -> list[CalendarEntry]:
        """Return upcoming calendar entries.

        Returns:
            Empty list (stub).
        """
        logger.info("GoogleCalendarAdapter.get_calendar_entries: stub returning []")
        return []

    def get_entries_for_range(
        self,
        start: datetime,
        end: datetime,
    ) -> list[CalendarEntry]:
        """Return calendar entries in the given time range.

        Args:
            start: Range start (timezone-aware).
            end: Range end (timezone-aware).

        Returns:
            Empty list (stub).
        """
        logger.info(
            "GoogleCalendarAdapter.get_entries_for_range: stub returning [] for %s..%s",
            start.isoformat() if start else "?",
            end.isoformat() if end else "?",
        )
        return []

    def get_entries_for_today(self, *, tz: Any = None) -> list[CalendarEntry]:
        """Return calendar entries for today.

        Returns:
            Empty list (stub).
        """
        logger.info("GoogleCalendarAdapter.get_entries_for_today: stub returning []")
        return []

    def get_entries_for_week(self, *, tz: Any = None) -> list[CalendarEntry]:
        """Return calendar entries for the current week (Mon-Sun).

        Returns:
            Empty list (stub).
        """
        logger.info("GoogleCalendarAdapter.get_entries_for_week: stub returning []")
        return []

    @property
    def is_stub(self) -> bool:
        """True if this is a stub adapter (no real calendar backend)."""
        return True
