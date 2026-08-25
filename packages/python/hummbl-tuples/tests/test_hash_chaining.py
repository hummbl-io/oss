#!/usr/bin/env python3
"""Tests for hash chaining layer (issue #29)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from hummbl_tuples.base import IDPTuple, _sha256_hex
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ContractTuple(IDPTuple):
    tuple_type: str = "CONTRACT"


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceTuple(IDPTuple):
    tuple_type: str = "EVIDENCE"


@dataclass(frozen=True, slots=True, kw_only=True)
class AttestTuple(IDPTuple):
    tuple_type: str = "ATTEST"


def test_idptuple_has_previous_hash():
    """IDPTuple should have a previous_hash field."""
    t = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    assert hasattr(t, "previous_hash")
    assert t.previous_hash is None


def test_hash_excludes_integrity_fields():
    """Hash should be stable regardless of previous_hash value."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    t2 = t1.with_chain("a" * 64)
    # Hash should be the same because integrity fields are excluded
    assert t1.hash == t2.hash


def test_with_chain_sets_previous_hash():
    """with_chain should return a new tuple with previous_hash set."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    assert t1.previous_hash is None
    t2 = t1.with_chain("abc123")
    assert t2.previous_hash == "abc123"
    # Original should be unchanged
    assert t1.previous_hash is None


def test_with_chain_none_clears_link():
    """with_chain(None) should clear the chain link."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1", previous_hash="abc")
    t2 = t1.with_chain(None)
    assert t2.previous_hash is None


def test_verify_chain_match():
    """verify_chain should return True when hashes match."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    t2 = t1.with_chain(t1.hash)
    assert t2.verify_chain(t1.hash) is True


def test_verify_chain_mismatch():
    """verify_chain should return False when hashes don't match."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    t2 = t1.with_chain("wrong_hash")
    assert t2.verify_chain(t1.hash) is False


def test_verify_chain_both_none():
    """verify_chain should return True when both are None (unchained)."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    assert t1.verify_chain(None) is True


def test_chain_construction():
    """A 3-tuple chain should verify correctly."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    t2 = EvidenceTuple(agent="beta", intent_id="i1", task_id="t1").with_chain(t1.hash)
    t3 = AttestTuple(agent="verifier", intent_id="i1", task_id="t1").with_chain(t2.hash)

    # Verify chain
    assert t2.verify_chain(t1.hash) is True
    assert t3.verify_chain(t2.hash) is True


def test_chain_tamper_detection():
    """Tampering with a tuple should break the chain."""
    t1 = ContractTuple(agent="alpha", intent_id="i1", task_id="t1")
    t2 = EvidenceTuple(agent="beta", intent_id="i1", task_id="t1").with_chain(t1.hash)

    # Tamper: create a different t1 with different agent
    t1_tampered = ContractTuple(agent="eve", intent_id="i1", task_id="t1")
    # t2's previous_hash still points to original t1's hash
    assert t2.verify_chain(t1_tampered.hash) is False


def test_sha256_hex():
    """_sha256_hex should produce a 64-char hex string."""
    h = _sha256_hex("test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_schema_extension_exists():
    """The hash chaining schema extension should exist."""
    schema = REPO_ROOT / "schemas" / "extensions" / "hash_chaining.schema.json"
    assert schema.exists()


def test_design_doc_exists():
    """The design rationale document should exist."""
    doc = REPO_ROOT / "docs" / "specs" / "HASH_CHAINING_DESIGN.md"
    assert doc.exists()


def test_examples_exist():
    """Three worked chain examples should exist."""
    examples_dir = REPO_ROOT / "examples" / "hash_chaining"
    assert (examples_dir / "chain_step1.json").exists()
    assert (examples_dir / "chain_step2.json").exists()
    assert (examples_dir / "chain_step3.json").exists()


def test_genesis_example_has_null_previous_hash():
    """The genesis example should have previous_hash null."""
    import json
    p = REPO_ROOT / "examples" / "hash_chaining" / "chain_step1.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data.get("previous_hash") is None


def test_chained_examples_have_previous_hash():
    """Non-genesis examples should have non-null previous_hash."""
    import json
    for name in ("chain_step2.json", "chain_step3.json"):
        p = REPO_ROOT / "examples" / "hash_chaining" / name
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("previous_hash") is not None
        assert len(data["previous_hash"]) == 64


if __name__ == "__main__":
    test_idptuple_has_previous_hash()
    test_hash_excludes_integrity_fields()
    test_with_chain_sets_previous_hash()
    test_with_chain_none_clears_link()
    test_verify_chain_match()
    test_verify_chain_mismatch()
    test_verify_chain_both_none()
    test_chain_construction()
    test_chain_tamper_detection()
    test_sha256_hex()
    test_schema_extension_exists()
    test_design_doc_exists()
    test_examples_exist()
    test_genesis_example_has_null_previous_hash()
    test_chained_examples_have_previous_hash()
    print("All hash chaining tests passed")
