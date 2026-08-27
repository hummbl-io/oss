# HUMMBL Agent Fleet Trust-Boundary Diagram

**Standard:** S8 #3 (trust-boundary diagram)
**Issue:** #409 (gap-4)
**Federal standards:** NIST 800-53 RA-3, SC-7
**Date:** 2026-08-27
**Status:** ACTIVE

## Data flow diagram

```
                    EXTERNAL UNTRUSTED ZONE
    ┌──────────────────────────────────────────────────────────┐
    │                                                          │
    │   ┌─────────────┐      ┌─────────────┐                  │
    │   │   GitHub    │      │ Cloudflare  │                  │
    │   │   API       │      │   Edge      │                  │
    │   │             │      │             │                  │
    │   └──────┬──────┘      └──────┬──────┘                  │
    │          │                    │                          │
    └──────────┼────────────────────┼──────────────────────────┘
               │                    │
        ═══════╪════════════════════╪══════ BOUNDARY 1 (GitHub API + TLS)
               │                    │
        ═══════╪════════════════════╪══════ BOUNDARY 2 (Cloudflare Access + TLS)
               │                    │
               │              ┌─────▼──────┐
               │              │ cloudflared │
               │              │   tunnel    │
               │              └─────┬──────┘
               │                    │
    ┌──────────┼────────────────────┼──────────────────────────┐
    │          │          INTERNAL SEMI-TRUSTED ZONE            │
    │          │                    │                           │
    │    ┌─────▼──────┐    ┌────────▼───────┐                  │
    │    │  GitHub    │    │  Internal      │                  │
    │    │  Operations│    │  Services      │                  │
    │    │  (repos,   │    │  (bus bridge,  │                  │
    │    │   CI, etc) │    │   dashboards)  │                  │
    │    └─────┬──────┘    └────────┬───────┘                  │
    │          │                    │                           │
    │          │              ┌─────▼──────┐                    │
    │          │              │  Bus TSV   │                    │
    │          │              │  (append-  │                    │
    │          │              │   only)    │                    │
    │          │              └─────┬──────┘                    │
    │          │                    │                           │
    │    ┌─────▼────────────────────▼──────┐                    │
    │    │     PRE-MUTATION GATE (gap-1)   │                    │
    │    │                                 │                    │
    │    │  1. Resolve identity (gap-1)    │                    │
    │    │  2. Classify severity (gap-1)   │                    │
    │    │  3. Authority check (gap-9)     │                    │
    │    │  4. Two-person rule (HIGH/CRIT) │                    │
    │    │  5. Return GateDecision         │                    │
    │    └─────────────┬───────────────────┘                    │
    │                  │                                        │
    │    ═══════════════╪═══════════════════ BOUNDARY 3         │
    │                  │   (Gate -> GitHub API)                 │
    │                  │                                        │
    │    ┌─────────────▼───────────────────┐                    │
    │    │     AUTH PROVIDER (gap-3)       │                    │
    │    │                                 │                    │
    │    │  EnvVarAuthProvider (default)   │                    │
    │    │  PATAuthProvider                │                    │
    │    │  GitHubAppAuthProvider          │                    │
    │    └─────────────┬───────────────────┘                    │
    │                  │                                        │
    │    ═══════════════╪═══════════════════ BOUNDARY 4         │
    │                  │   (Credential -> API call)             │
    │                  │                                        │
    │    ┌─────────────▼───────────────────┐                    │
    │    │     AGENT CLI RUNTIMES          │                    │
    │    │                                 │                    │
    │    │  devin   codex   claude-code    │                    │
    │    │  opencode   gemini              │                    │
    │    └─────────────┬───────────────────┘                    │
    │                  │                                        │
    │    ═══════════════╪═══════════════════ BOUNDARY 5         │
    │                  │   (Agent -> Credential Manager)        │
    │                  │                                        │
    │    ┌─────────────▼───────────────────┐                    │
    │    │   WINDOWS CREDENTIAL MANAGER    │                    │
    │    │   (OS-managed token storage)    │                    │
    │    └─────────────────────────────────┘                    │
    │                                                           │
    │    ┌─────────────────────────────────┐                    │
    │    │       GPG KEYRING (gap-2)       │                    │
    │    │                                 │                    │
    │    │  operator  devin   codex        │                    │
    │    │  claude-code  opencode  gemini  │                    │
    │    │  (EdDSA/ed25519, 2y expiry)     │                    │
    │    └─────────────────────────────────┘                    │
    │                                                           │
    └───────────────────────────────────────────────────────────┘
               │
        ═══════╪══════════════════════════════════════ BOUNDARY 6
               │   (Tailscale WireGuard + ACLs)
               │
    ┌──────────▼───────────────────────────────────────────────┐
    │                  TAILSCALE MESH                           │
    │                                                          │
    │   ┌─────────┐     ┌─────────┐     ┌─────────┐           │
    │   │  Anvil  │─────│  Delta  │─────│   VPS   │           │
    │   │ (agent  │     │ (agent  │     │ (bus    │           │
    │   │  host)  │     │  host)  │     │  bridge)│           │
    │   └─────────┘     └─────────┘     └─────────┘           │
    │                                                          │
    └──────────────────────────────────────────────────────────┘
               │
        ═══════╪══════════════════════════════════════ BOUNDARY 7
               │   (Operator physical access + OS login)
               │
    ┌──────────▼───────────────────────────────────────────────┐
    │                  TRUSTED ZONE (OPERATOR)                  │
    │                                                          │
    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
    │   │  Operator   │  │  Operator   │  │  Operator   │     │
    │   │  (human)    │  │  GPG key    │  │  OS admin   │     │
    │   │             │  │  (private)  │  │  access     │     │
    │   └─────────────┘  └─────────────┘  └─────────────┘     │
    │                                                          │
    └──────────────────────────────────────────────────────────┘
```

