"""BaseNTuple — universal governance tuple for any BaseN tool call.

Bridges three existing tuple implementations:
  - OperatorTuple (Base120): KRINEIA 4-node fields (id, time, state, drift)
  - GovernanceEntry (IDP): tuple_type ∈ {DCTX, CONTRACT, DCT, EVIDENCE, ATTEST}
  - AdapterReceipt: 13-field per-inference governance proof

The BaseNTuple is the atomic governance record for the BaseN tool surface.
Every governed write operation produces one. Reads of sensitive resources
(Tier 0S) produce a READ_EVIDENCE tuple recording the access event.

Tier model:
  Tier 0:   reads — no tuple
  Tier 0S:  sensitive reads — READ_EVIDENCE tuple (access event only, no data)
  Tier 1:   writes — EVIDENCE only (no CONTRACT or DCT)
  Tier 2:   governed decisions — full (CONTRACT, DCT, EVIDENCE)
  Tier 3:   chains — hash-linked sequential tuples

Signing:
  HMAC-SHA256 (symmetric, shared secret) — v0.1, kept for backward compat.
  Ed25519 (asymmetric, external key custody) — v0.3, tamper-evident against
  the operator holding the shared secret. See sign_tuple_ed25519().

Stdlib-only for core. Ed25519 signing requires the `cryptography` package
(already an optional dependency in pyproject.toml [bus-authority]).

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
    tier: int = 1  # 0=read, 0S=sensitive read, 1=write/evidence, 2=governed, 3=chain

    # Authority fields (Tier 2+ only)
    contract_id: str | None = None
    dct_id: str | None = None
    dct_chain_depth: int = 0

    # Chain fields (Tier 3 only)
    previous_hash: str | None = None

    # Integrity
    signature: str | None = None
    signature_algorithm: str | None = None  # "hmac-sha256" or "ed25519"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict, omitting None fields for compactness."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    def to_json(self) -> str:
        """Canonical JSON for hashing and logging."""
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    def content_hash(self) -> str:
        """SHA-256 of canonical JSON (excludes signature and signature_algorithm)."""
        d = self.to_dict()
        d.pop("signature", None)
        d.pop("signature_algorithm", None)
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


def create_read_evidence_tuple(
    agent: str,
    resource_type: str,
    resource_id: str,
    *,
    tool: str = "",
    state: str = "ok",
    drift: float = 0.0,
) -> BaseNTuple:
    """Create a Tier 0S READ_EVIDENCE tuple for a sensitive read operation.

    Closes the read-operation covert channel (NIM review Round 3, Popper/Measurement).
    Records that a read of a sensitive resource occurred, WITHOUT recording the
    data read (privacy-preserving). The evidence dict contains:
      - resource_type: e.g., "pii", "secret", "classified"
      - resource_id: identifier of the resource accessed (not the content)

    This does NOT record the data read — only the access event. The tuple is
    hash-chainable and signature-capable like any other tuple.

    Args:
        agent: Who performed the read.
        resource_type: Sensitivity class of the resource ("pii", "secret", etc.).
        resource_id: Identifier of the resource (path, key, handle — not content).
        tool: Tool that performed the read (optional, for correlation).
        state: Outcome of the read ("ok", "blocked", "denied").
        drift: Drift score for the read event.

    Returns:
        A Tier 0S BaseNTuple recording the read access event.
    """
    return BaseNTuple(
        agent=agent,
        tool=tool or f"read:{resource_type}",
        args_hash="",  # reads don't have write args
        state=state,
        drift=drift,
        evidence={
            "read_event": True,
            "resource_type": resource_type,
            "resource_id": resource_id,
        },
        tier=0,  # 0S — stored as 0 with read_event=True in evidence
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


def create_revocation_tuple(
    agent: str,
    revoked_dct_id: str,
    reason: str,
    revoked_by: str,
    effective_immediately: bool = True,
    propagation_proof: dict[str, Any] | None = None,
    state: str = "ok",
    drift: float = 0.0,
) -> BaseNTuple:
    """Create a REVOCATION tuple for immediate authority withdrawal.

    Broadcasts revocation; scope_gate checks revocation list before allowing.

    Args:
        agent: Who is emitting the revocation (typically operator or governance agent).
        revoked_dct_id: The DCT ID being revoked.
        reason: Human-readable reason for revocation.
        revoked_by: Identity that authorized the revocation.
        effective_immediately: If True, revocation takes effect at emission time.
        propagation_proof: Optional proof of propagation to dependent tuples.
        state: Outcome state ("ok", "blocked", "error").
        drift: Drift score for the revocation event.

    Returns:
        A Tier 2 BaseNTuple recording the revocation event.
    """
    evidence = {
        "revocation_event": True,
        "revoked_dct_id": revoked_dct_id,
        "reason": reason,
        "revoked_by": revoked_by,
        "effective_immediately": effective_immediately,
    }
    if propagation_proof:
        evidence["propagation_proof"] = propagation_proof

    return BaseNTuple(
        agent=agent,
        tool="governance.revoke",
        args_hash="",
        state=state,
        drift=drift,
        evidence=evidence,
        tier=2,
    )


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_tuple(t: BaseNTuple, secret: bytes) -> BaseNTuple:
    """Return a new tuple with HMAC-SHA256 signature.

    The signature covers the content_hash (which excludes the signature and
    signature_algorithm fields), making it tamper-evident.
    """
    content = t.content_hash()
    sig = hmac.new(secret, content.encode("utf-8"), hashlib.sha256).hexdigest()
    # frozen dataclass — create new instance with signature
    d = t.to_dict()
    d["signature"] = sig
    d["signature_algorithm"] = "hmac-sha256"
    return BaseNTuple(**d)


def verify_tuple_signature(t: BaseNTuple, secret: bytes) -> bool:
    """Verify the HMAC-SHA256 signature on a tuple."""
    if t.signature is None:
        return False
    content = t.content_hash()
    expected = hmac.new(secret, content.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(t.signature, expected)


# ---------------------------------------------------------------------------
# Ed25519 signing (asymmetric — tamper-evident against compromised operator)
# ---------------------------------------------------------------------------


def sign_tuple_ed25519(t: BaseNTuple, private_key_bytes: bytes) -> BaseNTuple:
    """Return a new tuple with an Ed25519 asymmetric signature.

    Unlike HMAC-SHA256 (which uses a shared secret the operator holds), Ed25519
    uses asymmetric keys: the signing key is held in external custody (HSM or
    KMS), and the operator does not have direct access. This makes the tuple
    tamper-evident against a compromised operator who holds the HMAC shared
    secret but cannot produce valid Ed25519 signatures.

    The signature covers the content_hash (same as HMAC), encoded as base64.

    Requires the `cryptography` package (already an optional dependency).

    Args:
        t: The tuple to sign.
        private_key_bytes: Raw 32-byte Ed25519 private key (from HSM/KMS).

    Returns:
        New BaseNTuple with Ed25519 signature and signature_algorithm="ed25519".

    Raises:
        ImportError: If the cryptography package is not installed.
    """
    import base64

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    content = t.content_hash()
    sig = key.sign(content.encode("utf-8"))
    d = t.to_dict()
    d["signature"] = base64.b64encode(sig).decode("ascii")
    d["signature_algorithm"] = "ed25519"
    return BaseNTuple(**d)


def verify_tuple_ed25519(t: BaseNTuple, public_key_bytes: bytes) -> bool:
    """Verify an Ed25519 signature on a tuple.

    Args:
        t: The tuple to verify.
        public_key_bytes: Raw 32-byte Ed25519 public key.

    Returns:
        True if the signature is valid, False otherwise.

    Raises:
        ImportError: If the cryptography package is not installed.
    """
    import base64

    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if t.signature is None or t.signature_algorithm != "ed25519":
        return False

    try:
        key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        sig = base64.b64decode(t.signature)
        content = t.content_hash()
        key.verify(sig, content.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Generate a new Ed25519 keypair for testing/development.

    In production, the private key should be generated and stored in an HSM
    or KMS — never in process memory or on disk.

    Returns:
        (private_key_bytes, public_key_bytes) — each 32 bytes.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )

    key = Ed25519PrivateKey.generate()
    private_bytes = key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    public_bytes = key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    return private_bytes, public_bytes


def verify_tuple(
    t: BaseNTuple,
    contract_ops_allowed: list[str] | None = None,
    secret: bytes | None = None,
    ed25519_public_key: bytes | None = None,
) -> tuple[bool, str | None]:
    """Verify a governance tuple against its defining constraints.

    Implements Property 3 (Execution-Authorization Consistency) runtime
    enforcement (B4 fix). Checks that the operations executed (recorded
    in EVIDENCE) are a subset of the operations authorized (in CONTRACT).

    Args:
        t: The BaseNTuple to verify.
        contract_ops_allowed: The CONTRACT's ops_allowed list. If None,
            the subset check is skipped (returns True for that check).
        secret: Optional HMAC shared secret for HMAC-SHA256 signature
            verification. If None, HMAC verification is skipped.
        ed25519_public_key: Optional Ed25519 public key for asymmetric
            signature verification. If the tuple's signature_algorithm is
            "ed25519", this key is used instead of the HMAC secret.

    Returns:
        Tuple of (is_valid, error_code). On success: (True, None).
        On failure: (False, error_code) where error_code is one of:
        - "TUPLE_E_SIGNATURE_INVALID": Signature verification failed
        - "TUPLE_E_OPS_NOT_SUBSET": EVIDENCE ops_executed not subset of
          CONTRACT ops_allowed (Property 3 violation)
    """
    # Signature check
    if t.signature is not None:
        if t.signature_algorithm == "ed25519":
            if ed25519_public_key is not None:
                if not verify_tuple_ed25519(t, ed25519_public_key):
                    return False, "TUPLE_E_SIGNATURE_INVALID"
        elif secret is not None:
            if not verify_tuple_signature(t, secret):
                return False, "TUPLE_E_SIGNATURE_INVALID"

    # Property 3: Execution-Authorization Consistency
    # EVIDENCE.ops_executed ⊆ CONTRACT.ops_allowed
    if contract_ops_allowed is not None:
        ops_executed = t.evidence.get("ops_executed", [])
        if not isinstance(ops_executed, list):
            ops_executed = [ops_executed]
        allowed_set = set(contract_ops_allowed)
        executed_set = set(ops_executed)
        if not executed_set.issubset(allowed_set):
            return False, "TUPLE_E_OPS_NOT_SUBSET"

    return True, None


def get_signing_secret() -> bytes | None:
    """Load signing secret from environment (BUS_SIGNING_SECRET)."""
    raw = os.environ.get("BUS_SIGNING_SECRET", "")
    if not raw:
        return None
    return raw.encode("utf-8")


# ---------------------------------------------------------------------------
# JSONL persistence (KRINEIA-aligned: append-only)
# ---------------------------------------------------------------------------

_DEFAULT_TUPLE_LOG = "hummbl_governance/_state/governance/tuples.jsonl"


def _acquire_file_lock(f, exclusive: bool = True) -> None:
    """Acquire a file lock (cross-platform: portalocker on Windows, fcntl on Unix)."""
    try:
        import portalocker
        flags = portalocker.LOCK_EX if exclusive else portalocker.LOCK_SH
        portalocker.lock(f, flags)
    except ImportError:
        # Fallback to fcntl on Unix
        import fcntl
        flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(f, flags)


def _release_file_lock(f) -> None:
    """Release a file lock (cross-platform)."""
    try:
        import portalocker
        portalocker.unlock(f)
    except ImportError:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)


def append_tuple(
    t: BaseNTuple,
    path: str | None = None,
) -> None:
    """Append a tuple to the JSONL log. Append-only — never deletes.

    Uses portalocker (cross-platform) with fcntl fallback for file locking.
    """
    from pathlib import Path

    if path is None:
        # Resolve relative to repo root
        try:
            import subprocess

            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            log_path = Path(root) / _DEFAULT_TUPLE_LOG
        except Exception:
            log_path = Path(_DEFAULT_TUPLE_LOG)
    else:
        log_path = Path(path)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = t.to_json() + "\n"

    with open(log_path, "a", encoding="utf-8") as f:
        _acquire_file_lock(f, exclusive=True)
        try:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            _release_file_lock(f)
