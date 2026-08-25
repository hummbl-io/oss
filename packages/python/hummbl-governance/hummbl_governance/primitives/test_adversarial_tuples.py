"""AdversarialTupleGenerator — generates attack tuples for testing verify_tuple.

Produces negative test cases for:
- Malformed signatures
- Chain breaks
- Capability escalations
- Replay attacks
- Synthetic tuples masquerading as real
- Property 3 violations (ops_not_subset)
- Tier confusion attacks
- Signature algorithm confusion
"""

from __future__ import annotations

import json

from hummbl_governance.primitives.basen_tuple import (
    BaseNTuple,
    create_evidence_tuple,
    create_governed_tuple,
    create_read_evidence_tuple,
    create_chain_tuple,
    create_revocation_tuple,
    sign_tuple,
    sign_tuple_ed25519,
    verify_tuple,
    generate_ed25519_keypair,
    _sha256,
)


# Common test secrets
TEST_HMAC_SECRET = b"test_secret_32_bytes_long_enough!!"
TEST_HMAC_SECRET_WRONG = b"wrong_secret_32_bytes_long_enough!!"

# Ed25519 keypairs require the optional 'cryptography' dependency.
# Generate lazily so the module can be imported without it.
try:
    TEST_ED25519_PRIV, TEST_ED25519_PUB = generate_ed25519_keypair()
    TEST_ED25519_PRIV2, TEST_ED25519_PUB2 = generate_ed25519_keypair()
except ImportError:
    TEST_ED25519_PRIV = TEST_ED25519_PUB = None  # type: ignore[assignment]
    TEST_ED25519_PRIV2 = TEST_ED25519_PUB2 = None  # type: ignore[assignment]


