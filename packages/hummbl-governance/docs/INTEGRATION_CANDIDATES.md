# hummbl-governance v1.1.0 Integration Candidate Report

**Date**: 2026-06-17
**Analyst**: devin
**Source**: ROLLOUT_v1.1.0.md, live repo inspection (GitHub + Gitea + local machine)
**Scope**: All repos that should integrate the Governance Kernel (26th primitive)

---

## 1. Summary

| Category | Count | Action |
|----------|-------|--------|
| **Existing dependents** (need version bump) | 10 | Bump pyproject.toml to `>=1.1.0` |
| **Optional adoption** (no current dep) | 4 | Add dependency + integration code |
| **Local-only candidates** | 2 | Add dependency + integration code |
| **GitHub-only candidates** (need discovery) | 3 | Verify existence, then add dep |

---

## 2. Existing Dependents — Version Bump Required

These 10 repos already declare `hummbl-governance` as a dependency and **must bump to `>=1.1.0`**.

| # | Repo | Host | Current Spec | Target Spec | Verified? | Migration Notes |
|---|------|------|-------------|-------------|-----------|-----------------|
| 1 | **hummbl-governance** | GitHub `hummbl-io/hummbl-governance` | CI clones from GitHub (`../hummbl-governance`) | `>=1.1.0` via PyPI | **YES** — local copy on <machine> | **CRITICAL** — also migrate `hummbl_governance.kernel` imports to `hummbl_governance.kernel` |
| 2 | **adversary-emulation-playbook** | GitHub `hummbl-io/adversary-emulation-playbook` | `>=1.0.0` | `>=1.1.0` | **YES** — pyproject.toml confirmed | None — additive change |
| 3 | **hummbl-governance-showcase** | GitHub `hummbl-io/hummbl-governance-showcase` | `>=1.0.0` (assumed per rollout doc) | `>=1.1.0` | NO — not inspected | None — additive change |
| 4 | **hummbl-agent-sdk** | GitHub `hummbl-io/hummbl-agent` (assumed) | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not inspected | Pin for reproducibility |
| 5 | **hummbl-cli** | GitHub `hummbl-io/cli` (assumed) | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not inspected | Pin for reproducibility |
| 6 | **hummbl-dashboard** | Unknown | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not found on GitHub or local | Verify existence |
| 7 | **hummbl-foundry** | Unknown | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not found on GitHub or local | Verify existence |
| 8 | **hummbl-py** | Unknown | `>=1.0.0` (assumed per rollout doc) | `>=1.1.0` | NO — not found on GitHub or local | Verify existence |
| 9 | **hummbl-scheduler** | Unknown | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not found on GitHub or local | Verify existence |
| 10 | **hummbl-scripts** | Unknown | unpinned (assumed per rollout doc) | `>=1.1.0` | NO — not found on GitHub or local | Verify existence |

### Verified Details

**hummbl-governance** (local machine):
- Dependency is NOT in `pyproject.toml` — it is installed via CI workflow (`.github/workflows/ci.yml` lines 77-80, 176-179)
- CI clones `hummbl-io/hummbl-governance` to `../hummbl-governance` and installs with `pip install -e ../hummbl-governance`
- **Recommendation**: Change CI to `pip install hummbl-governance>=1.1.0` instead of cloning
- **Breaking**: `hummbl_governance/kernel/` exists in working tree (never committed) and must be migrated to `hummbl_governance.kernel` imports
- Files confirmed to import from `hummbl_governance.kernel`:
  - `hummbl_governance/services/compliance_daemon.py` — `Kernel`, `KernelPanic`
  - `hummbl_governance/bus/bus_writer_core.py` — `Kernel`, `KernelPanic`

**adversary-emulation-playbook** (GitHub):
- `pyproject.toml` line: `dependencies = ["hummbl-governance>=1.0.0"]`
- Simple one-line bump

---

## 3. Optional Adoption Candidates

Repos that do NOT currently depend on `hummbl-governance` but would benefit from the Kernel:

