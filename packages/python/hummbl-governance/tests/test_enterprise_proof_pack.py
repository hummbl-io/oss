"""Regression tests for examples/enterprise_proof_pack.py."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_proof_pack():
    script_path = Path(__file__).resolve().parent.parent / "examples" / "enterprise_proof_pack.py"
    spec = importlib.util.spec_from_file_location("enterprise_proof_pack", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_enterprise_proof_pack_end_to_end():
    mod = _load_proof_pack()
    res = mod.run_proof_pack()

    assert res["step1"]["hmac_token_valid"] is True
    assert res["step1"]["least_priv_allow"] is True
    assert res["step1"]["least_priv_deny_blocked"] is True
    assert res["step1"]["ed25519_token_valid"] is True

    assert res["step2"]["ttr_pre_decision"] == "ALLOW"
    assert res["step2"]["ttr_pre_verified"] is True
    assert res["step2"]["r2_prev_matches_r1"] is True
    assert res["step2"]["chain_verified"] is True
    assert res["step2"]["inclusion_verified"] is True
    assert res["step2"]["sth_verified"] is True
    assert res["step2"]["witness_cosig_verified"] is True

    assert res["step3"]["agent_critical_blocked"] is True
    assert res["step3"]["single_approver_blocked"] is True
    assert res["step3"]["two_person_permitted"] is True
    assert res["step3"]["kill_switch_mode"] == "HALT_ALL"
    assert res["step3"]["ttr_blocked_decision"] == "HARD_BLOCK"

    assert res["step4"]["rim_panic_triggered"] is False
    assert res["step4"]["d5_empty_approver_blocked"] is True
    assert res["step4"]["eu_annex_iv_verified"] is True
    assert res["step4"]["soc2_verified"] is True
