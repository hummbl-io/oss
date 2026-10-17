#!/usr/bin/env python3
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

"""Verify fail-closed GovernanceLifecycle authorization claims.

Claims checked (stdlib only, in-process, no network):

1. With a registry wired, an unregistered/unknown agent is denied
   (reason ``agent:unknown``).
2. A registered active agent is allowed.
3. Suspended and retired agents are denied (``agent:suspended`` /
   ``agent:retired``).
4. Decision ``checks`` include ``agent_status``, ``agent_trust``, and
   ``agent_registered``.
5. ``log_decision`` writes those identity checks into the audit record.
6. ``allow_unregistered_agents=True`` allows unknown agents but still
   denies suspended and retired agents.
7. No registry still skips the identity gate (nothing is wired).

Usage::

    python scripts/verify_claims.py

Exit code 0 if every claim holds; 1 otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[1]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from hummbl_governance.audit_log import AuditLog  # noqa: E402
from hummbl_governance.identity import AgentRegistry  # noqa: E402
from hummbl_governance.lifecycle import GovernanceLifecycle  # noqa: E402


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def _identity_registry() -> AgentRegistry:
    reg = AgentRegistry()
    reg.register_agent("worker-1", trust="medium", status="active")
    reg.register_agent("suspended-agent", trust="low", status="suspended")
    reg.register_agent("retired-agent", trust="low", status="retired")
    return reg


def verify_fail_closed(failures: list[str]) -> None:
    lifecycle = GovernanceLifecycle(registry=_identity_registry())

    unknown = lifecycle.authorize("ghost-agent", "database", "write")
    _require(unknown.allowed is False, "unknown agent must be denied", failures)
    _require(unknown.reason == "agent:unknown", f"unknown reason was {unknown.reason!r}", failures)
    _require(unknown.checks.get("agent_status") == "unknown", "unknown checks.agent_status", failures)
    _require(unknown.checks.get("agent_trust") == "unknown", "unknown checks.agent_trust", failures)
    _require(unknown.checks.get("agent_registered") is False, "unknown checks.agent_registered", failures)

    active = lifecycle.authorize("worker-1", "database", "write")
    _require(active.allowed is True, "active agent must be allowed", failures)
    _require(active.reason == "authorized", f"active reason was {active.reason!r}", failures)
    _require(active.checks.get("agent_status") == "active", "active checks.agent_status", failures)
    _require(active.checks.get("agent_trust") == "medium", "active checks.agent_trust", failures)
    _require(active.checks.get("agent_registered") is True, "active checks.agent_registered", failures)

    suspended = lifecycle.authorize("suspended-agent", "database", "write")
    _require(suspended.allowed is False, "suspended agent must be denied", failures)
    _require(suspended.reason == "agent:suspended", f"suspended reason was {suspended.reason!r}", failures)
    _require(suspended.checks.get("agent_registered") is True, "suspended checks.agent_registered", failures)

    retired = lifecycle.authorize("retired-agent", "database", "write")
    _require(retired.allowed is False, "retired agent must be denied", failures)
    _require(retired.reason == "agent:retired", f"retired reason was {retired.reason!r}", failures)
    _require(retired.checks.get("agent_registered") is True, "retired checks.agent_registered", failures)


def verify_opt_in(failures: list[str]) -> None:
    lifecycle = GovernanceLifecycle(
        registry=_identity_registry(),
        allow_unregistered_agents=True,
    )
    unknown = lifecycle.authorize("ghost-agent", "database", "write")
    _require(unknown.allowed is True, "opt-in must allow unknown agents", failures)
    _require(unknown.checks.get("agent_registered") is False, "opt-in unknown still unregistered", failures)

    override = GovernanceLifecycle(registry=_identity_registry()).authorize(
        "ghost-agent",
        "database",
        "write",
        allow_unregistered_agents=True,
    )
    _require(override.allowed is True, "per-call opt-in must allow unknown agents", failures)

    suspended = lifecycle.authorize("suspended-agent", "database", "write")
    _require(suspended.allowed is False, "opt-in must still deny suspended", failures)
    _require(suspended.reason == "agent:suspended", "opt-in suspended reason", failures)

    retired = lifecycle.authorize("retired-agent", "database", "write")
    _require(retired.allowed is False, "opt-in must still deny retired", failures)
    _require(retired.reason == "agent:retired", "opt-in retired reason", failures)


def verify_no_registry(failures: list[str]) -> None:
    decision = GovernanceLifecycle().authorize("ghost-agent", "database", "write")
    _require(decision.allowed is True, "no registry must skip identity gate", failures)
    _require("agent_registered" not in decision.checks, "no registry must omit identity checks", failures)


def verify_audit_record(failures: list[str]) -> None:
    tmpdir = tempfile.mkdtemp(prefix="hummbl-verify-claims-")
    audit = AuditLog(base_dir=tmpdir, require_signature=False)
    lifecycle = GovernanceLifecycle(audit_log=audit, registry=_identity_registry())
    decision = lifecycle.authorize("worker-1", "database", "write")
    lifecycle.log_decision("worker-1", "database", "write", decision)
    entries = list(audit.query_by_intent("lifecycle"))
    audit.close()
    _require(len(entries) == 1, "log_decision must write one audit entry", failures)
    if not entries:
        return
    checks = entries[0].tuple_data.get("checks") or {}
    _require(checks.get("agent_status") == "active", "audit agent_status", failures)
    _require(checks.get("agent_trust") == "medium", "audit agent_trust", failures)
    _require(checks.get("agent_registered") is True, "audit agent_registered", failures)

    deny_dir = tempfile.mkdtemp(prefix="hummbl-verify-claims-deny-")
    deny_audit = AuditLog(base_dir=deny_dir, require_signature=False)
    denier = GovernanceLifecycle(audit_log=deny_audit, registry=AgentRegistry())
    denied = denier.authorize("ghost", "database", "write")
    denier.log_decision("ghost", "database", "write", denied)
    deny_entries = list(deny_audit.query_by_intent("lifecycle"))
    deny_audit.close()
    _require(len(deny_entries) == 1, "denied log_decision must write one audit entry", failures)
    if deny_entries:
        data = deny_entries[0].tuple_data
        _require(data.get("allowed") is False, "audit allowed flag for unknown", failures)
        _require(data.get("reason") == "agent:unknown", "audit reason for unknown", failures)
        deny_checks = data.get("checks") or {}
        _require(deny_checks.get("agent_registered") is False, "audit agent_registered for unknown", failures)


def main() -> int:
    failures: list[str] = []
    verify_fail_closed(failures)
    verify_opt_in(failures)
    verify_no_registry(failures)
    verify_audit_record(failures)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("verify_claims: fail-closed authorization claims hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
