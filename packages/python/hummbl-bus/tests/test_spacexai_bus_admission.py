"""Admission-contract tests for the two probationary SpaceXAI bus senders.

These tests exercise the HTTP bridge boundary.  ``grok-bot`` and
``grok-build`` are protected workload identities: a general bridge credential
must never be enough to assert either sender, and an accepted request is
limited to the exact status envelope declared in fleet governance.
"""

from __future__ import annotations

import base64
import contextlib
import datetime as dt
import hashlib
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from hummbl_bus import bridge_server, bus_writer
from hummbl_bus.authority import CANONICAL_BUS_ID, DEFAULT_AUDIENCE
from hummbl_bus.bridge_server import BusBridgeHandler
from hummbl_bus.bus_writer import BusWriteResult
from hummbl_bus.replay_ledger import request_guard


SHARED_TOKEN = "test-shared-token"
SENDER_TOKENS = {
    "grok-bot": "test-grok-bot-token",
    "grok-build": "test-grok-build-token",
}
MESSAGE_PREFIXES = {
    "grok-bot": "host=unknown surface=cursor-grok-bot lane=",
    "grok-build": "host=anvil surface=terminal-grok-build lane=",
}
ORIGINS = {
    "grok-bot": ("unknown", "cursor-grok-bot"),
    "grok-build": ("anvil", "terminal-grok-build"),
}
REAL_LOOKUP_AUTH_EVENT_REQUEST = bridge_server._lookup_auth_event_request
REAL_RECORD_AUTH_EVENT = bridge_server._record_auth_event
PRINCIPAL_KEY_ID = "operator-ed25519-admission-v1"


def _principal_proof(
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
        "key_id": PRINCIPAL_KEY_ID,
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


def _configure_principal_verifier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Ed25519PrivateKey:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_file = tmp_path / "operator.pub"
    key_file.write_bytes(base64.b64encode(public_key))
    monkeypatch.setenv("BUS_PRINCIPAL_PUBLIC_KEY_FILE", str(key_file))
    monkeypatch.setenv("BUS_PRINCIPAL_ID", "reuben")
    monkeypatch.setenv("BUS_PRINCIPAL_KEY_ID", PRINCIPAL_KEY_ID)
    monkeypatch.setenv("BUS_PRINCIPAL_NONCE_DIR", str(tmp_path / "nonces"))
    monkeypatch.delenv("BUS_REMOTE_URL", raising=False)
    monkeypatch.delenv("BUS_SIGNING_SECRET", raising=False)
    return private_key


def _request_body(
    sender: str,
    *,
    recipient: str = "codex",
    msg_type: str = "STATUS",
    message: str | None = None,
    request_id: str | None = None,
) -> dict[str, object]:
    if message is None:
        message = f"{MESSAGE_PREFIXES[sender]}admission-test state=ok"
    if request_id is None:
        request_id = f"req:{sender}:admission:0001"
    return {
        "from": sender,
        "to": recipient,
        "type": msg_type,
        "message": message,
        "request_id": request_id,
        "origin_machine": ORIGINS[sender][0],
        "origin_surface": ORIGINS[sender][1],
    }


def _fake_write_result(**kwargs: object) -> BusWriteResult:
    message_sha256 = hashlib.sha256(
        str(kwargs["message"]).encode("utf-8")
    ).hexdigest()
    return BusWriteResult(
        bus_path=str(kwargs["bus_path"]),
        timestamp=str(kwargs.get("timestamp") or "2026-08-31T00:00:00Z"),
        sender=str(kwargs["from_id"]),
        recipient=str(kwargs["to_id"]),
        msg_type=str(kwargs["msg_type"]),
        authorized_content_sha256=message_sha256,
        persisted_message_sha256="2" * 64,
        row_sha256="3" * 64,
        verified_principal=None,
    )


def _delayed_fake_write_result(**kwargs: object) -> BusWriteResult:
    time.sleep(0.05)
    return _fake_write_result(**kwargs)


def _make_post_handler(
    *,
    body: dict[str, object] | str,
    token: str,
    client_id: str | None,
) -> BusBridgeHandler:
    encoded = (
        body.encode("utf-8")
        if isinstance(body, str)
        else json.dumps(body).encode("utf-8")
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Length": str(len(encoded)),
        "Content-Type": "application/json",
    }
    if client_id is not None:
        headers["X-Bridge-Client-ID"] = client_id

    handler = object.__new__(BusBridgeHandler)
    handler.path = "/bus"
    handler.headers = headers
    handler.rfile = io.BytesIO(encoded)
    handler.wfile = io.BytesIO()
    handler.client_address = ("127.0.0.1", 12345)
    handler._response_code = None
    handler._error = None

    def send_response(code: int, *_args: object, **_kwargs: object) -> None:
        handler._response_code = code

    def send_header(*_args: object, **_kwargs: object) -> None:
        return None

    def end_headers(*_args: object, **_kwargs: object) -> None:
        return None

    def send_error(
        code: int,
        message: str | None = None,
        *_args: object,
        **_kwargs: object,
    ) -> None:
        handler._response_code = code
        handler._error = message

    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = end_headers
    handler.send_error = send_error
    return handler


def _response_json(handler: BusBridgeHandler) -> dict[str, object]:
    raw = handler.wfile.getvalue()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _configure_token_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    sender_map_raw: str | None = None,
    sender_map: dict[str, str] | None = None,
) -> None:
    credentials = {"default": SHARED_TOKEN, **SENDER_TOKENS}
    credentials_file = tmp_path / "bridge_credentials.json"
    credentials_file.write_text(json.dumps(credentials), encoding="utf-8")

    monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
    monkeypatch.setenv("BUS_BRIDGE_TOKEN_FILE", str(credentials_file))

    if sender_map_raw is None and sender_map is None:
        sender_map = dict(SENDER_TOKENS)
    if sender_map_raw is not None or sender_map is not None:
        sender_tokens_file = tmp_path / "sender_tokens.json"
        sender_tokens_file.write_text(
            sender_map_raw if sender_map_raw is not None else json.dumps(sender_map),
            encoding="utf-8",
        )
        monkeypatch.setenv("BUS_SENDER_TOKENS_FILE", str(sender_tokens_file))
    else:
        monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)


