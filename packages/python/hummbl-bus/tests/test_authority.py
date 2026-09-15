from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from hummbl_bus.authority import (
    _CONSTRUCTOR_GUARD,
    CANONICAL_BUS_ID,
    DEFAULT_AUDIENCE,
    PRIVILEGED_TYPES,
    PRIVILEGED_MESSAGE_SCHEMA,
    VERIFIED_PRINCIPAL_SCHEMA,
    VerifiedPrincipal,
    _consume_nonce,
    _message_digest,
    build_privileged_message,
    principal_authorizes,
    verified_principal_receipt,
    verify_principal_proof,
)


KEY_ID = "operator-ed25519-v1"
KEY_SHA256 = "1" * 64
PROOF_SHA256 = "2" * 64
PROOF_JSON = '{"sig":"fixture"}'


def _verified_fixture() -> VerifiedPrincipal:
    return VerifiedPrincipal(
        "reuben",
        KEY_ID,
        KEY_SHA256,
        "codex",
        DEFAULT_AUDIENCE,
        "req-1",
        "3" * 64,
        "all",
        "DECISION",
        _message_digest("test"),
        CANONICAL_BUS_ID,
        1700000000,
        1700000060,
        PROOF_JSON,
        PROOF_SHA256,
        _guard=_CONSTRUCTOR_GUARD,
    )