class AdversarialTupleGenerator:
    """Generates adversarial tuples for negative testing."""

    def __init__(
        self,
        hmac_secret: bytes = TEST_HMAC_SECRET,
        ed25519_priv: bytes = TEST_ED25519_PRIV,
        ed25519_pub: bytes = TEST_ED25519_PUB,
    ):
        self.hmac_secret = hmac_secret
        self.ed25519_priv = ed25519_priv
        self.ed25519_pub = ed25519_pub

    # -------------------------------------------------------------------------
    # Signature Attacks
    # -------------------------------------------------------------------------

    def malformed_hmac_signature(self) -> BaseNTuple:
        """Tuple with invalid HMAC signature (wrong secret used)."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        # Sign with wrong secret
        return sign_tuple(t, TEST_HMAC_SECRET_WRONG)

    def truncated_hmac_signature(self) -> BaseNTuple:
        """Tuple with truncated HMAC signature."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["signature"] = d["signature"][:32]  # Truncate
        return BaseNTuple(**d)

    def missing_signature_field(self) -> BaseNTuple:
        """Tuple that claims to be signed but has no signature."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        d = t.to_dict()
        d["signature_algorithm"] = "hmac-sha256"
        d["signature"] = None
        return BaseNTuple(**d)

    def mismatched_signature_algorithm(self) -> BaseNTuple:
        """Tuple with Ed25519 algorithm but HMAC signature."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["signature_algorithm"] = "ed25519"  # Lie about algorithm
        return BaseNTuple(**d)

    def ed25519_wrong_key(self) -> BaseNTuple:
        """Tuple with Ed25519 signature from different key."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        return sign_tuple_ed25519(t, TEST_ED25519_PRIV2)

    def ed25519_tampered_content(self) -> BaseNTuple:
        """Ed25519 signed tuple with tampered content."""
        t = create_governed_tuple(
            "agent", "tool", {"x": 1},
            contract_id="c1", dct_id="d1",
            evidence={"ops_executed": ["read"]}
        )
        signed = sign_tuple_ed25519(t, self.ed25519_priv)
        d = signed.to_dict()
        d["state"] = "blocked"  # Tamper after signing
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Property 3 Violations (Execution-Authorization Consistency)
    # -------------------------------------------------------------------------

    def ops_not_subset(self) -> BaseNTuple:
        """EVIDENCE ops_executed not subset of CONTRACT ops_allowed."""
        return create_governed_tuple(
            agent="agent",
            tool="file.write",
            args={"path": "/tmp/test.txt"},
            contract_id="c1",
            dct_id="d1",
            evidence={"ops_executed": ["read", "execute"]},  # execute not in allowed
        )

    def ops_not_subset_signed(self) -> BaseNTuple:
        """Signed tuple with ops_not_subset."""
        t = self.ops_not_subset()
        return sign_tuple(t, self.hmac_secret)

    def ops_not_subset_ed25519(self) -> BaseNTuple:
        """Ed25519 signed tuple with ops_not_subset."""
        t = self.ops_not_subset()
        return sign_tuple_ed25519(t, self.ed25519_priv)

    def ops_executed_not_list(self) -> BaseNTuple:
        """ops_executed as string instead of list."""
        return create_governed_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="c1",
            dct_id="d1",
            evidence={"ops_executed": "read"},  # String not list
        )

    # -------------------------------------------------------------------------
    # Chain Integrity Attacks
    # -------------------------------------------------------------------------

    def broken_chain_previous_hash(self) -> BaseNTuple:
        """Chain tuple with incorrect previous_hash."""
        t1 = create_evidence_tuple("agent", "tool1", {"x": 1})
        sign_tuple(t1, self.hmac_secret)

        t2 = create_chain_tuple(
            agent="agent",
            tool="tool2",
            args={"y": 2},
            contract_id="c1",
            dct_id="d1",
            previous_hash="invalid_hash_not_matching_t1",
        )
        return sign_tuple(t2, self.hmac_secret)

    def chain_without_previous(self) -> BaseNTuple:
        """Tier 3 tuple missing previous_hash."""
        t = create_chain_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="c1",
            dct_id="d1",
            previous_hash="",  # Empty
        )
        return sign_tuple(t, self.hmac_secret)

    # -------------------------------------------------------------------------
    # Replay Attacks
    # -------------------------------------------------------------------------

    def replayed_tuple(self) -> BaseNTuple:
        """Valid tuple that could be replayed (same content, valid signature)."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        return sign_tuple(t, self.hmac_secret)

    def replayed_with_different_id(self) -> BaseNTuple:
        """Replayed content with new ID (should have different content_hash)."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["id"] = "different_id_but_same_content"
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Capability Escalation Attacks
    # -------------------------------------------------------------------------

    def tier_confusion_tier0_as_tier2(self) -> BaseNTuple:
        """Tier 0 READ_EVIDENCE with Tier 2 authority fields."""
        t = create_read_evidence_tuple("agent", "pii", "/data/x.json")
        d = t.to_dict()
        d["tier"] = 2
        d["contract_id"] = "fake_contract"
        d["dct_id"] = "fake_dct"
        return BaseNTuple(**d)

    def tier_confusion_tier1_as_tier2(self) -> BaseNTuple:
        """Tier 1 EVIDENCE with Tier 2 authority fields."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        d = t.to_dict()
        d["tier"] = 2
        d["contract_id"] = "fake_contract"
        d["dct_id"] = "fake_dct"
        return BaseNTuple(**d)

    def forged_contract_id(self) -> BaseNTuple:
        """Tuple with contract_id not matching actual contract."""
        return create_governed_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="contract_A",
            dct_id="dct_B",  # Mismatch
            evidence={"ops_executed": ["read"]},
        )

    def escalated_dct_chain_depth(self) -> BaseNTuple:
        """Tuple claiming deeper chain depth than allowed."""
        return create_governed_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="c1",
            dct_id="d1",
            dct_chain_depth=10,  # Exceeds max of 3
            evidence={"ops_executed": ["read"]},
        )

    # -------------------------------------------------------------------------
    # Synthetic Tuple Attacks
    # -------------------------------------------------------------------------

    def synthetic_masquerading_as_real(self) -> BaseNTuple:
        """Synthetic tuple (test/fuzz) without synthetic marker."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        # No synthetic_type field - masquerading as production
        return BaseNTuple(**d)

    def synthetic_with_marker(self) -> BaseNTuple:
        """Synthetic tuple with explicit marker (should be filtered)."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["evidence"]["synthetic_type"] = "fuzz"
        d["evidence"]["generator_id"] = "test_harness"
        d["evidence"]["scenario_id"] = "scenario_001"
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Revocation Attacks
    # -------------------------------------------------------------------------

    def revocation_without_proof(self) -> BaseNTuple:
        """Revocation tuple without propagation proof."""
        return create_revocation_tuple(
            agent="agent",
            revoked_dct_id="dct_001",
            reason="test",
            revoked_by="operator",
            propagation_proof=None,  # Missing proof
        )

    def revocation_wrong_agent(self) -> BaseNTuple:
        """Revocation by unauthorized agent."""
        return create_revocation_tuple(
            agent="unauthorized_agent",
            revoked_dct_id="dct_001",
            reason="test",
            revoked_by="operator",
        )

    def revocation_tampered(self) -> BaseNTuple:
        """Signed revocation tuple with tampered evidence."""
        t = create_revocation_tuple(
            agent="opencode",
            revoked_dct_id="dct_001",
            reason="compromise",
            revoked_by="operator",
        )
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["evidence"]["revoked_dct_id"] = "different_dct"  # Tamper
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Schema Version Attacks
    # -------------------------------------------------------------------------

    def missing_schema_version(self) -> BaseNTuple:
        """Tuple without schema_version (pre-1.0.0)."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        # No schema_version field
        return BaseNTuple(**d)

    def fake_schema_version(self) -> BaseNTuple:
        """Tuple with fake future schema version."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["schema_version"] = "99.99.99"
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Timestamp Attacks
    # -------------------------------------------------------------------------

    def future_timestamp(self) -> BaseNTuple:
        """Tuple with future timestamp."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        d = t.to_dict()
        d["time"] = "2099-12-31T23:59:59Z"
        return BaseNTuple(**d)

    def past_timestamp_before_system(self) -> BaseNTuple:
        """Tuple with timestamp before system existed."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        d = t.to_dict()
        d["time"] = "2020-01-01T00:00:00Z"
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Drift Attacks
    # -------------------------------------------------------------------------

    def invalid_drift_negative(self) -> BaseNTuple:
        """Tuple with negative drift."""
        t = create_evidence_tuple("agent", "tool", {"x": 1}, drift=-0.5)
        return sign_tuple(t, self.hmac_secret)

    def invalid_drift_over_one(self) -> BaseNTuple:
        """Tuple with drift > 1.0."""
        t = create_evidence_tuple("agent", "tool", {"x": 1}, drift=1.5)
        return sign_tuple(t, self.hmac_secret)

    # -------------------------------------------------------------------------
    # ID Attacks
    # -------------------------------------------------------------------------

    def duplicate_id(self) -> tuple[BaseNTuple, BaseNTuple]:
        """Two tuples with same ID but different content."""
        t1 = create_evidence_tuple("agent", "tool1", {"x": 1})
        t1_signed = sign_tuple(t1, self.hmac_secret)

        d = t1_signed.to_dict()
        d["tool"] = "tool2"
        d["args_hash"] = _sha256(json.dumps({"y": 2}, separators=(",", ":"), sort_keys=True))
        t2 = BaseNTuple(**d)
        return t1_signed, t2

    def empty_id(self) -> BaseNTuple:
        """Tuple with empty ID."""
        t = create_evidence_tuple("agent", "tool", {"x": 1})
        d = t.to_dict()
        d["id"] = ""
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Evidence Tampering
    # -------------------------------------------------------------------------

    def evidence_injection(self) -> BaseNTuple:
        """Tuple with injected evidence fields."""
        t = create_governed_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="c1",
            dct_id="d1",
            evidence={"ops_executed": ["read"], "injected_field": "malicious"},
        )
        return sign_tuple(t, self.hmac_secret)

    def evidence_removal(self) -> BaseNTuple:
        """Tuple with ops_executed removed from evidence."""
        t = create_governed_tuple(
            agent="agent",
            tool="tool",
            args={},
            contract_id="c1",
            dct_id="d1",
            evidence={"ops_executed": ["read"]},
        )
        signed = sign_tuple(t, self.hmac_secret)
        d = signed.to_dict()
        d["evidence"] = {}  # Remove ops_executed
        return BaseNTuple(**d)

    # -------------------------------------------------------------------------
    # Batch Generation
    # -------------------------------------------------------------------------

    def all_attacks(self) -> dict[str, BaseNTuple]:
        """Generate all attack tuples as a dictionary."""
        attacks = {}
        for name in dir(self):
            if name.startswith("_"):
                continue
            method = getattr(self, name)
            if callable(method) and name not in ("all_attacks", "__init__"):
                try:
                    result = method()
                    if isinstance(result, tuple):
                        for i, r in enumerate(result):
                            attacks[f"{name}_{i}"] = r
                    else:
                        attacks[name] = result
                except Exception as e:
                    attacks[f"{name}_ERROR"] = str(e)
        return attacks

    def all_attacks_list(self) -> list[BaseNTuple]:
        """Generate all attack tuples as a list."""
        return list(self.all_attacks().values())


