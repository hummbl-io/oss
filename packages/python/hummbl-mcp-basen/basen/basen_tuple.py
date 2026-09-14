"""BaseNTuple — universal governance tuple for any BaseN tool call.

Bridges three existing tuple implementations:
  - OperatorTuple (Base120): KRINEIA 4-node fields (id, time, state, drift)
  - GovernanceEntry (IDP): tuple_type ∈ {DCTX, CONTRACT, DCT, EVIDENCE, ATTEST}
  - AdapterReceipt: 13-field per-inference governance proof

The BaseNTuple is the atomic governance record for the BaseN tool surface.
Every governed write operation produces one. Reads (Tier 0) produce none.

Tier model:
  Tier 0: reads — no tuple
  Tier 1: writes — EVIDENCE only (no CONTRACT or DCT)
  Tier 2: governed decisions — full (CONTRACT, DCT, EVIDENCE)
  Tier 3: chains — hash-linked sequential tuples

Stdlib-only. No third-party dependencies.

Reference: BASEN_DESIGN.md §3, TUPLE_ATOMIC_RECORD_DRAFT.md §3.2
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# BaseNTuple dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseNTuple:
    """Universal governance tuple for any BaseN tool call.

    Fields are grouped by layer:
      KRINEIA 4-node:  id, time, state, drift
      Governance:    agent, tool, args_hash, evidence, tier
      Authority:     contract_id, dct_id, dct_chain_depth  (Tier 2+ only)
      Chain:         previous_hash  (Tier 3 only)
      Integrity:     signature  (when signing is enabled)
    """

    # KRINEIA 4-node fields
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    time: str = field(default_factory=_utc_now_iso)
    state: str = "ok"  # outcome: "ok", "blocked", "error"
    drift: float = 0.0  # 0.0 = perfect, 1.0 = total failure

    # Governance fields (Tier 1+)
    agent: str = ""  # who called it
    tool: str = ""  # namespaced tool name (e.g., "bus.post", "base120.record")
    args_hash: str = ""  # SHA-256 of canonical JSON args
    evidence: dict[str, Any] = field(default_factory=dict)
    tier: int = 1  # 0=read, 1=write/evidence, 2=governed, 3=chain

    # Authority fields (Tier 2+ only)
    contract_id: str | None = None
    dct_id: str | None = None
    dct_chain_depth: int = 0

    # Chain fields (Tier 3 only)
    previous_hash: str | None = None

    # Integrity
    signature: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, omitting None fields for compactness."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    def to_json(self) -> str:
        """Canonical JSON for hashing and logging."""
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    def content_hash(self) -> str:
        """SHA-256 of canonical JSON (excludes signature field)."""
        d = self.to_dict()
        d.pop("signature", None)
        canonical = json.dumps(d, separators=(",", ":"), sort_keys=True)
        return _sha256(canonical)


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def create_evidence_tuple(
    agent: str,
    tool: str,
    args: dict[str, Any],
    state: str = "ok",
    drift: float = 0.0,
    evidence: dict[str, Any] | None = None,
) -> BaseNTuple:
    """Create a Tier 1 EVIDENCE tuple for a write operation."""
    args_json = json.dumps(args, separators=(",", ":"), sort_keys=True)
    return BaseNTuple(
        agent=agent,
        tool=tool,
        args_hash=_sha256(args_json),
        state=state,
        drift=drift,
        evidence=evidence or {},
        tier=1,
    )


def create_governed_tuple(
    agent: str,
    tool: str,
    args: dict[str, Any],
    contract_id: str,
    dct_id: str,
    dct_chain_depth: int = 0,
    state: str = "ok",
    drift: float = 0.0,
    evidence: dict[str, Any] | None = None,
) -> BaseNTuple:
    """Create a Tier 2 governed tuple (CONTRACT + DCT + EVIDENCE)."""
    args_json = json.dumps(args, separators=(",", ":"), sort_keys=True)
    return BaseNTuple(
        agent=agent,
        tool=tool,
        args_hash=_sha256(args_json),
        state=state,
        drift=drift,
        evidence=evidence or {},
        tier=2,
        contract_id=contract_id,
        dct_id=dct_id,
        dct_chain_depth=dct_chain_depth,
    )


def create_chain_tuple(
    agent: str,
    tool: str,
    args: dict[str, Any],
    contract_id: str,
    dct_id: str,
    previous_hash: str,
    dct_chain_depth: int = 0,
    state: str = "ok",
    drift: float = 0.0,
    evidence: dict[str, Any] | None = None,
) -> BaseNTuple:
    """Create a Tier 3 chain-linked tuple."""
    args_json = json.dumps(args, separators=(",", ":"), sort_keys=True)
    return BaseNTuple(
        agent=agent,
        tool=tool,
        args_hash=_sha256(args_json),
        state=state,
        drift=drift,
        evidence=evidence or {},
        tier=3,
        contract_id=contract_id,
        dct_id=dct_id,
        dct_chain_depth=dct_chain_depth,
        previous_hash=previous_hash,
    )


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_tuple(t: BaseNTuple, secret: bytes) -> BaseNTuple:
    """Return a new tuple with HMAC-SHA256 signature.

    The signature covers the content_hash (which excludes the signature field),
    making it tamper-evident.
    """
    content = t.content_hash()
    sig = hmac.new(secret, content.encode("utf-8"), hashlib.sha256).hexdigest()
    # frozen dataclass — create new instance with signature
    d = t.to_dict()
    d["signature"] = sig
    return BaseNTuple(**d)


def verify_tuple_signature(t: BaseNTuple, secret: bytes) -> bool:
    """Verify the HMAC-SHA256 signature on a tuple."""
    if t.signature is None:
        return False
    content = t.content_hash()
    expected = hmac.new(secret, content.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(t.signature, expected)


def get_signing_secret() -> bytes | None:
    """Load signing secret from environment (BUS_SIGNING_SECRET)."""
    raw = os.environ.get("BUS_SIGNING_SECRET", "")
    if not raw:
        return None
    return raw.encode("utf-8")


# ---------------------------------------------------------------------------
# JSONL persistence (KRINEIA-aligned: append-only)
# ---------------------------------------------------------------------------

_DEFAULT_TUPLE_LOG = "_state/governance/tuples.jsonl"


def append_tuple(
    t: BaseNTuple,
    path: str | None = None,
) -> None:
    """Append a tuple to the JSONL log. Append-only — never deletes.

    Cross-platform: uses fcntl on POSIX, msvcrt on Windows.
    """
    from pathlib import Path

    if path is None:
        log_path = Path(_DEFAULT_TUPLE_LOG)
    else:
        log_path = Path(path)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = t.to_json() + "\n"

    with open(log_path, "a", encoding="utf-8") as f:
        try:
            import fcntl

            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        except ImportError:
            # Windows: msvcrt-based locking
            import os

            if os.name == "nt":
                import msvcrt

                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                except OSError:
                    pass
                try:
                    f.write(line)
                finally:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
            else:
                f.write(line)