def _signed_proof(
    private_key: Ed25519PrivateKey,
    *,
    principal: str = "reuben",
    message: str = "test",
    request_id: str = "req-real-0001",
    nonce: str = "unique-nonce-real-0001",
    now: int = 1700000000,
) -> dict[str, object]:
    proof: dict[str, object] = {
        "v": 1,
        "principal": principal,
        "audience": DEFAULT_AUDIENCE,
        "request_id": request_id,
        "iat": now,
        "exp": now + 60,
        "nonce": nonce,
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": _message_digest(message),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": KEY_ID,
    }
    canonical = json.dumps(
        proof,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    proof["sig"] = base64.b64encode(private_key.sign(canonical)).decode("ascii")
    return proof


def test_privileged_types_are_decision_and_directive() -> None:
    assert PRIVILEGED_TYPES == frozenset({"DECISION", "DIRECTIVE"})


def test_identity_strings_updated_to_hummbl_bus() -> None:
    """Promoted module must not retain hummbl-governance identity strings."""
    assert DEFAULT_AUDIENCE == "hummbl-bus:coordination-bus:privileged-write"
    assert CANONICAL_BUS_ID == "hummbl-bus:canonical-coordination-bus"


def test_verified_principal_requires_guard() -> None:
    with pytest.raises(TypeError, match="verifier-derived"):
        VerifiedPrincipal(
            "reuben",
            KEY_ID,
            KEY_SHA256,
            "codex",
            DEFAULT_AUDIENCE,
            "req-1",
            "3" * 64,
            "all",
            "DECISION",
            "abc",
            CANONICAL_BUS_ID,
            1700000000,
            1700000060,
            PROOF_JSON,
            PROOF_SHA256,
            _guard=object(),
        )


def test_verified_principal_constructs_with_guard() -> None:
    vp = _verified_fixture()
    assert vp.principal == "reuben"
    assert vp.key_id == KEY_ID
    assert vp.sender == "codex"
    assert vp.msg_type == "DECISION"


def test_message_digest_is_sha256_hex() -> None:
    digest = _message_digest("hello")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_consume_nonce_creates_marker_and_rejects_reuse(tmp_path: Path) -> None:
    nonce_dir = tmp_path / "nonces"
    _consume_nonce(
        nonce="unique-nonce-value-1234",
        principal="reuben",
        key_id=KEY_ID,
        key_sha256=KEY_SHA256,
        request_id="req-1",
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message_sha256=_message_digest("test"),
        audience=DEFAULT_AUDIENCE,
        bus_id=CANONICAL_BUS_ID,
        issued_at=1700000000,
        expires_at=1700000060,
        proof_sha256=PROOF_SHA256,
        nonce_dir=nonce_dir,
        consumed_at=1700000000,
    )
    markers = list(nonce_dir.glob("*.json"))
    assert len(markers) == 1
    receipt = json.loads(markers[0].read_text(encoding="utf-8"))
    assert receipt["schema"] == "hummbl_bus.principal_nonce.v2"
    assert receipt["principal"] == "reuben"
    assert receipt["key_sha256"] == KEY_SHA256
    assert receipt["request_id"] == "req-1"
    assert receipt["message_sha256"] == _message_digest("test")
    assert receipt["proof_sha256"] == PROOF_SHA256

    # Reuse must fail
    with pytest.raises(PermissionError, match="already been consumed"):
        _consume_nonce(
            nonce="unique-nonce-value-1234",
            principal="reuben",
            key_id=KEY_ID,
            key_sha256=KEY_SHA256,
            request_id="req-1",
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message_sha256=_message_digest("test"),
            audience=DEFAULT_AUDIENCE,
            bus_id=CANONICAL_BUS_ID,
            issued_at=1700000000,
            expires_at=1700000060,
            proof_sha256=PROOF_SHA256,
            nonce_dir=nonce_dir,
            consumed_at=1700000001,
        )


def test_verify_principal_proof_rejects_empty_proof(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="requires authenticated principal proof"):
        verify_principal_proof(
            None,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
        )


def test_verify_principal_proof_rejects_missing_request_id(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="proof-bound request_id"):
        verify_principal_proof(
            "{}",
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id=None,
            nonce_dir=tmp_path,
        )


def test_verify_principal_proof_rejects_non_human_principal(tmp_path: Path) -> None:
    proof = {
        "v": 1,
        "principal": "evil-agent",
        "audience": DEFAULT_AUDIENCE,
        "request_id": "req-1",
        "iat": 1700000000,
        "exp": 1700000060,
        "nonce": "unique-nonce-abc12345",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": _message_digest("test"),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": "operator-ed25519-v1",
        "sig": "fakesig",
    }
    with pytest.raises(PermissionError, match="not bound to the verifier key"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
        )


def test_real_signature_is_bound_to_principal_key_and_envelope(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    proof = _signed_proof(private_key)
    verified = verify_principal_proof(
        proof,
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message="test",
        request_id="req-real-0001",
        nonce_dir=tmp_path,
        key=public_key,
        trusted_principal="reuben",
        trusted_key_id=KEY_ID,
        now=1700000000,
    )

    assert verified.principal == "reuben"
    assert verified.key_sha256 == hashlib.sha256(public_key).hexdigest()
    receipt = verified_principal_receipt(verified)
    assert receipt["schema"] == VERIFIED_PRINCIPAL_SCHEMA
    assert receipt["proof_sha256"] == verified.proof_sha256

    envelope = json.loads(build_privileged_message("test", verified))
    assert envelope["schema"] == PRIVILEGED_MESSAGE_SCHEMA
    assert envelope["content"] == "test"
    assert envelope["authority"]["receipt"] == receipt
    assert envelope["authority"]["principal_proof"] == proof


def test_same_key_cannot_select_another_principal(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    proof = _signed_proof(
        private_key,
        principal="dan",
        nonce="unique-nonce-other-0001",
    )
    with pytest.raises(PermissionError, match="not bound to the verifier key"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-real-0001",
            nonce_dir=tmp_path,
            key=public_key,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
            now=1700000000,
        )


def test_principal_proof_string_rejects_duplicate_keys(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="not valid JSON"):
        verify_principal_proof(
            '{"v":1,"v":1}',
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-real-0001",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
            now=1700000000,
        )


def test_principal_proof_rejects_sequence_shaped_input(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="must be a JSON object"):
        verify_principal_proof(
            [["v", 1]],  # type: ignore[arg-type]
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-real-0001",
            nonce_dir=tmp_path,
            key=b"0" * 32,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
            now=1700000000,
        )


def test_verify_principal_proof_rejects_wrong_audience(tmp_path: Path) -> None:
    proof = {
        "v": 1,
        "principal": "reuben",
        "audience": "wrong-audience",
        "request_id": "req-1",
        "iat": 1700000000,
        "exp": 1700000060,
        "nonce": "unique-nonce-abc12345",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": _message_digest("test"),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": "operator-ed25519-v1",
        "sig": "fakesig",
    }
    with pytest.raises(PermissionError, match="audience does not match"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
        )


def test_verify_principal_proof_rejects_expired_proof(tmp_path: Path) -> None:
    proof = {
        "v": 1,
        "principal": "reuben",
        "audience": DEFAULT_AUDIENCE,
        "request_id": "req-1",
        "iat": 1700000000,
        "exp": 1700000010,
        "nonce": "unique-nonce-abc12345",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": _message_digest("test"),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": "operator-ed25519-v1",
        "sig": "fakesig",
    }
    with pytest.raises(PermissionError, match="expired"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
            now=1700000100,
        )


def test_verify_principal_proof_rejects_exact_expiry_boundary(
    tmp_path: Path,
) -> None:
    proof = {
        "v": 1,
        "principal": "reuben",
        "audience": DEFAULT_AUDIENCE,
        "request_id": "req-1",
        "iat": 1700000000,
        "exp": 1700000010,
        "nonce": "unique-nonce-boundary-001",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": _message_digest("test"),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": KEY_ID,
        "sig": "fakesig",
    }
    with pytest.raises(PermissionError, match="expired"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
            trusted_principal="reuben",
            trusted_key_id=KEY_ID,
            now=1700000010,
        )


def test_principal_authorizes_checks_all_fields() -> None:
    vp = _verified_fixture()
    assert principal_authorizes(
        vp,
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message="test",
        request_id="req-1",
    )
    # Wrong sender
    assert not principal_authorizes(
        vp,
        sender="claude-code",
        recipient="all",
        msg_type="DECISION",
        message="test",
        request_id="req-1",
    )
    # Wrong message
    assert not principal_authorizes(
        vp,
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message="wrong",
        request_id="req-1",
    )
    # None principal
    assert not principal_authorizes(
        None,
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message="test",
        request_id="req-1",
    )
