"""Bus posting backoff helper.

Calculates the wait time needed before posting to the coordination bus,
based on the bus rate limit (5-second minimum interval between posts).
This eliminates the manual `sleep` guessing that caused 4 retry attempts
during the 2026-09-02 stale-branch-remediation session.

Usage:
    from hummbl_gitops.bus_backoff import BusBackoff

    backoff = BusBackoff(min_interval=5.0)
    backoff.wait()  # blocks if needed
    post_to_bus(message)
    backoff.mark_posted()  # record the post time

Or as a context manager:
    with BusBackoff(min_interval=5.0) as backoff:
        # backoff.wait() called on enter
        post_to_bus(message)
        # backoff.mark_posted() called on exit
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class BusBackoff:
    """Rate limiter for bus postings.

    Tracks the last post time and calculates the wait needed before
    the next post to respect the minimum interval.
    """

    min_interval: float = 5.0  # seconds between posts
    _last_post: Optional[float] = None  # monotonic time of last post

    def seconds_until_next_post(self) -> float:
        """How many seconds to wait before the next post is allowed.

        Returns 0.0 if posting is allowed now.
        """
        if self._last_post is None:
            return 0.0
        elapsed = time.monotonic() - self._last_post
        remaining = self.min_interval - elapsed
        return max(0.0, remaining)

    def can_post(self) -> bool:
        """Check if a post is allowed now without waiting."""
        return self.seconds_until_next_post() == 0.0

    def wait(self) -> float:
        """Block until posting is allowed. Returns the time waited."""
        wait_time = self.seconds_until_next_post()
        if wait_time > 0:
            time.sleep(wait_time)
        return wait_time

    def mark_posted(self) -> None:
        """Record that a post was just made. Call after every successful post."""
        self._last_post = time.monotonic()

    def __enter__(self) -> "BusBackoff":
        self.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Only mark posted if no exception occurred
        if exc_type is None:
            self.mark_posted()
