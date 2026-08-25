# ADR-002: Bus File Permissions Standard
**Status**: ACCEPTED  
**Date**: 2026-05-04  
**Author**: Reuben Bowlby  
**Deciders**: Reuben Bowlby

---

## Context

The coordination bus is an append-only TSV file written by multiple agent processes. The
bus file contains potentially sensitive coordination data (agent actions, capability grants,
budget events). The file permission policy determines who can read or write the bus outside
the owning process.

A bug was found on 2026-05-04: `bus_writer.py:776` was setting permissions to `0o660`
(owner + group read/write) despite the PRD (F-BUS-010) and the function docstring specifying
`0o600` (owner-only). This ADR records the correct policy and rationale.

---

## Decision

Bus file permissions are set to **`0o600`** (owner read/write only) on creation and enforced
on each write on POSIX systems.

```python
path.chmod(0o600)
```

On Windows, `chmod` is a no-op for these bits; the platform-specific security model applies.
The implementation gracefully skips the chmod on Windows without error.

---

## Rationale

**Why 0o600 and not 0o660?**

`0o660` grants group read/write, which would allow any process running as the same group
to read or append to the bus. In a multi-user server environment (nodezero, shared CI
runners), this creates two risks:

1. **Confidentiality**: Group-readable bus exposes agent coordination history to other
   processes in the same group.
2. **Integrity**: Group-writable bus allows any group member to inject arbitrary messages
   into the coordination log.

`0o600` restricts access to the owning process's user only. Group members cannot read
or append.

**Why not 0o644?**

`0o644` (owner read/write, group+world read) would allow any user on the system to read
the bus. This violates the principle of least privilege for a coordination log that may
contain sensitive agent state.

**Why not 0o400?**

Read-only permissions would prevent the bus writer from appending. The bus is append-only
but append still requires write permission.

---

## Consequences

- Bus contents are only readable by the process owner. ✅
- Cross-user or cross-process bus inspection requires explicit permission escalation. ✅
- On multi-user systems, each user's bus is isolated. ✅
- Group-based log aggregation (e.g., centralised log readers) cannot read the bus directly —
  they must go through the bridge server API. ⚠️
- Windows: no enforcement at the OS level; trust the bridge server access controls. ⚠️

---

## Supersedes

PRD F-BUS-010 remains the source of truth for the functional spec. This ADR documents
the rationale behind the `0o600` choice and records the correction of the `0o660` bug.