| Repo | Host | Current hummbl-governance Dep? | Use Case | Adoption Effort | Verified? |
|------|------|------------------------------|----------|----------------|-----------|
| **hummbl-bus** | Local (self-hosted runner) + GitHub `hummbl-io/hummbl-bus` (assumed) | **NO** — `dependencies = []` | Governance receipts on every bus post | Low — add `Kernel.create_receipt()` call | **YES** — local pyproject.toml inspected |
| **hummbl-cognition** | Unknown | Unknown | Evidence grading for ledger entries | Low — use `EvidenceEngine.grade()` | NO |
| **hummbl-autonomy** | Unknown | Unknown | Scaling-law evaluation for autonomous decisions | Low — use `LawEngine.evaluate()` | NO |
| **hummbl-iac** | GitHub `hummbl-io/hummbl-iac` | Unknown | Infrastructure governance — compliance checks, audit trails | Medium — wire `ComplianceMapper` + `AuditLog` | NO |

---

## 4. Local PROJECTS Candidates (self-hosted runner)

Repos under `/path/to/projects/` that are HUMMBL-owned and should adopt hummbl-governance:

| Repo | Host | Has hummbl-governance? | Recommendation | Effort |
|------|------|----------------------|----------------|--------|
| **hummbl-governance** | GitHub + Gitea | CI-only (not in pyproject.toml) | **Bump CI + migrate imports** | High |
| **hummbl-bus** | Local only (not on GitHub org list) | No | **Add dep** — receipts on bus writes | Low |
| **hummbl-governance** | GitHub + Gitea | N/A (self) | N/A | — |
| **arbiter** | GitHub `hummbl-io/arbiter` | Unknown | Candidate — code quality scoring could use `EvidenceEngine` | Low |
| **agent-governance-demo** | GitHub `hummbl-io/agent-governance-demo` | Unknown | Likely already has it (demo repo) | Verify |
| **hummbl-asi** | GitHub `hummbl-io/hummbl-asi` | Unknown | Candidate — safety monitoring | Low |
| **mcp-server** | GitHub `hummbl-io/mcp-server` | Unknown | Candidate — governance MCP tools | Low |
| **bif** | GitHub `hummbl-io/bif` | Unknown | Candidate — framework integration | Medium |
| **base120** | GitHub `hummbl-io/base120` | Unknown | Candidate — reasoning engine already in hummbl-governance | Verify |
| **crab** | GitHub `hummbl-io/crab` | Unknown | Candidate — safety/consequence analysis | Low |

---

## 5. GitHub hummbl-dev Org — Full Inventory

All 90 repos in `hummbl-dev` org. Candidates flagged with `[CANDIDATE]`.

