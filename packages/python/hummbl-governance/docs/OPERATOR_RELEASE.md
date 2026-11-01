# Operator-controlled kill-switch release

Current source denies release by default. This is a breaking change planned for
the next release; installing the published 1.5.1 wheel does not apply this fix.

The general governance MCP servers expose status and engagement, but no release
tool. Calling the former `kill_switch_disengage` name or its old handler returns
an error. The general REST `/api/v1/kill-switch/disengage` endpoint returns 403
after API authentication, including with `confirm: true`. Its bearer token may
belong to an agent and grants no release authority. Engagement can repeat or
increase the current halt level; it cannot weaken it. Reducing restrictions
requires a separate operator release. Both MCP wrappers refuse engagement when
loaded with an older core lacking the release-authorization capability. Adopt
the fixed governance core and wrapper together; updating only a wrapper cannot
repair direct library calls in an older installed core. Cached MCP and REST
instances use verified authoritative reads at every mode, status, history and
task decision. They observe both external stops and operator releases without a
restart. Missing credentials, missing/corrupt state, and failed engagement lock
setup fail closed. After a failed engagement write or lock setup, the affected
instance refuses decisions until it successfully persists an explicit EMERGENCY.
MCP wrappers also reject older cores without authoritative-read support.

## Required deployment boundary

Use a separately protected operator account/process for the control path. The
operator credential, its configured verifier and identity, the installed control
code, and state-directory write permissions must be outside governed agents'
control. Keep `release_authority=None` on agent-facing core objects. Do not expose
the operator CLI as an agent shell tool, share its environment with agents, or
load operator credentials into an MCP/API process. A differently named token in
the same agent-readable environment does not establish this boundary.

The library authenticates possession of an operator credential assigned by the
deployer to one configured operator identity. It does not independently establish
that a human is at the keyboard. Protect that credential and channel accordingly.
It cannot isolate arbitrary Python running in its own process, an attacker with
the operator account's privileges, or a caller that can replace configuration or
write signed state directly. State HMACs protect integrity; possession of the
state-signing key is **not** release authorization through the core API, but a
holder with direct state write access can bypass the API. If agents have those
privileges, first separate the service/account and filesystem permissions.

All cooperating state writers must run this version. They serialize transitions
using the persistent `.kill-switch.lock` in the state directory; do not delete
that file while writers are active. Older writers or direct file writes bypass
this coordination. The persisted file contains the latest event, not a complete
cross-process audit log; retain release events in your protected audit service
when a full history is required.

## Initial state and server startup

The REST and MCP servers require existing signed state at their explicitly
configured state directory. An empty directory is not evidence of DISENGAGED
state, and a server read never initializes or repairs it. Before first startup,
a trusted provisioning process can construct `KillSwitch(state_dir=...)` with
the protected state-signing key and deliberately call
`engage(KillSwitchMode.EMERGENCY, reason, triggered_by)`. This creates a signed
halt, not permission to work. Review the deployment and use the authenticated
operator release path below before resuming normal work. The release command
itself does not perform initialization. Restoring a missing file or signing key
alone must not be treated as release approval.

## Local operator command

There is no new network listener or external authentication dependency. The
wheel includes the interactive command:

```sh
python -m hummbl_governance.operator_release --state-dir /protected/governance --reason "Remediation verified"
```

Before running it, a trusted launcher under the operator account must supply:

| Configuration | Meaning |
| --- | --- |
| `GOVERNANCE_OPERATOR_ID` | Fixed operator identity associated with the credential, set by the deployer |
| `GOVERNANCE_OPERATOR_CREDENTIAL_VERIFIER` | Versioned salted PBKDF2 verifier of a separate high-entropy operator credential |
| `HUMMBL_SIGNING_SECRET` (or `DCT_SECRET`) | Existing state integrity key, obtained from the protected secret store |

Generate the operator credential with at least 32 cryptographically random bytes
and keep it in the operator's secret store. Use a different credential from any
agent/API token and from the state-signing key. Provision its verifier with
`OperatorReleaseAuthority.create_verifier(credential)` in the trusted operator
process. This generates a fresh 16-byte random salt and derives a 32-byte verifier
with PBKDF2-HMAC-SHA256 at 600,000 iterations. The expensive KDF also slows offline
guessing if a weaker value is supplied; it does not replace the long random
credential requirement. This work factor follows the
[OWASP PBKDF2 guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2).
The implementation uses [Python's standard-library KDF](https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac)
with an OpenSSL-enabled Python build.

The accepted format is exactly
`pbkdf2-sha256-v1$600000$<32 lowercase salt hex characters>$<64 lowercase digest hex characters>`.
Malformed, unsupported, or cheaper verifiers are rejected; plain SHA-256 verifiers
are not accepted. Input credentials are bounded to 1,024 UTF-8 bytes. Keep the
verifier and identity in protected startup configuration, never request fields.
For example, a trusted provisioning process can obtain the secret without echo:

```python
from getpass import GetPassWarning, getpass
import warnings
from hummbl_governance.kill_switch import OperatorReleaseAuthority

with warnings.catch_warnings():
    warnings.simplefilter("error", GetPassWarning)  # Never fall back to echoed input.
    verifier = OperatorReleaseAuthority.create_verifier(getpass("Operator credential: "))
# Transfer verifier to protected operator configuration through your secret store.
# Never put the raw credential in command arguments, logs, or agent environments.
```

Rotate
by replacing that protected verifier and retiring the old secret. This command
does not provision credentials, initialize missing state, repair corrupt state,
or release anything when configuration is absent.

The command reads and verifies existing signed state, displays the halt and
release reason, and requires typing `RELEASE <event_id>`. It then prompts for the
operator credential without echo. Noninteractive input and unavailable hidden
input fail closed; credentials are not command-line options. An updated halt,
a repeated/replayed release, missing or wrong credentials, or failed persistence
prevents success. Re-read and reconfirm a changed halt after reviewing its cause.

## Embedding in a trusted operator service

Import `OperatorReleaseAuthority` and `KillSwitchAuthorizationError` from
`hummbl_governance.kill_switch`. Configure an authority at trusted startup, using
only the protected operator ID and verifier. Pass it to `KillSwitch` or
`KillSwitch.load_from_file(..., release_authority=authority)`. Do not let request
payloads choose the authority, identity, or credential verifier.

`disengage` requires all of `credential`, literal `confirm=True`, a nonblank
`reason`, and `expected_event_id` from the reviewed halt's `get_status()` result.
The core authenticates the credential, then checks that exact halt under the
same cross-process lock used for writing the release. Each transition gets a new
random event ID, including repeated emergencies. Older signed states without an
ID receive a stable content-derived challenge until their next transition.

The resulting event's `triggered_by` is always the identity returned by the
configured authority. Optional caller-supplied `triggered_by` is untrusted and
recorded separately as `requested_by`; it cannot choose the authenticated actor.
A successful state load does not inherit a release authority. Configure it
explicitly only in the operator control process. An in-memory switch likewise
requires a configured authority for release.

## Regression contract

Tests reproduce the former reason-only MCP release of HALT_ALL and EMERGENCY,
then assert denial even with forged operator attribution, confirmation, and a
credential supplied to the hidden tool call. Additional tests cover direct core
calls without authority, invalid credentials, non-boolean confirmation, stale
and replayed halt IDs, persisted identity, fresh-instance downgrade attempts,
legacy state, process serialization, and an authenticated operator release.
The general API credential is tested as insufficient. All tests use temporary
state and synthetic credentials; no running deployment is operated by them.
