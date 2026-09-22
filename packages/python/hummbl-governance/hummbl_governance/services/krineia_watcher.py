# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Krineia Watcher — Service agent that observes the coordination bus and
creates Krineia cryptographic receipts for skill invocations.

This module satisfies Krineia Invariant 5 (Trust-Root Separation) by running
as a structurally independent observer process that:
- Reads the coordination bus (read-only; never writes to it)
- Detects SKILL_INVOKE events posted by fleet agents
- Creates and signs receipts independently
- Writes receipts to its own append-only JSONL log

The observed agents NEVER:
- Generate their own receipts
- Hold signing keys for the receipt chain
- Control the receipt-generation process

Schema: governance/schemas/krineia_receipt.schema.json
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import os
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WATCHER_IDENTITY = "krineia-watcher"
RECEIPT_VERSION = "2.0.0"
EVENT_PREFIX = "skill.invoked"
DEFAULT_POLL_INTERVAL = 5  # seconds
DEFAULT_BUS_PATH = "founder_mode/_state/coordination/messages.tsv"
DEFAULT_RECEIPT_PATH = "founder_mode/_state/governance/skill_receipts.jsonl"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 Z format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_text(text: str) -> str:
    """Compute SHA-256 of UTF-8 text. Returns 64 hex chars."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hmac_sign(message: str, secret: str) -> str:
    """HMAC-SHA256 hex-digest of message using secret."""
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _canonical_json(obj: dict[str, Any]) -> str:
    """Serialize dict to canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _parse_skill_invoke(message: str) -> dict[str, str] | None:
    """Parse a SKILL_INVOKE bus message into structured fields.

    Expected format: [skill=<name>] [mode=<mode>] [args_hash=<sha256>] [session=<id>]
    Returns None if parsing fails.
    """
    result: dict[str, str] = {}
    # Simple bracket-pair extraction: [key=value]
    for match in _SKILL_INVOKE_RE.finditer(message):
        key = match.group(1)
        value = match.group(2)
        result[key] = value

    required = {"skill", "mode", "args_hash", "session"}
    if not required.issubset(result.keys()):
        return None
    return result


import re

_SKILL_INVOKE_RE = re.compile(r"\[(\w+)=([^\]]+)\]")

# ---------------------------------------------------------------------------
# Receipt creation
# ---------------------------------------------------------------------------


