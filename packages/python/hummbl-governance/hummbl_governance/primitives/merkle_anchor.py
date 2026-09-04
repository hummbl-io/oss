"""CT-style Merkle anchoring for governance tuple logs.

Implements Certificate Transparency (RFC 6962) semantics for the tuple log:
  - Merkle tree over tuple entries at periodic intervals
  - Signed Tree Head (STH): root hash + size + timestamp, signed by external key
  - Inclusion proof: prove a specific tuple is included in a tree
  - Consistency proof: prove a new STH extends an old STH (no fork)
  - Witness cosigning: multiple witnesses co-sign STHs so forks are detectable

This closes the Byzantine operator threat model: a compromised operator can
forge HMAC-signed entries, but cannot forge a Merkle root that matches the
externally-signed tree head. If the operator forks the log (presents different
views to different observers), consistency proofs detect the fork. If multiple
witnesses co-sign tree heads, a fork is detectable by gossip even without
a consistency proof between the two views.

The Merkle tree uses SHA-256 with RFC 6962 leaf/interior hashing:
  - Leaf hash: SHA-256(0x00 || entry_hash)
  - Interior hash: SHA-256(0x01 || left_hash || right_hash)
  - Empty tree root: SHA-256("") (the hash of empty string)

Reference: RFC 6962 Section 2.1, Section 3.1-3.4
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# RFC 6962 hashing primitives
# ---------------------------------------------------------------------------


def _leaf_hash(entry_hash: str) -> str:
    """RFC 6962 leaf hash: SHA-256(0x00 || entry_hash_bytes).

    Args:
        entry_hash: Hex-encoded hash of the tuple entry content.

    Returns:
        Hex-encoded leaf hash.
    """
    h = hashlib.sha256()
    h.update(b"\x00")
    h.update(bytes.fromhex(entry_hash))
    return h.hexdigest()


def _interior_hash(left: str, right: str) -> str:
    """RFC 6962 interior hash: SHA-256(0x01 || left_bytes || right_bytes).

    Args:
        left: Hex-encoded left child hash.
        right: Hex-encoded right child hash.

    Returns:
        Hex-encoded interior node hash.
    """
    h = hashlib.sha256()
    h.update(b"\x01")
    h.update(bytes.fromhex(left))
    h.update(bytes.fromhex(right))
    return h.hexdigest()


def _empty_root() -> str:
    """Empty tree root: SHA-256 of empty bytes.

    Returns:
        Hex-encoded hash of the empty tree.
    """
    return hashlib.sha256(b"").hexdigest()


# ---------------------------------------------------------------------------
# MerkleTree
# ---------------------------------------------------------------------------


class MerkleTree:
    """A Merkle tree over tuple entry hashes.

    Uses RFC 6962 hashing (0x00 prefix for leaves, 0x01 for interior).
    Supports incremental append and inclusion proof generation.

    Attributes:
        leaves: List of leaf hashes (hex strings).
    """

    def __init__(self) -> None:
        self.leaves: list[str] = []

    def append(self, entry_hash: str) -> None:
        """Append an entry hash to the tree.

        Args:
            entry_hash: Hex-encoded content hash of the tuple entry.
        """
        self.leaves.append(_leaf_hash(entry_hash))

    def root_hash(self) -> str:
        """Compute the Merkle root hash.

        Returns:
            Hex-encoded Merkle root hash, or the empty-tree root if no leaves.
        """
        if not self.leaves:
            return _empty_root()
        level = list(self.leaves)
        while len(level) > 1:
            next_level: list[str] = []
            i = 0
            while i < len(level):
                if i + 1 < len(level):
                    next_level.append(_interior_hash(level[i], level[i + 1]))
                    i += 2
                else:
                    # Odd node promoted as-is (RFC 6962: no duplication)
                    next_level.append(level[i])
                    i += 1
            level = next_level
        return level[0]

    def inclusion_proof(self, index: int) -> list[str]:
        """Generate an inclusion proof for the leaf at index.

        Returns a list of sibling hashes from leaf to root.
        The verifier combines these with the leaf hash to recompute the root.

        Args:
            index: Leaf index (0-based).

        Returns:
            List of sibling hashes (hex strings) from bottom to top.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"leaf index {index} out of range (size {len(self.leaves)})")
        proof: list[str] = []
        level = list(self.leaves)
        idx = index
        while len(level) > 1:
            if idx % 2 == 0:
                # Left node: sibling is to the right (if it exists)
                if idx + 1 < len(level):
                    proof.append(level[idx + 1])
                # else: odd node promoted, no sibling at this level
            else:
                # Right node: sibling is to the left
                proof.append(level[idx - 1])
            # Build next level
            next_level: list[str] = []
            i = 0
            while i < len(level):
                if i + 1 < len(level):
                    next_level.append(_interior_hash(level[i], level[i + 1]))
                    i += 2
                else:
                    next_level.append(level[i])
                    i += 1
            level = next_level
            idx = idx // 2
        return proof

    def size(self) -> int:
        """Number of leaves in the tree.

        Returns:
            The leaf count.
        """
        return len(self.leaves)

    @classmethod
    def from_entries(cls, entry_hashes: list[str]) -> MerkleTree:
        """Build a tree from a list of entry hashes.

        Args:
            entry_hashes: List of hex-encoded content hashes.

        Returns:
            A new MerkleTree populated with the given entries.
        """
        tree = cls()
        for h in entry_hashes:
            tree.append(h)
        return tree


