# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
# SPDX-License-Identifier: Apache-2.0
"""Tests for Ed25519 asymmetric ledger signing (ed25519_signing module).

Skipped when the optional 'cryptography' dependency is absent — signing is
opt-in by key presence and the package must remain stdlib-functional.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hummbl_cognition import ed25519_signing  # noqa: E402
from hummbl_cognition.ledger_writer import post_entry, validate_integrity  # noqa: E402
from hummbl_cognition.models import LedgerEntry, compute_content_hash  # noqa: E402

pytestmark = pytest.mark.skipif(
    not ed25519_signing.available(), reason="cryptography not installed"
)


def _entry(agent: str = "devin") -> LedgerEntry:
    return LedgerEntry(
        id="clp-0123456789ab",
        timestamp="2026-09-26T12:00:00Z",
        agent=agent,
        vendor="anthropic",
        model="swe-2-max",
        type="discovery",
        scope="project",
        content="test entry for ed25519 signing",
        content_hash=compute_content_hash(
            agent=agent,
            vendor="anthropic",
            model="swe-2-max",
            entry_type="discovery",
            scope="project",
            content="test entry for ed25519 signing",
        ),
    )


def test_keygen_and_signer_key_id(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    key_id, priv, pub = ed25519_signing.keygen("devin", ledger)
    assert key_id.startswith("devin:")
    assert len(key_id.split(":")[1]) == 16
    assert priv.is_file() and pub.is_file()
    assert priv.name.endswith(".key.pem") and pub.name.endswith(".pub.pem")


def test_maybe_sign_no_key_is_noop(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    d = {"id": "clp-0123456789ab", "agent": "devin"}
    out = ed25519_signing.maybe_sign(d, "devin", ledger)
    assert out is d or "ed25519_sig" not in out


def test_post_entry_signs_when_key_present(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    written = post_entry(_entry(), ledger_path=ledger)
    assert written.ed25519_sig is not None
    assert len(written.ed25519_sig) == 128
    assert written.signer_key_id is not None
    assert written.signer_key_id.startswith("devin:")


def test_post_entry_unsigned_when_no_key(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    written = post_entry(_entry(), ledger_path=ledger)
    assert written.ed25519_sig is None
    assert written.signer_key_id is None


def test_verify_roundtrip(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
    ok, detail = ed25519_signing.verify(json.loads(line), ledger)
    assert ok, detail


def test_verify_detects_tamper(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
    d = json.loads(line)
    d["content"] = "tampered content"
    ok, detail = ed25519_signing.verify(d, ledger)
    assert not ok


def test_validate_integrity_accepts_signed(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    valid, errors = validate_integrity(ledger_path=ledger)
    assert errors == []
    assert valid == 1


def test_validate_integrity_flags_forged_sig(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
    d = json.loads(line)
    d["ed25519_sig"] = "0" * 128
    ledger.write_text(json.dumps(d) + "\n", encoding="utf-8")
    valid, errors = validate_integrity(ledger_path=ledger)
    assert valid == 0
    assert any("ed25519" in e for e in errors)


def test_chain_continuity_with_signed_entries(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    e2 = _entry()
    e2 = LedgerEntry.from_dict({**e2.to_dict(), "id": "clp-0123456789cd"})
    post_entry(e2, ledger_path=ledger)
    valid, errors = validate_integrity(ledger_path=ledger)
    assert errors == []
    assert valid == 2


def test_verify_rejects_malformed_key_ids(tmp_path: Path) -> None:
    """Path-traversal and malformed signer_key_ids never reach the filesystem."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    d = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    for bad in (
        "..:aaaaaaaaaaaaaaaa",
        "../x:aaaaaaaaaaaaaaaa",
        "a/b:aaaaaaaaaaaaaaaa",
        "a:b:c:aaaaaaaaaaaaaaaa",
        "devin:zzzzzzzzzzzzzzzz",
        "devin:aaaaaaaaaaaaaaaa:",  # extra colon
        ":aaaaaaaaaaaaaaaa",
        "devin:",  # missing fp16
        "devin:aaaaaaaaaaaaaaa",  # 15 hex
        "devin:AAAAAAAAAAAAAAAA",  # uppercase hex
        "devin",  # no colon
        "",
    ):
        d["signer_key_id"] = bad
        ok, detail = ed25519_signing.verify(d, ledger)
        assert not ok, f"malformed id {bad!r} verified: {detail}"


def test_verify_missing_public_key(tmp_path: Path) -> None:
    """A valid-shaped but absent pubkey fails closed, not open."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    d = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    d["signer_key_id"] = "ghost:0123456789abcdef"
    ok, detail = ed25519_signing.verify(d, ledger)
    assert not ok
    assert "not found" in detail


def test_verify_wrong_key_fails(tmp_path: Path) -> None:
    """Signature verifies only under its own key — cross-agent forgery fails."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    key_id_eve, _, _ = ed25519_signing.keygen("eve", ledger)
    post_entry(_entry(), ledger_path=ledger)
    d = json.loads(ledger.read_text(encoding="utf-8").strip().splitlines()[-1])
    # Sig was made by devin's key; claim it was eve's
    d["signer_key_id"] = key_id_eve
    ok, _ = ed25519_signing.verify(d, ledger)
    assert not ok


def test_model_rejects_malformed_signer_key_id() -> None:
    e = _entry()
    d = e.to_dict()
    d["ed25519_sig"] = "ab" * 64
    d["signer_key_id"] = "not a key id"
    with pytest.raises(ValueError):
        LedgerEntry.from_dict(d)
    d["signer_key_id"] = "devin:0123456789abcdef"  # valid shape
    LedgerEntry.from_dict(d)


def test_model_rejects_orphan_signer_key_id() -> None:
    d = _entry().to_dict()
    d["signer_key_id"] = "devin:0123456789abcdef"
    with pytest.raises(ValueError):
        LedgerEntry.from_dict(d)


def test_hmac_and_ed25519_coexist(tmp_path: Path) -> None:
    """Entry carrying both signatures passes integrity when keys are present."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    secret = b"unit-test-secret"
    post_entry(_entry(), ledger_path=ledger, secret=secret)
    valid, errors = validate_integrity(ledger_path=ledger, secret=secret)
    assert errors == []
    assert valid == 1
    line = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
    d = json.loads(line)
    assert d.get("signature") and d.get("ed25519_sig")


def test_key_rotation_preserves_verification(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    key_id_1, _, _ = ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger)
    key_id_2, _, _ = ed25519_signing.keygen("devin", ledger)
    assert key_id_1 != key_id_2
    e2 = LedgerEntry.from_dict({**_entry().to_dict(), "id": "clp-0123456789cd"})
    post_entry(e2, ledger_path=ledger)
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    ok1, _ = ed25519_signing.verify(json.loads(lines[0]), ledger)
    ok2, _ = ed25519_signing.verify(json.loads(lines[1]), ledger)
    assert ok1 and ok2
    assert json.loads(lines[0])["signer_key_id"] == key_id_1
    assert json.loads(lines[1])["signer_key_id"] == key_id_2
