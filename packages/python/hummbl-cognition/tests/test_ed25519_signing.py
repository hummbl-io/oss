# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
# SPDX-License-Identifier: Apache-2.0
"""Tests for Ed25519 asymmetric ledger signing (ed25519_signing module).

Skipped when the optional 'cryptography' dependency is absent — signing is
opt-in by key presence and the package must remain stdlib-functional.
"""

import json
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hummbl_cognition import ed25519_signing  # noqa: E402
from hummbl_cognition.ledger_writer import (  # noqa: E402
    post_entry,
    read_entries,
    validate_integrity,
)
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


def test_keygen_posix_private_mode_0600(tmp_path: Path) -> None:
    if os.name != "posix":
        pytest.skip("POSIX mode bits only authoritative on POSIX")
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    priv = next((tmp_path / "keys").glob("devin-*.key.pem"))
    assert stat.S_IMODE(priv.stat().st_mode) == 0o600


def test_keygen_leaves_no_temp_files(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    for p in (tmp_path / "keys").iterdir():
        assert not p.name.startswith("tmp")
        assert p.name.endswith((".key.pem", ".pub.pem", ".latest"))


def test_cmd_keygen_never_emits_private_path(tmp_path: Path, capsys) -> None:
    from hummbl_cognition import __main__ as cli

    args = SimpleNamespace(agent="devin", ledger=str(tmp_path / "ledger.jsonl"))
    assert cli.cmd_keygen(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out) == {"signer_key_id", "public_key"}
    assert "private" not in json.dumps(out).lower()
    assert "key.pem" not in out["public_key"] or out["public_key"].endswith(".pub.pem")


def test_canonical_payload_parity_across_sig_layers(tmp_path: Path) -> None:
    """Ed25519 and HMAC sign the same bytes: LedgerEntry.to_jsonl() minus sigs.

    Independently reconstructs the HMAC payload (a LedgerEntry serialized via
    to_jsonl() with signature fields absent) and asserts the Ed25519
    canonical_bytes() output is byte-identical — if the two canonical forms
    ever drift, one signature layer verifies a different byte string.
    """
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    post_entry(_entry(), ledger_path=ledger, secret=b"shared-secret")
    raw = json.loads(ledger.read_text(encoding="utf-8").strip())
    # Independent construction: rebuild the unsigned LedgerEntry and emit
    # its canonical JSONL — the exact bytes the HMAC layer signs/verifies.
    unsigned = LedgerEntry.from_dict(
        {k: v for k, v in raw.items() if k not in ed25519_signing._SIGN_FIELDS}
    )
    hmac_payload = unsigned.to_jsonl().encode("utf-8")
    assert ed25519_signing.canonical_bytes(raw) == hmac_payload
    # And the HMAC actually verifies over those bytes.
    import hashlib
    import hmac as _hmac

    expected = _hmac.new(b"shared-secret", hmac_payload, hashlib.sha256).hexdigest()
    assert expected == raw["signature"]


def test_mixed_ledger_unsigned_hmac_signed(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    # 1: unsigned entry written before any key exists
    post_entry(_entry(), ledger_path=ledger)
    # 2: HMAC-only entry
    e2 = LedgerEntry.from_dict({**_entry().to_dict(), "id": "clp-000000000002"})
    post_entry(e2, ledger_path=ledger, secret=b"shared-secret")
    # 3: Ed25519 (+HMAC) entry after keygen
    ed25519_signing.keygen("devin", ledger)
    e3 = LedgerEntry.from_dict({**_entry().to_dict(), "id": "clp-000000000003"})
    post_entry(e3, ledger_path=ledger, secret=b"shared-secret")

    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    dicts = [json.loads(x) for x in lines]
    assert dicts[0].get("ed25519_sig") is None
    assert dicts[1].get("ed25519_sig") is None and dicts[1].get("signature")
    assert dicts[2].get("ed25519_sig") and dicts[2].get("signature")
    # All three parse back into entries without error.
    entries = read_entries(ledger_path=ledger)
    assert len(entries) == 3
    # Only the third verifies asymmetrically; the other two are unsigned
    # for that layer and must not fail closed.
    ok3, _ = ed25519_signing.verify(dicts[2], ledger)
    assert ok3
    # Whole-ledger integrity: unsigned + HMAC-only + signed all validate
    # together under the same secret.
    valid, errors = validate_integrity(ledger_path=ledger, secret=b"shared-secret")
    assert errors == []
    assert valid == 3


def test_latest_pointer_malformed_contents_ignored(tmp_path: Path) -> None:
    """A poisoned .latest pointer is ignored; fallback mtime selection applies."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    kdir = tmp_path / "keys"
    pointer = kdir / "devin.latest"
    for bad in ("../../escape", "nothex!!", "", "g" * 16, "A" * 16):
        pointer.write_text(bad, encoding="utf-8")
        p = ed25519_signing._private_key_path("devin", ledger)
        # Falls back to the real key file (only one exists), never escapes.
        assert p is not None and p.parent == kdir.resolve()
        assert p.name.endswith(".key.pem")


def test_latest_pointer_symlink_escape_rejected(tmp_path: Path) -> None:
    """A .latest symlink pointing outside keys/ must not be followed."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    kdir = tmp_path / "keys"
    outside = tmp_path / "outside.latest"
    outside.write_text("0123456789abcdef", encoding="utf-8")
    pointer = kdir / "devin.latest"
    pointer.unlink()
    try:
        pointer.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable (Windows without privilege)")
    p = ed25519_signing._private_key_path("devin", ledger)
    assert p is not None and p.parent == kdir.resolve()


def test_fallback_key_symlink_escape_rejected(tmp_path: Path) -> None:
    """A slug-*.key.pem symlink to an outside file never becomes the signer."""
    ledger = tmp_path / "ledger.jsonl"
    ed25519_signing.keygen("devin", ledger)
    kdir = tmp_path / "keys"
    (kdir / "devin.latest").unlink()  # force fallback path
    outside = tmp_path / "evil.key.pem"
    outside.write_text("not a key", encoding="utf-8")
    decoy = kdir / "devin-ffffffffffffffff.key.pem"
    try:
        decoy.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable (Windows without privilege)")
    p = ed25519_signing._private_key_path("devin", ledger)
    assert p is not None
    assert p.parent == kdir.resolve()
    assert p.name != decoy.name


def test_crypto_absent_hmac_and_unsigned_still_work(
    tmp_path: Path, monkeypatch
) -> None:
    """Simulates cryptography being unavailable: writes stay unsigned and
    HMAC verification is unaffected — the core never hard-depends on the
    optional extra."""
    monkeypatch.setattr(ed25519_signing, "_crypto", lambda: None)
    ledger = tmp_path / "ledger.jsonl"
    # Unsigned write is a no-op for the Ed25519 layer.
    post_entry(_entry(), ledger_path=ledger)
    e2 = LedgerEntry.from_dict({**_entry().to_dict(), "id": "clp-000000000004"})
    post_entry(e2, ledger_path=ledger, secret=b"shared-secret")
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert all(json.loads(x).get("ed25519_sig") is None for x in lines)
    # maybe_sign explicitly no-ops.
    d = json.loads(lines[1])
    assert ed25519_signing.maybe_sign(dict(d), "devin", ledger) == d
    # verify() reports the missing dependency rather than raising.
    d2 = dict(d)
    d2["ed25519_sig"] = "ab" * 64
    d2["signer_key_id"] = "devin:0123456789abcdef"
    ok, detail = ed25519_signing.verify(d2, ledger)
    assert not ok and "cryptography" in detail
    # HMAC layer still validates the signed entry.
    valid, errors = validate_integrity(ledger_path=ledger, secret=b"shared-secret")
    assert errors == []
    assert valid == 2


def _link(src: Path, dst: Path) -> None:
    try:
        src.symlink_to(dst)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable (Windows without privilege)")


def test_keygen_rejects_symlinked_keys_dir(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    real = tmp_path / "elsewhere"
    real.mkdir()
    _link(tmp_path / "keys", real)
    with pytest.raises(OSError):
        ed25519_signing.keygen("devin", ledger)
    assert list(real.iterdir()) == []  # nothing written outside


def test_keygen_rejects_symlinked_destinations(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    kdir = tmp_path / "keys"
    kdir.mkdir()
    outside = tmp_path / "escape.txt"
    outside.write_text("must not be overwritten", encoding="utf-8")
    # Pre-plant a symlink at every destination keygen will write.
    _link(kdir / "devin-0000000000000000.pub.pem", outside)
    _link(kdir / "devin.latest", outside)
    with pytest.raises(OSError):
        ed25519_signing.keygen("devin", ledger)
    assert outside.read_text(encoding="utf-8") == "must not be overwritten"


def test_symlinked_keys_dir_blocks_signing_and_verification(
    tmp_path: Path,
) -> None:
    """Read-side mirror of keygen's guard: a symlinked keys/ dir is never
    followed — signing silently no-ops and verify fails closed."""
    ledger = tmp_path / "ledger.jsonl"
    real_keys = tmp_path / "attacker_keys"
    real_keys.mkdir()
    # Plant an attacker's key inside the redirect target.
    ed25519_signing.keygen("devin", tmp_path / "other" / "ledger.jsonl")
    other_kdir = tmp_path / "other" / "keys"
    for p in other_kdir.iterdir():
        (real_keys / p.name).write_bytes(p.read_bytes())
    _link(tmp_path / "keys", real_keys)

    # Signing: _private_key_path must not see through the symlink.
    assert ed25519_signing._private_key_path("devin", ledger) is None
    post_entry(_entry(), ledger_path=ledger)
    d = json.loads(ledger.read_text(encoding="utf-8").strip())
    assert d.get("ed25519_sig") is None  # stayed unsigned

    # Verification: _public_key_path must not resolve through it either.
    d["ed25519_sig"] = "ab" * 64
    d["signer_key_id"] = "devin:0123456789abcdef"
    ok, detail = ed25519_signing.verify(d, ledger)
    assert not ok and "not found" in detail
