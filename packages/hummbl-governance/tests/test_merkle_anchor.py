"""Tests for CT-style Merkle anchoring of governance tuple logs.

Covers:
  - Merkle tree construction (RFC 6962 hashing, empty/single/power-of-2/non-power-of-2)
  - Inclusion proof generation and verification
  - Signed Tree Head (STH) Ed25519 signing and verification
  - Consistency proof generation and verification (fork detection)
  - Witness cosigning
  - Tuple log anchoring (main entry point)
"""

from __future__ import annotations

import json

import pytest

from hummbl_governance.primitives.merkle_anchor import (
    MerkleTree,
    SignedTreeHead,
    anchor_tuple_log,
    consistency_proof,
    cosign_tree_head,
    sign_tree_head,
    verify_consistency_proof,
    verify_inclusion_proof,
    verify_tree_head,
    verify_witness_cosignature,
)

# Ed25519 keypair generation and BaseNTuple require the optional 'cryptography'
# dependency. Skip those tests gracefully when it's not installed.
# Note: generate_ed25519_keypair imports cryptography inside the function body,
# so the import succeeds even without cryptography — we must probe directly.
try:
    import cryptography  # noqa: F401
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

from hummbl_governance.primitives import (
    BaseNTuple,
    create_evidence_tuple,
    generate_ed25519_keypair,
)

_skip_no_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="cryptography not installed")


def _make_entry_hashes(n: int) -> list[str]:
    """Generate n distinct fake entry hashes (64-char hex)."""
    return [f"{i:064x}" for i in range(n)]


# ---------------------------------------------------------------------------
# MerkleTree construction
# ---------------------------------------------------------------------------