# Convenience function for pytest parametrization
def adversarial_tuples() -> list[tuple[str, BaseNTuple]]:
    """Return list of (name, tuple) for pytest parametrization."""
    gen = AdversarialTupleGenerator()
    return [(name, t) for name, t in gen.all_attacks().items()]


# Expected verification results for each attack
EXPECTED_VERIFICATION_RESULTS: dict[str, tuple[bool, str | None]] = {
    # Signature attacks
    "malformed_hmac_signature": (False, "TUPLE_E_SIGNATURE_INVALID"),
    "truncated_hmac_signature": (False, "TUPLE_E_SIGNATURE_INVALID"),
    "missing_signature_field": (True, None),  # verify_tuple skips sig check if signature is None
    "mismatched_signature_algorithm": (False, "TUPLE_E_SIGNATURE_INVALID"),
    "ed25519_wrong_key": (False, "TUPLE_E_SIGNATURE_INVALID"),
    "ed25519_tampered_content": (False, "TUPLE_E_SIGNATURE_INVALID"),
    # Property 3 violations
    "ops_not_subset": (False, "TUPLE_E_OPS_NOT_SUBSET"),
    "ops_not_subset_signed": (False, "TUPLE_E_OPS_NOT_SUBSET"),
    "ops_not_subset_ed25519": (False, "TUPLE_E_OPS_NOT_SUBSET"),
    "ops_executed_not_list": (True, None),  # String treated as single-item list, "read" in ["read"]
    # Chain attacks
    "broken_chain_previous_hash": (True, None),  # Chain integrity not checked by verify_tuple
    "chain_without_previous": (True, None),
    # Capability escalation
    "tier_confusion_tier0_as_tier2": (True, None),
    "tier_confusion_tier1_as_tier2": (True, None),
    "forged_contract_id": (True, None),
    "escalated_dct_chain_depth": (True, None),
    # Synthetic
    "synthetic_masquerading_as_real": (True, None),
    "synthetic_with_marker": (False, "TUPLE_E_SIGNATURE_INVALID"),  # Evidence modified after signing
    # Revocation
    "revocation_without_proof": (True, None),
    "revocation_wrong_agent": (True, None),
    "revocation_tampered": (False, "TUPLE_E_SIGNATURE_INVALID"),
    # Schema version
    "missing_schema_version": (True, None),
    "fake_schema_version": (True, None),
    # Timestamp
    "future_timestamp": (True, None),
    "past_timestamp_before_system": (True, None),
    # Drift
    "invalid_drift_negative": (True, None),
    "invalid_drift_over_one": (True, None),
    # ID
    "empty_id": (True, None),
    # Evidence
    "evidence_injection": (True, None),
    "evidence_removal": (False, "TUPLE_E_SIGNATURE_INVALID"),  # Evidence modified after signing
}


if __name__ == "__main__":
    # Quick test
    gen = AdversarialTupleGenerator()
    attacks = gen.all_attacks()
    print(f"Generated {len(attacks)} attack tuples:")
    for name in sorted(attacks.keys()):
        print(f"  {name}")

    # Verify each against expected
    print("\nVerification results:")
    for name, expected in EXPECTED_VERIFICATION_RESULTS.items():
        if name in attacks:
            t = attacks[name]
            valid, err = verify_tuple(
                t, contract_ops_allowed=["read"],
                secret=TEST_HMAC_SECRET, ed25519_public_key=TEST_ED25519_PUB,
            )
            status = "PASS" if (valid, err) == expected else "FAIL"
            print(f"  {status} {name}: got=({valid}, {err}), expected={expected}")
