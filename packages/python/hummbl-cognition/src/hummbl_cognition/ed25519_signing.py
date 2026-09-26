# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
"""Ed25519 asymmetric signing for Cognitive Ledger entries (Option A interop).

Complements the existing HMAC-SHA256 ``signature`` field (symmetric,
BUS_SIGNING_SECRET) with a per-agent asymmetric signature: the signer can be
identified and verified by anyone holding the public key, without sharing a
secret. This is the field-level shape external standards (MS AGT verifiable
receipts, IETF SCITT) use — ``signer_key_id`` parallels ``signerKeyId`` /
protected-header ``issuer``.

Opt-in by key presence: if ``<ledger_dir>/keys/<slug>-<fp16>.key.pem`` exists
and ``cryptography`` is importable, ``post_entry`` attaches ``ed25519_sig`` and
``signer_key_id``. Without a key or the package, writes proceed unchanged.

Key files (rotation-safe naming — fingerprint embedded):
    private: keys/<slug>-<fp16>.key.pem   (PKCS8, chmod 600)
    public:  keys/<slug>-<fp16>.pub.pem   (SPKI)
    pointer: keys/<slug>.latest           (fp16 of the active signing key)

``signer_key_id`` = ``<slug>:<fp16>`` where slug is the agent name reduced to
``[a-zA-Z0-9_-]`` and fp16 is the first 16 hex of sha256(raw public key).

Signed payload: canonical JSON of the entry dict minus ``signature``,
``ed25519_sig``, and ``signer_key_id`` (sorted keys, compact separators) —
the same canonical form ``to_jsonl()`` produces, so the Ed25519 layer is
independent of the HMAC layer and verifiable from the ledger line alone.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import warnings
from pathlib import Path
from typing import Any

_SIGN_FIELDS = ("signature", "ed25519_sig", "signer_key_id")


def _crypto():
    """Return cryptography primitives or None when the extra isn't installed."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )

        return serialization, Ed25519PrivateKey, Ed25519PublicKey
    except ImportError:
        return None


def available() -> bool:
    """True when the ``cryptography`` optional dependency is importable."""
    return _crypto() is not None


def slugify_agent(agent: str) -> str:
    """Reduce an agent identifier to a filesystem-safe key slug."""
    return re.sub(r"[^a-zA-Z0-9_-]", "-", agent).strip("-") or "agent"


def fingerprint(pub_raw: bytes) -> str:
    """First 16 hex chars of the public key's SHA-256 — the fp16 key suffix."""
    return hashlib.sha256(pub_raw).hexdigest()[:16]


def keys_dir(ledger_path: Path) -> Path:
    """Key directory: ``<ledger_dir>/keys/`` (gitignored with state/)."""
    return Path(ledger_path).parent / "keys"


