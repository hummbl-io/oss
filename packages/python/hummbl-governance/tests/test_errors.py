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

"""Tests for the unified error taxonomy in hummbl_governance.errors."""

from __future__ import annotations

from hummbl_governance.errors import (
    FailureMode,
    HummblError,
    FM_TO_ERRORS,
    fm_to_errors,
    # IDP_E_* backward-compat aliases
    IDP_E_DCT_VIOLATION,
    IDP_E_TOKEN_EXPIRED,
    IDP_E_TOKEN_INVALID,
    IDP_E_BINDING_MISMATCH,
    IDP_E_DEPTH_EXCEEDED,
    IDP_E_CAPABILITY_ESCALATION,
    IDP_E_REPLAN_LIMIT,
    IDP_E_AUDIT_IMMUTABLE,
    IDP_E_AUDIT_INCOMPLETE,
    IDP_E_AMENDMENT_TARGET_MISSING,
    IDP_E_VERIFICATION_REF_INVALID,
    IDP_E_EVIDENCE_REQUIRED,
    IDP_E_CHAIN_BROKEN,
    IDP_E_INVALID_STATE_TRANSITION,
)


# ---------------------------------------------------------------------------
# FailureMode enum
# ---------------------------------------------------------------------------

class TestFailureMode:
    def test_all_30_codes_present(self):
        codes = {fm.value for fm in FailureMode}
        assert len(codes) == 30
        for i in range(1, 31):
            assert f"FM{i}" in codes, f"FM{i} missing from FailureMode enum"

    def test_string_subclass(self):
        assert isinstance(FailureMode.SPECIFICATION_AMBIGUITY, str)
        assert FailureMode.SPECIFICATION_AMBIGUITY == "FM1"

    def test_specific_codes(self):
        assert FailureMode.SPECIFICATION_AMBIGUITY.value == "FM1"
        assert FailureMode.SCHEMA_NON_COMPLIANCE.value == "FM15"
        assert FailureMode.AUTHORIZATION_FAILURE.value == "FM17"
        assert FailureMode.AUDIT_TRAIL_LOSS.value == "FM28"
        assert FailureMode.UNRECOVERABLE_SYSTEM_STATE.value == "FM30"

    def test_lookup_by_value(self):
        fm = FailureMode("FM4")
        assert fm == FailureMode.INVALID_STATE_TRANSITION

    def test_governance_codes_present(self):
        """Key governance failure modes must be in the enum."""
        governance_codes = [
            FailureMode.GOVERNANCE_BYPASS,
            FailureMode.ESCALATION_SUPPRESSION,
            FailureMode.AUDIT_TRAIL_LOSS,
            FailureMode.AUTHORIZATION_FAILURE,
        ]
        for fm in governance_codes:
            assert fm in FailureMode


# ---------------------------------------------------------------------------
# HummblError enum
# ---------------------------------------------------------------------------

class TestHummblError:
    def test_all_14_codes_present(self):
        codes = {e.value for e in HummblError}
        assert len(codes) == 14

    def test_hg_e_prefix(self):
        for error in HummblError:
            assert error.value.startswith("HG_E_"), (
                f"{error.name} value {error.value!r} must start with HG_E_"
            )

    def test_string_subclass(self):
        assert isinstance(HummblError.DCT_VIOLATION, str)
        assert HummblError.DCT_VIOLATION == "HG_E_DCT_VIOLATION"

    def test_delegation_codes(self):
        assert HummblError.DCT_VIOLATION.value == "HG_E_DCT_VIOLATION"
        assert HummblError.TOKEN_EXPIRED.value == "HG_E_TOKEN_EXPIRED"
        assert HummblError.TOKEN_INVALID.value == "HG_E_TOKEN_INVALID"
        assert HummblError.BINDING_MISMATCH.value == "HG_E_BINDING_MISMATCH"
        assert HummblError.DEPTH_EXCEEDED.value == "HG_E_DEPTH_EXCEEDED"
        assert HummblError.CAPABILITY_ESCALATION.value == "HG_E_CAPABILITY_ESCALATION"
        assert HummblError.REPLAN_LIMIT.value == "HG_E_REPLAN_LIMIT"

    def test_audit_codes(self):
        assert HummblError.AUDIT_IMMUTABLE.value == "HG_E_AUDIT_IMMUTABLE"
        assert HummblError.AUDIT_INCOMPLETE.value == "HG_E_AUDIT_INCOMPLETE"
        assert HummblError.AMENDMENT_TARGET_MISSING.value == "HG_E_AMENDMENT_TARGET_MISSING"
        assert HummblError.VERIFICATION_REF_INVALID.value == "HG_E_VERIFICATION_REF_INVALID"
        assert HummblError.EVIDENCE_REQUIRED.value == "HG_E_EVIDENCE_REQUIRED"
        assert HummblError.CHAIN_BROKEN.value == "HG_E_CHAIN_BROKEN"

    def test_state_machine_code(self):
        assert HummblError.INVALID_STATE_TRANSITION.value == "HG_E_INVALID_STATE_TRANSITION"


# ---------------------------------------------------------------------------
# FM_TO_ERRORS mapping + fm_to_errors()
# ---------------------------------------------------------------------------