def verify_inclusion_proof(
    leaf_hash: str,
    leaf_index: int,
    proof: list[str],
    root_hash: str,
    tree_size: int | None = None,
) -> bool:
    """Verify an inclusion proof.

    Recomputes the root from the leaf hash and proof path, comparing to root_hash.
    The leaf_index determines whether each proof element is a left or right sibling.

    When ``tree_size`` is provided, the verifier correctly handles non-power-of-2
    tree sizes by tracking the level width and skipping levels where the node was
    promoted (odd node, no sibling). Without ``tree_size``, the old behavior is
    used, which is correct for power-of-2 trees but may fail for non-power-of-2
    trees when a leaf is promoted through multiple levels.

    Args:
        leaf_hash: Hex-encoded leaf hash (already RFC 6962 leaf-hashed).
        leaf_index: Index of the leaf in the tree.
        proof: List of sibling hashes from bottom to top.
        root_hash: Expected Merkle root hash (hex).
        tree_size: Number of leaves in the tree. When provided, enables correct
            verification for non-power-of-2 tree sizes.

    Returns:
        True if the proof recomputes to the given root, False otherwise.
    """
    computed = leaf_hash
    idx = leaf_index

    if tree_size is not None:
        # Track level width to correctly handle promotions (odd nodes).
        level_width = tree_size
        proof_idx = 0
        while level_width > 1 and proof_idx < len(proof):
            if idx % 2 == 0:
                # Left child: sibling is on the right (if it exists).
                if idx + 1 < level_width:
                    computed = _interior_hash(computed, proof[proof_idx])
                    proof_idx += 1
                # else: node promoted as-is, no proof element consumed.
            else:
                # Right child: sibling is on the left.
                computed = _interior_hash(proof[proof_idx], computed)
                proof_idx += 1
            idx //= 2
            level_width = (level_width + 1) // 2
        return proof_idx == len(proof) and computed == root_hash

    # Original behavior (correct for power-of-2 trees).
    for sibling in proof:
        if idx % 2 == 0:
            # Leaf is a left child: sibling is on the right
            computed = _interior_hash(computed, sibling)
        else:
            # Leaf is a right child: sibling is on the left
            computed = _interior_hash(sibling, computed)
        idx = idx // 2
    return computed == root_hash


