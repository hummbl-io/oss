"""Tests for the BusBackoff rate limiter."""

from __future__ import annotations

import time

from hummbl_gitops.bus_backoff import BusBackoff


class TestBusBackoff:
    def test_first_post_no_wait(self) -> None:
        bo = BusBackoff(min_interval=5.0)
        assert bo.can_post() is True
        assert bo.seconds_until_next_post() == 0.0

    def test_wait_after_post(self) -> None:
        bo = BusBackoff(min_interval=0.1)
        bo.mark_posted()
        remaining = bo.seconds_until_next_post()
        assert 0 < remaining <= 0.1
        assert bo.can_post() is False

    def test_wait_blocks_until_allowed(self) -> None:
        bo = BusBackoff(min_interval=0.05)
        bo.mark_posted()
        waited = bo.wait()
        assert waited > 0
        assert bo.can_post() is True

    def test_context_manager_marks_posted(self) -> None:
        bo = BusBackoff(min_interval=0.05)
        with bo:
            pass  # simulate a post
        # After context exit, _last_post should be set
        assert bo._last_post is not None
        assert not bo.can_post()

    def test_context_manager_no_mark_on_exception(self) -> None:
        bo = BusBackoff(min_interval=0.05)
        try:
            with bo:
                raise ValueError("post failed")
        except ValueError:
            pass
        # Should NOT have marked posted since exception occurred
        assert bo._last_post is None
        assert bo.can_post()

    def test_can_post_after_interval_passes(self) -> None:
        bo = BusBackoff(min_interval=0.02)
        bo.mark_posted()
        time.sleep(0.03)
        assert bo.can_post() is True
        assert bo.seconds_until_next_post() == 0.0
