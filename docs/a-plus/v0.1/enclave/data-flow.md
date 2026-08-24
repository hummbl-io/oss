# Data-Flow and Exfiltration Model

**DRAFT — NON-CANONICAL — NOT AUTHORIZED FOR DEPLOYMENT**

Modes are explicit and mutually exclusive:

- `synthetic_public_autonomous`: synthetic/public input, allowlisted simulation
  outputs, no external writes.
- `sensitive_read_only`: labeled sensitive reads, no write gateway, constrained
  redacted outputs and approved destinations.
- `confidential_transform`: bounded transformation, taint-preserving outputs,
  approved destination and quota.
- `secret_unrestricted_output`: **PROHIBITED**.

Labels propagate through prompts, tool responses, files, logs, artifacts and
gateway requests. Destinations require classification compatibility. Content
inspection, output quotas, artifact scanning and log hygiene are mandatory.
Git, tickets, DNS, timing, error messages and image metadata are potential
exfiltration channels. Covert channels remain residual risk; arbitrary secret
access plus unrestricted communication cannot guarantee non-exfiltration.
