# Control and Invariant Catalog

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

| ID  | Invariant                                                 | Measure / evidence               |
| --- | --------------------------------------------------------- | -------------------------------- |
| C01 | No ambient admin credential enters model context          | secret scan and lease inspection |
| C02 | Capabilities are short-lived, non-transitive, nonce-bound | contract validator               |
| C03 | Every effect binds exact plan and target version          | gateway CAS receipt              |
| C04 | Unknown fields, selectors, scripts and wildcards deny     | negative fixtures                |
| C05 | External evidence survives guest compromise               | witness consistency test         |
| C06 | Runtime cannot mint, renew, waive or redelegate           | issuer integration test          |
| C07 | Secret-plus-unrestricted-output mode is prohibited        | mode classifier                  |
| C08 | Revocation works without guest cooperation                | out-of-band revocation exercise  |
| C09 | Recovery uses separate credentials, keys and network      | restore exercise                 |
| C10 | Human-required triggers cannot be downgraded              | review classifier fixtures       |
| C11 | Component digest mutation invalidates leases/reviews      | attestation drift test           |
| C12 | Failures and partitions default to no external write      | fault-injection test             |