| Repo | Visibility | Last Push | Candidate? | Rationale |
|------|-----------|-----------|-------------|-----------|
| hummbl-governance | PRIVATE | 2026-06-17 | **YES — existing dep** | Core platform, CI already clones hummbl-governance |
| hummbl-governance | PUBLIC | 2026-06-17 | N/A | Self |
| hummbl-production | PRIVATE | 2026-06-17 | **YES** | Production code — needs governance primitives |
| unified-frameworks | PRIVATE | 2026-06-17 | **YES** | Framework orchestration — needs Kernel |
| hummbl-dev | PUBLIC | 2026-06-17 | No | Meta/docs repo |
| adversary-emulation-playbook | PUBLIC | 2026-06-17 | **YES — existing dep** | Already depends on hummbl-governance |
| idp-spec | PUBLIC | 2026-06-17 | **YES** | Identity-delegation protocol — natural fit for IdentityEngine |
| agent-governance-demo | PUBLIC | 2026-06-16 | **YES** | Demo of governance primitives |
| bif | PUBLIC | 2026-06-16 | **YES** | Framework integration layer |
| arbiter | PUBLIC | 2026-06-16 | **YES** | Code quality scoring — EvidenceEngine |
| mcp-server | PUBLIC | 2026-06-16 | **YES** | MCP server — governance tools |
| hummbl-agent | PUBLIC | 2026-06-16 | **YES** | Agent runtime — needs Kernel |
| base120 | PUBLIC | 2026-06-16 | **YES** | Mental models — ReasoningEngine overlap |
| job-search-2026 | PRIVATE | 2026-06-16 | No | Personal/job search |
| whether-book | PRIVATE | 2026-06-16 | No | Book project |
| hummbl-music | PRIVATE | 2026-06-16 | No | Music project |
| hummingbird | PRIVATE | 2026-06-16 | **YES** | Unknown — inspect |
| hummbl-graphs | PRIVATE | 2026-06-15 | **YES** | Graph system — evidence chains |
| corpus | PRIVATE | 2026-06-15 | No | Research corpus |
| baseN | PRIVATE | 2026-06-15 | **YES** | BaseN system — governance |
| mtsmu | PRIVATE | 2026-06-15 | **YES** | Evidence-first methodology — natural fit |
| huaomp | PRIVATE | 2026-06-15 | **YES** | Analytical framework — LawEngine |
| hummbl-bibliography | PUBLIC | 2026-06-15 | No | Bibliography |
| general-claim-validator | PRIVATE | 2026-06-15 | **YES** | Claim validation — EvidenceEngine |
| hummbl-skills | PUBLIC | 2026-06-15 | No | Skills registry |
| autoresearch-reports | PUBLIC | 2026-06-14 | No | Research reports |
| psychedelic-claim-validator | PRIVATE | 2026-06-14 | No | Niche validator |
| evidence-gate | PUBLIC | 2026-06-14 | **YES** | Evidence validation — EvidenceEngine |
| hummbl-transparency | PUBLIC | 2026-06-14 | **YES** | Transparency reporting — AuditLog |
| .github | PUBLIC | 2026-06-14 | No | Org metadata |
| governed-compression | PUBLIC | 2026-06-14 | **YES** | Compression with governance |
| hummbl-brainstorm | PRIVATE | 2026-06-14 | No | Brainstorming tool |
| apex-nexus | PRIVATE | 2026-06-14 | **YES** | Apex/Nexus system — directly needs Kernel |
| hummbl-system-prompts | PRIVATE | 2026-06-14 | No | Prompts |
| lejepa | PRIVATE | 2026-06-13 | **YES** | JEPA implementation — needs governance |
| arcana | PRIVATE | 2026-06-13 | No | Research/lens system |
| HUMMBL-Unified-Tier-Framework | PUBLIC | 2026-06-13 | **YES** | Tier framework — AuthorityEngine |
| lsat-prep | PRIVATE | 2026-06-05 | No | Personal |
| fractional-bench | PRIVATE | 2026-06-05 | No | Benchmarking |
| swarm-test | PRIVATE | 2026-06-05 | **YES** | Swarm testing — Kernel needed |
| hummbl-tuples | PRIVATE | 2026-06-05 | **YES** | Tuple system — receipt integration |
| hummbl-research | PRIVATE | 2026-06-05 | No | Research |
| awesome-ai-agents-1 | PUBLIC | 2026-06-03 | No | Awesome list |
| awesome-ai-agents-2026 | PUBLIC | 2026-06-03 | No | Awesome list |
| awesome-python | PUBLIC | 2026-06-03 | No | Awesome list |
| hummbl-medical | PRIVATE | 2026-06-02 | **YES** | Medical AI — safety critical |
| crab | PRIVATE | 2026-06-02 | **YES** | Consequence analysis — safety |
| hummbl-iac | PUBLIC | 2026-05-31 | **YES** | Infrastructure governance |
| hummbl-cca-f | PRIVATE | 2026-05-31 | **YES** | CCA framework — compliance |
| hummbl-theory | PUBLIC | 2026-05-28 | No | Theory docs |
| agent-tools | PRIVATE | 2026-05-26 | **YES** | Agent tooling — needs governance |
| meeting-archive | PRIVATE | 2026-05-26 | No | Archive |
| hummbl-models | PRIVATE | 2026-05-26 | **YES** | Model governance — needed |
| hummbl-doctrine | PRIVATE | 2026-05-26 | **YES** | Doctrine — LawEngine |
| hummbl-brand | PRIVATE | 2026-05-26 | No | Brand |
| coaching | PRIVATE | 2026-05-26 | No | Coaching |
| autoresearch-pipeline | PRIVATE | 2026-05-26 | No | Pipeline |
| krineia | PUBLIC | 2026-05-17 | **YES** | Cryptographic receipts — ReceiptEngine |
| hermes-agent | PUBLIC | 2026-05-17 | **YES** | Agent steward — IdentityEngine |
| hummbl-papers | PUBLIC | 2026-05-17 | No | Papers |
| open_teamsuzie | PUBLIC | 2026-05-13 | No | Open source |
| autoresearch-win-rtx | PUBLIC | 2026-05-03 | No | Research |
| autoresearch | PUBLIC | 2026-05-03 | No | Research |
| Real-Time-Voice-Cloning | PUBLIC | 2026-04-22 | No | Fork |
| sint-protocol | PUBLIC | 2026-04-19 | No | Protocol |
| deer-flow | PUBLIC | 2026-04-18 | No | Flow system |
| cli | PUBLIC | 2026-04-18 | **YES** | CLI — likely hummbl-cli candidate |
| paramiko | PUBLIC | 2026-04-18 | No | Fork |
| rich | PUBLIC | 2026-04-18 | No | Fork |
| vllm | PUBLIC | 2026-04-18 | No | Fork |
| skills | PUBLIC | 2026-04-18 | No | Fork |
| markitdown | PUBLIC | 2026-04-18 | No | Fork |
| hummbl-assurance | PRIVATE | 2026-04-18 | **YES** | Assurance — compliance |
| CL4R1T4S | PUBLIC | 2026-04-17 | No | Project |
| ST3GG | PUBLIC | 2026-04-02 | No | Project |
| OBLITERATUS | PUBLIC | 2026-04-01 | No | Project |
| G0DM0D3 | PUBLIC | 2026-03-26 | No | Project |
| V3SP3R | PUBLIC | 2026-03-24 | No | Project |
| NATURALIS-FUTURA | PUBLIC | 2026-03-21 | No | Project |
| L1B3RT4S | PUBLIC | 2026-02-17 | No | Project |
| hummbl-asi | PRIVATE | 2025-10-26 | **YES** | ASI safety — critical |