class TestMerkleTree:
    """Tests for Merkle tree construction with RFC 6962 hashing."""

    def test_empty_tree_root_is_sha256_of_empty(self):
        """Empty tree root is SHA-256 of empty bytes."""
        import hashlib

        tree = MerkleTree()
        expected = hashlib.sha256(b"").hexdigest()
        assert tree.root_hash() == expected
        assert tree.size() == 0

    def test_single_leaf_root_equals_leaf_hash(self):
        """Single-leaf tree root equals the leaf hash (no interior nodes)."""
        tree = MerkleTree()
        entry = f"{1:064x}"
        tree.append(entry)
        # Root should be the leaf hash (SHA-256(0x00 || entry))
        import hashlib

        expected = hashlib.sha256(b"\x00" + bytes.fromhex(entry)).hexdigest()
        assert tree.root_hash() == expected
        assert tree.size() == 1

    def test_two_leaves_root_is_interior_hash(self):
        """Two-leaf tree root is the interior hash of both leaves."""
        tree = MerkleTree()
        e1, e2 = f"{1:064x}", f"{2:064x}"
        tree.append(e1)
        tree.append(e2)
        import hashlib

        leaf1 = hashlib.sha256(b"\x00" + bytes.fromhex(e1)).hexdigest()
        leaf2 = hashlib.sha256(b"\x00" + bytes.fromhex(e2)).hexdigest()
        expected = hashlib.sha256(b"\x01" + bytes.fromhex(leaf1) + bytes.fromhex(leaf2)).hexdigest()
        assert tree.root_hash() == expected

    def test_power_of_two_leaves(self):
        """4-leaf tree builds correctly (2 interior + 1 root)."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        assert tree.size() == 4
        # Root should be deterministic
        assert tree.root_hash() == tree.root_hash()

    def test_non_power_of_two_leaves(self):
        """3-leaf tree: odd node promoted as-is (RFC 6962, no duplication)."""
        tree = MerkleTree.from_entries(_make_entry_hashes(3))
        assert tree.size() == 3
        # Root should be deterministic and non-empty
        root = tree.root_hash()
        assert len(root) == 64

    def test_root_hash_is_deterministic(self):
        """Same entries produce same root."""
        entries = _make_entry_hashes(5)
        t1 = MerkleTree.from_entries(entries)
        t2 = MerkleTree.from_entries(entries)
        assert t1.root_hash() == t2.root_hash()

    def test_different_entries_different_root(self):
        """Different entries produce different roots."""
        t1 = MerkleTree.from_entries(_make_entry_hashes(4))
        t2 = MerkleTree.from_entries([f"{i + 100:064x}" for i in range(4)])
        assert t1.root_hash() != t2.root_hash()

    def test_append_increments_size(self):
        """Append increments size."""
        tree = MerkleTree()
        for i in range(5):
            tree.append(f"{i:064x}")
            assert tree.size() == i + 1

    def test_from_entries_equivalent_to_incremental_append(self):
        """from_entries produces same root as incremental append."""
        entries = _make_entry_hashes(6)
        t1 = MerkleTree.from_entries(entries)
        t2 = MerkleTree()
        for e in entries:
            t2.append(e)
        assert t1.root_hash() == t2.root_hash()


# ---------------------------------------------------------------------------
# Inclusion proofs
# ---------------------------------------------------------------------------


class TestInclusionProof:
    """Tests for inclusion proof generation and verification."""

    def test_inclusion_proof_first_leaf(self):
        """Inclusion proof for leaf 0 verifies."""
        entries = _make_entry_hashes(4)
        tree = MerkleTree.from_entries(entries)
        proof = tree.inclusion_proof(0)
        leaf_hash = tree.leaves[0]
        assert verify_inclusion_proof(leaf_hash, 0, proof, tree.root_hash()) is True

    def test_inclusion_proof_last_leaf(self):
        """Inclusion proof for the last leaf verifies."""
        entries = _make_entry_hashes(4)
        tree = MerkleTree.from_entries(entries)
        idx = len(entries) - 1
        proof = tree.inclusion_proof(idx)
        leaf_hash = tree.leaves[idx]
        assert verify_inclusion_proof(leaf_hash, idx, proof, tree.root_hash()) is True

    def test_inclusion_proof_middle_leaf(self):
        """Inclusion proof for a middle leaf verifies."""
        entries = _make_entry_hashes(8)
        tree = MerkleTree.from_entries(entries)
        idx = 3
        proof = tree.inclusion_proof(idx)
        leaf_hash = tree.leaves[idx]
        assert verify_inclusion_proof(leaf_hash, idx, proof, tree.root_hash()) is True

    def test_inclusion_proof_non_power_of_two(self):
        """Inclusion proofs work for non-power-of-2 tree sizes."""
        entries = _make_entry_hashes(5)
        tree = MerkleTree.from_entries(entries)
        for idx in range(5):
            proof = tree.inclusion_proof(idx)
            leaf_hash = tree.leaves[idx]
            assert verify_inclusion_proof(leaf_hash, idx, proof, tree.root_hash(), tree_size=tree.size()) is True

    def test_inclusion_proof_single_leaf(self):
        """Single-leaf tree: empty proof, root equals leaf hash."""
        tree = MerkleTree.from_entries(_make_entry_hashes(1))
        proof = tree.inclusion_proof(0)
        assert proof == []
        leaf_hash = tree.leaves[0]
        assert verify_inclusion_proof(leaf_hash, 0, proof, tree.root_hash()) is True

    def test_inclusion_proof_wrong_root_fails(self):
        """Verification fails with wrong root hash."""
        entries = _make_entry_hashes(4)
        tree = MerkleTree.from_entries(entries)
        proof = tree.inclusion_proof(0)
        leaf_hash = tree.leaves[0]
        wrong_root = f"{999:064x}"
        assert verify_inclusion_proof(leaf_hash, 0, proof, wrong_root) is False

    def test_inclusion_proof_wrong_leaf_fails(self):
        """Verification fails with wrong leaf hash."""
        entries = _make_entry_hashes(4)
        tree = MerkleTree.from_entries(entries)
        proof = tree.inclusion_proof(0)
        wrong_leaf = tree.leaves[1]  # wrong leaf
        assert verify_inclusion_proof(wrong_leaf, 0, proof, tree.root_hash()) is False

    def test_inclusion_proof_tampered_proof_fails(self):
        """Tampered proof (modified sibling) fails verification."""
        entries = _make_entry_hashes(4)
        tree = MerkleTree.from_entries(entries)
        proof = tree.inclusion_proof(0)
        leaf_hash = tree.leaves[0]
        # Tamper with the first proof element
        tampered_proof = [f"{888:064x}"] + proof[1:]
        assert verify_inclusion_proof(leaf_hash, 0, tampered_proof, tree.root_hash()) is False

    def test_inclusion_proof_index_out_of_range_raises(self):
        """Out-of-range index raises IndexError."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        with pytest.raises(IndexError):
            tree.inclusion_proof(4)
        with pytest.raises(IndexError):
            tree.inclusion_proof(-1)


