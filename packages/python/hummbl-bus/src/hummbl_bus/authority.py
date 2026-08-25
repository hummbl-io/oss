"""Authenticated principal proofs for privileged coordination-bus writes.

``DECISION`` and ``DIRECTIVE`` are operator-authority records.  A caller-
supplied ``from`` field, message-body marker, bridge bearer token, or ordinary
bus signature is not proof that the operator authored one.  The final writer
therefore requires a short-lived proof bound to the complete write request and
consumes its nonce exactly once.

Proof issuance intentionally does not live in this package.  A trusted
operator surface signs the canonical proof payload; bus runtimes only receive
the verifier key through a protected file.

Promoted from hummbl-governance/bus/authority.py 2026-08-15. Identity strings
updated from hummbl-governance to hummbl-bus.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PRIVILEGED_TYPES = frozenset({"DECISION", "DIRECTIVE"})
HUMAN_PRINCIPALS = frozenset({"human", "operator", "approver"})
DEFAULT_AUDIENCE = "hummbl-bus:coordination-bus:privileged-write"
CANONICAL_BUS_ID = "hummbl-bus:canonical-coordination-bus"
MAX_PROOF_TTL_SECONDS = 60
MAX_CLOCK_SKEW_SECONDS = 30
_NONCE_RE = re.compile(r"^[A-Za-z0-9._:-]{16,160}$")
_CONSTRUCTOR_GUARD = object()


@dataclass(frozen=True, slots=True, init=False)
class VerifiedPrincipal:
    """Opaque result produced only after a proof is verified and consumed."""

    principal: str
    sender: str
    audience: str
    request_id: str
    nonce: str
    recipient: str
    msg_type: str
    message_sha256: str
    bus_id: str

    def __init__(
        self,
        principal: str,
        sender: str,
        audience: str,
        request_id: str,
        nonce: str,
        recipient: str,
        msg_type: str,
        message_sha256: str,
        bus_id: str,
        *,
        _guard: object,
    ) -> None:
        if _guard is not _CONSTRUCTOR_GUARD:
            raise TypeError("VerifiedPrincipal instances are verifier-derived")
        object.__setattr__(self, "principal", principal)
        object.__setattr__(self, "sender", sender)
        object.__setattr__(self, "audience", audience)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "nonce", nonce)
        object.__setattr__(self, "recipient", recipient)
        object.__setattr__(self, "msg_type", msg_type)
        object.__setattr__(self, "message_sha256", message_sha256)
        object.__setattr__(self, "bus_id", bus_id)


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True
    ).encode("utf-8")


def _message_digest(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _load_public_key(key: bytes | None = None) -> bytes:
    if key is not None:
        resolved = key
    else:
        key_path = os.environ.get("BUS_PRINCIPAL_PUBLIC_KEY_FILE", "").strip()
        if not key_path:
            raise PermissionError("bus principal public key file is not configured")
        path = Path(key_path).expanduser()
        try:
            encoded = path.read_bytes().strip()
            resolved = base64.b64decode(encoded, validate=True)
        except OSError as exc:
            raise PermissionError(
                "bus principal public key file is unavailable"
            ) from exc
        except ValueError as exc:
            raise PermissionError(
                "bus principal public key file is not valid base64"
            ) from exc
    if len(resolved) != 32:
        raise PermissionError(
            "bus principal Ed25519 public key must be exactly 32 bytes"
        )
    return resolved


def _parse_epoch(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PermissionError(f"principal proof {field} must be an integer epoch")
    return value


def _consume_nonce(
    *,
    nonce: str,
    principal: str,
    request_id: str,
    nonce_dir: Path,
    consumed_at: int,
) -> None:
    """Atomically consume a nonce using an exclusive-create receipt."""
    nonce_dir.mkdir(parents=True, exist_ok=True)
    marker = nonce_dir / f"{hashlib.sha256(nonce.encode('utf-8')).hexdigest()}.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(marker, flags, 0o600)
    except FileExistsError as exc:
        raise PermissionError(
            "principal proof nonce has already been consumed"
        ) from exc
    receipt = {
        "schema": "hummbl_bus.principal_nonce.v1",
        "nonce_sha256": hashlib.sha256(nonce.encode("utf-8")).hexdigest(),
        "principal": principal,
        "request_id": request_id,
        "consumed_at": datetime.fromtimestamp(consumed_at, tz=UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, separators=(",", ":"), sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:  # noqa: TRY203
        # Preserve the marker on write failure. Reuse is less safe than burning
        # a proof whose audit receipt could not be fully persisted.
        raise


def resolve_nonce_dir() -> Path:
    """Resolve the single nonce authority for all accepted bus paths."""
    override = os.environ.get("BUS_PRINCIPAL_NONCE_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve(strict=False)
    from hummbl_bus.bus_writer import resolve_canonical_bus_path

    return resolve_canonical_bus_path().parent / "principal_nonces"


def verify_principal_proof(
    proof: str | Mapping[str, object] | None,
    *,
    sender: str,
    recipient: str,
    msg_type: str,
    message: str,
    request_id: str | None,
    audience: str = DEFAULT_AUDIENCE,
    nonce_dir: str | Path,
    key: bytes | None = None,
    now: int | None = None,
) -> VerifiedPrincipal:
    """Verify a complete privileged-write proof and consume its nonce."""
    if not proof:
        raise PermissionError(
            "privileged bus write requires authenticated principal proof"
        )
    if not request_id or not isinstance(request_id, str):
        raise PermissionError("privileged bus write requires a proof-bound request_id")
    if isinstance(proof, str):
        try:
            decoded = json.loads(proof)
        except json.JSONDecodeError as exc:
            raise PermissionError("principal proof is not valid JSON") from exc
    else:
        decoded = dict(proof)
    if not isinstance(decoded, dict):
        raise PermissionError("principal proof must be a JSON object")

    required = {
        "v",
        "principal",
        "audience",
        "request_id",
        "iat",
        "exp",
        "nonce",
        "sender",
        "recipient",
        "type",
        "message_sha256",
        "bus_id",
        "key_id",
        "sig",
    }
    if set(decoded) != required:
        raise PermissionError("principal proof fields do not match the v1 contract")
    if decoded["v"] != 1:
        raise PermissionError("unsupported principal proof version")

    principal = decoded["principal"]
    nonce = decoded["nonce"]
    signature = decoded["sig"]
    if not isinstance(principal, str) or principal.lower() not in HUMAN_PRINCIPALS:
        raise PermissionError(
            "principal proof does not name an authorized human principal"
        )
    if not isinstance(nonce, str) or not _NONCE_RE.fullmatch(nonce):
        raise PermissionError("principal proof nonce is malformed")
    if not isinstance(signature, str):
        raise PermissionError("principal proof signature is malformed")
    expected_key_id = os.environ.get("BUS_PRINCIPAL_KEY_ID", "operator-ed25519-v1")
    if decoded["key_id"] != expected_key_id:
        raise PermissionError("principal proof key_id is not trusted")

    normalized_type = msg_type.strip().upper()
    expected = {
        "audience": audience,
        "request_id": request_id,
        "sender": sender,
        "recipient": recipient,
        "type": normalized_type,
        "message_sha256": _message_digest(message),
        "bus_id": CANONICAL_BUS_ID,
    }
    for field, value in expected.items():
        if decoded[field] != value:
            raise PermissionError(
                f"principal proof {field} does not match the write request"
            )
    issued_at = _parse_epoch(decoded["iat"], "iat")
    expires_at = _parse_epoch(decoded["exp"], "exp")
    current = int(datetime.now(tz=UTC).timestamp()) if now is None else int(now)
    if expires_at <= issued_at or expires_at - issued_at > MAX_PROOF_TTL_SECONDS:
        raise PermissionError("principal proof lifetime exceeds the allowed bound")
    if issued_at > current + MAX_CLOCK_SKEW_SECONDS:
        raise PermissionError("principal proof was issued too far in the future")
    if expires_at < current:
        raise PermissionError("principal proof has expired")

    unsigned = {field: value for field, value in decoded.items() if field != "sig"}
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise PermissionError(
            "Ed25519 verification support is unavailable; privileged write denied"
        ) from exc
    try:
        signature_bytes = base64.b64decode(signature, validate=True)
        Ed25519PublicKey.from_public_bytes(_load_public_key(key)).verify(
            signature_bytes, _canonical_json(unsigned)
        )
    except (ValueError, InvalidSignature) as exc:
        raise PermissionError("principal proof signature is invalid") from exc

    _consume_nonce(
        nonce=nonce,
        principal=principal.lower(),
        request_id=request_id,
        nonce_dir=Path(nonce_dir),
        consumed_at=current,
    )
    return VerifiedPrincipal(
        principal.lower(),
        sender,
        audience,
        request_id,
        nonce,
        recipient,
        normalized_type,
        _message_digest(message),
        CANONICAL_BUS_ID,
        _guard=_CONSTRUCTOR_GUARD,
    )


def principal_authorizes(
    principal: VerifiedPrincipal | None,
    *,
    sender: str,
    recipient: str,
    msg_type: str,
    message: str,
    request_id: str,
    audience: str = DEFAULT_AUDIENCE,
) -> bool:
    return bool(
        isinstance(principal, VerifiedPrincipal)
        and principal.sender == sender
        and principal.request_id == request_id
        and principal.audience == audience
        and principal.recipient == recipient
        and principal.msg_type == msg_type.strip().upper()
        and principal.message_sha256 == _message_digest(message)
        and principal.bus_id == CANONICAL_BUS_ID
    )