## Boundary summary

| Boundary | Zone transition | Protection mechanism | Gap status |
|----------|----------------|---------------------|------------|
| 1 | Internal -> GitHub | Per-agent auth (gap-3), TLS | Built |
| 2 | Public -> Cloudflare -> internal | Cloudflare Access policy, TLS | Existing |
| 3 | Gate -> GitHub API | Gate authorization, two-person rule | Built (gap-1) |
| 4 | Credential -> API call | Auth provider abstraction (gap-3) | Built |
| 5 | Agent -> Credential Manager | OS-managed token storage | Existing |
| 6 | Host <-> Host (Tailscale) | WireGuard encryption, ACLs | Existing |
| 7 | Operator -> machine | OS login, physical access | Existing |

## Data flow descriptions

### Flow A: Agent commits to GitHub repo

```
Agent CLI -> AuthProvider.resolve(agent_id) -> AgentCredential
          -> PreMutationGate.check(agent_id, operation, action)
            -> IdentityResolver.resolve(agent_id) -> identity
            -> classify_mutation(operation, action) -> severity
            -> AuthorityEngine.check(agent_id, authority) -> permitted?
            -> if HIGH/CRITICAL: verify DECISION receipt
          -> if permitted: GitHub API call with AgentCredential.token
          -> if denied: raise PermissionError
```

### Flow B: Agent posts to coordination bus

```
Agent CLI -> bus-global.py post <sender> <recipient> <type> <message>
          -> HTTP bridge (authenticated)
          -> append to bus TSV file (local on VPS)
          -> [FUTURE: gap-6 Merkle hash-chaining + STH publication]
```

### Flow C: CI pipeline execution

```
GitHub PR/Push -> GitHub Actions webhook
              -> Self-hosted runner on Anvil
              -> Checkout repo
              -> Run tests, lint, validators
              -> Report status to GitHub
              -> Branch protection requires "ci" check to pass
```

## Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-27 | Initial trust-boundary diagram created (gap-4) | devin |