# ---------------------------------------------------------------------------
# Signed Tree Head (STH)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignedTreeHead:
    """A Signed Tree Head (STH) - the Merkle root signed by an external key.

    Attributes:
        tree_size: Number of entries in the tree.
        timestamp: Unix timestamp (seconds) when the STH was created.
        root_hash: The Merkle root hash (hex).
        signature: Ed25519 signature over (tree_size || timestamp || root_hash).
        key_id: Identifier of the signing key.
    """

    tree_size: int
    timestamp: int
    root_hash: str
    signature: str
    key_id: str


def _sth_signed_content(tree_size: int, timestamp: int, root_hash: str) -> bytes:
    """Build the bytes signed/verified for a Signed Tree Head.

    The signed content is: str(tree_size) || str(timestamp) || root_hash
    encoded as UTF-8.

    Args:
        tree_size: Number of entries in the tree.
        timestamp: Unix timestamp (seconds).
        root_hash: Merkle root hash (hex).

    Returns:
        The bytes to sign/verify.
    """
    return f"{tree_size}{timestamp}{root_hash}".encode("utf-8")


def sign_tree_head(
    tree: MerkleTree,
    private_key_bytes: bytes,
    key_id: str,
) -> SignedTreeHead:
    """Create a Signed Tree Head for a Merkle tree.

    Signs (tree_size || timestamp || root_hash) with Ed25519.

    Args:
        tree: The Merkle tree to sign.
        private_key_bytes: Raw 32-byte Ed25519 private key.
        key_id: Identifier of the signing key.

    Returns:
        A SignedTreeHead with the Ed25519 signature (base64-encoded).

    Raises:
        ImportError: If the cryptography package is not installed.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    tree_size = tree.size()
    timestamp = int(time.time())
    root = tree.root_hash()
    content = _sth_signed_content(tree_size, timestamp, root)
    sig = key.sign(content)
    return SignedTreeHead(
        tree_size=tree_size,
        timestamp=timestamp,
        root_hash=root,
        signature=base64.b64encode(sig).decode("ascii"),
        key_id=key_id,
    )


def verify_tree_head(
    sth: SignedTreeHead,
    public_key_bytes: bytes,
) -> bool:
    """Verify a Signed Tree Head's Ed25519 signature.

    Args:
        sth: The Signed Tree Head to verify.
        public_key_bytes: Raw 32-byte Ed25519 public key.

    Returns:
        True if the signature is valid, False otherwise.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        sig = base64.b64decode(sth.signature)
        content = _sth_signed_content(sth.tree_size, sth.timestamp, sth.root_hash)
        key.verify(sig, content)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


# ---------------------------------------------------------------------------
# Consistency proof (RFC 6962 Section 2.1.2)
# ---------------------------------------------------------------------------


def _build_level(hashes: list[str]) -> list[str]:
    """Build the next tree level from the current level.

    Args:
        hashes: Current level of node hashes.

    Returns:
        Next level (parent nodes), with odd nodes promoted as-is.
    """
    next_level: list[str] = []
    i = 0
    while i < len(hashes):
        if i + 1 < len(hashes):
            next_level.append(_interior_hash(hashes[i], hashes[i + 1]))
            i += 2
        else:
            next_level.append(hashes[i])
            i += 1
    return next_level


def _subtree_root(hashes: list[str]) -> str:
    """Compute the root of a subtree given a list of node hashes at one level.

    Args:
        hashes: Node hashes at a single level.

    Returns:
        The root hash of the subtree.
    """
    level = list(hashes)
    while len(level) > 1:
        level = _build_level(level)
    return level[0] if level else _empty_root()


