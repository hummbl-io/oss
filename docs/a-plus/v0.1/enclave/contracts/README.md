# Versioned Contracts

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

All contracts use JSON Schema draft 2020-12, UTF-8, sorted keys for signing,
explicit schema versions, UUID identifiers, issuer/subject/delegation lineage,
nonce, issue/expiry/freshness times, invalidation, evidence sink, and fail-closed
partition semantics. Capabilities are short-lived, non-transitive, and cannot be
minted, renewed, waived, or redelegated by the runtime.
