"""Governance primitives: BaseNTuple, TupleSchemaRegistry, AdversarialTupleGenerator, MerkleAnchor.

New in v1.3.0: BaseNTuple universal governance tuple with KRINEIA 4-node fields,
tiered emission (0/0S/1/2/3), dual signing (HMAC-SHA256 + Ed25519), Property 3
verification (ops_executed ⊆ ops_allowed), READ_EVIDENCE for sensitive reads,
REVOCATION tuple for immediate authority withdrawal.

Also includes TupleSchemaRegistry for versioned schema migrations with
BACKWARD/FORWARD/FULL compatibility checking, and AdversarialTupleGenerator
with 35 attack tuples across 8 categories for negative testing.

New in v1.4.0: MerkleAnchor — CT-style Merkle anchoring (RFC 6962) for
governance tuple logs with inclusion proofs, consistency proofs, and
witness cosigning.
"""

from .basen_tuple import (
    BaseNTuple,
    create_evidence_tuple,
    create_read_evidence_tuple,
    create_governed_tuple,
    create_chain_tuple,
    create_revocation_tuple,
    sign_tuple,
    sign_tuple_ed25519,
    verify_tuple,
    verify_tuple_signature,
    verify_tuple_ed25519,
    generate_ed25519_keypair,
    append_tuple,
    get_signing_secret,
    _sha256,
)

from .tuple_schema_registry import (
    TupleSchemaRegistry,
    migrate_tuple,
    check_compatibility,
    get_golden_fixture,
    validate_fixture,
    CURRENT_VERSION,
    SCHEMA_VERSIONS,
    COMPATIBILITY_MODES,
)

from .merkle_anchor import (
    MerkleTree,
    SignedTreeHead,
    WitnessCosignature,
    anchor_tuple_log,
    consistency_proof,
    cosign_tree_head,
    sign_tree_head,
    verify_consistency_proof,
    verify_inclusion_proof,
    verify_tree_head,
    verify_witness_cosignature,
)

# Test utility (not part of public API)
from .adversarial_tuples import AdversarialTupleGenerator

__all__ = [
    # BaseNTuple
    "BaseNTuple",
    "create_evidence_tuple",
    "create_read_evidence_tuple",
    "create_governed_tuple",
    "create_chain_tuple",
    "create_revocation_tuple",
    "sign_tuple",
    "sign_tuple_ed25519",
    "verify_tuple",
    "verify_tuple_signature",
    "verify_tuple_ed25519",
    "generate_ed25519_keypair",
    "_sha256",
    "append_tuple",
    "get_signing_secret",
    # TupleSchemaRegistry
    "TupleSchemaRegistry",
    "migrate_tuple",
    "check_compatibility",
    "get_golden_fixture",
    "validate_fixture",
    "CURRENT_VERSION",
    "SCHEMA_VERSIONS",
    "COMPATIBILITY_MODES",
    # MerkleAnchor (v1.4.0)
    "MerkleTree",
    "SignedTreeHead",
    "WitnessCosignature",
    "anchor_tuple_log",
    "consistency_proof",
    "cosign_tree_head",
    "sign_tree_head",
    "verify_consistency_proof",
    "verify_inclusion_proof",
    "verify_tree_head",
    "verify_witness_cosignature",
    # Test utility
    "AdversarialTupleGenerator",
]