def consistency_proof(
    old_tree: MerkleTree,
    new_tree: MerkleTree,
) -> list[str]:
    """Generate a consistency proof that new_tree extends old_tree.

    Returns the list of intermediate hashes needed to verify that
    new_tree's root is consistent with old_tree's root (no fork).
    Implements RFC 6962 Section 2.1.2 consistency proof algorithm.

    The proof consists of the subtree roots that tile [0, old_size)
    followed by the subtree roots that tile [old_size, new_size)
    in the new tree. The verifier reconstructs old_root from the
    first set and new_root from the full set.

    Args:
        old_tree: The earlier (smaller) Merkle tree.
        new_tree: The later (larger) Merkle tree.

    Returns:
        List of hex-encoded hashes forming the consistency proof.

    Raises:
        ValueError: If old_tree is larger than new_tree, or if old_tree is empty
            (consistency with an empty tree is trivially true).
    """
    old_size = old_tree.size()
    new_size = new_tree.size()
    if old_size == 0:
        return []
    if old_size > new_size:
        raise ValueError(
            f"old tree size {old_size} exceeds new tree size {new_size}"
        )
    if old_size == new_size:
        return []

    new_leaves = list(new_tree.leaves)

    # Build all levels of the new tree for subtree root lookup.
    levels: list[list[str]] = [list(new_leaves)]
    while len(levels[-1]) > 1:
        levels.append(_build_level(levels[-1]))

    def _decompose(start: int, size: int) -> list[str]:
        """Decompose [start, start+size) into aligned perfect subtrees.
        Returns the root hash of each subtree."""
        result: list[str] = []
        remaining = size
        offset = start
        while remaining > 0:
            k = 1
            while k * 2 <= remaining and (offset % (k * 2)) == 0:
                k *= 2
            level = k.bit_length() - 1
            idx = offset >> level
            result.append(levels[level][idx])
            offset += k
            remaining -= k
        return result

    # Old subtree roots (cover [0, old_size)) + new subtree roots (cover [old_size, new_size))
    return _decompose(0, old_size) + _decompose(old_size, new_size - old_size)


def verify_consistency_proof(
    old_root: str,
    old_size: int,
    new_root: str,
    new_size: int,
    proof: list[str],
) -> bool:
    """Verify a consistency proof.

    Verifies that the new tree (size new_size, root new_root) is a valid
    extension of the old tree (size old_size, root old_root).

    The proof consists of subtree roots that tile [0, old_size) followed
    by subtree roots that tile [old_size, new_size) in the new tree.
    The verifier:
    1. Reconstructs old_root from the first set of subtree roots
    2. Reconstructs new_root from all subtree roots using a stack-based
       tree-building algorithm

    Args:
        old_root: Root hash of the old tree (hex).
        old_size: Number of leaves in the old tree.
        new_root: Root hash of the new tree (hex).
        new_size: Number of leaves in the new tree.
        proof: Consistency proof (list of hex hashes).

    Returns:
        True if the proof is valid, False otherwise.
    """
    if old_size == 0:
        return len(proof) == 0
    if old_size > new_size:
        return False
    if old_size == new_size:
        return old_root == new_root and len(proof) == 0

    def _decompose_sizes(start: int, size: int) -> list[int]:
        """Decompose [start, start+size) into aligned perfect subtree sizes."""
        sizes: list[int] = []
        remaining = size
        offset = start
        while remaining > 0:
            k = 1
            while k * 2 <= remaining and (offset % (k * 2)) == 0:
                k *= 2
            sizes.append(k)
            offset += k
            remaining -= k
        return sizes

    old_sizes = _decompose_sizes(0, old_size)
    new_sizes = _decompose_sizes(old_size, new_size - old_size)
    all_sizes = old_sizes + new_sizes

    if len(proof) != len(all_sizes):
        return False

    # Phase 1: Reconstruct old_root from the first len(old_sizes) proof nodes.
    proof_idx = 0
    old_hash: str | None = None
    for _ in old_sizes:
        node = proof[proof_idx]
        proof_idx += 1
        if old_hash is None:
            old_hash = node
        else:
            old_hash = _interior_hash(old_hash, node)

    if old_hash != old_root:
        return False

    # Phase 2: Reconstruct new_root from all proof nodes.
    # Build the tree using a stack: push nodes left-to-right, combining
    # adjacent same-size pairs (like a binary counter).
    stack: list[tuple[int, str]] = []
    for size, h in zip(all_sizes, proof):
        stack.append((size, h))
        while len(stack) >= 2 and stack[-2][0] == stack[-1][0]:
            s2, h2 = stack.pop()
            s1, h1 = stack.pop()
            stack.append((s1 * 2, _interior_hash(h1, h2)))

    # Combine any remaining stack elements (non-perfect tree root).
    while len(stack) >= 2:
        s2, h2 = stack.pop()
        s1, h1 = stack.pop()
        stack.append((s1 + s2, _interior_hash(h1, h2)))

    if len(stack) != 1:
        return False

    return stack[0][1] == new_root


