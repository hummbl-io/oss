# Third-Party Fork & Upstream Contribution Protocol v0.1

**Status: PROPOSED FLEET STANDARD — MANDATORY AGENT GATE FOR ACTIVE THIRD-PARTY FORKS**

Issue: hummbl-io/hummbl-governance#239

## Purpose

Define a mandatory preflight gate that ensures upstream contribution instructions are inspected and followed before any external issue, comment, discussion, or PR action from an agent fork.

A fork is a workspace only. It does not grant permission to represent upstream, imply maintainership, or alter upstream governance semantics without validation and authorization.

## Foundation issues

- #204 (hummbl-io/hummbl-io): Repository clones vs. forks — Git, platform, and governance model
- #125 (hummbl-io/hummbl-governance): standards: apply HUMMBL_FORK boundary files to fork and import repos
- #205 (hummbl-io/hummbl-io): External Collaboration Program v0.1
- #208 (hummbl-io/hummbl-io): Define External Representation Contract v0.1 and collaboration receipts

These establish topology, boundaries, and external-representation controls. This protocol adds the single enforceable preflight that ensures upstream contribution instructions are inspected and followed before any external action.

## Repository relationship classification

Before any external action, the agent must classify the repository relationship:

| Classification | Description | External actions permitted? |
|---|---|---|
| **HUMMBL-native** | Created and owned by HUMMBL | Yes — standard HUMMBL workflows apply |
| **HUMMBL-controlled fork** | Forked into hummbl-io org, HUMMBL owns the fork | Yes to fork-internal work; upstream actions require this protocol |
| **Preserved upstream import** | Copied for reference/dependency, not for contribution | No external actions unless upstream explicitly solicited |
| **Active third-party fork** | Forked for the purpose of contributing upstream | Yes, but **only after completing this protocol's preflight** |
| **Independent repository with shared history** | Not a fork, but shares git history | Treated as third-party — complete preflight |

## Mandatory preflight gate (v0.1)

Before any external issue, comment, discussion, or PR action, the agent must complete all five steps below. The preflight result must be recorded as a receipt before the action is taken.

### Step 1: Classify repository relationship

Determine which of the five classifications above applies. Record the classification and the evidence for it (remote URLs, org ownership, fork metadata).

### Step 2: Read upstream authority documents

Read the following files from the **upstream** repository (not the fork):

- `README*`
- `CONTRIBUTING*`
- `CODE_OF_CONDUCT*`
- `SECURITY*`
- `SUPPORT*`
- `GOVERNANCE*`
- `LICENSE*`
- Issue templates (`.github/ISSUE_TEMPLATE/*`)
- PR templates (`.github/PULL_REQUEST_TEMPLATE*` or `.github/pull_request_template.md`)
- `AGENTS.md` or equivalent agent instruction files
- CLA/DCO/sign-off requirements (often in CONTRIBUTING or a `CLA.md`)

If any required document is missing, record its absence. Missing documents do not default to permissive — they default to **caution** (no action without operator escalation).

### Step 3: Extract operative rules

From the authority documents, extract and record:

| Rule | Question |
|---|---|
| Unsolicited PRs | Are unsolicited PRs permitted? |
| Issue-first requirement | Must an issue be filed before a PR? |
| Contribution categories | What contribution types are accepted/rejected? |
| Branch/commit conventions | What naming and commit formats are required? |
| Required tests/formatting/docs | What CI checks must pass? |
| AI-generated disclosure | Are there AI-generated content disclosure requirements? |
| Sign-off/licensing | Is DCO sign-off, CLA, or specific licensing required? |
| Preferred PR scope/sizing | Are there limits on PR size or scope? |
| Explicit prohibitions | What actions are explicitly prohibited? |

### Step 4: Verify remote topology

Verify the git remote topology before action:

- `origin` = HUMMBL-controlled fork (or the fork being worked on)
- `upstream` = the original third-party repository
- If `upstream` is not configured, configure it: `git remote add upstream <upstream-url>`
- Verify the local branch is based on the current upstream `main` (or the appropriate base branch): `git fetch upstream && git rebase upstream/main`

### Step 5: Record preflight receipt

Record the preflight result as a structured receipt before taking the external action. The receipt must include:

```json
{
  "protocol_version": "0.1",
  "timestamp": "2026-08-22T...",
  "agent": "devin",
  "repository": "hummbl-io/<fork-name>",
  "upstream": "<upstream-org>/<upstream-repo>",
  "classification": "active-third-party-fork",
  "authority_documents_read": ["README.md", "CONTRIBUTING.md", "..."],
  "operative_rules": {
    "unsolicited_prs_permitted": true,
    "issue_first_required": true,
    "ai_disclosure_required": true,
    "dco_signoff_required": false,
    "..."
  },
  "remote_topology_verified": true,
  "preflight_pass": true,
  "operator_escalation": false
}
```

If any step fails or produces uncertain results, `preflight_pass` must be `false` and the agent must escalate to the operator before proceeding.

## Fail-closed defaults

When a rule cannot be determined from the authority documents:

| Unknown rule | Default |
|---|---|
| Unsolicited PRs permitted? | **No** — escalate to operator |
| Issue-first required? | **Yes** — file an issue first |
| AI disclosure required? | **Yes** — disclose AI-generated content |
| DCO/CLA required? | **Yes** — assume sign-off is required |
| Contribution categories | **Narrow scope only** — documentation or bug fixes; escalate for features |

## Operator escalation

The agent must escalate to the operator when:

1. The repository classification is ambiguous
2. A required authority document is missing and the action is not trivially safe
3. An operative rule cannot be determined and the fail-closed default is restrictive
4. The upstream has explicit AI-generated content prohibitions
5. The action would be the agent's first external interaction with this upstream
6. The action involves licensing, CLA, or legal implications

## Enforcement

This protocol is enforced by:

1. **Preflight script**: `scripts/fork_upstream_preflight.py` — automates steps 1-5 and generates the receipt
2. **Agent guardrails**: Each agent's guardrails file must reference this protocol for external actions
3. **Review gates**: PRs that touch external-facing actions must show a preflight receipt

## Scope

This protocol applies to all HUMMBL agents that interact with third-party repositories:

- `devin`
- `codex`
- `claude-code`
- `opencode`
- `gemini`
- any future agent that forks or contributes to third-party repositories

## Limitations of v0.1

- The preflight is a checklist, not an automated policy engine
- Authority document parsing is manual (the script reads files but does not interpret them)
- No cross-repo receipt registry yet (receipts are per-action, not aggregated)
- No automated blocking (enforcement is via guardrails and review, not technical gates)

Future versions may add:
- Automated authority document parsing
- Cross-repo receipt registry
- Technical blocking via pre-commit hooks or CI gates
- Integration with the External Collaboration Program (#205)

## Related

- `docs/cross-repo-contract-standard-v0.1.md` — cross-repo contract identifiers and compatibility
- `docs/gates/admission-gates-reuploads-issues-prs.md` — admission gates for uploads, issues, and PRs
- Issue #125 — HUMMBL_FORK boundary files
- Issue #205 — External Collaboration Program v0.1
- Issue #208 — External Representation Contract v0.1
