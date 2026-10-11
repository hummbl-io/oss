"""Sender allowlist — channel addresses mapped to bus identities.

Config is JSON (stdlib-only). Real phone numbers / emails live in a
local, uncommitted config file or in env-var references — never in
this repo.

Config shape::

    {
      "senders": {
        "+15550001111": {"from": "operator", "channels": ["sms","voice","signal"],
                         "pin_env": "BUS_INGRESS_OPERATOR_PIN"},
        "me@example.com": {"from": "operator", "channels": ["email"],
                           "pin_env": "BUS_INGRESS_OPERATOR_PIN"},
        "default": {"from": "channel-ingress", "channels": ["*"]}
      },
      "unknown_sender": "quarantine"   // "quarantine" | "drop"
    }

A sender allowed on ANY channel is matched per-channel: an allowlisted
email doesn't grant the same identity over SMS (From:/caller-ID are
independently spoofable; scope matters).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SenderPolicy:
    bus_from: str
    pin_env: str | None = None  # env var holding this sender's PIN
    quarantine: bool = False  # unknown sender parked as *-ingress

    def pin_matches(self, pin: str | None) -> bool:
        """Constant-shape PIN check; missing env means no PIN authority."""
        if self.pin_env is None or pin is None:
            return False
        expected = os.environ.get(self.pin_env, "")
        return bool(expected) and pin == expected


class Allowlist:
    def __init__(self, senders: dict[str, dict], *, unknown_sender: str = "quarantine"):
        if unknown_sender not in ("quarantine", "drop"):
            raise ValueError("unknown_sender must be 'quarantine' or 'drop'")
        self._senders = senders
        self.unknown_sender = unknown_sender

    @classmethod
    def load(cls, path: str | Path) -> Allowlist:
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            cfg.get("senders", {}),
            unknown_sender=cfg.get("unknown_sender", "quarantine"),
        )

    def lookup(self, sender_addr: str, channel: str) -> SenderPolicy | None:
        """Resolve sender+channel to a bus identity, or None to drop."""
        entry = self._senders.get(sender_addr)
        if entry is None:
            entry = self._senders.get("default", {})
            if self.unknown_sender == "drop":
                return None
            bus_from = entry.get("from", f"{channel}-ingress")
            return SenderPolicy(bus_from=bus_from, quarantine=True)

        channels = entry.get("channels", ["*"])
        if "*" not in channels and channel not in channels:
            # Right address, wrong channel — treat as unknown for safety.
            if self.unknown_sender == "drop":
                return None
            return SenderPolicy(bus_from=f"{channel}-ingress", quarantine=True)
        return SenderPolicy(bus_from=entry["from"], pin_env=entry.get("pin_env"))
