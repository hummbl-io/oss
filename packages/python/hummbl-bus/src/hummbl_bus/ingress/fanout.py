"""Bus -> channel fan-out watcher.

Tails the canonical bus (local mirror file or HTTP read surface) and
routes rows addressed to configured recipients onto outbound channels
by urgency tier. The reverse direction of the normalizer.

Loop safety: rows that originated through ingress carry ``via=<channel>``
in the body — the watcher skips them so a bus->channel->bus echo cannot
form. Fan-out is strictly one-way: bus rows never re-enter the bus.

Delivery backends are pluggable callables; the reference backend shells
out to an existing channel dispatcher (e.g. a gateway-style
``dispatch(recipient, message, channel)``), an ntfy topic, or an SMTP
send — anything the deployment already has.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

log = logging.getLogger("bus-fanout")

_VIA_RE = re.compile(r"\bvia=[A-Za-z0-9._-]+\b")
HIGH_URGENCY_TYPES = frozenset({"ALERT", "VETO", "BLOCKED"})


@dataclass(frozen=True, slots=True)
class BusRow:
    ts: str
    sender: str
    to: str
    msg_type: str
    message: str

    @property
    def from_ingress(self) -> bool:
        return bool(_VIA_RE.search(self.message))


def parse_tsv_line(line: str) -> BusRow | None:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 5:
        return None
    return BusRow(parts[0], parts[1], parts[2], parts[3], "\t".join(parts[4:]))


def tail_rows(
    path: str, *, from_end: bool = True, poll_seconds: float = 2.0
) -> Iterator[BusRow]:
    """Tail a local bus mirror file; yields parsed rows forever."""
    with open(path, encoding="utf-8", errors="replace") as f:
        if from_end:
            f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(poll_seconds)
                continue
            row = parse_tsv_line(line)
            if row is not None:
                yield row


@dataclass(slots=True)
class Route:
    """Where a matching row goes."""

    recipients: frozenset[str]  # match row.to (case-insensitive)
    channel: str  # "signal"|"email"|"sms"|...
    backend: Callable[[str, str], bool]  # (recipient, text) -> ok
    urgency: frozenset[str] | None = None  # limit to these types; None=all
    target_addr: str = ""  # channel address (env-resolved)


@dataclass(slots=True)
class FanoutStats:
    matched: int = 0
    delivered: int = 0
    skipped_ingress: int = 0
    failed: int = 0
    by_channel: dict = field(default_factory=dict)


def route_row(
    row: BusRow, routes: list[Route], stats: FanoutStats | None = None
) -> int:
    """Route one row; returns number of successful deliveries."""
    stats = stats or FanoutStats()
    if row.from_ingress:
        stats.skipped_ingress += 1
        return 0

    sent = 0
    for route in routes:
        if row.to.lower() not in {r.lower() for r in route.recipients}:
            continue
        if route.urgency is not None and row.msg_type not in route.urgency:
            continue
        stats.matched += 1
        text = f"[{row.msg_type}] {row.sender}: {row.message}"
        try:
            ok = route.backend(route.target_addr or row.to, text)
        except Exception as e:
            log.warning("fanout backend %s failed: %s", route.channel, e)
            ok = False
        if ok:
            sent += 1
            stats.delivered += 1
            stats.by_channel[route.channel] = stats.by_channel.get(route.channel, 0) + 1
        else:
            stats.failed += 1
    return sent


def subprocess_backend(cmd_template: list[str]) -> Callable[[str, str], bool]:
    """Backend factory: substitute {to} and {msg} into a command line."""

    def _send(recipient: str, text: str) -> bool:
        cmd = [c.format(to=recipient, msg=text) for c in cmd_template]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=30)
            return r.returncode == 0
        except Exception:
            return False

    return _send


def run(bus_path: str, routes: list[Route], *, from_end: bool = True) -> None:
    stats = FanoutStats()
    for row in tail_rows(bus_path, from_end=from_end):
        route_row(row, routes, stats)