class SkillReceiptWriter:
    """Creates and persists Krineia receipts for skill invocations.

    Each receipt is:
    - Cryptographically signed (HMAC-SHA256) via BUS_SIGNING_SECRET
    - Hash-chained to the prior receipt (genesis uses zeros)
    - Append-only (never edited in place)
    """

    def __init__(
        self,
        receipt_path: str | Path,
        signing_secret: str | None = None,
        signing_key_id: str = "v1",
    ) -> None:
        self.receipt_path = Path(receipt_path)
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self.signing_key_id = signing_key_id
        self._secret: str | None = signing_secret or os.environ.get(
            "BUS_SIGNING_SECRET"
        )
        self._last_hash: str | None = None
        self._chain_length: int = 0
        self._load_chain_tail()

    def _load_chain_tail(self) -> None:
        """Read the last receipt to recover chain state."""
        if not self.receipt_path.exists():
            self._last_hash = "0" * 64
            self._chain_length = 0
            return

        with open(self.receipt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        self._chain_length = len(lines)
        if lines:
            last = json.loads(lines[-1])
            self._last_hash = last.get("hash", "0" * 64)
        else:
            self._last_hash = "0" * 64

    def generate(
        self,
        actor_identity: str,
        skill_name: str,
        execution_mode: str,
        args_hash: str,
        session_id: str,
        bus_timestamp: str,
    ) -> dict[str, Any]:
        """Create a Krineia receipt for a skill invocation.

        Args:
            actor_identity: Bare canonical identity of the invoking agent.
            skill_name: Name of the invoked skill.
            execution_mode: The skill's execution-mode value.
            args_hash: SHA-256 hash of the skill arguments.
            session_id: Session UUID from the SKILL_INVOKE event.
            bus_timestamp: Timestamp from the bus message.
        """
        receipt_id = str(uuid.uuid4())
        timestamp = _utc_now()

        payload = {
            "skill": skill_name,
            "mode": execution_mode,
            "args_hash": args_hash,
            "session_id": session_id,
            "bus_timestamp": bus_timestamp,
        }

        receipt: dict[str, Any] = {
            "schema_version": RECEIPT_VERSION,
            "id": receipt_id,
            "session_id": session_id,
            "actor_identity": actor_identity,
            "time": timestamp,
            "state": {
                "event": f"{EVENT_PREFIX}.{skill_name}",
                "payload": payload,
            },
            "drift": 0.0,
            "prev_hash": self._last_hash,
            "signature_envelope": {},
            "hash": "",
        }

        # Compute hash (sans signature envelope and top-level hash)
        body = {k: v for k, v in receipt.items() if k not in ("signature_envelope", "hash")}
        body_json = _canonical_json(body)
        receipt_hash = _sha256_text(body_json)
        receipt["hash"] = receipt_hash

        # Sign if secret available
        if self._secret:
            signature = _hmac_sign(receipt_hash, self._secret)
            receipt["signature_envelope"] = {
                "key_id": self.signing_key_id,
                "signer_identity": WATCHER_IDENTITY,
                "algorithm": "HMAC-SHA256",
                "signature": signature,
            }
        else:
            logger.warning(
                "BUS_SIGNING_SECRET not set; receipt %s generated unsigned",
                receipt_id,
            )

        return receipt

    def append(self, receipt: dict[str, Any]) -> None:
        """Append receipt to the chain log."""
        line = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
        with open(self.receipt_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        self._last_hash = receipt["hash"]
        self._chain_length += 1

    @property
    def chain_length(self) -> int:
        return self._chain_length


# ---------------------------------------------------------------------------
# Bus polling
# ---------------------------------------------------------------------------


class BusPoller:
    """Reads the coordination bus and yields new entries since last poll."""

    def __init__(self, bus_path: str | Path) -> None:
        self.bus_path = Path(bus_path)
        self._last_line_count: int = 0
        self._init_cursor()

    def _init_cursor(self) -> None:
        """Initialize cursor to end of existing file."""
        if not self.bus_path.exists():
            self._last_line_count = 0
            return
        with open(self.bus_path, "r", encoding="utf-8") as f:
            self._last_line_count = sum(1 for _ in f)

    def poll(self) -> list[dict[str, str]]:
        """Read new bus entries since last poll."""
        if not self.bus_path.exists():
            return []

        with open(self.bus_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = lines[self._last_line_count :]
        self._last_line_count = len(lines)

        entries: list[dict[str, str]] = []
        for line in new_lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            entries.append({
                "timestamp": parts[0],
                "from": parts[1],
                "to": parts[2],
                "type": parts[3],
                "message": "\t".join(parts[4:]),  # message may contain tabs
            })
        return entries


# ---------------------------------------------------------------------------
# Main watcher loop
# ---------------------------------------------------------------------------


class KrineiaWatcher:
    """Main watcher daemon."""

    def __init__(
        self,
        bus_path: str | Path,
        receipt_path: str | Path,
        poll_interval: float,
        signing_secret: str | None = None,
    ) -> None:
        self.poller = BusPoller(bus_path)
        self.writer = SkillReceiptWriter(receipt_path, signing_secret)
        self.poll_interval = poll_interval
        self._running = False
        self._receipts_written = 0

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        """Graceful shutdown on SIGTERM/SIGINT."""
        logger.info(
            "Krineia watcher shutting down (signal %d); receipts_written=%d",
            signum,
            self._receipts_written,
        )
        self._running = False

    def run(self) -> None:
        """Main loop: poll bus, create receipts, append to chain."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info(
            "Krineia watcher started; chain_length=%d; poll_interval=%.1fs",
            self.writer.chain_length,
            self.poll_interval,
        )

        while self._running:
            try:
                self._tick()
            except Exception:
                logger.exception("Tick failed; continuing")
            time.sleep(self.poll_interval)

    def _tick(self) -> None:
        """Single poll-and-process cycle."""
        entries = self.poller.poll()
        for entry in entries:
            if entry["type"] != "SKILL_INVOKE":
                continue

            parsed = _parse_skill_invoke(entry["message"])
            if parsed is None:
                logger.warning("Malformed SKILL_INVOKE: %s", entry["message"])
                continue

            receipt = self.writer.generate(
                actor_identity=entry["from"],
                skill_name=parsed["skill"],
                execution_mode=parsed["mode"],
                args_hash=parsed["args_hash"],
                session_id=parsed["session"],
                bus_timestamp=entry["timestamp"],
            )
            self.writer.append(receipt)
            self._receipts_written += 1
            logger.debug(
                "Receipt created: id=%s skill=%s actor=%s",
                receipt["id"],
                parsed["skill"],
                entry["from"],
            )

    def verify_chain(self) -> bool:
        """Verify receipt chain integrity. Returns True if valid."""
        if not self.writer.receipt_path.exists():
            return True

        with open(self.writer.receipt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        prev_hash = "0" * 64
        for i, line in enumerate(lines):
            receipt = json.loads(line)

            # Check prev_hash linkage
            if receipt["prev_hash"] != prev_hash:
                logger.error(
                    "Chain broken at receipt %d: prev_hash mismatch", i
                )
                return False

            # Recompute hash
            body = {k: v for k, v in receipt.items() if k not in ("signature_envelope", "hash")}
            expected_hash = _sha256_text(_canonical_json(body))
            if receipt["hash"] != expected_hash:
                logger.error(
                    "Hash mismatch at receipt %d: expected=%s got=%s",
                    i,
                    expected_hash,
                    receipt["hash"],
                )
                return False

            # Verify signature if present
            sig_env = receipt.get("signature_envelope", {})
            if sig_env and self.writer._secret:
                expected_sig = _hmac_sign(receipt["hash"], self.writer._secret)
                if sig_env.get("signature") != expected_sig:
                    logger.error(
                        "Signature mismatch at receipt %d", i
                    )
                    return False

            prev_hash = receipt["hash"]

        logger.info("Chain verified: %d receipts, valid", len(lines))
        return True

    def tail(self, n: int) -> list[dict[str, Any]]:
        """Return last N receipts."""
        if not self.writer.receipt_path.exists():
            return []
        with open(self.writer.receipt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return [json.loads(line) for line in lines[-n:]]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Krineia Watcher Service Agent")
    parser.add_argument(
        "--bus-path",
        default=DEFAULT_BUS_PATH,
        help=f"Path to coordination bus TSV (default: {DEFAULT_BUS_PATH})",
    )
    parser.add_argument(
        "--receipt-path",
        default=DEFAULT_RECEIPT_PATH,
        help=f"Path to receipt JSONL (default: {DEFAULT_RECEIPT_PATH})",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Poll interval in seconds (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuous polling loop",
    )
    parser.add_argument(
        "--verify-chain",
        action="store_true",
        help="Verify receipt chain integrity and exit",
    )
    parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Print last N receipts and exit",
    )
    parser.add_argument(
        "--signing-secret",
        default=None,
        help="HMAC signing secret (or use BUS_SIGNING_SECRET env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    watcher = KrineiaWatcher(
        bus_path=args.bus_path,
        receipt_path=args.receipt_path,
        poll_interval=args.poll_interval,
        signing_secret=args.signing_secret,
    )

    if args.verify_chain:
        ok = watcher.verify_chain()
        return 0 if ok else 1

    if args.tail is not None:
        receipts = watcher.tail(args.tail)
        for r in receipts:
            print(json.dumps(r, indent=2))
        return 0

    if args.daemon:
        watcher.run()
        return 0

    # One-shot poll
    watcher._tick()
    logger.info("One-shot poll complete; receipts_written=%d", watcher._receipts_written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
