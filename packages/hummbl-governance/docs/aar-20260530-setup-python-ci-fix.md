AAR: fix-ci-setup-python-v5 | INTERNAL | 20260530-1400Z | codex
═══════════════════════════════════════════════════════════════════

## 1. Mission & Intent
- **Objective**: Fix CI failure where `actions/setup-python@v5` fails on the self-hosted Windows runner at Anvil due to lack of admin rights for the NSIS Python installer.
- **Success criteria**: CI run passes lint + test matrix on both Python 3.12 and 3.13.
- **Constraints**: No admin access on runner process. No modification to host Windows system Python. All provisioning must happen through the Gitea Actions toolcache.

## 2. Chronology
| Commit | Action | Result |
|--------|--------|--------|
| `b942da9` | Fix lint issues (unused imports/vars) so CI gets past lint stage | Run 560 — lint passed, install step failed |
| `1d72ffa` | Add `x64.complete` marker files to toolcache for 3.12.13 and 3.13.13 | Run 561 — **never picked up** (runner stopped after run 560) |
| `bd881e4` | Pin `python-version` from ranges to exact patches (`3.12.13`, `3.13.13`) | Run 562 — **still queued** (no runner) |

## 3. Outcome vs Plan
- **Planned**: Pin versions + add toolcache markers → CI picks up local Python install → passes.
- **Actual**: First fix committed and pushed; runner crashed or stopped during/after the failing run 560. Runs 561 and 562 are queued with no daemon to pick them up.
- **Delta**: The CI fix may be correct, but we cannot verify because the runner daemon (`act_runner`) is not running. The process table shows no `act_runner` process.

## 4. Root Causes
**Deviation: CI failed with NSIS installer admin error**
- Why 1: `setup-python@v5` resolved `3.12` → `3.12.10` via remote manifest, then tried to download+run the NSIS installer.
- Why 2: The Windows runner process runs without admin rights; NSIS installer requires elevation.
- Why 3: The toolcache already had a manually-provisioned 3.12.13 but the action deleted it because the manifest said 3.12.10.
- Root cause: `setup-python@v5` does not treat the toolcache as authoritative when using version ranges — it always defers to the remote manifest and replaces non-matching cache entries.

**Deviation: Runner daemon stopped after run 560**
- Why 1: `act_runner` process is not running (verified via Get-Process).
- Why 2: The runner may have crashed during or after the failed run 560 (the last log entry is at 20:46:25 on 2026-05-29 for task 692).
- Root cause: Unknown — no crash log captured. [unverified — runner may have been stopped by operator or Windows Update/restart]

## 5. Sustains
- Correctly diagnosed setup-python@v5's manifest-resolution behavior as the root cause. — evidence: PR #498 AAR identified the "looks up remote manifest not toolcache" mechanism.
- Manually provisioned 3.12.13 + 3.13.13 in the toolcache with working `python.exe` and `x64.complete` markers. — evidence: `Get-ChildItem C:\gitea\runner\toolcache\Python\3.12.13\x64\` confirmed python.exe present.

## 6. Improves
- Runner daemon not monitored. Runner stopped between run 560 and run 561; no alert fired. — evidence: `Get-Process -Name "act_runner"` returned empty; runs 561/562 stuck at "queued".
- No mechanism to verify CI fixes without a live runner. The session spent 2 commits trying to fix setup-python but never got feedback. — evidence: both 561 and 562 remain queued.
- Toolcache provisioning is manual (copy from WSL venv). No repeatable provisioning script. — evidence: the 3.12.13 and 3.13.13 were copied from WSL Python installations, not installed via a repeatable process.

## 7. Recommendations
1. **[HIGH]** Restart the act_runner daemon. Check Task Scheduler for `Gitea Runner` scheduled task; if absent, reinstall or create it. Then verify runs 561/562 get picked up.
2. **[MED]** Add a dead-runner heartbeat — a scheduled script or bus check that polls `Get-Process -Name "act_runner"` and posts STATUS/BLOCKED if missing. Wire into the morning-kickoff or fmproc digest.
3. **[LOW]** Write a provisioning script for toolcache Python entries so they can be rebuilt on demand instead of copied from WSL. Path: `C:\gitea\runner\toolcache\Python\<version>\x64\`.

---
Base120 Applied: P6 (Point-of-View Anchoring), RE17 (Versioning & Diff), DE1 (Root Cause Analysis), DE7 (Pareto Decomposition)
Evidence: `C:\gitea\runner\runner.log` (last entry 20:46:25), Gitea API (runs 560/561/562 status), `git log --oneline -10`
Bus: N (runner down, no write path — deferred to next session operator restart)