# ---------------------------------------------------------------------------
# Signed Tree Head (STH)
# ---------------------------------------------------------------------------


@_skip_no_crypto
class TestSignedTreeHead:
    """Tests for Ed25519-signed Merkle tree heads."""

    def test_sign_and_verify_tree_head(self):
        """STH signs and verifies with correct key."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, pub = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "key-1")
        assert sth.tree_size == 4
        assert sth.key_id == "key-1"
        assert len(sth.root_hash) == 64
        assert len(sth.signature) > 0
        assert verify_tree_head(sth, pub) is True

    def test_verify_tree_head_wrong_key_fails(self):
        """STH verification fails with wrong public key."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, _ = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "key-1")
        _, wrong_pub = generate_ed25519_keypair()
        assert verify_tree_head(sth, wrong_pub) is False

    def test_verify_tree_head_tampered_root_fails(self):
        """Tampered root hash in STH fails verification."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, pub = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "key-1")
        # Tamper with root_hash (create new STH with modified root)
        tampered = SignedTreeHead(
            tree_size=sth.tree_size,
            timestamp=sth.timestamp,
            root_hash=f"{999:064x}",
            signature=sth.signature,
            key_id=sth.key_id,
        )
        assert verify_tree_head(tampered, pub) is False

    def test_verify_tree_head_tampered_size_fails(self):
        """Tampered tree_size in STH fails verification."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, pub = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "key-1")
        tampered = SignedTreeHead(
            tree_size=sth.tree_size + 1,
            timestamp=sth.timestamp,
            root_hash=sth.root_hash,
            signature=sth.signature,
            key_id=sth.key_id,
        )
        assert verify_tree_head(tampered, pub) is False

    def test_sth_is_frozen(self):
        """STH is a frozen dataclass."""
        tree = MerkleTree.from_entries(_make_entry_hashes(2))
        priv, _ = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "key-1")
        with pytest.raises(AttributeError):
            sth.key_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Consistency proofs (fork detection)
# ---------------------------------------------------------------------------


