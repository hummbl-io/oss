from __future__ import annotations

import json
from pathlib import Path

import pytest
from hummbl_bus.authority import (
    _CONSTRUCTOR_GUARD,
    CANONICAL_BUS_ID,
    DEFAULT_AUDIENCE,
    PRIVILEGED_TYPES,
    VerifiedPrincipal,
    _consume_nonce,
    _message_digest,
    principal_authorizes,
    verify_principal_proof,
)


def test_privileged_types_are_decision_and_directive() -> None:
    assert PRIVILEGED_TYPES == frozenset({"DECISION", "DIRECTIVE"})


def test_identity_strings_updated_to_hummbl_bus() -> None:
    """Promoted module must not retain hummbl-governance identity strings."""
    assert DEFAULT_AUDIENCE == "hummbl-bus:coordination-bus:privileged-write"
    assert CANONICAL_BUS_ID == "hummbl-bus:canonical-coordination-bus"


def test_verified_principal_requires_guard() -> None:
    with pytest.raises(TypeError, match="verifier-derived"):
        VerifiedPrincipal(
            "operator",
            "codex",
            DEFAULT_AUDIENCE,
            "req-1",
            "nonce-1234567890abcdef",
            "all",
            "DECISION",
            "abc",
            CANONICAL_BUS_ID,
            _guard=object(),
        )


def test_verified_principal_constructs_with_guard() -> None:
    vp = VerifiedPrincipal(
        "operator",
        "codex",
        DEFAULT_AUDIENCE,
        "req-1",
        "nonce-1234567890abcdef",
        "all",
        "DECISION",
        "abc",
        CANONICAL_BUS_ID,
        _guard=_CONSTRUCTOR_GUARD,
    )
    assert vp.principal == "operator"
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
        principal="operator",
        request_id="req-1",
        nonce_dir=nonce_dir,
        consumed_at=1700000000,
    )
    markers = list(nonce_dir.glob("*.json"))
    assert len(markers) == 1
    receipt = json.loads(markers[0].read_text(encoding="utf-8"))
    assert receipt["schema"] == "hummbl_bus.principal_nonce.v1"
    assert receipt["principal"] == "operator"
    assert receipt["request_id"] == "req-1"

    # Reuse must fail
    with pytest.raises(PermissionError, match="already been consumed"):
        _consume_nonce(
            nonce="unique-nonce-value-1234",
            principal="operator",
            request_id="req-1",
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
    with pytest.raises(PermissionError, match="authorized human principal"):
        verify_principal_proof(
            proof,
            sender="codex",
            recipient="all",
            msg_type="DECISION",
            message="test",
            request_id="req-1",
            nonce_dir=tmp_path,
        )


def test_verify_principal_proof_rejects_wrong_audience(tmp_path: Path) -> None:
    proof = {
        "v": 1,
        "principal": "operator",
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
        )


def test_verify_principal_proof_rejects_expired_proof(tmp_path: Path) -> None:
    proof = {
        "v": 1,
        "principal": "operator",
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
            now=1700000100,
        )


def test_principal_authorizes_checks_all_fields() -> None:
    vp = VerifiedPrincipal(
        "operator",
        "codex",
        DEFAULT_AUDIENCE,
        "req-1",
        "nonce-1234567890abcdef",
        "all",
        "DECISION",
        _message_digest("test"),
        CANONICAL_BUS_ID,
        _guard=_CONSTRUCTOR_GUARD,
    )
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
