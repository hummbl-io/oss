"""CLI interface for the coordination bus writer.

Runnable as:
    python -m hummbl_bus.bus_writer_cli <from> <to> <type> <message> [--bus PATH]

Split from bus_writer.py for maintainability. Import from bus_writer.py
for backward compatibility.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from hummbl_bus.bus_writer import (
    DEFAULT_BUS_PATH,
    _resolve_common_repo_root,
    _resolve_repo_root,
    post_message,
)


def _bus_validation_roots() -> tuple[Path, ...]:
    """Return repo roots accepted for COORDINATION_BUS env overrides."""
    roots: list[Path] = []
    for root in (_resolve_common_repo_root(), _resolve_repo_root()):
        if root is not None and root not in roots:
            roots.append(root)
    return tuple(roots)


def _is_relative_to_any(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved_path = path.resolve(strict=False)
    for root in roots:
        try:
            resolved_path.relative_to(root.resolve(strict=False))
        except ValueError:
            continue
        return True
    return False


def _resolve_bus_path(override: str | None = None) -> Path:
    """Resolve the bus path from override, env, or package-relative location.

    ASI07: Validates that resolved path is within repo to prevent
    path traversal attacks via COORDINATION_BUS environment variable.

    Resolution order:
      1. ``--bus`` CLI override (must be absolute)
      2. ``COORDINATION_BUS`` env var (validated against repo roots)
      3. ``BUS_CANONICAL_FILE_PATH`` env var (canonical override)
      4. Package-relative: ``<package_parent>/DEFAULT_BUS_PATH``
         (always correct regardless of repo dir name)
      5. Git toplevel + ``DEFAULT_BUS_PATH`` (fallback)
    """
    if override:
        path = Path(override)
        # ASI07: Validate override path is absolute and within allowed directories
        if not path.is_absolute():
            raise ValueError(f"Bus path must be absolute: {path}")
        return path

    env_path = os.environ.get("COORDINATION_BUS")
    if env_path:
        path = Path(env_path)
        # ASI07: Validate env path doesn't traverse outside repo
        roots = _bus_validation_roots()
        if roots and path.is_absolute():
            if not _is_relative_to_any(path, roots):
                raise ValueError(
                    f"COORDINATION_BUS path {path} is outside repo roots {roots}. "
                    "Path traversal attack detected or misconfigured."
                )
        return path

    # BUS_CANONICAL_FILE_PATH: canonical override (same as bus_writer_core)
    canonical_override = os.environ.get("BUS_CANONICAL_FILE_PATH", "").strip()
    if canonical_override:
        return Path(canonical_override)

    # Primary: package-relative resolution (always correct regardless of repo dir name).
    # Path-drift note: git toplevel + DEFAULT_BUS_PATH resolves to
    # <repo_root>/_state/... which is wrong when the package lives in a
    # subdirectory (e.g. repo/package/).
    pkg_parent = Path(__file__).resolve().parents[2]
    pkg_bus = pkg_parent / DEFAULT_BUS_PATH
    if pkg_bus.parent.exists():
        return pkg_bus

    # Fallback: git toplevel + DEFAULT_BUS_PATH for non-standard layouts.
    root = _resolve_common_repo_root() or _resolve_repo_root()
    if root is not None:
        return root / DEFAULT_BUS_PATH
    return Path(DEFAULT_BUS_PATH)


def _extract_flag(
    args: list[str], flag: str, needs_value: bool = True
) -> tuple[list[str], str | bool | None]:
    """Extract a CLI flag and its optional value from *args*.

    Returns ``(remaining_args, value)`` where *value* is ``None`` when the
    flag is absent, ``True`` for boolean flags, or the string value for
    flags that require one.
    """
    if flag not in args:
        return args, None
    idx = args.index(flag)
    if not needs_value:
        return args[:idx] + args[idx + 1 :], True
    if idx + 1 >= len(args):
        return args, None  # caller detects missing value
    value = args[idx + 1]
    return args[:idx] + args[idx + 2 :], value


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for posting to the coordination bus.

    Usage:
        python -m hummbl_bus.bus_writer_cli <from> <to> <type> <message> [options]

    Options:
        --bus PATH          Override bus file path
        --cid ID            Attach a correlation ID
        --secret-file PATH  Sign with key from a KeyManager JSON file
        --sign              Sign using KeyManager auto-resolve for <from>
    """
    args = argv if argv is not None else sys.argv[1:]

    args, bus_override = _extract_flag(args, "--bus")
    if bus_override is None and "--bus" in (argv if argv is not None else sys.argv[1:]):
        print("ERROR: --bus requires a path argument", file=sys.stderr)
        return 2

    args, correlation_id = _extract_flag(args, "--cid")
    if correlation_id is None and "--cid" in (
        argv if argv is not None else sys.argv[1:]
    ):
        print("ERROR: --cid requires a correlation id argument", file=sys.stderr)
        return 2

    args, secret_file = _extract_flag(args, "--secret-file")
    if secret_file is None and "--secret-file" in (
        argv if argv is not None else sys.argv[1:]
    ):
        print("ERROR: --secret-file requires a path argument", file=sys.stderr)
        return 2

    args, sign_flag = _extract_flag(args, "--sign", needs_value=False)

    if len(args) < 4:
        print(
            "Usage: python -m hummbl_bus.bus_writer_cli <from> <to> <type> <message> [--bus PATH] [--sign | --secret-file PATH]",
            file=sys.stderr,
        )
        return 2

    from_id, to_id, msg_type, message = args[0], args[1], args[2], " ".join(args[3:])
    try:
        bus_path = _resolve_bus_path(bus_override)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # Resolve signing secret
    secret: bytes | None = None
    if secret_file:
        import base64

        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            secret = base64.b64decode(key_data["key"])
        except (OSError, KeyError, json.JSONDecodeError) as e:
            print(f"ERROR: failed to load secret file: {e}", file=sys.stderr)
            return 1
    elif sign_flag:
        try:
            try:
                from hummbl_governance.key_management import KeyManager
            except ImportError:
                from security.key_management import KeyManager
            km = KeyManager()
            # Strip parenthetical suffix: "claude-code (god-mode)" -> "claude-code"
            base_identity = from_id.split("(")[0].strip() if "(" in from_id else from_id
            secret = km.get_key(base_identity)
        except Exception as e:
            print(
                f"ERROR: --sign failed to resolve key for {from_id!r}: {e}",
                file=sys.stderr,
            )
            return 1

    try:
        post_message(
            bus_path,
            from_id,
            to_id,
            msg_type,
            message,
            correlation_id=correlation_id,
            secret=secret,
        )
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # #1859: When remote-first mode is active, the write went to the canonical
    # bridge, not the local bus_path. Show the bridge URL to avoid confusion.
    canonical_bridge_url = os.environ.get("BUS_CANONICAL_BRIDGE_URL", "").strip()
    if canonical_bridge_url:
        print(f"OK: {from_id} -> {to_id} [{msg_type}] -> remote {canonical_bridge_url}")
    else:
        print(f"OK: {from_id} -> {to_id} [{msg_type}] -> {bus_path}")
    return 0