# ---------------------------------------------------------------------------
# Witness cosigning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WitnessCosignature:
    """A witness cosignature on a Signed Tree Head.

    Attributes:
        witness_id: Identifier of the witness.
        signature: Ed25519 signature over the STH's signed content.
    """

    witness_id: str
    signature: str


def cosign_tree_head(
    sth: SignedTreeHead,
    witness_private_key: bytes,
    witness_id: str,
) -> WitnessCosignature:
    """A witness cosigns an STH, providing independent attestation.

    Args:
        sth: The Signed Tree Head to cosign.
        witness_private_key: Raw 32-byte Ed25519 private key of the witness.
        witness_id: Identifier of the witness.

    Returns:
        A WitnessCosignature with the base64-encoded Ed25519 signature.

    Raises:
        ImportError: If the cryptography package is not installed.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.from_private_bytes(witness_private_key)
    content = _sth_signed_content(sth.tree_size, sth.timestamp, sth.root_hash)
    sig = key.sign(content)
    return WitnessCosignature(
        witness_id=witness_id,
        signature=base64.b64encode(sig).decode("ascii"),
    )


def verify_witness_cosignature(
    sth: SignedTreeHead,
    cosignature: WitnessCosignature,
    witness_public_key: bytes,
) -> bool:
    """Verify a witness cosignature on an STH.

    Args:
        sth: The Signed Tree Head that was cosigned.
        cosignature: The witness cosignature to verify.
        witness_public_key: Raw 32-byte Ed25519 public key of the witness.

    Returns:
        True if the cosignature is valid, False otherwise.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        key = Ed25519PublicKey.from_public_bytes(witness_public_key)
        sig = base64.b64decode(cosignature.signature)
        content = _sth_signed_content(sth.tree_size, sth.timestamp, sth.root_hash)
        key.verify(sig, content)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


# ---------------------------------------------------------------------------
# Tuple log anchoring (main entry point)
# ---------------------------------------------------------------------------


def anchor_tuple_log(
    tuple_log_path: str,
    private_key_bytes: bytes,
    key_id: str,
) -> SignedTreeHead:
    """Build a Merkle tree from a tuple log JSONL file and sign the tree head.

    Reads the JSONL file, computes content_hash for each tuple, builds a
    Merkle tree, and signs the tree head. This is the main entry point
    for periodic anchoring.

    Each line of the JSONL file is a serialized BaseNTuple. The content_hash
    is recomputed from the tuple (excluding signature and signature_algorithm
    fields), so the anchor is over the tuple content, not the stored JSON.

    Args:
        tuple_log_path: Path to the JSONL tuple log file.
        private_key_bytes: Raw 32-byte Ed25519 private key for signing.
        key_id: Identifier of the signing key.

    Returns:
        A SignedTreeHead anchoring the entire tuple log.

    Raises:
        ImportError: If the cryptography package is not installed.
        FileNotFoundError: If the tuple log file does not exist.
    """
    from hummbl_governance.primitives import BaseNTuple

    log_path = Path(tuple_log_path)
    entry_hashes: list[str] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data: dict[str, Any] = json.loads(line)
            # Reconstruct the tuple to compute its content hash deterministically.
            t = BaseNTuple(**data)
            entry_hashes.append(t.content_hash())

    tree = MerkleTree.from_entries(entry_hashes)
    return sign_tree_head(tree, private_key_bytes, key_id)
