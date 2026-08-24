# Independent Review Handoff

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

Review the exact package identified by `package-manifest.json` after it is
committed and its SHA-256 is frozen. The manifest uses explicit self-exclusion:
`package-manifest.json` is not included in the payload hash because its hash
field would otherwise create a circular digest. Every other committed file in
this directory, including this handoff, must appear in `files` and be hashed.
Retrieve the artifact independently;
inspect every contract, validator and fixture; run `python validate_enclave.py`;
test unknown fields, prohibited secret mode, stale state, wildcard selectors,
conflicted reviewers, replay/revocation and partition behavior; and issue a
receipt using the existing HUMMBL cross-check protocol.

The reviewer must be non-author, registry-eligible, unconflicted, independently
retrieving evidence, and must disposition every applicable review dimension.
No reviewer may waive human-required work, unresolved P0/P1 risk, or operator
adoption. Any mutation invalidates this handoff and requires a new package hash.