class TestFMToErrors:
    def test_fm_to_errors_invalid_state_transition(self):
        errors = fm_to_errors("FM4")
        assert HummblError.INVALID_STATE_TRANSITION in errors

    def test_fm_to_errors_authorization_failure(self):
        errors = fm_to_errors("FM17")
        assert HummblError.DCT_VIOLATION in errors
        assert HummblError.TOKEN_INVALID in errors

    def test_fm_to_errors_policy_violation(self):
        errors = fm_to_errors("FM18")
        assert HummblError.CAPABILITY_ESCALATION in errors

    def test_fm_to_errors_governance_bypass(self):
        errors = fm_to_errors("FM25")
        assert HummblError.DCT_VIOLATION in errors

    def test_fm_to_errors_audit_trail_loss(self):
        errors = fm_to_errors("FM28")
        assert HummblError.AUDIT_IMMUTABLE in errors
        assert HummblError.AUDIT_INCOMPLETE in errors

    def test_fm_to_errors_escalation_suppression(self):
        errors = fm_to_errors("FM26")
        assert HummblError.CHAIN_BROKEN in errors

    def test_fm_to_errors_invalid_reference(self):
        errors = fm_to_errors("FM16")
        assert HummblError.VERIFICATION_REF_INVALID in errors

    def test_fm_to_errors_incomplete_validation(self):
        errors = fm_to_errors("FM6")
        assert HummblError.EVIDENCE_REQUIRED in errors

    def test_unmapped_fm_returns_empty(self):
        errors = fm_to_errors("FM1")
        assert errors == []

    def test_unknown_fm_returns_empty(self):
        errors = fm_to_errors("FM99")
        assert errors == []

    def test_fm_to_errors_dict_keys_are_fm_values(self):
        for key in FM_TO_ERRORS:
            assert key.startswith("FM"), f"Key {key!r} should be an FM code"

    def test_fm_to_errors_dict_values_are_hummbl_errors(self):
        for errors in FM_TO_ERRORS.values():
            for error in errors:
                assert isinstance(error, HummblError)


# ---------------------------------------------------------------------------
# IDP_E_* backward-compatibility aliases
# ---------------------------------------------------------------------------

class TestIDPAliases:
    """IDP_E_* aliases must resolve to the canonical HummblError members."""

    def test_idp_dct_violation(self):
        assert IDP_E_DCT_VIOLATION is HummblError.DCT_VIOLATION

    def test_idp_token_expired(self):
        assert IDP_E_TOKEN_EXPIRED is HummblError.TOKEN_EXPIRED

    def test_idp_token_invalid(self):
        assert IDP_E_TOKEN_INVALID is HummblError.TOKEN_INVALID

    def test_idp_binding_mismatch(self):
        assert IDP_E_BINDING_MISMATCH is HummblError.BINDING_MISMATCH

    def test_idp_depth_exceeded(self):
        assert IDP_E_DEPTH_EXCEEDED is HummblError.DEPTH_EXCEEDED

    def test_idp_capability_escalation(self):
        assert IDP_E_CAPABILITY_ESCALATION is HummblError.CAPABILITY_ESCALATION

    def test_idp_replan_limit(self):
        assert IDP_E_REPLAN_LIMIT is HummblError.REPLAN_LIMIT

    def test_idp_audit_immutable(self):
        assert IDP_E_AUDIT_IMMUTABLE is HummblError.AUDIT_IMMUTABLE

    def test_idp_audit_incomplete(self):
        assert IDP_E_AUDIT_INCOMPLETE is HummblError.AUDIT_INCOMPLETE

    def test_idp_amendment_target_missing(self):
        assert IDP_E_AMENDMENT_TARGET_MISSING is HummblError.AMENDMENT_TARGET_MISSING

    def test_idp_verification_ref_invalid(self):
        assert IDP_E_VERIFICATION_REF_INVALID is HummblError.VERIFICATION_REF_INVALID

    def test_idp_evidence_required(self):
        assert IDP_E_EVIDENCE_REQUIRED is HummblError.EVIDENCE_REQUIRED

    def test_idp_chain_broken(self):
        assert IDP_E_CHAIN_BROKEN is HummblError.CHAIN_BROKEN

    def test_idp_invalid_state_transition(self):
        assert IDP_E_INVALID_STATE_TRANSITION is HummblError.INVALID_STATE_TRANSITION

    def test_aliases_are_enum_members_not_strings(self):
        """Aliases must be HummblError enum members, not bare strings."""
        aliases = [
            IDP_E_DCT_VIOLATION,
            IDP_E_TOKEN_EXPIRED,
            IDP_E_TOKEN_INVALID,
            IDP_E_BINDING_MISMATCH,
            IDP_E_DEPTH_EXCEEDED,
            IDP_E_CAPABILITY_ESCALATION,
            IDP_E_REPLAN_LIMIT,
            IDP_E_AUDIT_IMMUTABLE,
            IDP_E_AUDIT_INCOMPLETE,
            IDP_E_AMENDMENT_TARGET_MISSING,
            IDP_E_VERIFICATION_REF_INVALID,
            IDP_E_EVIDENCE_REQUIRED,
            IDP_E_CHAIN_BROKEN,
            IDP_E_INVALID_STATE_TRANSITION,
        ]
        for alias in aliases:
            assert isinstance(alias, HummblError), (
                f"{alias!r} should be a HummblError enum member"
            )
