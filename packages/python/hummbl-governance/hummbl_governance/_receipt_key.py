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
    """Restrict key-file access: POSIX chmod 0600, Windows icacls owner-only."""
    if os.name == "nt":
        username = os.environ.get("USERNAME") or os.environ.get("USER", "")
        if not username:
            return
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
        except (OSError, subprocess.CalledProcessError):
            pass
    else:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


@lru_cache(maxsize=1)
def resolve_receipt_key() -> bytes:
    """Return the HMAC key for GDPR receipt signing.

    Raises RuntimeError if no env var is set and the per-user key file cannot
    be created (fail-closed: never fall back to an ephemeral or published key).
    """
    env_key = os.environ.get(_ENV_VAR) or os.environ.get(_FLEET_ENV_VAR)
    if env_key:
        return env_key.encode("utf-8")

    key_path = _key_dir() / _KEY_FILENAME
    try:
        return key_path.read_bytes()
    except OSError:
        pass

    secret = secrets.token_bytes(32)
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        # codeql[py/clear-text-storage-sensitive-data]: a local HMAC key file
        # is cleartext by design; access is restricted by platform ACL
        # (chmod 0600 / icacls owner-only), same as kernel .kernel_secret.
        key_path.write_bytes(secret)
        _secure_secret_file(key_path)
    except OSError as exc:
        raise RuntimeError(
            "Cannot persist GDPR receipt HMAC key and neither "
            f"{_ENV_VAR} nor {_FLEET_ENV_VAR} is set. Set one of the env vars "
            "or ensure the key directory is writable. "
            f"Error: {exc}"
        ) from exc
    return secret
