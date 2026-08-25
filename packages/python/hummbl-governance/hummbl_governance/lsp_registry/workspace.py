"""Workspace utilities for LSP registry.

Provides functions for finding project roots, resolving git workspaces,
and caching workspace lookups.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional, Sequence


def nearest_root(
    file_path: str,
    markers: Sequence[str],
    excludes: Sequence[str] = (),
    ceiling: Optional[str] = None,
) -> Optional[str]:
    """Find the nearest ancestor directory containing any marker file.

    Args:
        file_path: Starting file path (absolute or relative).
        markers: Filenames or glob patterns to search for.
        excludes: Filenames that, if found first, cause early return of None.
        ceiling: Stop searching at this directory (exclusive).

    Returns:
        Absolute path to the directory containing a marker, or None.
    """
    path = Path(file_path).resolve()
    if path.is_file():
        path = path.parent

    ceiling_path = Path(ceiling).resolve() if ceiling else None

    for parent in [path] + list(path.parents):
        if ceiling_path and parent == ceiling_path:
            break
        # Check excludes first
        for exc in excludes:
            if (parent / exc).exists():
                return None
        # Check markers
        for marker in markers:
            if (parent / marker).exists():
                return str(parent)
    return None


@lru_cache(maxsize=128)
def _cached_nearest_root(
    file_path: str,
    markers_tuple: tuple,
    excludes_tuple: tuple,
    ceiling: Optional[str],
) -> Optional[str]:
    """Cached version of nearest_root for repeated lookups."""
    return nearest_root(file_path, markers_tuple, excludes_tuple, ceiling)


def resolve_workspace_for_file(file_path: str) -> tuple[Optional[str], bool]:
    """Resolve the git workspace root for a file.

    Returns:
        Tuple of (workspace_root, gated_in). gated_in is False if
        the file is not inside a git worktree.
    """
    path = Path(file_path).resolve()
    if path.is_file():
        path = path.parent

    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return str(parent), True
    return None, False


def clear_cache() -> None:
    """Clear the workspace lookup cache."""
    _cached_nearest_root.cache_clear()


def is_inside_workspace(file_path: str) -> bool:
    """Quick check if a file is inside a git workspace."""
    _, gated = resolve_workspace_for_file(file_path)
    return gated


def get_workspace_root(file_path: str) -> Optional[str]:
    """Get the workspace root for a file, or None if not in a workspace."""
    root, gated = resolve_workspace_for_file(file_path)
    return root if gated else None


__all__ = [
    "nearest_root",
    "resolve_workspace_for_file",
    "clear_cache",
    "is_inside_workspace",
    "get_workspace_root",
]