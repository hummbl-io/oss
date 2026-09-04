"""Small cross-platform file locks implemented with the Python standard library."""

from __future__ import annotations

import os
from typing import IO, Any

FileHandle = int | IO[Any]


def _fileno(handle: FileHandle) -> int:
    return handle if isinstance(handle, int) else handle.fileno()


def acquire_file_lock(handle: FileHandle, *, exclusive: bool = True) -> None:
    """Block until a process-scoped lock can be acquired for ``handle``.

    POSIX uses ``flock``. Windows locks the first byte range with ``msvcrt``;
    all HUMMBL writers use that same range, including for an initially empty
    file, so the lock remains stable while append-only content grows.
    """
    fd = _fileno(handle)
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        mode = msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK
        msvcrt.locking(fd, mode, 1)
        os.lseek(fd, 0, os.SEEK_END)
        return

    import fcntl

    mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    fcntl.flock(fd, mode)


def release_file_lock(handle: FileHandle) -> None:
    """Release a lock previously acquired by :func:`acquire_file_lock`."""
    fd = _fileno(handle)
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        os.lseek(fd, 0, os.SEEK_END)
        return

    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)
