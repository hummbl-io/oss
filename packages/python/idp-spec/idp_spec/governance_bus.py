"""Governance Bus - Append-only audit log for IDP tuples.

This module implements the governance event store per IDP v0.1 I6 invariant
(Audit Completeness). All IDP tuples (DCTX, CONTRACT, EVIDENCE, ATTEST, DCT)
are written to an append-only JSONL log with rotation and retention.

IDP References:
- IDP_SPEC.md: All tuple schemas
- IDP_INVARIANTS.md Section I6: Audit Completeness
- IDP_INTEGRATION_PLAN.md: Storage recommendations
"""

from __future__ import annotations

import gzip
import hashlib
import hmac
import json
import logging
import os
import shutil
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# PII protection: import scrubber from cognition layer.
# Governance bus tuple_data is scrubbed before append to prevent
# PII from entering the hash-chained, effectively irremovable log.
try:
    from hummbl_governance.cognition.ledger_writer import scrub_pii_from_dict as _scrub_pii
except ImportError:
    # Fallback: if cognition module unavailable, pass through unscrubbed
    # but log a warning. This should only happen in isolated test envs.
    def _scrub_pii(data: dict) -> dict:  # type: ignore[misc]
        logger.warning("PII scrubber unavailable — tuple_data written unscrubbed")
        return data


def _is_idp_enabled() -> bool:
    """Check if IDP feature flag is enabled (runtime check).

    ASI07: Changed from fail-open to fail-closed.
    Governance audit is now mandatory.
    Set ENABLE_IDP=false ONLY for emergency bypass (logs warning).
    """
    enabled = os.environ.get("ENABLE_IDP", "true").lower() == "true"
    if not enabled:
        logger.warning(
            "ENABLE_IDP=false: Governance audit BYPASSED. "
            "This is an emergency-only setting and creates compliance risk."
        )
    return enabled


# Default paths
DEFAULT_GOVERNANCE_DIR = Path.home() / ".local" / "share" / "idp-spec" / "governance"

# Retention configuration
DEFAULT_RETENTION_DAYS = 180  # EU AI Act Art 26(5) requires minimum 6 months
ROTATION_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

# Error codes
IDP_E_AUDIT_INCOMPLETE = "IDP_E_AUDIT_INCOMPLETE"
IDP_E_AUDIT_IMMUTABLE = "IDP_E_AUDIT_IMMUTABLE"
IDP_E_AMENDMENT_TARGET_MISSING = "IDP_E_AMENDMENT_TARGET_MISSING"
IDP_E_VERIFICATION_REF_INVALID = "IDP_E_VERIFICATION_REF_INVALID"
IDP_E_EVIDENCE_REQUIRED = "IDP_E_EVIDENCE_REQUIRED"
IDP_E_CHAIN_BROKEN = "IDP_E_CHAIN_BROKEN"
# D08: Lateral authority enforcement (ADR-FM-011)
IDP_E_LATERAL_AUTH = "IDP_E_LATERAL_AUTH"
IDP_E_DECISION_AUTH = "IDP_E_DECISION_AUTH"