def canonical_bytes(entry_dict: dict[str, Any]) -> bytes:
    """Canonical signing payload: sorted-keys compact JSON minus all signature
    fields. Same canonical form as ``LedgerEntry.to_jsonl()``."""
    stripped = {k: v for k, v in entry_dict.items() if k not in _SIGN_FIELDS}
    return json.dumps(
        stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def keygen(agent: str, ledger_path: Path) -> tuple[str, Path, Path]:
    """Generate an Ed25519 keypair for *agent* under the ledger's keys/ dir.

    Returns (signer_key_id, private_path, public_path).
    """
    crypto = _crypto()
    if crypto is None:
        raise RuntimeError(
            "ed25519 signing requires the 'cryptography' package "
            "(pip install 'hummbl-cognition[primitives]' or cryptography>=42)"
        )
    serialization, Ed25519PrivateKey, _ = crypto

    slug = slugify_agent(agent)
    priv = Ed25519PrivateKey.generate()
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    fp16 = fingerprint(pub_raw)
    key_id = f"{slug}:{fp16}"

    kdir = keys_dir(ledger_path)
    kdir.mkdir(parents=True, exist_ok=True)
    priv_path = kdir / f"{slug}-{fp16}.key.pem"
    pub_path = kdir / f"{slug}-{fp16}.pub.pem"

    # Atomic restrictive creation: write to a 0600 temp file then rename into
    # place, so no window exposes a loosely-permissioned private key.
    fd, tmp_name = tempfile.mkstemp(dir=kdir, prefix=".tmp-key-", suffix=".pem")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(
                priv.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
        os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_name, priv_path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    # Verify final permissions are owner-only where POSIX mode bits are
    # authoritative. On Windows, NT ACLs govern instead — mode bits always
    # read permissive (0o666) and real restriction comes from directory ACLs,
    # so the check is skipped rather than warning spuriously.
    if os.name == "posix":
        try:
            mode = stat.S_IMODE(priv_path.stat().st_mode)
            if mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
                warnings.warn(
                    f"private key {priv_path} is group/world-accessible (mode "
                    f"{oct(mode)}); restrict permissions manually"
                )
        except OSError:
            pass

    pub_path.write_bytes(
        priv.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
    # Rotation pointer: the latest keygen'd key signs new entries. Older
    # <slug>-<fp16> files remain for verifying historical signer_key_ids.
    (kdir / f"{slug}.latest").write_text(fp16, encoding="utf-8")
    return key_id, priv_path, pub_path


def _private_key_path(agent: str, ledger_path: Path) -> Path | None:
    """Private key file for the agent's slug, or None.

    Prefers the ``<slug>.latest`` pointer written by ``keygen`` (explicit
    rotation semantics); falls back to the newest matching file by mtime for
    key dirs that predate the pointer convention.
    """
    slug = slugify_agent(agent)
    kdir = keys_dir(ledger_path)
    if not kdir.is_dir():
        return None
    pointer = kdir / f"{slug}.latest"
    if pointer.is_file():
        fp16 = pointer.read_text(encoding="utf-8").strip()
        pointed = kdir / f"{slug}-{fp16}.key.pem"
        if pointed.is_file():
            return pointed
    matches = sorted(
        kdir.glob(f"{slug}-*.key.pem"),
        key=lambda p: (p.stat().st_mtime, p.name),
    )
    return matches[-1] if matches else None


_SIGNER_KEY_ID_RE = re.compile(r"^[A-Za-z0-9_-]+:[a-f0-9]{16}$")


def _public_key_path(signer_key_id: str, ledger_path: Path) -> Path | None:
    """Resolve a signer_key_id to its pubkey file inside the keys dir.

    Grammar-checked before any path join — a malformed or traversal-shaped
    id (path separators, extra colons, '..') yields None, never a path.
    """
    if not _SIGNER_KEY_ID_RE.match(signer_key_id):
        return None
    slug, _, fp16 = signer_key_id.partition(":")
    kdir = keys_dir(ledger_path)
    path = (kdir / f"{slug}-{fp16}.pub.pem").resolve()
    # Defense in depth: resolved path must stay inside the keys dir.
    if path.parent != kdir.resolve():
        return None
    return path if path.is_file() else None


def maybe_sign(
    entry_dict: dict[str, Any], agent: str, ledger_path: Path
) -> dict[str, Any]:
    """Attach ``ed25519_sig`` + ``signer_key_id`` when a key exists.

    Silent no-op without ``cryptography`` or a private key — unsigned writes
    remain legal; signing is opt-in by key presence.
    """
    crypto = _crypto()
    if crypto is None:
        return entry_dict
    priv_path = _private_key_path(agent, ledger_path)
    if priv_path is None:
        return entry_dict

    serialization, Ed25519PrivateKey, _ = crypto
    priv = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    fp16 = fingerprint(pub_raw)
    payload = canonical_bytes(entry_dict)
    sig_hex = priv.sign(payload).hex()
    out = dict(entry_dict)
    out["ed25519_sig"] = sig_hex
    out["signer_key_id"] = f"{slugify_agent(agent)}:{fp16}"
    return out


def verify(entry_dict: dict[str, Any], ledger_path: Path) -> tuple[bool, str]:
    """Verify an entry's ``ed25519_sig`` against its ``signer_key_id`` pubkey.

    Returns (ok, detail). detail explains failures: missing fields, missing
    pubkey, key-id/fingerprint mismatch, or signature invalid.
    """
    sig = entry_dict.get("ed25519_sig")
    key_id = entry_dict.get("signer_key_id")
    if not sig or not key_id:
        return False, "no ed25519_sig/signer_key_id"
    crypto = _crypto()
    if crypto is None:
        return False, "cryptography not installed"

    pub_path = _public_key_path(key_id, ledger_path)
    if pub_path is None:
        return False, f"public key not found for {key_id!r}"

    serialization, _, _ = crypto
    pub = serialization.load_pem_public_key(pub_path.read_bytes())
    pub_raw = pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    _, _, fp16 = key_id.partition(":")
    if fingerprint(pub_raw) != fp16:
        return False, f"public key fingerprint does not match key id {key_id!r}"

    try:
        pub.verify(bytes.fromhex(sig), canonical_bytes(entry_dict))
    except Exception:
        return False, "signature invalid"
    return True, "ok"