@pytest.fixture(autouse=True)
def _isolate_bridge_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep handler tests away from the canonical bus, replay, and auth logs."""
    # Linux CI creates pytest fixtures under /tmp, outside the package's
    # production path-confinement roots. Admit only this test's isolated root;
    # do not weaken the production confinement policy.
    monkeypatch.setenv("BUS_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.delenv("BUS_BRIDGE_TOKEN", raising=False)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    monkeypatch.setattr(bridge_server, "_resolve_bus_path", lambda _value: tmp_path / "bus.tsv")
    monkeypatch.setattr(bridge_server, "_lookup_auth_event_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "_record_auth_event", lambda **_kwargs: True)
    monkeypatch.setattr(
        bridge_server,
        "request_guard",
        lambda _rid: contextlib.nullcontext(),
    )


@pytest.mark.parametrize("sender", sorted(SENDER_TOKENS))
@pytest.mark.parametrize("recipient", ["codex", "all"])
def test_exact_bound_status_envelope_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sender: str,
    recipient: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "record_request", lambda **kwargs: kwargs)

    handler = _make_post_handler(
        body=_request_body(sender, recipient=recipient),
        token=SENDER_TOKENS[sender],
        client_id=sender,
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 200, _response_json(handler)
    assert _response_json(handler).get("duplicate") is False
    post.assert_called_once()
    call = post.call_args.kwargs
    assert call["from_id"] == sender
    assert call["to_id"] == recipient
    assert call["msg_type"] == "STATUS"
    assert call["known_agent_ids"] == {sender}


def test_bridge_correlation_is_receipt_metadata_not_writer_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    records: dict[str, dict[str, object]] = {}
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", records.get)

    def remember_request(**kwargs: object) -> dict[str, object]:
        record = dict(kwargs)
        records[str(kwargs["request_id"])] = record
        return record

    monkeypatch.setattr(bridge_server, "record_request", remember_request)
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "STATUS",
            "message": "host=anvil surface=desktop-codex lane=test state=ok",
            "request_id": "req:codex:correlation:0001",
            "correlation_id": "corr:codex:0001",
            "origin_machine": "anvil",
            "origin_surface": "desktop-codex",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 200, payload
    assert payload.get("receipt_durable") is True
    assert post.call_args.kwargs["correlation_id"] is None
    record = records["req:codex:correlation:0001"]
    assert record["correlation_id"] == "corr:codex:0001"
    assert record["authorized_content_sha256"] == record["message_sha256"]


@pytest.mark.parametrize(
    "correlation_id",
    [
        "contains whitespace",
        "control:\x1b",
        "c" * 129,
    ],
)
def test_general_bridge_client_rejects_noncanonical_correlation_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    correlation_id: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    request_suffix = hashlib.sha256(correlation_id.encode("utf-8")).hexdigest()[:12]
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "STATUS",
            "message": "host=anvil surface=desktop-codex lane=test state=ok",
            "request_id": f"req:codex:bad-correlation:{request_suffix}",
            "correlation_id": correlation_id,
            "origin_machine": "anvil",
            "origin_surface": "desktop-codex",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 400, _response_json(handler)
    post.assert_not_called()


def test_privileged_bridge_request_rejects_separate_correlation_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "DECISION",
            "message": "host=anvil decision=test",
            "request_id": "req:codex:decision:correlation:0001",
            "correlation_id": "corr:codex:decision:0001",
            "origin_machine": "anvil",
            "origin_surface": "desktop-codex",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 403, payload
    assert "correlation" in str(payload.get("error", "")).lower()
    post.assert_not_called()


@pytest.mark.parametrize("earlier_invalid_field", ["timestamp", "bus_path"])
def test_restricted_correlation_denial_precedes_other_request_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    earlier_invalid_field: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    auth_events: list[dict[str, object]] = []
    monkeypatch.setattr(
        bridge_server,
        "_record_auth_event",
        lambda **kwargs: auth_events.append(dict(kwargs)) or True,
    )
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body("grok-build")
    body["correlation_id"] = "corr:grok-build:denied:0001"
    body[earlier_invalid_field] = (
        "not-a-timestamp"
        if earlier_invalid_field == "timestamp"
        else "C:/attacker/messages.tsv"
    )
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )

    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 403, payload
    assert payload.get("code") == "restricted_sender_acl_denied"
    assert auth_events
    assert all("correlation_id" not in event for event in auth_events)
    post.assert_not_called()


def test_privileged_correlation_denial_precedes_client_bus_path_rejection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    auth_events: list[dict[str, object]] = []
    monkeypatch.setattr(
        bridge_server,
        "_record_auth_event",
        lambda **kwargs: auth_events.append(dict(kwargs)) or True,
    )
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "DIRECTIVE",
            "message": "host=anvil directive=test",
            "request_id": "req:codex:directive:correlation:0001",
            "correlation_id": "corr:codex:directive:0001",
            "origin_machine": "anvil",
            "origin_surface": "desktop-codex",
            "bus_path": "C:/attacker/messages.tsv",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 403, payload
    assert payload.get("code") == "privileged_correlation_metadata_denied"
    assert auth_events
    assert all("correlation_id" not in event for event in auth_events)
    post.assert_not_called()


def test_auth_log_success_does_not_mask_invalid_receipt_linkage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    def fail_after_claim(**kwargs: object) -> dict[str, object]:
        if kwargs.get("state") == "pending":
            return dict(kwargs)
        raise OSError("ledger unavailable")

    monkeypatch.setattr(bridge_server, "record_request", fail_after_claim)
    monkeypatch.setattr(bridge_server, "_record_auth_event", lambda **_kwargs: True)

    def mismatched_write_result(**kwargs: object) -> BusWriteResult:
        result = _fake_write_result(**kwargs)
        return BusWriteResult(
            bus_path=result.bus_path,
            timestamp=result.timestamp,
            sender=result.sender,
            recipient=result.recipient,
            msg_type=result.msg_type,
            authorized_content_sha256="1" * 64,
            persisted_message_sha256=result.persisted_message_sha256,
            row_sha256=result.row_sha256,
            verified_principal=None,
        )

    monkeypatch.setattr(bridge_server, "post_message", mismatched_write_result)
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "STATUS",
            "message": "host=anvil surface=desktop-codex lane=test state=ok",
            "request_id": "req:codex:invalid-linkage:0001",
            "origin_machine": "anvil",
            "origin_surface": "desktop-codex",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 200, payload
    assert payload.get("auth_recorded") is True
    assert payload.get("receipt_durable") is False


GROK_BUILD_NONPRIVILEGED_TYPES = (
    "ACK",
    "BLOCKED",
    "PROPOSAL",
    "QUESTION",
    "SITREP",
    "STATUS",
    "WIP_END",
    "WIP_START",
)


@pytest.mark.parametrize("msg_type", GROK_BUILD_NONPRIVILEGED_TYPES)
@pytest.mark.parametrize("recipient", ["codex", "all"])
def test_grok_build_bound_envelope_accepts_operator_authorized_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    msg_type: str,
    recipient: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "record_request", lambda **kwargs: kwargs)

    handler = _make_post_handler(
        body=_request_body(
            "grok-build",
            recipient=recipient,
            msg_type=msg_type,
            request_id=f"req:grok-build:{msg_type.lower()}:0001",
        ),
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 200, _response_json(handler)
    post.assert_called_once()
    assert post.call_args.kwargs["msg_type"] == msg_type
    assert post.call_args.kwargs["from_id"] == "grok-build"
    assert post.call_args.kwargs["to_id"] == recipient


@pytest.mark.parametrize("msg_type", ["VETO", "APPROVE", "HANDOFF", "SKILL_INVOKE", "status"])
def test_grok_build_still_rejects_types_outside_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    msg_type: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    handler = _make_post_handler(
        body=_request_body("grok-build", msg_type=msg_type),
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert _response_json(handler).get("code") == "restricted_sender_acl_denied"
    post.assert_not_called()


@pytest.mark.parametrize("msg_type", ["DECISION", "DIRECTIVE"])
def test_grok_build_privileged_types_are_operationally_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    msg_type: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "record_request", lambda **kwargs: kwargs)

    handler = _make_post_handler(
        body=_request_body(
            "grok-build",
            msg_type=msg_type,
            request_id=f"req:grok-build:{msg_type.lower()}:noproof:0001",
        ),
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    payload = _response_json(handler)
    assert handler._response_code == 403, payload
    assert payload.get("code") == "restricted_sender_acl_denied"
    assert "operationally disabled" in str(payload.get("error", "")).lower()


def test_protected_ids_are_not_globally_activated_in_direct_writer() -> None:
    assert "grok-bot" not in bus_writer._RESERVED_AGENT_IDS
    assert "grok-build" not in bus_writer._RESERVED_AGENT_IDS


def test_raw_request_rejects_duplicate_sender_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    raw = (
        '{"from":"grok-bot","from":"codex","to":"codex",'
        '"type":"STATUS","message":"host=anvil state=spoof",'
        '"request_id":"req:duplicate:sender:0001"}'
    )
    handler = _make_post_handler(
        body=raw,
        token=SHARED_TOKEN,
        client_id="default",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 400, _response_json(handler)
    assert "duplicate key" in str(_response_json(handler).get("error", ""))
    post.assert_not_called()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("origin_machine", None),
        ("origin_machine", "delta"),
        ("origin_surface", None),
        ("origin_surface", "desktop-codex"),
    ],
)
def test_restricted_origin_claims_must_match_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    field: str,
    value: str | None,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body(
        "grok-build",
        request_id=f"req:grok-build:origin:{field}:0001",
    )
    if value is None:
        body.pop(field)
    else:
        body[field] = value
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert _response_json(handler).get("code") == "restricted_sender_acl_denied"
    post.assert_not_called()


@pytest.mark.parametrize(
    "correlation_id",
    ["corr:caller-supplied:0001", "x host=evil", "corr\x1bspoof"],
)
def test_restricted_sender_rejects_caller_supplied_correlation_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    correlation_id: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    body = _request_body(
        "grok-build",
        request_id="req:grok-build:correlation-denied:0001",
    )
    body["correlation_id"] = correlation_id
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert _response_json(handler).get("code") == "restricted_sender_acl_denied"
    post.assert_not_called()


@pytest.mark.parametrize(
    "contradiction",
    ["host=delta", "surface=desktop-codex", "lane=other"],
)
def test_restricted_message_rejects_contradictory_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    contradiction: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body(
        "grok-build",
        message=(
            f"{MESSAGE_PREFIXES['grok-build']}admission-test "
            f"state=ok {contradiction}"
        ),
        request_id="req:grok-build:contradictory-provenance:0001",
    )
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert "exactly one" in str(_response_json(handler).get("error", ""))
    post.assert_not_called()


@pytest.mark.parametrize(
    ("token", "client_id", "sender_map", "payload_sender"),
    [
        (SHARED_TOKEN, "default", SENDER_TOKENS, "grok-bot"),
        (
            SENDER_TOKENS["grok-bot"],
            "grok-bot",
            {"grok-build": SENDER_TOKENS["grok-build"]},
            "grok-bot",
        ),
        (
            SENDER_TOKENS["grok-bot"],
            "grok-bot",
            SENDER_TOKENS,
            "grok-build",
        ),
    ],
    ids=["shared-token", "unmapped-token", "cross-token-spoof"],
)
def test_unbound_or_inconsistent_credentials_cannot_assert_protected_sender(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    token: str,
    client_id: str,
    sender_map: dict[str, str],
    payload_sender: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path, sender_map=sender_map)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    handler = _make_post_handler(
        body=_request_body(payload_sender),
        token=token,
        client_id=client_id,
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize(
    "sender_map",
    [
        {"grok-build": SENDER_TOKENS["grok-build"]},
        {
            "codex": SENDER_TOKENS["grok-bot"],
            "grok-build": SENDER_TOKENS["grok-build"],
        },
    ],
    ids=["protected-client-unmapped", "protected-client-misbound"],
)
def test_protected_client_credential_cannot_escape_through_legacy_sender(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sender_map: dict[str, str],
) -> None:
    _configure_token_files(monkeypatch, tmp_path, sender_map=sender_map)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)

    body = _request_body("grok-bot")
    body["from"] = "codex"
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert _response_json(handler).get("code") == "restricted_sender_binding_denied"
    post.assert_not_called()


def test_protected_credential_rejects_mismatched_client_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)

    handler = _make_post_handler(
        body=_request_body("grok-bot"),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 401, _response_json(handler)
    post.assert_not_called()


def test_protected_sender_requires_bearer_scheme(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)

    handler = _make_post_handler(
        body=_request_body("grok-bot"),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    handler.headers["Authorization"] = SENDER_TOKENS["grok-bot"]
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    assert _response_json(handler).get("code") == "restricted_sender_binding_denied"
    post.assert_not_called()


@pytest.mark.parametrize("declaration", ["missing", "dual"])
def test_protected_sender_must_be_declared_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    declaration: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    body = _request_body("grok-bot")
    if declaration == "missing":
        body.pop("from")
    else:
        body["sender"] = "grok-bot"
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize(
    "sender_map_raw",
    [
        "",
        "{}",
        "{",
        '{"grok-bot":"first","grok-bot":"second"}',
        '{"grok-bot":"same-token","grok-build":"same-token"}',
    ],
    ids=["empty-file", "empty-object", "malformed", "duplicate-key", "duplicate-token"],
)
def test_invalid_sender_token_map_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sender_map_raw: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path, sender_map_raw=sender_map_raw)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)

    handler = _make_post_handler(
        body=_request_body("grok-bot"),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 503, _response_json(handler)
    assert _response_json(handler).get("code") == "sender_binding_configuration_error"
    post.assert_not_called()


@pytest.mark.parametrize(
    ("canonical_sender", "variant"),
    [
        ("grok-bot", "Grok Bot"),
        ("grok-bot", "GROK-BOT"),
        ("grok-bot", " grok-bot "),
        ("grok-bot", "grok_bot"),
        ("grok-bot", "grok-bot (cloud)"),
        ("grok-bot", "hummbl-grok-bot"),
        ("grok-bot", "cursor-grok-bot"),
        ("grok-build", "GROK-BUILD"),
        ("grok-build", " grok-build "),
        ("grok-build", "grok-build (anvil)"),
    ],
)
def test_sender_variants_are_rejected_instead_of_canonicalized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    canonical_sender: str,
    variant: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    body = _request_body(canonical_sender)
    body["from"] = variant
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS[canonical_sender],
        client_id=canonical_sender,
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize("msg_type", ["DECISION", "DIRECTIVE", "APPROVE", "VETO", "status"])
def test_grok_bot_cannot_use_privileged_or_noncanonical_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    msg_type: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    handler = _make_post_handler(
        body=_request_body("grok-bot", msg_type=msg_type),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize("recipient", ["operator", "grok-build", " codex "])
def test_protected_sender_cannot_address_any_other_recipient(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    recipient: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    handler = _make_post_handler(
        body=_request_body("grok-build", recipient=recipient),
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize(
    ("sender", "message"),
    [
        ("grok-bot", "prefix host=unknown surface=cursor-grok-bot lane=test"),
        ("grok-bot", "host=anvil surface=cursor-grok-bot lane=test"),
        ("grok-bot", "host=unknown surface=desktop-grok-bot lane=test"),
        ("grok-bot", "host=unknown surface=cursor-grok-bot lane="),
        ("grok-build", "host=unknown surface=terminal-grok-build lane=test"),
        ("grok-build", "host=anvil surface=terminal-grok-build lane=<bad>"),
        ("grok-build", "host=anvil surface=terminal-grok-build"),
    ],
)
def test_host_surface_and_lane_prefix_must_be_exact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sender: str,
    message: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    handler = _make_post_handler(
        body=_request_body(sender, message=message),
        token=SENDER_TOKENS[sender],
        client_id=sender,
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


@pytest.mark.parametrize("request_id", [None, "short", "bad request id", 42])
def test_protected_sender_requires_canonical_request_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    request_id: object,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)

    body = _request_body("grok-bot")
    if request_id is None:
        body.pop("request_id")
    else:
        body["request_id"] = request_id
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    post.assert_not_called()


def test_exact_request_replay_is_duplicate_without_second_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    records: dict[str, dict[str, object]] = {}
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", records.get)

    def remember_request(**kwargs: object) -> dict[str, object]:
        record = dict(kwargs)
        records[str(kwargs["request_id"])] = record
        return record

    monkeypatch.setattr(bridge_server, "record_request", remember_request)
    body = _request_body("grok-bot")

    first = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    second = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(first)
    BusBridgeHandler.do_POST(second)

    assert first._response_code == 200, _response_json(first)
    assert second._response_code == 200, _response_json(second)
    assert _response_json(second).get("duplicate") is True
    assert _response_json(second).get("receipt_durable") is True
    post.assert_called_once()


def test_hashless_receipt_fails_closed_as_unverifiable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(
        bridge_server,
        "lookup_request",
        lambda request_id: {
            "request_id": request_id,
            "operation": "remote_write",
            "accepted_at": "2026-08-30T23:59:00Z",
        },
    )

    handler = _make_post_handler(
        body=_request_body("grok-bot"),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 409, _response_json(handler)
    assert (
        _response_json(handler).get("code")
        == "idempotency_record_unverifiable"
    )
    post.assert_not_called()


def test_incomplete_v2_replay_requires_reconciliation_without_second_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body("grok-build")
    stale_timestamp = "2026-01-01T00:00:00Z"
    body["timestamp"] = stale_timestamp
    request_sha256, message_sha256 = bridge_server._request_fingerprint(
        request_id=str(body["request_id"]),
        client_id="grok-build",
        sender="grok-build",
        recipient=str(body["to"]),
        msg_type=str(body["type"]),
        message=str(body["message"]),
        timestamp=stale_timestamp,
        correlation_id=None,
        origin_machine=str(body["origin_machine"]),
        origin_surface=str(body["origin_surface"]),
    )
    monkeypatch.setattr(
        bridge_server,
        "lookup_request",
        lambda request_id: {
            "request_id": request_id,
            "request_schema": bridge_server.REMOTE_WRITE_REQUEST_SCHEMA,
            "request_sha256": request_sha256,
            "message_sha256": message_sha256,
            "accepted_at": stale_timestamp,
        },
    )

    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 409, _response_json(handler)
    assert (
        _response_json(handler).get("code")
        == "idempotency_reconciliation_required"
    )
    assert _response_json(handler).get("receipt_durable") is False
    post.assert_not_called()


def test_v1_replay_fingerprint_requires_reconciliation_without_reappend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    body = _request_body(
        "grok-build",
        request_id="req:grok-build:v1-replay:0001",
    )
    legacy_sha256 = bridge_server._legacy_request_fingerprint(
        request_id=str(body["request_id"]),
        client_id="grok-build",
        sender="grok-build",
        recipient=str(body["to"]),
        msg_type=str(body["type"]),
        message=str(body["message"]),
        timestamp=None,
        correlation_id=None,
        origin_machine=str(body["origin_machine"]),
    )
    monkeypatch.setattr(
        bridge_server,
        "lookup_request",
        lambda request_id: {
            "request_id": request_id,
            "state": "accepted",
            "request_schema": "hummbl_bus.remote_write.v1",
            "request_sha256": legacy_sha256,
            "message_sha256": hashlib.sha256(
                str(body["message"]).encode("utf-8")
            ).hexdigest(),
            "accepted_at": "2026-08-30T23:59:00Z",
        },
    )
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )

    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 409, _response_json(handler)
    assert (
        _response_json(handler).get("code")
        == "idempotency_reconciliation_required"
    )
    assert _response_json(handler).get("receipt_durable") is False
    post.assert_not_called()


@pytest.mark.parametrize(
    ("changed_message", "expected_status"),
    [(False, 200), (True, 409)],
    ids=["matching-auth-receipt", "altered-auth-receipt"],
)
def test_accepted_auth_log_fallback_binds_request_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    changed_message: bool,
    expected_status: int,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setenv("BUS_AUTH_EVENT_LOG", str(tmp_path / "auth-events.jsonl"))
    monkeypatch.setattr(
        bridge_server,
        "_lookup_auth_event_request",
        REAL_LOOKUP_AUTH_EVENT_REQUEST,
    )
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)

    original = _request_body("grok-bot")
    request_sha256, message_sha256 = bridge_server._request_fingerprint(
        request_id=str(original["request_id"]),
        client_id="grok-bot",
        sender="grok-bot",
        recipient=str(original["to"]),
        msg_type=str(original["type"]),
        message=str(original["message"]),
        timestamp=None,
        correlation_id=None,
        origin_machine=str(original["origin_machine"]),
        origin_surface=str(original["origin_surface"]),
    )
    assert REAL_RECORD_AUTH_EVENT(
        outcome="accepted",
        client_ip="127.0.0.1",
        sender="grok-bot",
        recipient=str(original["to"]),
        msg_type=str(original["type"]),
        request_id=str(original["request_id"]),
        client_id="grok-bot",
        request_schema=bridge_server.REMOTE_WRITE_REQUEST_SCHEMA,
        request_sha256=request_sha256,
        message_sha256=message_sha256,
        bus_path=str(tmp_path / "messages.tsv"),
        written_timestamp="2026-08-31T00:00:00Z",
        authorized_content_sha256=message_sha256,
        persisted_message_sha256="2" * 64,
        row_sha256="3" * 64,
    )
    retry = dict(original)
    if changed_message:
        retry["message"] = (
            f"{MESSAGE_PREFIXES['grok-bot']}admission-test state=altered"
        )
    handler = _make_post_handler(
        body=retry,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == expected_status, _response_json(handler)
    if changed_message:
        assert _response_json(handler).get("code") == "idempotency_key_conflict"
    else:
        assert _response_json(handler).get("duplicate") is True
    post.assert_not_called()


def test_duplicate_only_auth_event_is_not_an_authoritative_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setenv("BUS_AUTH_EVENT_LOG", str(tmp_path / "auth-events.jsonl"))
    monkeypatch.setattr(
        bridge_server,
        "_lookup_auth_event_request",
        REAL_LOOKUP_AUTH_EVENT_REQUEST,
    )
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "record_request", lambda **kwargs: kwargs)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body("grok-build")
    request_sha256, message_sha256 = bridge_server._request_fingerprint(
        request_id=str(body["request_id"]),
        client_id="grok-build",
        sender="grok-build",
        recipient=str(body["to"]),
        msg_type=str(body["type"]),
        message=str(body["message"]),
        timestamp=None,
        correlation_id=None,
        origin_machine=str(body["origin_machine"]),
        origin_surface=str(body["origin_surface"]),
    )
    assert REAL_RECORD_AUTH_EVENT(
        outcome="duplicate",
        client_ip="127.0.0.1",
        sender="grok-build",
        recipient=str(body["to"]),
        msg_type=str(body["type"]),
        request_id=str(body["request_id"]),
        client_id="grok-build",
        request_schema=bridge_server.REMOTE_WRITE_REQUEST_SCHEMA,
        request_sha256=request_sha256,
        message_sha256=message_sha256,
    )
    handler = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 200, _response_json(handler)
    assert _response_json(handler).get("duplicate") is False
    post.assert_called_once()


def test_concurrent_auth_events_are_all_persisted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    auth_log = tmp_path / "auth-events.jsonl"
    monkeypatch.setenv("BUS_AUTH_EVENT_LOG", str(auth_log))

    def record_event(index: int) -> bool:
        return REAL_RECORD_AUTH_EVENT(
            outcome="rejected",
            client_ip="127.0.0.1",
            sender="grok-bot",
            recipient="codex",
            msg_type="STATUS",
            request_id=f"req:grok-bot:thread:{index:04d}",
            client_id="grok-bot",
            reason="concurrency-test",
        )

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(record_event, range(16)))

    assert results == [True] * 16
    events = [
        json.loads(line)
        for line in auth_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 16
    assert len({event["request_id"] for event in events}) == 16


@pytest.mark.parametrize(
    ("changed_message", "expected_status"),
    [(False, 200), (True, 409)],
    ids=["exact-privileged-retry", "changed-privileged-retry"],
)
def test_privileged_receipt_replay_precedes_one_time_proof_verification(
    monkeypatch: pytest.MonkeyPatch,
    changed_message: bool,
    expected_status: int,
) -> None:
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", SHARED_TOKEN)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    body: dict[str, object] = {
        "from": "codex",
        "to": "all",
        "type": "DECISION",
        "message": "host=anvil decision=approved",
        "request_id": "req:codex:decision:0001",
    }
    request_sha256, message_sha256 = bridge_server._request_fingerprint(
        request_id=str(body["request_id"]),
        client_id="default",
        sender="codex",
        recipient="all",
        msg_type="DECISION",
        message=str(body["message"]),
        timestamp=None,
        correlation_id=None,
        origin_machine=None,
    )
    receipt = {
        "request_id": body["request_id"],
        "operation": "remote_write",
        "state": "accepted",
        "sender": "codex",
        "recipient": "all",
        "type": "DECISION",
        "request_schema": bridge_server.REMOTE_WRITE_REQUEST_SCHEMA,
        "request_sha256": request_sha256,
        "message_sha256": message_sha256,
        "bus_path": "/canonical/messages.tsv",
        "written_timestamp": "2026-08-31T00:00:00Z",
        "authorized_content_sha256": message_sha256,
        "persisted_message_sha256": "2" * 64,
        "row_sha256": "3" * 64,
        "authority": {
            "schema": "hummbl_bus.verified_principal.v1",
            "principal": "reuben",
            "key_id": "operator-ed25519-v1",
            "key_sha256": "4" * 64,
            "request_id": body["request_id"],
            "sender": "codex",
            "recipient": "all",
            "type": "DECISION",
            "message_sha256": message_sha256,
            "nonce_sha256": "5" * 64,
            "audience": "hummbl-bus",
            "bus_id": "hummbl-bus",
            "issued_at": 1700000000,
            "expires_at": 1700000060,
            "proof_sha256": "6" * 64,
        },
    }
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: receipt)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    if changed_message:
        body["message"] = "host=anvil decision=changed"
    handler = _make_post_handler(
        body=body,
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == expected_status, _response_json(handler)
    if changed_message:
        assert _response_json(handler).get("code") == "idempotency_key_conflict"
    else:
        assert _response_json(handler).get("duplicate") is True
    post.assert_not_called()


def test_rejected_privileged_write_does_not_persist_pending_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", SHARED_TOKEN)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    record = mock.Mock()
    monkeypatch.setattr(bridge_server, "record_request", record)
    monkeypatch.setattr(
        bridge_server,
        "post_message",
        mock.Mock(side_effect=PermissionError("principal proof required")),
    )
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": "DECISION",
            "message": "host=anvil decision=pending",
            "request_id": "req:codex:decision:pending:0001",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 403, _response_json(handler)
    record.assert_not_called()


@pytest.mark.parametrize("msg_type", ["STATUS", "DECISION"])
def test_legacy_hashless_receipt_is_unverifiable_for_every_request_type(
    monkeypatch: pytest.MonkeyPatch,
    msg_type: str,
) -> None:
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", SHARED_TOKEN)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    monkeypatch.setattr(
        bridge_server,
        "lookup_request",
        lambda request_id: {
            "request_id": request_id,
            "operation": "remote_write",
            "accepted_at": "2026-08-30T23:59:00Z",
        },
    )
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    handler = _make_post_handler(
        body={
            "from": "codex",
            "to": "all",
            "type": msg_type,
            "message": "host=anvil state=legacy-retry",
            "request_id": f"req:codex:{msg_type.lower()}:legacy:0001",
        },
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 409, _response_json(handler)
    assert (
        _response_json(handler).get("code")
        == "idempotency_record_unverifiable"
    )
    post.assert_not_called()


@pytest.mark.parametrize(
    "changed_field",
    [
        "to",
        "type",
        "message",
        "timestamp",
        "origin_machine",
        "origin_surface",
    ],
)
def test_request_id_reuse_with_changed_request_conflicts_without_second_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    changed_field: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    records: dict[str, dict[str, object]] = {}
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", records.get)

    def remember_request(**kwargs: object) -> dict[str, object]:
        record = dict(kwargs)
        records[str(kwargs["request_id"])] = record
        return record

    monkeypatch.setattr(bridge_server, "record_request", remember_request)
    accepted = _request_body("grok-bot")
    changed = dict(accepted)
    replacements = {
        "to": "all",
        "type": "SITREP",
        "message": f"{MESSAGE_PREFIXES['grok-bot']}admission-test state=changed",
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "origin_machine": "anvil",
        "origin_surface": "desktop-codex",
    }
    changed[changed_field] = replacements[changed_field]

    first = _make_post_handler(
        body=accepted,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    second = _make_post_handler(
        body=changed,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(first)
    BusBridgeHandler.do_POST(second)

    assert first._response_code == 200, _response_json(first)
    assert second._response_code == 409, _response_json(second)
    assert _response_json(second).get("duplicate") is not True
    post.assert_called_once()


def test_request_id_reuse_by_different_bound_client_conflicts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    records: dict[str, dict[str, object]] = {}
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", records.get)

    def remember_request(**kwargs: object) -> dict[str, object]:
        record = dict(kwargs)
        records[str(kwargs["request_id"])] = record
        return record

    monkeypatch.setattr(bridge_server, "record_request", remember_request)
    request_id = "req:spacexai:cross-client:0001"
    first = _make_post_handler(
        body=_request_body("grok-bot", request_id=request_id),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    second = _make_post_handler(
        body=_request_body("grok-build", request_id=request_id),
        token=SENDER_TOKENS["grok-build"],
        client_id="grok-build",
    )
    BusBridgeHandler.do_POST(first)
    BusBridgeHandler.do_POST(second)

    assert first._response_code == 200, _response_json(first)
    assert second._response_code == 409, _response_json(second)
    assert _response_json(second).get("code") == "idempotency_key_conflict"
    post.assert_called_once()


def test_concurrent_exact_replay_appends_at_most_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setenv("BUS_REPLAY_LEDGER_PATH", str(tmp_path / "replay.jsonl"))
    monkeypatch.setattr(bridge_server, "request_guard", request_guard)

    post = mock.Mock(side_effect=_delayed_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    body = _request_body("grok-build")
    handlers = [
        _make_post_handler(
            body=body,
            token=SENDER_TOKENS["grok-build"],
            client_id="grok-build",
        )
        for _ in range(2)
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(BusBridgeHandler.do_POST, handlers))

    assert sorted(handler._response_code for handler in handlers) == [200, 200]
    assert sorted(
        bool(_response_json(handler).get("duplicate")) for handler in handlers
    ) == [False, True]
    post.assert_called_once()


def test_crash_after_durable_claim_fails_retry_closed_without_second_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    monkeypatch.setenv("BUS_REPLAY_LEDGER_PATH", str(tmp_path / "replay.jsonl"))
    monkeypatch.setattr(bridge_server, "request_guard", request_guard)
    bus_rows = tmp_path / "simulated-bus-rows.txt"

    def append_then_crash(**_kwargs: object) -> None:
        with bus_rows.open("a", encoding="utf-8") as stream:
            stream.write("accepted-row\n")
        raise SystemExit("simulated process crash")

    monkeypatch.setattr(bridge_server, "post_message", append_then_crash)
    body = _request_body("grok-bot")
    first = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    with pytest.raises(SystemExit, match="simulated process crash"):
        BusBridgeHandler.do_POST(first)

    retry_post = mock.Mock()
    monkeypatch.setattr(bridge_server, "post_message", retry_post)
    retry = _make_post_handler(
        body=body,
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(retry)

    assert retry._response_code == 409, _response_json(retry)
    assert (
        _response_json(retry).get("code")
        == "idempotency_reconciliation_required"
    )
    assert bus_rows.read_text(encoding="utf-8").splitlines() == ["accepted-row"]
    retry_post.assert_not_called()


def test_privileged_crash_after_append_fails_retry_closed_without_second_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", SHARED_TOKEN)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    monkeypatch.setenv("BUS_REPLAY_LEDGER_PATH", str(tmp_path / "replay.jsonl"))
    monkeypatch.setattr(bridge_server, "request_guard", request_guard)
    private_key = _configure_principal_verifier(monkeypatch, tmp_path)
    real_post_message = bus_writer.post_message
    request_id = "req:codex:decision:crash:0001"
    message = "host=anvil decision=crash-window"

    first_body: dict[str, object] = {
        "from": "codex",
        "to": "all",
        "type": "DECISION",
        "message": message,
        "request_id": request_id,
        "principal_proof": _principal_proof(
            private_key,
            message=message,
            request_id=request_id,
            nonce="privileged-crash-proof-nonce-0001",
        ),
    }

    def append_then_crash(**kwargs: object) -> BusWriteResult:
        result = real_post_message(**kwargs)
        assert isinstance(result, BusWriteResult)
        raise SystemExit("simulated process crash after privileged append")

    monkeypatch.setattr(bridge_server, "post_message", append_then_crash)
    first = _make_post_handler(
        body=first_body,
        token=SHARED_TOKEN,
        client_id="default",
    )
    with pytest.raises(SystemExit, match="after privileged append"):
        BusBridgeHandler.do_POST(first)

    pending = bridge_server.lookup_request(request_id)
    assert pending is not None
    assert pending["state"] == "pending"
    assert pending["request_schema"] == bridge_server.REMOTE_WRITE_REQUEST_SCHEMA
    assert pending["authority"]["request_id"] == request_id
    assert pending["authority"]["message_sha256"] == hashlib.sha256(
        message.encode("utf-8")
    ).hexdigest()

    retry_body = dict(first_body)
    retry_body["principal_proof"] = _principal_proof(
        private_key,
        message=message,
        request_id=request_id,
        nonce="privileged-crash-proof-nonce-0002",
    )
    retry_post = mock.Mock(side_effect=real_post_message)
    monkeypatch.setattr(bridge_server, "post_message", retry_post)
    retry = _make_post_handler(
        body=retry_body,
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(retry)

    assert retry._response_code == 409, _response_json(retry)
    assert (
        _response_json(retry).get("code")
        == "idempotency_reconciliation_required"
    )
    assert len((tmp_path / "bus.tsv").read_text(encoding="utf-8").splitlines()) == 1
    retry_post.assert_not_called()


def test_privileged_claim_failure_burns_proof_before_any_append(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("BUS_BRIDGE_TOKEN", SHARED_TOKEN)
    monkeypatch.delenv("BUS_BRIDGE_TOKEN_FILE", raising=False)
    monkeypatch.delenv("BUS_SENDER_TOKENS_FILE", raising=False)
    monkeypatch.setenv("BUS_REPLAY_LEDGER_PATH", str(tmp_path / "replay.jsonl"))
    private_key = _configure_principal_verifier(monkeypatch, tmp_path)
    request_id = "req:codex:decision:claim-failure:0001"
    message = "host=anvil decision=claim-failure"
    proof = _principal_proof(
        private_key,
        message=message,
        request_id=request_id,
        nonce="privileged-claim-failure-nonce-0001",
    )
    body: dict[str, object] = {
        "from": "codex",
        "to": "all",
        "type": "DECISION",
        "message": message,
        "request_id": request_id,
        "principal_proof": proof,
    }
    monkeypatch.setattr(
        bridge_server,
        "record_request",
        mock.Mock(side_effect=OSError("simulated replay ledger failure")),
    )

    first = _make_post_handler(
        body=body,
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(first)

    assert first._response_code == 503, _response_json(first)
    assert _response_json(first).get("code") == "idempotency_claim_unavailable"
    assert not (tmp_path / "bus.tsv").exists()

    retry = _make_post_handler(
        body=body,
        token=SHARED_TOKEN,
        client_id="default",
    )
    BusBridgeHandler.do_POST(retry)

    assert retry._response_code == 403, _response_json(retry)
    assert "nonce" in str(_response_json(retry).get("error", "")).lower()
    assert not (tmp_path / "bus.tsv").exists()

GROK_BOT_COORDINATION_TYPES = ('ACK', 'BLOCKED', 'HANDOFF', 'MILESTONE', 'PROPOSAL', 'QUESTION', 'SITREP', 'SKILL_INVOKE', 'STATUS', 'WIP_END', 'WIP_START')

@pytest.mark.parametrize("msg_type", GROK_BOT_COORDINATION_TYPES)
@pytest.mark.parametrize("recipient", ["codex", "all"])
def test_grok_bot_bound_envelope_accepts_operator_authorized_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    msg_type: str,
    recipient: str,
) -> None:
    _configure_token_files(monkeypatch, tmp_path)
    post = mock.Mock(side_effect=_fake_write_result)
    monkeypatch.setattr(bridge_server, "post_message", post)
    monkeypatch.setattr(bridge_server, "lookup_request", lambda _rid: None)
    monkeypatch.setattr(bridge_server, "record_request", lambda **kwargs: kwargs)

    handler = _make_post_handler(
        body=_request_body(
            "grok-bot",
            recipient=recipient,
            msg_type=msg_type,
            request_id=f"req:grok-bot:{msg_type.lower()}:0001",
        ),
        token=SENDER_TOKENS["grok-bot"],
        client_id="grok-bot",
    )
    BusBridgeHandler.do_POST(handler)

    assert handler._response_code == 200, _response_json(handler)
    post.assert_called_once()
    assert post.call_args.kwargs["msg_type"] == msg_type
    assert post.call_args.kwargs["from_id"] == "grok-bot"
    assert post.call_args.kwargs["to_id"] == recipient
