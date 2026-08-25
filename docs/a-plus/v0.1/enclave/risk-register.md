# Risk and Residual-Risk Register

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

| Risk                       | Severity | Disposition                                            | Gate                     |
| -------------------------- | -------- | ------------------------------------------------------ | ------------------------ |
| Control-plane collusion    | Critical | prohibit enterprise deployment; quorum design required | formal compromise test   |
| Covert exfiltration        | High     | residual; restrict modes and destinations              | data-flow test           |
| Hypervisor escape          | Critical | disposable-only until independent lab evidence         | escape exercise          |
| Evidence truth gap         | High     | integrity is not truth/completeness                    | independent verification |
| Recovery domain compromise | Critical | separate keys/operators/networks                       | restore exercise         |
| Gateway semantic mismatch  | High     | typed effects + CAS + simulation                       | effect test catalog      |
| Supply-chain mutation      | High     | digest admission and revocation                        | provenance test          |
| Multi-agent composition    | High     | global graph and aggregate quotas                      | collusion test           |