---

## 6. Gitea HUMMBL Org — Known Repos

The internal Gitea org `HUMMBL` hosts solo/internal repos.

| Repo | Status | hummbl-governance? | Action |
|------|--------|-------------------|--------|
| **hummbl-governance** | Active | CI-only | Bump CI + migrate imports |
| **hummbl-governance** | Active | Self | N/A |
| **ownward-app** | Unknown | Unknown | Verify |
| Other solo HUMMBL repos | Unknown | Unknown | Audit |

**Note**: Gitea API access failed during this session (token issue). Manual audit required.

---

## 7. Priority Queue

### Phase 1: Immediate (This Session)
1. **hummbl-governance** — Bump CI to `>=1.1.0`, migrate `hummbl_governance.kernel` imports
2. **adversary-emulation-playbook** — One-line pyproject.toml bump

### Phase 2: Short-term (Next 7 Days)
3. **hummbl-bus** — Add `hummbl-governance>=1.1.0` dep, wire `ReceiptEngine` into bus writes
4. **apex-nexus** — Add dep, wire `Kernel` into assessment flow
5. **hummbl-iac** — Add dep, wire `ComplianceMapper` + `AuditLog`
6. **idp-spec** — Add dep, wire `IdentityEngine` + `DelegationTokenManager`
7. **krineia** — Add dep, wire `ReceiptEngine` for cryptographic receipts

### Phase 3: Medium-term (Next 30 Days)
8. **hummbl-agent** — Add dep, wire `Kernel` into agent lifecycle
9. **mcp-server** — Add dep, expose Kernel primitives as MCP tools
10. **hummbl-production** — Add dep, production governance
11. **unified-frameworks** — Add dep, framework governance
12. **hummbl-assurance** — Add dep, assurance compliance

---

## 8. Verification Commands

```bash
# Check if a repo already has hummbl-governance
grep -r "hummbl-governance" pyproject.toml requirements.txt setup.py setup.cfg 2>/dev/null

# Check CI workflows for clone+install pattern
grep -r "hummbl-governance" .github/workflows/ 2>/dev/null

# Check Python imports
 grep -r "from hummbl_governance\|import hummbl_governance" --include="*.py" . 2>/dev/null
```

---

## 9. Ledger Tag

```
integration_candidates: v1.1.0 | analyst: devin | date: 2026-06-17 | existing_deps: 10 | verified: 2 | optional_adoption: 4 | github_candidates: 35 | gitea_candidates: 3 | local_candidates: 2 | phase_1: 2 | phase_2: 5 | phase_3: 5
```