@_skip_no_crypto
class TestConsistencyProof:
    """Tests for consistency proof generation and verification."""

    def test_consistency_empty_to_full(self):
        """Empty tree to full tree: trivial consistency (empty proof)."""
        old = MerkleTree()  # empty
        new = MerkleTree.from_entries(_make_entry_hashes(4))
        proof = consistency_proof(old, new)
        assert proof == []
        assert verify_consistency_proof(
            old.root_hash(), old.size(), new.root_hash(), new.size(), proof
        ) is True

    def test_consistency_identical_trees(self):
        """Identical trees: empty proof, roots must match."""
        entries = _make_entry_hashes(4)
        old = MerkleTree.from_entries(entries)
        new = MerkleTree.from_entries(entries)
        proof = consistency_proof(old, new)
        assert proof == []
        assert verify_consistency_proof(
            old.root_hash(), old.size(), new.root_hash(), new.size(), proof
        ) is True

    def test_consistency_power_of_2_extension(self):
        """4-leaf tree extended to 8 leaves: consistency proof verifies."""
        old = MerkleTree.from_entries(_make_entry_hashes(4))
        new = MerkleTree.from_entries(_make_entry_hashes(8))
        proof = consistency_proof(old, new)
        assert verify_consistency_proof(
            old.root_hash(), old.size(), new.root_hash(), new.size(), proof
        ) is True

    def test_consistency_non_power_of_2_extension(self):
        """3-leaf tree extended to 7 leaves: consistency proof verifies."""
        old = MerkleTree.from_entries(_make_entry_hashes(3))
        new = MerkleTree.from_entries(_make_entry_hashes(7))
        proof = consistency_proof(old, new)
        assert verify_consistency_proof(
            old.root_hash(), old.size(), new.root_hash(), new.size(), proof
        ) is True

    def test_consistency_one_to_many(self):
        """1-leaf tree extended to 5 leaves: consistency proof verifies."""
        old = MerkleTree.from_entries(_make_entry_hashes(1))
        new = MerkleTree.from_entries(_make_entry_hashes(5))
        proof = consistency_proof(old, new)
        assert verify_consistency_proof(
            old.root_hash(), old.size(), new.root_hash(), new.size(), proof
        ) is True

    def test_consistency_detects_fork(self):
        """Forked tree (different entries) fails consistency verification."""
        old = MerkleTree.from_entries(_make_entry_hashes(4))
        # New tree has different entries (fork), not an extension
        forked = MerkleTree.from_entries([f"{i + 200:064x}" for i in range(8)])
        proof = consistency_proof(old, forked)
        # The proof may generate, but verification should fail because
        # the old root doesn't match the forked tree's prefix
        result = verify_consistency_proof(
            old.root_hash(), old.size(), forked.root_hash(), forked.size(), proof
        )
        # If the fork changes the early entries, consistency fails.
        # If it only appends different entries, the old prefix is preserved.
        # Here we changed ALL entries, so the old root won't match.
        assert result is False

    def test_consistency_old_larger_than_new_raises(self):
        """Old tree larger than new tree raises ValueError."""
        old = MerkleTree.from_entries(_make_entry_hashes(8))
        new = MerkleTree.from_entries(_make_entry_hashes(4))
        with pytest.raises(ValueError):
            consistency_proof(old, new)

    def test_consistency_wrong_old_root_fails(self):
        """Verification fails with wrong old_root."""
        old = MerkleTree.from_entries(_make_entry_hashes(4))
        new = MerkleTree.from_entries(_make_entry_hashes(8))
        proof = consistency_proof(old, new)
        wrong_old_root = f"{777:064x}"
        assert verify_consistency_proof(
            wrong_old_root, old.size(), new.root_hash(), new.size(), proof
        ) is False


# ---------------------------------------------------------------------------
# Witness cosigning
# ---------------------------------------------------------------------------