@dataclass(frozen=True)
class GovernanceEntry:
    """Single entry in the governance audit log.

    Wraps any IDP tuple with metadata for audit trail.

    Cross-link fields (contract_id, capability_token_id, verification_id)
    are top-level to enable direct traversal without inspecting tuple_data.
    The amendment_of field enables structural amendment tracking per IDP Sec 3.5.
    """

    timestamp: str  # ISO8601 UTC
    entry_id: str  # UUID for this entry
    intent_id: str  # Root intent (links delegation tree)
    task_id: str  # Specific task
    tuple_type: Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"]
    tuple_data: dict[str, Any]  # The actual IDP tuple
    signature: str | None = None  # Optional HMAC for integrity
    
    # KRINEIA 4-node fields (Layer 2 judgment)
    state: str = "ok"  # outcome: "ok", "blocked", "error"
    drift: float = 0.0  # 0.0 = perfect, 1.0 = total failure

    # Cross-link identifiers (top-level for direct traversal)
    contract_id: str | None = None  # Links to governing CONTRACT
    capability_token_id: str | None = None  # Links to authorizing DCT
    verification_id: str | None = None  # Links ATTEST to EVIDENCE
    # Amendment tracking (append-only correction chain)
    amendment_of: str | None = None  # entry_id of the entry being amended
    # Hash-chaining for tamper-evident audit trail
    previous_hash: str | None = None  # SHA-256 of prior entry's canonical JSONL

    def to_jsonl(self) -> str:
        """Serialize to JSONL line."""
        data: dict[str, Any] = {
            "timestamp": self.timestamp,
            "entry_id": self.entry_id,
            "intent_id": self.intent_id,
            "task_id": self.task_id,
            "tuple_type": self.tuple_type,
            "tuple_data": self.tuple_data,
            "signature": self.signature,
            "state": self.state,
            "drift": self.drift,
        }
        # Include cross-link fields when present (backward-compatible)
        if self.contract_id is not None:
            data["contract_id"] = self.contract_id
        if self.capability_token_id is not None:
            data["capability_token_id"] = self.capability_token_id
        if self.verification_id is not None:
            data["verification_id"] = self.verification_id
        if self.amendment_of is not None:
            data["amendment_of"] = self.amendment_of
        if self.previous_hash is not None:
            data["previous_hash"] = self.previous_hash
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GovernanceEntry:
        """Deserialize from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            entry_id=data["entry_id"],
            intent_id=data["intent_id"],
            task_id=data["task_id"],
            tuple_type=data["tuple_type"],
            tuple_data=data["tuple_data"],
            signature=data.get("signature"),
            state=data.get("state", "ok"),
            drift=data.get("drift", 0.0),
            contract_id=data.get("contract_id"),
            capability_token_id=data.get("capability_token_id"),
            verification_id=data.get("verification_id"),
            amendment_of=data.get("amendment_of"),
            previous_hash=data.get("previous_hash"),
        )


class GovernanceBus:
    """Append-only governance audit log for IDP tuples.

    Implements I6 invariant (Audit Completeness) with:
    - Atomic append-only writes
    - Daily file rotation
    - 180-day retention (EU AI Act Art 26(5) minimum 6 months)
    - Query by intent_id or task_id
    - Optional async buffering

    Thread-safe for concurrent writes.
    """

    def __init__(
        self,
        base_dir: Path | str | None = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        enable_async: bool = False,
    ):
        """Initialize governance bus.

        Args:
            base_dir: Directory for audit logs (default: ~/.local/share/idp-spec/governance)
            retention_days: Days to retain logs (default: 180)
            enable_async: Enable async write buffering (default: False)
        """
        if base_dir is None:
            base_dir = DEFAULT_GOVERNANCE_DIR
        self._base_dir = Path(base_dir)
        self._retention_days = retention_days
        self._enable_async = enable_async

        # Ensure directory exists with restrictive permissions
        self._base_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._base_dir, 0o700)
        except OSError as e:
            logger.debug("Could not set governance dir permissions: %s", e)

        # Thread lock for concurrent writes
        self._lock = threading.RLock()

        # Async buffer (if enabled)
        self._buffer: list[GovernanceEntry] = []
        self._buffer_lock = threading.RLock()

        # Current file handle (lazy init)
        self._current_file: Path | None = None
        self._file_handle: Any = None

    def _get_current_file(self) -> Path:
        """Get current log file path (daily rotation)."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self._base_dir / f"governance-{today}.jsonl"

    def _rotate_if_needed(self) -> None:
        """Check and perform file rotation if needed."""
        current = self._get_current_file()

        # Check if file changed (day rollover)
        if self._current_file != current:
            # Close old file
            if self._file_handle:
                self._file_handle.close()
                self._file_handle = None
            self._current_file = current

        # Check size rotation (if file > 10MB, compress and start new)
        if current.exists() and current.stat().st_size > ROTATION_SIZE_BYTES:
            if self._file_handle:
                self._file_handle.close()
                self._file_handle = None
            # Compress current file
            compressed = current.with_suffix(".jsonl.gz")
            with open(current, "rb") as f_in, gzip.open(compressed, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            current.unlink()

    def _open_file(self) -> Any:
        """Open current log file for appending."""
        if self._file_handle is None or self._file_handle.closed:
            self._current_file = self._get_current_file()
            self._file_handle = open(self._current_file, "a", encoding="utf-8")
        return self._file_handle

    def append(
        self,
        intent_id: str,
        task_id: str,
        tuple_type: Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"],
        tuple_data: dict[str, Any],
        signature: str | None = None,
        require_signature: bool = True,  # ASI07: Mandatory signatures
        state: str = "ok",
        drift: float = 0.0,
        contract_id: str | None = None,
        capability_token_id: str | None = None,
        verification_id: str | None = None,
        amendment_of: str | None = None,
        authority_class: bool = False,  # ADR-FM-011: authority-class entry requires DCT linkage
    ) -> tuple[bool, str | None]:
        """Append entry to governance log.

        ASI07: Signatures are now mandatory for audit integrity.

        Args:
            intent_id: Root intent identifier
            task_id: Task identifier
            tuple_type: Type of IDP tuple
            tuple_data: The tuple data
            signature: HMAC signature (required unless require_signature=False)
            require_signature: If True (default), rejects entries without signatures
            state: KRINEIA state ("ok", "blocked", "error")
            drift: KRINEIA drift (0.0 to 1.0)
            contract_id: Cross-link to governing CONTRACT entry
            capability_token_id: Cross-link to authorizing DCT entry
            verification_id: Cross-link from ATTEST to EVIDENCE entry
            amendment_of: entry_id of the entry being amended (append-only correction)
            authority_class: If True, requires capability_token_id referencing a valid DCT
                (ADR-FM-011 lateral authority enforcement).

        Returns:
            Tuple of (success, error_code). Error codes:
            - IDP_E_AUDIT_INCOMPLETE: Write failed
            - IDP_E_AUDIT_IMMUTABLE: Signature required but missing
            - IDP_E_AMENDMENT_TARGET_MISSING: amendment_of references nonexistent entry
            - IDP_E_EVIDENCE_REQUIRED: ATTEST without verification_id (I1 violation)
            - IDP_E_LATERAL_AUTH: authority_class entry without capability_token_id
            - IDP_E_DECISION_AUTH: authority_class entry with invalid DCT reference
        """
        if not _is_idp_enabled():
            # ASI07: Even when IDP disabled, log attempt (but allow)
            logger.warning(
                "Governance append while IDP disabled - entry not audited"
            )
            return True, None

        # ASI07: Mandatory signature check
        if require_signature and not signature:
            logger.error(
                "Governance entry rejected: signature required but not provided. "
                "Set require_signature=False only for emergency recovery."
            )
            return False, IDP_E_AUDIT_IMMUTABLE

        # I1: Evidence-before-verify — ATTEST tuples must reference EVIDENCE
        if tuple_type == "ATTEST" and verification_id is None:
            logger.error(
                "Governance entry rejected: ATTEST tuple requires verification_id "
                "(evidence-before-verify invariant I1)."
            )
            return False, IDP_E_EVIDENCE_REQUIRED

        # I1 referential integrity — verification_id must reference existing EVIDENCE entry
        if tuple_type == "ATTEST" and verification_id is not None:
            ref_entry = self.query_by_entry_id(verification_id)
            if ref_entry is None or ref_entry.tuple_type != "EVIDENCE":
                logger.error(
                    "Governance entry rejected: verification_id %s does not reference "
                    "an existing EVIDENCE entry (I1 referential integrity).",
                    verification_id,
                )
                return False, IDP_E_VERIFICATION_REF_INVALID

        # Amendment validation — referenced entry must exist
        if amendment_of is not None:
            found = False
            for entry in self._query(lambda e: e.entry_id == amendment_of):
                found = True
                break
            if not found:
                logger.error(
                    "Governance entry rejected: amendment_of references "
                    f"nonexistent entry {amendment_of}."
                )
                return False, IDP_E_AMENDMENT_TARGET_MISSING

        # ADR-FM-011: Lateral authority enforcement
        # Authority-class entries must carry a valid DCT cross-link.
        if authority_class:
            if capability_token_id is None:
                logger.error(
                    "Governance entry rejected: authority_class entry requires "
                    "capability_token_id (ADR-FM-011 lateral authority)."
                )
                return False, IDP_E_LATERAL_AUTH
            # Validate that the referenced DCT exists in the governance log
            ref_dct = self.query_by_entry_id(capability_token_id)
            if ref_dct is None or ref_dct.tuple_type != "DCT":
                logger.error(
                    "Governance entry rejected: capability_token_id %s does not "
                    "reference an existing DCT entry (ADR-FM-011).",
                    capability_token_id,
                )
                return False, IDP_E_DECISION_AUTH

        # PII scrub: sanitize tuple_data before it enters the hash-chained log.
        # This replaces PII (emails, phones, SSNs, IPs) with SHA-256 pseudonyms,
        # preserving data utility while ensuring GDPR Art. 17 compatibility.
        scrubbed_data = _scrub_pii(tuple_data)

        # Hash-chaining: link to prior entry for tamper-evident audit trail
        with self._lock:
            prev_hash = self._get_last_entry_hash()

        entry = GovernanceEntry(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            entry_id=self._generate_entry_id(),
            intent_id=intent_id,
            task_id=task_id,
            tuple_type=tuple_type,
            tuple_data=scrubbed_data,
            signature=signature,
            state=state,
            drift=drift,
            contract_id=contract_id,
            capability_token_id=capability_token_id,
            verification_id=verification_id,
            amendment_of=amendment_of,
            previous_hash=prev_hash,
        )

        if self._enable_async:
            return self._append_async(entry)
        else:
            return self._append_sync(entry)

    def _append_sync(self, entry: GovernanceEntry) -> tuple[bool, str | None]:
        """Synchronous append with atomic write and permission hardening (ASI07)."""
        with self._lock:
            try:
                self._rotate_if_needed()
                f = self._open_file()
                f.write(entry.to_jsonl() + "\n")
                f.flush()  # Ensure written to disk
                os.fsync(f.fileno())  # Force OS flush

                # ASI07: Harden file permissions on governance logs
                if self._current_file:
                    try:
                        self._current_file.chmod(0o600)
                    except OSError as e:
                        logger.warning("Failed to harden governance log permissions: %s", e)

                return True, None
            except (IOError, OSError):
                return False, IDP_E_AUDIT_INCOMPLETE

    def _append_async(self, entry: GovernanceEntry) -> tuple[bool, str | None]:
        """Async append to buffer (flushed periodically)."""
        with self._buffer_lock:
            self._buffer.append(entry)
            # Flush if buffer reaches 100 entries
            if len(self._buffer) >= 100:
                return self._flush_buffer()
            return True, None

    def _flush_buffer(self) -> tuple[bool, str | None]:
        """Flush async buffer to disk with permission hardening (ASI07)."""
        with self._lock, self._buffer_lock:
            if not self._buffer:
                return True, None

            try:
                self._rotate_if_needed()
                f = self._open_file()
                for entry in self._buffer:
                    f.write(entry.to_jsonl() + "\n")
                f.flush()
                os.fsync(f.fileno())

                # ASI07: Harden file permissions on governance logs
                if self._current_file:
                    try:
                        self._current_file.chmod(0o600)
                    except OSError as e:
                        logger.warning("Failed to harden governance log permissions: %s", e)

                self._buffer.clear()
                return True, None
            except (IOError, OSError):
                return False, IDP_E_AUDIT_INCOMPLETE

    def _generate_entry_id(self) -> str:
        """Generate unique entry ID."""
        return str(uuid.uuid4())

    @staticmethod
    def compute_entry_hash(jsonl_line: str) -> str:
        """Compute SHA-256 hash of a JSONL entry line.

        This is the hash that the *next* entry stores in its previous_hash
        field, creating a tamper-evident chain.
        """
        return hashlib.sha256(jsonl_line.encode("utf-8")).hexdigest()

    def _get_last_entry_hash(self) -> str | None:
        """Read the last entry from the current log file and return its hash.

        Returns None if the log is empty or doesn't exist yet (genesis entry).
        """
        current = self._get_current_file()
        if not current.exists():
            return None

        last_line = None
        try:
            with open(current, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
        except (IOError, OSError):
            return None

        if last_line is None:
            return None
        return self.compute_entry_hash(last_line)

    def verify_chain(self, filepath: Path | None = None) -> tuple[bool, list[dict]]:
        """Verify hash-chain integrity of a governance log file.

        Walks every entry in order and confirms each entry's previous_hash
        matches the SHA-256 of the prior entry's canonical JSONL. Reports
        all breaks found.

        Args:
            filepath: Specific log file to verify. Defaults to current day's file.

        Returns:
            Tuple of (chain_valid, breaks) where breaks is a list of dicts:
            [{"line": int, "entry_id": str, "expected": str, "actual": str}]
        """
        if filepath is None:
            filepath = self._get_current_file()

        if not filepath.exists():
            return True, []  # Empty log is trivially valid

        breaks: list[dict] = []
        prev_line: str | None = None
        line_num = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for raw_line in f:
                    stripped = raw_line.strip()
                    if not stripped:
                        continue
                    line_num += 1

                    try:
                        data = json.loads(stripped)
                    except json.JSONDecodeError:
                        breaks.append({
                            "line": line_num,
                            "entry_id": "PARSE_ERROR",
                            "expected": "valid JSON",
                            "actual": "malformed",
                        })
                        prev_line = stripped
                        continue

                    if data is None or not isinstance(data, dict):
                        breaks.append({
                            "line": line_num,
                            "entry_id": "PARSE_ERROR",
                            "expected": "JSON object",
                            "actual": str(data),
                        })
                        prev_line = stripped
                        continue

                    entry_prev_hash = data.get("previous_hash")

                    if line_num == 1:
                        # Genesis entry: previous_hash should be None
                        if entry_prev_hash is not None:
                            breaks.append({
                                "line": 1,
                                "entry_id": data.get("entry_id", "UNKNOWN"),
                                "expected": "null (genesis)",
                                "actual": entry_prev_hash,
                            })
                    else:
                        # Non-genesis: previous_hash must match hash of prior line
                        expected_hash = self.compute_entry_hash(prev_line) if prev_line else None
                        if entry_prev_hash != expected_hash:
                            breaks.append({
                                "line": line_num,
                                "entry_id": data.get("entry_id", "UNKNOWN"),
                                "expected": expected_hash or "null",
                                "actual": entry_prev_hash or "null",
                            })

                    prev_line = stripped

        except (IOError, OSError) as e:
            breaks.append({
                "line": 0,
                "entry_id": "FILE_ERROR",
                "expected": "readable file",
                "actual": str(e),
            })

        return len(breaks) == 0, breaks

    def query_by_intent(
        self,
        intent_id: str,
        tuple_type: (
            Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"] | None
        ) = None,
        since: str | None = None,
    ) -> Iterator[GovernanceEntry]:
        """Query entries by intent_id.

        Args:
            intent_id: Intent to query
            tuple_type: Optional filter by tuple type
            since: Optional ISO8601 timestamp filter

        Yields:
            GovernanceEntry objects matching query
        """
        if not _is_idp_enabled():
            return

        yield from self._query(
            lambda e: e.intent_id == intent_id,
            tuple_type=tuple_type,
            since=since,
        )

    def query_by_task(
        self,
        task_id: str,
        tuple_type: (
            Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"] | None
        ) = None,
    ) -> Iterator[GovernanceEntry]:
        """Query entries by task_id.

        Args:
            task_id: Task to query
            tuple_type: Optional filter by tuple type

        Yields:
            GovernanceEntry objects matching query
        """
        if not _is_idp_enabled():
            return

        yield from self._query(
            lambda e: e.task_id == task_id,
            tuple_type=tuple_type,
        )

    def query_by_entry_id(self, entry_id: str) -> GovernanceEntry | None:
        """Query a single entry by its entry_id."""
        if not _is_idp_enabled():
            return None
        for entry in self._query(lambda e: e.entry_id == entry_id):
            return entry
        return None

    def query_by_contract(
        self,
        contract_id: str,
        tuple_type: (
            Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"] | None
        ) = None,
    ) -> Iterator[GovernanceEntry]:
        """Query entries by contract_id cross-link."""
        if not _is_idp_enabled():
            return
        yield from self._query(
            lambda e: e.contract_id == contract_id,
            tuple_type=tuple_type,
        )

    def query_amendments(self, entry_id: str) -> Iterator[GovernanceEntry]:
        """Query all amendments to a given entry."""
        if not _is_idp_enabled():
            return
        yield from self._query(lambda e: e.amendment_of == entry_id)

    def query_all(
        self,
        tuple_type: (
            Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"] | None
        ) = None,
        since: str | None = None,
    ) -> Iterator[GovernanceEntry]:
        """Yield every governance entry (gated by ENABLE_IDP).

        Returns an empty iterator when IDP is disabled. Files are walked
        newest-first; callers that need timestamp order should sort.
        """
        if not _is_idp_enabled():
            return
        yield from self._query(lambda e: True, tuple_type=tuple_type, since=since)

    def _query(
        self,
        predicate: callable,
        tuple_type: (
            Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"] | None
        ) = None,
        since: str | None = None,
    ) -> Iterator[GovernanceEntry]:
        """Internal query implementation."""
        # Get all log files (newest first)
        files = sorted(self._base_dir.glob("governance-*.jsonl*"), reverse=True)

        for filepath in files:
            # Use partial to avoid lambda closure bug (filepath captured by value)
            if filepath.suffix == ".gz":
                opener = partial(gzip.open, filepath, "rt", encoding="utf-8")
            else:
                opener = partial(open, filepath, "r", encoding="utf-8")
                # Read-time chain validation for uncompressed files (P0-3).
                # Detects tampering on every read path, not just explicit verify_chain calls.
                chain_valid, breaks = self.verify_chain(filepath)
                if not chain_valid:
                    logger.error(
                        "%s: %d chain break(s) detected during read — "
                        "governance log may have been tampered with. "
                        "error_code=%s breaks=%s",
                        filepath.name,
                        len(breaks),
                        IDP_E_CHAIN_BROKEN,
                        breaks[:3],  # cap log volume
                    )

            try:
                with opener() as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            entry = GovernanceEntry.from_dict(data)

                            # Apply filters
                            if not predicate(entry):
                                continue
                            if tuple_type and entry.tuple_type != tuple_type:
                                continue
                            if since and entry.timestamp < since:
                                continue

                            yield entry
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            logger.warning("Corrupted governance entry in %s: %s", filepath, e)
                            continue
            except (IOError, OSError) as e:
                logger.warning("Unreadable governance log %s: %s", filepath, e)
                continue

    def enforce_retention(self) -> int:
        """Enforce retention policy by deleting old logs.

        Returns:
            Number of files deleted
        """
        if not _is_idp_enabled():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        deleted = 0

        for filepath in self._base_dir.glob("governance-*.jsonl*"):
            # Extract date from filename (governance-YYYY-MM-DD.jsonl)
            try:
                date_str = filepath.stem.split("-")[1:4]
                file_date = datetime(
                    int(date_str[0]),
                    int(date_str[1]),
                    int(date_str[2]),
                    tzinfo=timezone.utc,
                )
                if file_date < cutoff:
                    filepath.unlink()
                    deleted += 1
            except (ValueError, IndexError):
                continue

        return deleted

    def close(self) -> None:
        """Close file handles and flush buffers."""
        if self._enable_async:
            self._flush_buffer()

        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()
                self._file_handle = None

    def __enter__(self) -> GovernanceBus:
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()


# Module-level singleton
_default_bus: GovernanceBus | None = None
_default_bus_lock = threading.Lock()
_ephemeral_signing_secret: bytes | None = None
_ephemeral_signing_secret_lock = threading.Lock()


def _get_signing_secret() -> bytes:
    """Return signing secret for governance entries.

    Prefers the persistent DCT secret when configured. Falls back to a
    process-local ephemeral key so append_audit_entry() can still satisfy the
    fail-closed signature requirement during local development.

    SECURITY NOTE: The ephemeral fallback is for development only. Production
    deployments MUST set DCT_SECRET — without it, signatures cannot survive
    process restarts and the tamper-evidence chain cannot be independently
    verified after the process exits. Set DCT_SECRET to a persistent random
    secret (e.g. `python3 -c "import secrets; print(secrets.token_hex(32))"`).
    """
    secret = os.environ.get("DCT_SECRET")
    if secret:
        return secret.encode("utf-8")

    global _ephemeral_signing_secret
    if _ephemeral_signing_secret is None:
        with _ephemeral_signing_secret_lock:
            if _ephemeral_signing_secret is None:
                logger.error(
                    "DCT_SECRET not set — governance bus using ephemeral signing key. "
                    "Audit signatures are NOT persistent across process restarts. "
                    "Chain integrity cannot be verified after this process exits. "
                    "Set DCT_SECRET in production. This is a security gap."
                )
                _ephemeral_signing_secret = os.urandom(32)
    return _ephemeral_signing_secret


def _compute_entry_signature(
    intent_id: str,
    task_id: str,
    tuple_type: Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"],
    tuple_data: dict[str, Any],
    state: str = "ok",
    drift: float = 0.0,
) -> str:
    """Compute deterministic HMAC signature for a governance entry payload."""
    payload = {
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_type": tuple_type,
        "tuple_data": tuple_data,
        "state": state,
        "drift": drift,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        _get_signing_secret(),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_governance_bus() -> GovernanceBus:
    """Get default governance bus instance.

    Returns:
        Shared GovernanceBus instance
    """
    global _default_bus
    if _default_bus is None:
        with _default_bus_lock:
            if _default_bus is None:
                _default_bus = GovernanceBus()
    return _default_bus


def append_audit_entry(
    intent_id: str,
    task_id: str,
    tuple_type: Literal["DCTX", "CONTRACT", "EVIDENCE", "ATTEST", "DCT", "SYSTEM"],
    tuple_data: dict[str, Any],
    signature: str | None = None,
    state: str = "ok",
    drift: float = 0.0,
    contract_id: str | None = None,
    capability_token_id: str | None = None,
    verification_id: str | None = None,
    amendment_of: str | None = None,
) -> tuple[bool, str | None]:
    """Convenience function to append via default bus."""
    if signature is None:
        signature = _compute_entry_signature(
            intent_id=intent_id,
            task_id=task_id,
            tuple_type=tuple_type,
            tuple_data=tuple_data,
            state=state,
            drift=drift,
        )
    return get_governance_bus().append(
        intent_id=intent_id,
        task_id=task_id,
        tuple_type=tuple_type,
        tuple_data=tuple_data,
        signature=signature,
        state=state,
        drift=drift,
        contract_id=contract_id,
        capability_token_id=capability_token_id,
        verification_id=verification_id,
        amendment_of=amendment_of,
    )


def query_intent(intent_id: str, **kwargs) -> Iterator[GovernanceEntry]:
    """Convenience function to query via default bus."""
    return get_governance_bus().query_by_intent(intent_id, **kwargs)
