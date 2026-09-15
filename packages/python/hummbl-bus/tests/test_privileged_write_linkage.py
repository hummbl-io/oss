from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from hummbl_bus.authority import (
    CANONICAL_BUS_ID,
    DEFAULT_AUDIENCE,
    PRIVILEGED_MESSAGE_SCHEMA,
    VERIFIED_PRINCIPAL_SCHEMA,
    VerifiedPrincipal,
)
from hummbl_bus.bus_writer import BusWriteResult, post_message


KEY_ID = "operator-ed25519-linkage-v1"


def _proof(
    private_key: Ed25519PrivateKey,
    *,
    message: str,
    request_id: str,
    nonce: str,
) -> dict[str, object]:
    now = int(time.time())
    unsigned: dict[str, object] = {
        "v": 1,
        "principal": "reuben",
        "audience": DEFAULT_AUDIENCE,
        "request_id": request_id,
        "iat": now,
        "exp": now + 60,
        "nonce": nonce,
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
        "bus_id": CANONICAL_BUS_ID,
        "key_id": KEY_ID,
    }
    canonical = json.dumps(
        unsigned,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    return {
        **unsigned,
        "sig": base64.b64encode(private_key.sign(canonical)).decode("ascii"),
    }


def _configure_verifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Ed25519PrivateKey, bytes]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_file = tmp_path / "operator.pub"
    key_file.write_bytes(base64.b64encode(public_key))
    monkeypatch.setenv("BUS_PRINCIPAL_PUBLIC_KEY_FILE", str(key_file))
    monkeypatch.setenv("BUS_PRINCIPAL_ID", "reuben")
    monkeypatch.setenv("BUS_PRINCIPAL_KEY_ID", KEY_ID)
    monkeypatch.setenv("BUS_PRINCIPAL_NONCE_DIR", str(tmp_path / "nonces"))
    monkeypatch.delenv("BUS_REMOTE_URL", raising=False)
    monkeypatch.delenv("BUS_SIGNING_SECRET", raising=False)
    return private_key, public_key


def test_privileged_row_embeds_proof_and_exact_hash_linkage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    private_key, public_key = _configure_verifier(monkeypatch, tmp_path)
    bus_path = tmp_path / "messages.tsv"
    message = "host=anvil lane=authority decision=approve"
    request_id = "req:codex:decision:linkage:0001"
    proof = _proof(
        private_key,
        message=message,
        request_id=request_id,
        nonce="privileged-linkage-nonce-0001",
    )

    result = post_message(
        bus_path=bus_path,
        from_id="codex",
        to_id="all",
        msg_type="decision",
        message=message,
        request_id=request_id,
        principal_proof=proof,
        validate=False,
    )

    assert isinstance(result, BusWriteResult)
    assert result.msg_type == "DECISION"
    assert result.authorized_content_sha256 == hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()
    row = bus_path.read_text(encoding="utf-8").rstrip("\n")
    timestamp, sender, recipient, msg_type, persisted_message = row.split("\t")
    assert (timestamp, sender, recipient, msg_type) == (
        result.timestamp,
        "codex",
        "all",
        "DECISION",
    )
    assert result.persisted_message_sha256 == hashlib.sha256(
        persisted_message.encode("utf-8")
    ).hexdigest()
    assert result.row_sha256 == hashlib.sha256(row.encode("utf-8")).hexdigest()

    envelope = json.loads(persisted_message)
    assert envelope["schema"] == PRIVILEGED_MESSAGE_SCHEMA
    assert envelope["content"] == message
    authority = envelope["authority"]
    assert authority["principal_proof"] == proof
    receipt = authority["receipt"]
    assert receipt["schema"] == VERIFIED_PRINCIPAL_SCHEMA
    assert receipt["request_id"] == request_id
    assert receipt["key_id"] == KEY_ID
    assert receipt["key_sha256"] == hashlib.sha256(public_key).hexdigest()
    canonical_proof = json.dumps(
        proof,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("ascii")
    assert receipt["proof_sha256"] == hashlib.sha256(canonical_proof).hexdigest()


def test_privileged_write_ahead_hook_runs_after_proof_before_append(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    private_key, _public_key = _configure_verifier(monkeypatch, tmp_path)
    bus_path = tmp_path / "messages.tsv"
    message = "host=anvil lane=authority decision=write-ahead"
    request_id = "req:codex:decision:write-ahead:0001"
    observed: list[VerifiedPrincipal] = []

    def claim(principal: VerifiedPrincipal) -> None:
        assert not bus_path.exists()
        observed.append(principal)

    result = post_message(
        bus_path=bus_path,
        from_id="codex",
        to_id="all",
        msg_type="DECISION",
        message=message,
        request_id=request_id,
        principal_proof=_proof(
            private_key,
            message=message,
            request_id=request_id,
            nonce="privileged-write-ahead-nonce-0001",
        ),
        before_privileged_append=claim,
        validate=False,
    )

    assert isinstance(result, BusWriteResult)
    assert len(observed) == 1
    assert observed[0] is result.verified_principal
    assert observed[0].request_id == request_id
    assert len(bus_path.read_text(encoding="utf-8").splitlines()) == 1


def test_nonprivileged_write_rejects_privileged_write_ahead_hook(
    tmp_path: Path,
) -> None:
    bus_path = tmp_path / "messages.tsv"

    with pytest.raises(ValueError, match="only valid for privileged writes"):
        post_message(
            bus_path=bus_path,
            from_id="codex",
            to_id="all",
            msg_type="STATUS",
            message="host=anvil status=ok",
            before_privileged_append=lambda _principal: None,
            validate=False,
        )

    assert not bus_path.exists()


def test_hmac_wrap_preserves_privileged_authority_envelope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    private_key, _public_key = _configure_verifier(monkeypatch, tmp_path)
    message = "host=anvil lane=authority decision=approve-hmac"
    request_id = "req:codex:decision:linkage:0002"
    bus_path = tmp_path / "messages.tsv"

    result = post_message(
        bus_path=bus_path,
        from_id="codex",
        to_id="all",
        msg_type="DECISION",
        message=message,
        request_id=request_id,
        principal_proof=_proof(
            private_key,
            message=message,
            request_id=request_id,
            nonce="privileged-linkage-nonce-0002",
        ),
        secret=b"x" * 32,
        validate=False,
    )

    assert isinstance(result, BusWriteResult)
    persisted_message = bus_path.read_text(encoding="utf-8").split("\t", 4)[4]
    signed_envelope = json.loads(persisted_message)
    privileged_envelope = json.loads(signed_envelope["c"])
    assert privileged_envelope["schema"] == PRIVILEGED_MESSAGE_SCHEMA
    assert privileged_envelope["authority"]["receipt"]["request_id"] == request_id


@pytest.mark.parametrize(
    ("extra", "error"),
    [
        ({"timestamp": "2026-08-31T00:00:00Z"}, "writer-generated timestamp"),
        ({"correlation_id": "corr-privileged-0001"}, "already be inside"),
    ],
)
def test_privileged_v1_rejects_unsigned_row_metadata(
    tmp_path: Path,
    extra: dict[str, str],
    error: str,
) -> None:
    with pytest.raises(PermissionError, match=error):
        post_message(
            bus_path=tmp_path / "messages.tsv",
            from_id="codex",
            to_id="all",
            msg_type="DECISION",
            message="host=anvil decision=approve",
            request_id="req:codex:decision:unsigned-meta:0001",
            principal_proof={"placeholder": True},
            validate=False,
            **extra,
        )

    assert not (tmp_path / "messages.tsv").exists()
