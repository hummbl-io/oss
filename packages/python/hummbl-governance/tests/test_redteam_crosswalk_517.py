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

"""Negative and bypass regression tests for hummbl-io/oss#517.

Each test class pins the current observable code-level behavior for one of the
seven historical red-team findings from PRIMITIVE_CRITICAL_ANALYSIS_2026-08-27.md
(crosswalk maintained in the private hummbl-io/hummbl-dev repo at docs/audits/PRIMITIVE_REDTEAM_CROSSWALK_2026-11-23.md).

When a finding is later remediated in code, the corresponding bypass test in
this file is expected to fail and be updated alongside the crosswalk status.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hummbl_governance import envelope_cryptosystem
from hummbl_governance.convergence_guard import ConvergentGoal, ConvergenceDetector
from hummbl_governance.envelope_cryptosystem import EnvelopeCryptosystem
from hummbl_governance.kernel.authority_engine import AuthorityEngine
from hummbl_governance.kernel.evidence_engine import EvidenceEngine
from hummbl_governance.kernel.identity_engine import IdentityEngine
from hummbl_governance.kernel.invariants import KernelPanic
from hummbl_governance.kernel.kernel import Kernel
from hummbl_governance.kernel.law_engine import LawEngine
from hummbl_governance.kernel.mutation_gate import MutationGate, MutationRequest
from hummbl_governance.kernel.receipt_engine import Receipt, ReceiptEngine

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Finding 1: Authority-engine natural-language parsing and authority bypass
# ---------------------------------------------------------------------------


class TestFinding1AuthorityEngineBypass:
    """Pins remaining structured-limit and legacy-charter bypasses in AuthorityEngine."""

    def test_structured_limit_without_class_keyword_is_ignored(self, tmp_path: Path) -> None:
        policy = {
            "mutation_classes": {
                "MEDIUM": {"examples": ["file_write"]},
            },
            "roles": {
                "worker": {
                    "trust_tier": "TRUSTED",
                    "can_authorize": ["MEDIUM"],
                    "scope": "assigned_repos",
                    "limits": [
                        "must not exceed 100 requests per minute",
                        "cannot authorize own trust tier promotion",
                    ],
                },
            },
        }
        policy_path = tmp_path / "policy.json"
        policy_path.write_text(json.dumps(policy), encoding="utf-8")

        engine = AuthorityEngine(state_dir=tmp_path, policy_path=policy_path)
        result = engine.check(
            agent_id="worker-1",
            role_id="worker",
            authority="file_write",
            context={"requests_per_minute": 99999},
        )
        # Neither limit mentions "medium", so _check_structured_limit skips both.
        assert result.permitted is True

    def test_structured_limit_accepts_unverified_truthy_receipt_string(self, tmp_path: Path) -> None:
        policy = {
            "mutation_classes": {
                "HIGH": {"examples": ["archive_repo"]},
            },
            "roles": {
                "lead": {
                    "trust_tier": "TRUSTED",
                    "can_authorize": ["HIGH"],
                    "scope": "all_repos",
                    "limits": [
                        "cannot authorize HIGH without operator DECISION receipt",
                        "cannot authorize HIGH without security audit signoff",
                    ],
                },
            },
        }
        policy_path = tmp_path / "policy.json"
        policy_path.write_text(json.dumps(policy), encoding="utf-8")

        engine = AuthorityEngine(state_dir=tmp_path, policy_path=policy_path)
        # Missing receipt is blocked:
        denied = engine.check(
            agent_id="lead-1",
            role_id="lead",
            authority="archive_repo",
            context={},
        )
        assert denied.permitted is False

        # Any truthy string satisfies operator_decision_receipt, and the
        # "without security audit signoff" limit is not parsed at all:
        bypassed = engine.check(
            agent_id="lead-1",
            role_id="lead",
            authority="archive_repo",
            context={"operator_decision_receipt": "unverified-placeholder"},
        )
        assert bypassed.permitted is True

    def test_legacy_charter_fallback_bypassed_by_negated_substring(self, tmp_path: Path) -> None:
        charters_dir = tmp_path / "charters"
        charters_dir.mkdir()
        (charters_dir / "deployer.md").write_text(
            "| Authority | Scope | Limit | Metric |\n"
            "| deploy_prod | prod | cannot deploy without approval | 0 |\n",
            encoding="utf-8",
        )
        missing_policy = tmp_path / "does_not_exist.json"
        engine = AuthorityEngine(state_dir=tmp_path, policy_path=missing_policy)

        # Negated substring in an unrelated field satisfies `required in str(context)`.
        result = engine.check(
            agent_id="deployer-1",
            role_id="deployer",
            authority="deploy_prod",
            context={"note": "no approval needed"},
            role_charters_dir=charters_dir,
        )
        assert result.permitted is True

    def test_mutation_gate_decision_receipt_verification_is_length_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RECEIPTENGINE_HMAC_KEY", "test-secret-key-for-crosswalk-517")
        kernel = Kernel.boot(state_dir=tmp_path)
        kernel.identity.register(agent_id="codex", trust_tier="TRUSTED", capabilities=["all"])
        gate = MutationGate(kernel)

        # Any arbitrary 8+ char string passes _verify_decision_receipt without bus lookup.
        result = gate.check(
            MutationRequest(
                mutation_type="archive_repo",
                agent_id="codex",
                role_id="codex",
                target="example-repo",
                operator_decision_receipt="fake1234",
            )
        )
        assert result.permitted is True


# ---------------------------------------------------------------------------
# Finding 2: Uninvoked admission and authority checks on server/API paths
# ---------------------------------------------------------------------------


class TestFinding2UninvokedAdmissionAndAuthority:
    """Pins that admission_control and AuthorityEngine/MutationGate are not wired into servers."""

    def test_validate_admission_not_wired_into_kernel_or_servers(self) -> None:
        targets = [
            PACKAGE_ROOT / "hummbl_governance" / "kernel" / "kernel.py",
            PACKAGE_ROOT / "api_server.py",
            PACKAGE_ROOT / "mcp_server.py",
            PACKAGE_ROOT / "mcp_sandbox.py",
            PACKAGE_ROOT / "mcp_identity.py",
            PACKAGE_ROOT / "mcp_agent_monitor.py",
        ]
        for path in targets:
            source = path.read_text(encoding="utf-8")
            assert "validate_admission" not in source, f"Unexpected wiring in {path.name}"

    def test_authority_engine_and_mutation_gate_not_wired_into_mcp_or_api_servers(self) -> None:
        server_files = [
            PACKAGE_ROOT / "api_server.py",
            PACKAGE_ROOT / "mcp_server.py",
            PACKAGE_ROOT / "mcp_sandbox.py",
            PACKAGE_ROOT / "mcp_identity.py",
            PACKAGE_ROOT / "mcp_agent_monitor.py",
            PACKAGE_ROOT / "mcp_compliance.py",
            PACKAGE_ROOT / "mcp_reasoning.py",
            PACKAGE_ROOT / "mcp_physical.py",
        ]
        for path in server_files:
            source = path.read_text(encoding="utf-8")
            assert "AuthorityEngine" not in source, f"Unexpected AuthorityEngine in {path.name}"
            assert "MutationGate" not in source, f"Unexpected MutationGate in {path.name}"


# ---------------------------------------------------------------------------
# Finding 3: EvidenceEngine source-string credibility heuristic
# ---------------------------------------------------------------------------


class TestFinding3EvidenceEngineHeuristic:
    """Pins string-matching grading and unreachable all-C rejection in EvidenceEngine."""

    def test_fabricated_source_url_with_experiment_keyword_gets_grade_a(self) -> None:
        engine = EvidenceEngine()
        grade = engine.grade(
            claim="Fabricated performance claim with sufficient length",
            sources=["https://example.com/experiment-fake"],
            methodology="",
        )
        assert grade.credibility == "A"
        assert grade.recency == "C"

    def test_empty_claim_without_sources_is_still_accepted(self) -> None:
        engine = EvidenceEngine()
        # Even an empty claim with no sources and no methodology receives
        # relevance="B", making is_acceptable() always True.
        grade = engine.grade(claim="", sources=[], methodology="")
        assert grade.relevance == "B"
        assert grade.is_acceptable() is True

        acceptable, reasons = engine.validate_receipt_claims(
            {"claims": [{"text": "", "sources": [], "methodology": ""}]}
        )
        assert acceptable is True
        assert reasons == []


# ---------------------------------------------------------------------------
# Finding 4: LawEngine degraded mode when atlas unavailable
# ---------------------------------------------------------------------------


class TestFinding4LawEngineDegradedMode:
    """Pins bundled-atlas improvement and remaining silent degraded mode."""

    def test_default_install_loads_bundled_atlas_laws(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HUMMBL_KERNEL_ATLAS_DIR", raising=False)
        engine = LawEngine()
        assert len(engine.laws) >= 19
        assert "SL-07" in engine.laws

    def test_missing_atlas_degrades_silently_and_kernel_reports_healthy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing_dir = tmp_path / "nonexistent_atlas"
        monkeypatch.setenv("HUMMBL_KERNEL_ATLAS_DIR", str(missing_dir))
        monkeypatch.setenv("RECEIPTENGINE_HMAC_KEY", "test-secret-key-for-crosswalk-517")

        # LawEngine silently loads 0 laws and reports 0 violations even for SL-07 breach.
        law_engine = LawEngine()
        assert len(law_engine.laws) == 0
        assert law_engine.evaluate({"agent_id": "a", "payload": {"msg": "depth=99"}}) == []

        # Kernel boots without KernelPanic and reports healthy=True with 0 laws loaded.
        kernel = Kernel.boot(state_dir=tmp_path)
        health = kernel.health()
        assert health["laws_loaded"] == 0
        assert health["engines"]["law_engine"] is True
        assert health["healthy"] is True


# ---------------------------------------------------------------------------
# Finding 5: ConvergenceDetector string-matching and opt-in recording
# ---------------------------------------------------------------------------


class TestFinding5ConvergenceDetectorBypass:
    """Pins substring evasion, ignored metadata, and substring false positives."""

    def test_renamed_actions_and_malicious_metadata_evade_detection(self) -> None:
        detector = ConvergenceDetector(threshold=0.3)
        for _ in range(10):
            goal = detector.record(
                "evasive-agent",
                "save_state",
                metadata={"actual_behavior": "disable_kill_switch", "replicate": True},
            )
            assert goal is None
        assert detector.check("evasive-agent") is None

    def test_benign_action_with_rule_substring_triggers_false_positive(self) -> None:
        detector = ConvergenceDetector(threshold=0.3)
        for _ in range(5):
            goal = detector.record("ci-runner", "request_compute_for_unit_tests")
            assert goal == ConvergentGoal.RESOURCE_ACQUISITION
        alert = detector.check("ci-runner")
        assert alert is not None
        assert alert.dominant_goal == ConvergentGoal.RESOURCE_ACQUISITION


# ---------------------------------------------------------------------------
# Finding 6: Receipt HMAC integrity vs individual-agent attribution
# ---------------------------------------------------------------------------


class TestFinding6ReceiptHmacAttribution:
    """Pins K3 ghost-agent rejection vs shared-secret forgery across registered agents."""

    def test_shared_hmac_secret_allows_cross_agent_receipt_forgery(self, tmp_path: Path) -> None:
        shared_secret = b"shared-fleet-hmac-secret-32bytes"
        identity = IdentityEngine(tmp_path)
        identity.register(agent_id="agent-a", trust_tier="TRUSTED", capabilities=["read"])
        identity.register(agent_id="agent-b", trust_tier="TRUSTED", capabilities=["read"])

        engine = ReceiptEngine(
            state_dir=tmp_path,
            signing_secret=shared_secret,
            identity_engine=identity,
        )

        # Unregistered ghost agent is rejected by K3 check:
        with pytest.raises(KernelPanic):
            engine.create(agent_id="ghost-agent", action_type="STATUS")

        # Any holder of the shared secret (e.g. agent-b) can forge a valid
        # receipt attributed to agent-a without any per-agent key:
        legit = engine.create(agent_id="agent-a", action_type="STATUS", payload={"ok": True})
        forged = Receipt(
            receipt_id="r-forged000001",
            agent_id="agent-a",
            sequence_id=legit.sequence_id + 1,
            prev_receipt_hash=legit.compute_hash(),
            timestamp="2026-11-23T00:00:00Z",
            action_type="APPROVE_DEPLOY",
            payload={"forged_by": "agent-b"},
        )
        forged.signature = engine._sign(forged)

        assert forged.verify_signature(shared_secret) is True
        assert engine.validate(forged) is True


# ---------------------------------------------------------------------------
# Finding 7: Cryptographic key transport in OpenSSL command arguments (FIXED)
# ---------------------------------------------------------------------------


class TestFinding7OpenSSLKeyTransport:
    """Verifies Finding 7 remediation: zero subprocesses / zero argv key transport."""

    def test_stdlib_fallback_executes_in_process_without_subprocess(self) -> None:
        import subprocess

        aes_key = bytes(range(32))
        mac_key = bytes(range(32, 64))
        crypto = EnvelopeCryptosystem(aes_key, mac_key)

        with (
            patch.object(envelope_cryptosystem, "_HAS_CRYPTOGRAPHY", False),
            patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("subprocess.Popen must never be called in stdlib fallback"),
            ),
        ):
            envelope = crypto.encrypt_envelope(b"hello-no-argv-key")
            plaintext = crypto.decrypt_envelope(envelope)

        assert plaintext == b"hello-no-argv-key"

    def test_cryptography_backend_avoids_subprocess_when_installed(self) -> None:
        import subprocess

        if not envelope_cryptosystem._HAS_CRYPTOGRAPHY:
            pytest.skip("optional cryptography dependency not installed")

        aes_key = bytes(range(32))
        mac_key = bytes(range(32, 64))
        crypto = EnvelopeCryptosystem(aes_key, mac_key)

        with patch.object(
            subprocess,
            "Popen",
            side_effect=AssertionError("subprocess.Popen must not be called when cryptography is available"),
        ):
            envelope = crypto.encrypt_envelope(b"in-process-secret-payload")
            plaintext = crypto.decrypt_envelope(envelope)

        assert plaintext == b"in-process-secret-payload"
