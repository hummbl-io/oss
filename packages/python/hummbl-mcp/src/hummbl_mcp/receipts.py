"""Audit receipts — every tool call emits a bus STATUS post.

Wraps the coordination bus (via bus_writer) to produce a compact
per-call audit record: tool name, args summary, result status, timing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolCallReceipt:
    tool: str
    args_summary: str
    status: str  # "ok" | "error"
    duration_ms: int
    result_preview: str = ""
    error: str = ""


def _summarize_args(args: dict[str, Any], max_len: int = 200) -> str:
    """Compact one-line JSON summary, truncated."""
    try:
        s = json.dumps(args, separators=(",", ":"), default=str)
    except Exception:
        s = str(args)
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s


def _preview(value: Any, max_len: int = 200) -> str:
    try:
        s = json.dumps(value, separators=(",", ":"), default=str) if not isinstance(value, str) else value
    except Exception:
        s = str(value)
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s


def post_receipt(receipt: ToolCallReceipt, identity: str = "hummbl-mcp") -> None:
    """Post a receipt to the coordination bus.

    Best-effort. Failures are swallowed — audit should never block a tool call.
    Bus write location is configurable via HUMMBL_MCP_REPO env var;
    defaults to the repo root of this installation.
    """
    repo = os.environ.get("HUMMBL_MCP_REPO", str(Path(__file__).resolve().parent.parent.parent))
    if not os.path.isdir(repo):
        return

    message = {
        "c": f"mcp.{receipt.tool}",
        "args": receipt.args_summary,
        "status": receipt.status,
        "duration_ms": receipt.duration_ms,
    }
    if receipt.result_preview:
        message["preview"] = receipt.result_preview
    if receipt.error:
        message["error"] = receipt.error

    msg_str = json.dumps(message, separators=(",", ":"))

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "bus.bus_writer",
                identity,
                "all",
                "STATUS",
                msg_str,
            ],
            cwd=repo,
            env={**os.environ, "PYTHONPATH": repo},
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        pass  # audit is best-effort


class ReceiptTimer:
    """Context manager that builds a receipt from timing + outcome."""

    def __init__(self, tool: str, args: dict[str, Any], *, identity: str = "hummbl-mcp"):
        self.tool = tool
        self.args_summary = _summarize_args(args)
        self.identity = identity
        self._start: float = 0.0
        self._posted: bool = False

    def __enter__(self) -> "ReceiptTimer":
        self._start = time.monotonic()
        return self

    def ok(self, result: Any) -> None:
        duration_ms = int((time.monotonic() - self._start) * 1000)
        post_receipt(
            ToolCallReceipt(
                tool=self.tool,
                args_summary=self.args_summary,
                status="ok",
                duration_ms=duration_ms,
                result_preview=_preview(result),
            ),
            identity=self.identity,
        )
        self._posted = True

    def error(self, err: str) -> None:
        duration_ms = int((time.monotonic() - self._start) * 1000)
        post_receipt(
            ToolCallReceipt(
                tool=self.tool,
                args_summary=self.args_summary,
                status="error",
                duration_ms=duration_ms,
                error=_preview(err),
            ),
            identity=self.identity,
        )
        self._posted = True

    def __exit__(self, exc_type, exc, tb):
        if not self._posted:
            if exc is None:
                self.ok("<no-result-reported>")
            else:
                self.error(f"{exc_type.__name__}: {exc}")
        return False  # don't suppress
