# Copyright 2024-2026 HUMMBL
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

"""Shared receipt-signing key resolution for GDPR receipt modules.

Replaces the previously hardcoded, published HMAC key constant (issue #458):
receipt HMACs signed with a key shipped in public source carry no evidentiary
weight.  Key material is now operator-supplied or per-installation, never
in-source.

Resolution priority (mirrors ``kernel.receipt_engine``):

1. ``HUMMBL_GOVERNANCE_RECEIPT_KEY`` env var (module-specific, primary path)
2. ``HUMMBL_SIGNING_SECRET`` env var (fleet-wide fallback, same as kernel)
3. Persisted per-user key file (generated once, platform-protected)
4. Fail closed with RuntimeError if no key can be obtained or persisted

This module is not part of the public API.
"""

from __future__ import annotations

import os
import secrets
import subprocess
from functools import lru_cache
from pathlib import Path

_ENV_VAR = "HUMMBL_GOVERNANCE_RECEIPT_KEY"
_FLEET_ENV_VAR = "HUMMBL_SIGNING_SECRET"
_KEY_FILENAME = "receipt.key"


def _key_dir() -> Path:
    override = os.environ.get("HUMMBL_GOVERNANCE_KEY_DIR")
    if override:
        return Path(override)
    return Path.home() / ".hummbl-governance"


def _secure_secret_file(path: Path) -> None:
    """Restrict key-file access: POSIX chmod 0600, Windows icacls owner-only.

    Raises RuntimeError if the file cannot be restricted — an unsecured key
    file is worse than failing closed (issue #458 follow-up).
    """
    if os.name == "nt":
        username = os.environ.get("USERNAME") or os.environ.get("USER", "")
        if not username:
            raise RuntimeError(
                "Cannot determine current user to ACL the receipt key file"
            )
        try:
            subprocess.run(  # nosec B603 — icacls is a trusted Windows system utility; args are not user input
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{username}:F",
                ],
                check=True,
                capture_output=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                f"Failed to restrict receipt key file ACL: {exc}"
            ) from exc
    else:
        try:
            os.chmod(path, 0o600)
        except OSError as exc:
            raise RuntimeError(
                f"Failed to chmod 0600 receipt key file: {exc}"
            ) from exc


@lru_cache(maxsize=1)
def resolve_receipt_key() -> bytes:
    """Return the HMAC key for GDPR receipt signing.

    Raises RuntimeError if no env var is set and the per-user key file cannot
    be created or secured (fail-closed: never fall back to an ephemeral or
    published key).
    """
    env_key = os.environ.get(_ENV_VAR) or os.environ.get(_FLEET_ENV_VAR)
    if env_key:
        return env_key.encode("utf-8")

    key_path = _key_dir() / _KEY_FILENAME
    try:
        existing = key_path.read_bytes()
    except OSError:
        existing = b""
    if existing:
        return existing
    if key_path.exists():
        # Empty file: an interrupted first-run write left a useless key.
        # hmac accepts b"" silently, so regenerate rather than sign weakly.
        try:
            key_path.unlink()
        except OSError:
            pass

    secret = secrets.token_bytes(32)
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # O_EXCL makes first-run creation atomic: a concurrent process
            # either wins (we re-read its key) or loses (we keep ours).
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            # Lost a first-run race: adopt the winner's key, but fail closed
            # if it is empty rather than sign with a weak key.
            try:
                winner = key_path.read_bytes()
            except OSError as exc:
                raise RuntimeError(
                    f"Receipt key file appeared but cannot be read: {exc}"
                ) from exc
            if not winner:
                raise RuntimeError(
                    f"Receipt key file {key_path} is empty; remove it or set "
                    f"{_ENV_VAR}/{_FLEET_ENV_VAR}."
                )
            return winner
        # Restrict access before secret material touches disk. A local HMAC
        # key file is cleartext by design; access is restricted by platform
        # ACL (chmod 0600 / icacls owner-only), same as kernel
        # .kernel_secret and ~/.ssh keys.
        try:
            _secure_secret_file(key_path)
        except Exception:
            os.close(fd)
            key_path.unlink(missing_ok=True)
            raise
        with os.fdopen(fd, "wb") as fh:
            fh.write(secret)  # codeql[py/clear-text-storage-sensitive-data]
    except OSError as exc:
        raise RuntimeError(
            "Cannot persist GDPR receipt HMAC key and neither "
            f"{_ENV_VAR} nor {_FLEET_ENV_VAR} is set. Set one of the env vars "
            "or ensure the key directory is writable. "
            f"Error: {exc}"
        ) from exc
    return secret