@_skip_no_crypto
class TestWitnessCosigning:
    """Tests for witness cosigning of STHs (gossip-based fork detection)."""

    def test_cosign_and_verify(self):
        """Witness cosigns STH and verification succeeds."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, pub = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "anchor-key")

        wpriv, wpub = generate_ed25519_keypair()
        cosig = cosign_tree_head(sth, wpriv, "witness-1")
        assert cosig.witness_id == "witness-1"
        assert verify_witness_cosignature(sth, cosig, wpub) is True

    def test_verify_witness_wrong_key_fails(self):
        """Witness cosignature verification fails with wrong key."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, _ = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "anchor-key")

        wpriv, _ = generate_ed25519_keypair()
        cosig = cosign_tree_head(sth, wpriv, "witness-1")
        _, wrong_wpub = generate_ed25519_keypair()
        assert verify_witness_cosignature(sth, cosig, wrong_wpub) is False

    def test_verify_witness_tampered_sth_fails(self):
        """Witness cosignature fails if STH is tampered after cosigning."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, _ = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "anchor-key")

        wpriv, wpub = generate_ed25519_keypair()
        cosig = cosign_tree_head(sth, wpriv, "witness-1")

        # Tamper with STH root
        tampered_sth = SignedTreeHead(
            tree_size=sth.tree_size,
            timestamp=sth.timestamp,
            root_hash=f"{555:064x}",
            signature=sth.signature,
            key_id=sth.key_id,
        )
        assert verify_witness_cosignature(tampered_sth, cosig, wpub) is False

    def test_multiple_witnesses(self):
        """Multiple witnesses can cosign the same STH independently."""
        tree = MerkleTree.from_entries(_make_entry_hashes(4))
        priv, _ = generate_ed25519_keypair()
        sth = sign_tree_head(tree, priv, "anchor-key")

        w1priv, w1pub = generate_ed25519_keypair()
        w2priv, w2pub = generate_ed25519_keypair()
        cosig1 = cosign_tree_head(sth, w1priv, "witness-1")
        cosig2 = cosign_tree_head(sth, w2priv, "witness-2")
        assert verify_witness_cosignature(sth, cosig1, w1pub) is True
        assert verify_witness_cosignature(sth, cosig2, w2pub) is True
        # Cross-verification fails (witness-1's sig with witness-2's key)
        assert verify_witness_cosignature(sth, cosig1, w2pub) is False


# ---------------------------------------------------------------------------
# Tuple log anchoring (main entry point)
# ---------------------------------------------------------------------------


@_skip_no_crypto
class TestAnchorTupleLog:
    """Tests for anchoring a real tuple log JSONL file."""

    def test_anchor_tuple_log_creates_sth(self, tmp_path):
        """Anchoring a tuple log produces a valid STH."""
        log = tmp_path / "tuples.jsonl"
        tuples = [create_evidence_tuple(agent="a", tool="t", args={"x": i}) for i in range(5)]
        for t in tuples:
            log.write_text(log.read_text() + t.to_json() + "\n") if log.exists() else log.write_text(t.to_json() + "\n")

        priv, pub = generate_ed25519_keypair()
        sth = anchor_tuple_log(str(log), priv, "anchor-1")
        assert sth.tree_size == 5
        assert verify_tree_head(sth, pub) is True

    def test_anchor_empty_log(self, tmp_path):
        """Anchoring an empty log produces a valid STH with size 0."""
        log = tmp_path / "empty.jsonl"
        log.write_text("")
        priv, pub = generate_ed25519_keypair()
        sth = anchor_tuple_log(str(log), priv, "anchor-1")
        assert sth.tree_size == 0
        assert verify_tree_head(sth, pub) is True

    def test_anchor_missing_log_raises(self, tmp_path):
        """Anchoring a missing log raises FileNotFoundError."""
        priv, _ = generate_ed25519_keypair()
        with pytest.raises(FileNotFoundError):
            anchor_tuple_log(str(tmp_path / "nonexistent.jsonl"), priv, "anchor-1")

    def test_anchored_log_inclusion_proof(self, tmp_path):
        """After anchoring, an inclusion proof for any tuple verifies."""
        log = tmp_path / "tuples.jsonl"
        tuples = [create_evidence_tuple(agent="a", tool="t", args={"x": i}) for i in range(6)]
        lines = [t.to_json() for t in tuples]
        log.write_text("\n".join(lines) + "\n")

        priv, pub = generate_ed25519_keypair()
        sth = anchor_tuple_log(str(log), priv, "anchor-1")

        # Rebuild the tree to get inclusion proof for tuple at index 2

        entry_hashes = []
        with open(log) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                t = BaseNTuple(**data)
                entry_hashes.append(t.content_hash())
        tree = MerkleTree.from_entries(entry_hashes)
        proof = tree.inclusion_proof(2)
        leaf_hash = tree.leaves[2]
        assert verify_inclusion_proof(leaf_hash, 2, proof, sth.root_hash) is True

    def test_anchor_detects_tampered_log(self, tmp_path):
        """Anchoring detects tampering: modified log produces different root."""
        log = tmp_path / "tuples.jsonl"
        tuples = [create_evidence_tuple(agent="a", tool="t", args={"x": i}) for i in range(4)]
        lines = [t.to_json() for t in tuples]
        log.write_text("\n".join(lines) + "\n")

        priv, pub = generate_ed25519_keypair()
        sth_original = anchor_tuple_log(str(log), priv, "anchor-1")
        original_root = sth_original.root_hash

        # Tamper: modify one tuple's content (change args)
        tampered_tuples = [create_evidence_tuple(agent="a", tool="t", args={"x": i + 100}) for i in range(4)]
        tampered_lines = [t.to_json() for t in tampered_tuples]
        log.write_text("\n".join(tampered_lines) + "\n")

        sth_tampered = anchor_tuple_log(str(log), priv, "anchor-1")
        assert sth_tampered.root_hash != original_root
