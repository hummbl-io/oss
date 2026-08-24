# Opportunity Register

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

| Opportunity                                   | Decision   | Value / risk                                             | Next gate                |
| --------------------------------------------- | ---------- | -------------------------------------------------------- | ------------------------ |
| Existing HUMMBL receipt/cross-check contracts | Adapt      | reuse reduces drift; verifier gaps remain                | contract crosswalk       |
| Policy-as-code / model checking               | Experiment | catches composition errors; modeling cost                | bounded simulation       |
| SPIFFE-like workload identity                 | Adapt      | rotation and domain separation; trust-root risk          | identity contract review |
| Transparency/witness service                  | Experiment | evidence survivability; availability cost                | witness fault test       |
| Deterministic simulation                      | Adopt      | safe effect rehearsal                                    | fixture coverage         |
| Explainable operator UX                       | Adapt      | improves intent review; false confidence risk            | usability review         |
| Red-team automation                           | Adopt      | repeatable adversarial evidence; self-certification risk | non-author review        |
| Enterprise-wide privileged runtime            | Avoid      | unacceptable blast radius                                | prohibited               |
