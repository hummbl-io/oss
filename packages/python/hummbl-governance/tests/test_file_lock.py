"""Cross-process tests for the stdlib-only file-locking primitive."""

from __future__ import annotations

import multiprocessing
import time
from pathlib import Path

from hummbl_governance._file_lock import acquire_file_lock, release_file_lock


def _wait_for_lock(path: str, acquired: multiprocessing.Queue) -> None:
    with open(path, "a+b") as stream:
        acquire_file_lock(stream)
        try:
            acquired.put(True)
        finally:
            release_file_lock(stream)


def test_lock_blocks_another_process_until_release(tmp_path: Path) -> None:
    lock_target = tmp_path / "shared.log"
    context = multiprocessing.get_context("spawn")
    acquired = context.Queue()

    with open(lock_target, "a+b") as stream:
        acquire_file_lock(stream)
        process = context.Process(
            target=_wait_for_lock,
            args=(str(lock_target), acquired),
        )
        process.start()
        time.sleep(0.25)
        assert acquired.empty()
        release_file_lock(stream)

    process.join(timeout=5)
    assert process.exitcode == 0
    assert acquired.get(timeout=1) is True
