"""Push/Pull work loop for the coordination bus.

Component 3 of PROPOSAL-012: Autonomous Agent Orchestration.

The bus IS the work queue.  This module provides helpers to:

- **Push**: Post ``PROPOSAL`` messages with ``event=task_request`` metadata.
- **Pull**: Scan the bus for unclaimed tasks matching an agent's capabilities.
- **Claim / Complete**: Post receipts that close the task lifecycle.

All operations are append-only and TSV-safe.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_TASK_ID_RE = re.compile(r"\btask_id=([^;,\s]+)")
_CLAIMED_RE = re.compile(r"\bclaimed_by=([^;,\s]+)")


@dataclass(frozen=True)
class TaskSpec:
    """Specification for a task pushed to the bus."""

    task_id: str
    lane: str
    task_name: str
    priority: str
    required_model_tier: str
    estimated_duration: str
    description: str
    host: str
    requester: str

    def to_bus_body(self) -> str:
        """Render as a TSV-safe bus message body."""
        # Escape newlines to keep single-line TSV safety
        desc = self.description.replace("\n", "\\n").replace("\r", "\\n")
        return (
            f"event=task_request; task_id={self.task_id}; lane={self.lane}; task={self.task_name}; "
            f"priority={self.priority}; model_tier={self.required_model_tier}; "
            f"estimated_duration={self.estimated_duration}; host={self.host}; "
            f"requester={self.requester}; desc={desc}"
        )


@dataclass(frozen=True)
class TaskItem:
    """A task read from the bus during pull."""

    timestamp: str
    task_id: str
    lane: str
    task_name: str
    priority: str
    required_model_tier: str
    estimated_duration: str
    description: str
    host: str
    requester: str
    message: str


def _extract_field(body: str, field: str) -> str | None:
    """Extract ``field=value`` from a semicolon-delimited task body."""
    pattern = rf"\b{re.escape(field)}=([^;]+)(?:;|$)"
    match = re.search(pattern, body)
    if match:
        return match.group(1).strip()
    return None


def _parse_task_request_line(
    timestamp: str, sender: str, message: str
) -> TaskItem | None:
    """Parse a TASK_REQUEST bus line into a TaskItem."""
    task_id = _extract_field(message, "task_id")
    if task_id is None:
        return None
    lane = _extract_field(message, "lane") or ""
    task_name = _extract_field(message, "task") or ""
    priority = _extract_field(message, "priority") or "P3"
    tier = _extract_field(message, "model_tier") or "T1"
    duration = _extract_field(message, "estimated_duration") or ""
    desc = _extract_field(message, "desc") or ""
    host = _extract_field(message, "host") or ""
    requester = _extract_field(message, "requester") or sender
    return TaskItem(
        timestamp=timestamp,
        task_id=task_id,
        lane=lane,
        task_name=task_name,
        priority=priority,
        required_model_tier=tier,
        estimated_duration=duration,
        description=desc,
        host=host,
        requester=requester,
        message=message,
    )


def push_task(
    bus_path: str | Path,
    from_id: str,
    task_spec: TaskSpec,
    correlation_id: str | None = None,
) -> None:
    """Push a task to the bus work queue.

    Args:
        bus_path: Path to messages.tsv.
        from_id: Sender identity (e.g. ``"codex"``).
        task_spec: Structured task specification.
        correlation_id: Optional trace ID.
    """
    from hummbl_bus.bus_writer import post_message

    post_message(
        bus_path=bus_path,
        from_id=from_id,
        to_id="all",
        msg_type="PROPOSAL",
        message=task_spec.to_bus_body(),
        correlation_id=correlation_id,
    )


def pull_tasks(
    bus_path: str | Path,
    *,
    agent_id: str,
    max_model_tier: str | None = None,
    allowed_lanes: list[str] | None = None,
    exclude_requester: str | None = None,
    tail_lines: int = 500,
) -> list[TaskItem]:
    """Pull unclaimed tasks from the bus matching agent capabilities.

    Args:
        bus_path: Path to messages.tsv.
        agent_id: Identity of the pulling agent (used to skip self-requested).
        max_model_tier: Highest tier this agent can run (``T0``/``T1``/``T2``).
            Defaults to no filtering.
        allowed_lanes: Lane prefixes the agent is allowed to pull from.
            Defaults to all lanes.
        exclude_requester: Skip tasks from this sender (usually the agent's
            own identity to avoid self-assignment).
        tail_lines: How many recent bus lines to scan.

    Returns:
        List of unclaimed TaskItems sorted by priority (P0 first).
    """
    path = Path(bus_path)
    if not path.exists():
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.strip().splitlines()
    if lines and lines[0].lower().startswith("timestamp"):
        lines = lines[1:]
    recent = lines[-tail_lines:]

    # First pass: collect task-request PROPOSALs and historical TASK_REQUESTs.
    requests: dict[str, TaskItem] = {}
    completed_ids: set[str] = set()

    for line in recent:
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        ts, sender, _target, mtype, body = parts
        mtype_upper = mtype.strip().upper()

        if mtype_upper == "TASK_REQUEST" or (
            mtype_upper == "PROPOSAL"
            and _extract_field(body, "event") == "task_request"
        ):
            item = _parse_task_request_line(ts.strip(), sender.strip(), body)
            if item is not None:
                # Keep the most recent request for each task_id
                requests[item.task_id] = item

        elif mtype_upper == "TASK_COMPLETE":
            tid = _extract_field(body, "task_id")
            if tid:
                completed_ids.add(tid)

    # Filter to unclaimed tasks
    unclaimed: list[TaskItem] = []
    for item in requests.values():
        if item.task_id in completed_ids:
            continue
        if exclude_requester and item.requester == exclude_requester:
            continue
        if max_model_tier is not None:
            if not _tier_leq(item.required_model_tier, max_model_tier):
                continue
        if allowed_lanes is not None:
            if not any(item.lane.startswith(prefix) for prefix in allowed_lanes):
                continue
        unclaimed.append(item)

    # Sort: P0 first, then P1, P2, P3
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    unclaimed.sort(key=lambda t: priority_order.get(t.priority.upper(), 4))
    return unclaimed


def claim_task(
    bus_path: str | Path,
    from_id: str,
    task_id: str,
    lane: str = "",
    host: str = "unknown",
) -> None:
    """Claim a task by posting a ``RECEIPT`` with ``claimed_by=`` marker.

    Args:
        bus_path: Path to messages.tsv.
        from_id: Agent claiming the task.
        task_id: The task ID to claim.
        lane: Lane name for traceability.
        host: Machine name.
    """
    from hummbl_bus.bus_writer import post_message

    body = f"task_id={task_id}; claimed_by={from_id}; host={host}"
    if lane:
        body += f"; lane={lane}"
    post_message(
        bus_path=bus_path,
        from_id=from_id,
        to_id="all",
        msg_type="RECEIPT",
        message=body,
    )


def complete_task(
    bus_path: str | Path,
    from_id: str,
    task_id: str,
    outcome: str,
    lane: str = "",
    host: str = "unknown",
    artifact: str = "",
) -> None:
    """Close a task by posting ``TASK_COMPLETE``.

    Args:
        bus_path: Path to messages.tsv.
        from_id: Agent completing the task.
        task_id: The task ID.
        outcome: Short outcome description.
        lane: Lane name.
        host: Machine name.
        artifact: Optional artifact reference.
    """
    from hummbl_bus.bus_writer import post_message

    body = f"task_id={task_id}; outcome={outcome}; completed_by={from_id}; host={host}"
    if lane:
        body += f"; lane={lane}"
    if artifact:
        body += f"; artifact={artifact}"
    post_message(
        bus_path=bus_path,
        from_id=from_id,
        to_id="all",
        msg_type="TASK_COMPLETE",
        message=body,
    )


def generate_task_id(prefix: str = "task") -> str:
    """Generate a compact task ID."""
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", prefix).strip("-") or "task"
    return f"{safe}-{uuid.uuid4().hex[:12]}"


def _tier_leq(tier_a: str, tier_b: str) -> bool:
    """Return True if tier_a is less than or equal to tier_b.

    Ordering: T0 < T1 < T2.
    """
    order = {"T0": 0, "T1": 1, "T2": 2, "T0-FREE": 0, "T1-LOW": 1, "T2-ZEN": 2}
    a = order.get(tier_a.strip().upper(), 99)
    b = order.get(tier_b.strip().upper(), 99)
    return a <= b
