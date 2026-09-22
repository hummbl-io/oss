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

#!/usr/bin/env python3
"""
Kill Switch Core - Emergency Halt System.

Thin wrapper re-exporting from hummbl-governance. The canonical implementation
lives in hummbl_governance.kill_switch. This module preserves the
founder_mode.services.kill_switch_core import path and adds founder-mode
specific features (OpenClaw export, singleton, feedback_store in critical tasks).

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from hummbl_governance.kill_switch import (
    KillSwitch,
    KillSwitchEngagedError,
    KillSwitchEvent,
    KillSwitchMode,
    KillSwitchTamperError,
)

logger = logging.getLogger(__name__)


class KillSwitchCore(KillSwitch):
    """Founder-mode kill switch -- inherits from hummbl_governance.KillSwitch."""

    CRITICAL_TASKS: frozenset[str] = frozenset([
        "safety_monitoring",
        "data_persistence",
        "audit_logging",
        "kill_switch_itself",
        "cost_tracking",
        "feedback_store",
    ])

    def __init__(self, state_dir: Path | None = None, require_hmac: bool = True):
        super().__init__(
            state_dir=state_dir,
            require_hmac=require_hmac,
            critical_tasks=self.CRITICAL_TASKS,
        )

    @staticmethod
    def _get_signing_secret() -> bytes | None:
        secret = os.environ.get("DCT_SECRET")
        if secret:
            return secret.encode("utf-8")
        return None

    @staticmethod
    def _compute_state_signature(data: dict[str, Any], secret: bytes) -> str:
        return KillSwitch._compute_signature(data, secret)

    @staticmethod
    def _verify_state_signature(data: dict[str, Any], signature: str, secret: bytes) -> bool:
        expected = KillSwitchCore._compute_state_signature(data, secret)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def load_from_file(cls, state_dir: Path, require_hmac: bool = True) -> KillSwitchCore:
        state_file = state_dir / "kill_switch_state.json"
        ks = cls(state_dir=state_dir, require_hmac=require_hmac)
        if not state_file.exists():
            return ks
        try:
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)
            secret = cls._get_signing_secret()
            signature = data.pop("signature", None)
            if secret and signature:
                if not cls._verify_state_signature(data, signature, secret):
                    logger.error("Kill switch state has INVALID HMAC signature")
                    if require_hmac:
                        raise KillSwitchTamperError("Kill switch state verification failed - tampering suspected")
                    return ks
            elif require_hmac:
                logger.error("Kill switch state lacks required HMAC signature")
                raise KillSwitchTamperError("Kill switch state missing mandatory HMAC signature")
            else:
                logger.warning("Kill switch state has no signature (legacy mode)")
            mode_str = data.get("mode", "DISENGAGED")
            ks._mode = KillSwitchMode[mode_str]
            if ks._mode != KillSwitchMode.DISENGAGED:
                event = KillSwitchEvent(
                    timestamp=data.get("engaged_at", datetime.now(timezone.utc).isoformat()),
                    mode=ks._mode,
                    reason=data.get("reason", "Restored from file"),
                    triggered_by=data.get("triggered_by", "system"),
                    affected_tasks=0,
                )
                ks._history.append(event)
        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.error("Kill switch state file corrupt: %s", e)
            if require_hmac:
                raise KillSwitchTamperError(f"Kill switch state file corrupt: {e}")
        return ks

    def _export_state_file(self, event: KillSwitchEvent) -> None:
        export_path = Path.home() / ".openclaw" / "workspace" / ".kill_switch_state"
        try:
            if not export_path.parent.exists():
                return
            data = json.dumps({
                "mode": self._mode.name,
                "engaged": self._mode != KillSwitchMode.DISENGAGED,
                "reason": event.reason,
                "triggered_by": event.triggered_by,
                "timestamp": event.timestamp,
            }, indent=2)
            export_path.write_text(data, encoding="utf-8")
            export_path.chmod(0o600)
        except OSError:
            pass

    def _notify(self, event: KillSwitchEvent) -> None:
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception:
                logger.debug("Kill switch subscriber callback failed", exc_info=True)
                continue
        self._export_state_file(event)

    def _persist(self) -> None:
        if self._state_dir is None:
            return
        state_file = self._state_dir / "kill_switch_state.json"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        last_event = self._history[-1] if self._history else None
        data = {
            "mode": self._mode.name,
            "engaged_at": last_event.timestamp if last_event else None,
            "reason": last_event.reason if last_event else None,
            "triggered_by": last_event.triggered_by if last_event else None,
        }
        secret = self._get_signing_secret()
        if secret:
            data["signature"] = self._compute_state_signature(
                {k: v for k, v in data.items() if k != "signature"}, secret
            )
        elif self._require_hmac:
            logger.error("DCT_SECRET not set but require_hmac=True")
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            state_file.chmod(0o600)
        except OSError:
            pass

    def check_task_allowed(self, task_type: str) -> Dict[str, Any]:
        is_critical = task_type in self.CRITICAL_TASKS
        with self._lock:
            current_mode = self._mode
        if current_mode == KillSwitchMode.DISENGAGED:
            return {"allowed": True, "action": "allow"}
        if current_mode == KillSwitchMode.HALT_NONCRITICAL:
            if is_critical:
                return {"allowed": True, "action": "allow", "note": "critical task exempted"}
            return {"allowed": False, "action": "queue", "reason": f"Kill switch engaged ({current_mode.name}): {task_type} queued"}
        if current_mode in (KillSwitchMode.HALT_ALL, KillSwitchMode.EMERGENCY):
            if is_critical and current_mode == KillSwitchMode.HALT_ALL:
                return {"allowed": True, "action": "allow", "note": "critical only"}
            return {"allowed": False, "action": "block", "reason": f"Kill switch engaged ({current_mode.name}): {task_type} blocked"}
        return {"allowed": False, "action": "block", "reason": "Unknown kill switch state"}


_global_kill_switch: KillSwitchCore | None = None


def _default_state_dir() -> Path:
    """Return the canonical runtime state directory for this checkout."""
    override = os.environ.get("FOUNDER_MODE_KILL_SWITCH_STATE_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "state"


def get_kill_switch_core(state_dir: Path | None = None) -> KillSwitchCore:
    global _global_kill_switch
    if _global_kill_switch is None:
        if state_dir is None:
            state_dir = _default_state_dir()
        _global_kill_switch = KillSwitchCore.load_from_file(state_dir)
    return _global_kill_switch


def reset_kill_switch_core() -> None:
    global _global_kill_switch
    _global_kill_switch = KillSwitchCore()


__all__ = [
    "KillSwitchCore",
    "KillSwitchEngagedError",
    "KillSwitchEvent",
    "KillSwitchMode",
    "KillSwitchTamperError",
    "get_kill_switch_core",
    "reset_kill_switch_core",
]
