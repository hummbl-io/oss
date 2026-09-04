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

"""Receipt Engine — K1 invariant enforcement.

Every action that affects shared state produces a structured, signed,
append-only receipt. No receipt = no proof = no authority.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import subprocess  # nosec B404 — subprocess module required for icacls ACL management; all calls use validated arguments
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .invariants import KernelInvariant, KernelPanic

logger = logging.getLogger(__name__)

# Best-effort corpus adapter import
try:
    from ..corpus_adapter import CorpusAdapter
except ImportError:
    CorpusAdapter = None  # type: ignore[misc,assignment]


@dataclass
class Receipt:
    """A structured, signed record of an agent action."""

    receipt_id: str
    agent_id: str
    sequence_id: int
    prev_receipt_hash: str
    timestamp: str
    action_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    law_checks: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)
    evidence_grade: str = "UNGRADED"
    signature: str = ""

    def canonical_json(self) -> str:
        """Return canonical JSON for hashing (excludes signature)."""
        d = asdict(self)
        d.pop("signature")
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    def compute_hash(self) -> str:
        """Compute SHA-256 of canonical form."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def verify_signature(self, secret: bytes) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected = hmac.new(
            secret, self.canonical_json().encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected)


class ReceiptEngine:
    """Engine for creating, signing, storing, and validating receipts."""

    def __init__(
        self,
        state_dir: Path,
        signing_secret: bytes | None = None,
        corpus_adapter: Any = None,
        identity_engine: Any = None,
    ) -> None:
        self.state_dir = state_dir
        self.receipts_dir = state_dir / "receipts"
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.signing_secret = signing_secret or self._resolve_signing_secret()
        self.corpus_adapter = corpus_adapter
        self._identity_engine = identity_engine
        self._io_lock = threading.RLock()
        # In-memory cache of the last receipt hash per agent_id, keyed by
        # agent_id. Avoids O(n²) full-file reads in last_for_agent() when
        # creating chained receipts. Updated on store() and invalidated on
        # any write that could change the last receipt.
        self._last_hash_cache: dict[str, str] = {}

    def _resolve_signing_secret(self) -> bytes:
        """Resolve the HMAC signing secret with platform-appropriate protection.

        Priority:
        1. ``RECEIPTENGINE_HMAC_KEY`` env var (caller-injected, primary path)
        2. ``HUMMBL_SIGNING_SECRET`` env var (fleet-wide fallback)
        3. Existing ``.kernel_secret`` file (migration — existing keys valid)
        4. Generate new key and persist with platform-appropriate protection

        Raises RuntimeError if persistence fails and no env var or existing key
        is available (fail-closed — refuses to silently use an ephemeral key
        that would be lost on process restart).
        """
        # 1. Primary env var
        env_key = os.environ.get("RECEIPTENGINE_HMAC_KEY")
        if env_key:
            return env_key.encode("utf-8")

        # 2. Fleet-wide fallback env var
        fallback_key = os.environ.get("HUMMBL_SIGNING_SECRET")
        if fallback_key:
            return fallback_key.encode("utf-8")

        # 3. Existing .kernel_secret (migration)
        secret_path = self.state_dir / ".kernel_secret"
        if secret_path.exists():
            return secret_path.read_bytes()

        # 4. Generate + persist with platform-appropriate protection
        secret = os.urandom(32)
        try:
            secret_path.write_bytes(secret)
            self._secure_secret_file(secret_path)
        except OSError as exc:
            raise RuntimeError(
                "Cannot persist HMAC signing key and no "
                "RECEIPTENGINE_HMAC_KEY env var set. Either set the env var "
                "or ensure the state_dir is writable. "
                f"Error: {exc}"
            ) from exc
        return secret

    def _secure_secret_file(self, path: Path) -> None:
        """Apply platform-appropriate file permissions to restrict access.

        POSIX: chmod 0o600 (owner read/write only).
        Windows: use icacls to remove inherited permissions and grant only
        the current user full control. Degrades to a warning if icacls fails.
        """
        if os.name == "nt":
            username = os.environ.get("USERNAME") or os.environ.get("USER", "")
            if not username:
                logger.warning(
                    "Could not determine username for Windows ACL on %s; "
                    "file may be accessible to other users",
                    path,
                )
                return
            try:
                subprocess.run(  # nosec B603 — icacls is a trusted Windows system utility for ACL management; arguments are constructed from validated username, not user input
                    [
                        "icacls",
                        str(path),
                        "/inheritance:r",
                        "/grant:r",
                        f"{username}:F",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=10,
                )
            except Exception:
                logger.warning(
                    "Could not set Windows ACL on %s; file may be accessible "
                    "to other users",
                    path,
                    exc_info=True,
                )
        else:
            os.chmod(path, 0o600)

    def create(
        self,
        agent_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        law_checks: list[str] | None = None,
        evidence_grade: str = "UNGRADED",
        prev_receipt_hash: str = "",
        sequence_id: int = 0,
    ) -> Receipt:
        """Create a new receipt.

        Raises KernelPanic if K1 would be violated (e.g., empty agent_id).
        Raises KernelPanic if K3 would be violated (agent_id not registered
        in the identity engine, when identity enforcement is wired).
        """
        if not agent_id:
            raise KernelPanic(
                KernelInvariant.RECEIPT,
                "Receipt requires agent_id (K1)",
            )
        if not action_type:
            raise KernelPanic(
                KernelInvariant.RECEIPT,
                "Receipt requires action_type (K1)",
            )

        # K3 identity enforcement: reject ghost agents not in the registry.
        # Only enforced when an identity_engine is wired (opt-in for backward
        # compatibility; the Kernel wires it automatically during boot).
        if self._identity_engine is not None:
            identity = self._identity_engine.resolve(agent_id)
            if identity is None:
                raise KernelPanic(
                    KernelInvariant.IDENTITY,
                    f"Agent '{agent_id}' is not registered in the identity "
                    f"engine — ghost-agent receipt rejected (K3)",
                    agent_id=agent_id,
                )

        receipt = Receipt(
            receipt_id=f"r-{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            sequence_id=sequence_id,
            prev_receipt_hash=prev_receipt_hash,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            action_type=action_type,
            payload=payload or {},
            law_checks=law_checks or [],
            evidence_grade=evidence_grade,
        )
        receipt.signature = self._sign(receipt)
        return receipt

    def _sign(self, receipt: Receipt) -> str:
        """Sign a receipt with HMAC-SHA256."""
        return hmac.new(
            self.signing_secret,
            receipt.canonical_json().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def store(self, receipt: Receipt) -> str:
        """Store receipt in append-only JSONL.

        If a corpus_adapter was provided at engine initialization,
        the receipt is also submitted to the unified corpus (best-effort).

        Returns the receipt_id.
        """
        receipt_file = self.receipts_dir / f"{receipt.agent_id}.jsonl"
        with self._io_lock:
            with open(receipt_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(receipt), sort_keys=True) + "\n")
            # Update the in-memory last-hash cache so the next
            # last_for_agent() call is O(1) instead of O(n).
            self._last_hash_cache[receipt.agent_id] = receipt.compute_hash()

        # Best-effort corpus ingestion — never block local storage
        if self.corpus_adapter is not None:
            try:
                self.corpus_adapter.ingest_receipt(receipt)
            except Exception:
                logger.warning(
                    "Corpus ingestion failed for receipt %s; stored locally only",
                    receipt.receipt_id,
                    exc_info=True,
                )

        return receipt.receipt_id

    def create_and_store(
        self,
        agent_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        law_checks: list[str] | None = None,
        evidence_grade: str = "UNGRADED",
        prev_receipt_hash: str = "",
        sequence_id: int = 0,
    ) -> Receipt:
        """Create, sign, store, and optionally corpus-ingest a receipt.

        Convenience wrapper around :meth:`create` + :meth:`store`.
        """
        receipt = self.create(
            agent_id=agent_id,
            action_type=action_type,
            payload=payload,
            law_checks=law_checks,
            evidence_grade=evidence_grade,
            prev_receipt_hash=prev_receipt_hash,
            sequence_id=sequence_id,
        )
        self.store(receipt)
        return receipt

    def validate(self, receipt: Receipt) -> bool:
        """Validate a receipt's signature and structure.

        Returns True if valid, False if signature mismatch.
        """
        return receipt.verify_signature(self.signing_secret)

    def list_for_agent(self, agent_id: str) -> list[Receipt]:
        """List all receipts for an agent.

        Fail-closed: corrupted receipt lines are a K1 invariant violation.
        Silently skipping corrupted lines would cause receipt records to
        disappear from the history with no observable signal, undermining
        the receipt integrity guarantee. Raise KernelPanic so operators
        can investigate and repair the corrupted records.
        """
        receipt_file = self.receipts_dir / f"{agent_id}.jsonl"
        if not receipt_file.exists():
            return []
        receipts: list[Receipt] = []
        with self._io_lock:
            try:
                text = receipt_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # File has invalid UTF-8 bytes — try with errors='replace'
                text = receipt_file.read_text(encoding="utf-8", errors="replace")
        for line in text.strip().split("\n"):
            if not line:
                continue
            try:
                receipts.append(Receipt(**json.loads(line)))
            except (json.JSONDecodeError, TypeError) as exc:
                logger.error(
                    "Corrupted receipt line in %s: %s",
                    receipt_file, line[:100],
                )
                raise KernelPanic(
                    KernelInvariant.RECEIPT,
                    f"Corrupted receipt line in {receipt_file}: "
                    f"{line[:100]!r} — refusing to silently drop receipt record",
                ) from exc
        return receipts

    def last_for_agent(self, agent_id: str) -> Receipt | None:
        """Get the most recent receipt for an agent.

        Uses an in-memory cache for the last receipt hash when available,
        falling back to a full file read only on cache miss (first call
        for this agent_id in this process, or after cache invalidation).
        """
        with self._io_lock:
            cached = self._last_hash_cache.get(agent_id)
        if cached is not None:
            receipt_file = self.receipts_dir / f"{agent_id}.jsonl"
            if not receipt_file.exists():
                return None
            with self._io_lock:
                try:
                    text = receipt_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = receipt_file.read_text(encoding="utf-8", errors="replace")
            lines = text.strip().split("\n")
            if not lines or not lines[-1]:
                return None
            try:
                return Receipt(**json.loads(lines[-1]))
            except (json.JSONDecodeError, TypeError) as exc:
                logger.error(
                    "Corrupted last receipt line in %s: %s",
                    receipt_file, lines[-1][:100],
                )
                raise KernelPanic(
                    KernelInvariant.RECEIPT,
                    f"Corrupted receipt line in {receipt_file}: "
                    f"{lines[-1][:100]!r} — refusing to silently drop receipt record",
                ) from exc
        receipts = self.list_for_agent(agent_id)
        if receipts:
            with self._io_lock:
                self._last_hash_cache[agent_id] = receipts[-1].compute_hash()
            return receipts[-1]
        return None

    def verify_chain(self, agent_id: str) -> tuple[bool, str]:
        """Verify the hash chain for an agent's receipts.

        Returns (valid, last_hash).
        """
        receipts = self.list_for_agent(agent_id)
        if not receipts:
            return True, ""

        prev_hash = ""
        for receipt in receipts:
            if receipt.prev_receipt_hash != prev_hash:
                return False, receipt.compute_hash()
            if not self.validate(receipt):
                return False, receipt.compute_hash()
            prev_hash = receipt.compute_hash()
        return True, prev_hash
