---
expires_for_review: 2026-11-16
last_reviewed: 2026-08-18
---

# Proposal: Containerize hummbl-ci Self-Hosted Runner

**Status:** DECIDED — operator ratified 2026-08-18: Option D (Hybrid — C now, A later)
**Date:** 2026-08-15
**Author:** Devin (reconnaissance action #8)
**Steward:** HUMMBL Research Institute

## Decision (operator-ratified 2026-08-18)

**Option D (Hybrid)** — implement Option C immediately (Python Dockerfile for local reproducibility), track Option A (full Linux runner containerization) as a follow-up.

## 1. Problem Statement

The hummbl-governance CI runs on a bare-metal Windows self-hosted Gitea runner (`anvil-ci`) with a hardcoded Python path (`C:\gitea\runner\toolcache\Python\3.13.13\x64`). This has several drawbacks:

1. **Environment drift** — the runner's Python, pip packages, and system tools drift from what developers run locally; CI passes/failures become non-reproducible
2. **No isolation** — every job runs in the same Windows user session; a failing job can pollute the environment for the next job (leftover files, pip cache, env vars)
3. **Single point of failure** — one runner, one host; if Anvil reboots or the runner process crashes, all CI stops
4. **Hardcoded paths** — the `PYTHON` env var in `.gitea/workflows/ci.yml` is brittle; upgrading Python requires editing the workflow
5. **No local reproducibility** — developers cannot run `docker run` to reproduce a CI failure locally; they must SSH to Anvil or guess
6. **Windows-only** — the fleet has macOS and (potentially) Linux hosts that cannot run these workflows because all shells are `powershell`

## 2. Current State

### Runner inventory (from `docs/runbooks/gitea-runners-operations.md`)

| Hostname | Runner Name | Status | Platform |
|----------|-------------|--------|----------|
| Anvil | anvil-windows-general | ONLINE | Windows 11 x86_64, Python 3.11.15 |
| Nodezero | nodezero-macos-* (3 runners) | OFFLINE | macOS 15 ARM64 |
| Anvil | anvil-windows-arm64/x64 | OFFLINE | Windows 11 |

**Total**: 6 runners, 1 online. Nodezero has been DORMANT since 2026-07-01.

### Current workflow (`.gitea/workflows/ci.yml`)

- **Runs-on**: `[self-hosted, windows, python-ci, anvil, windows-general]`
- **Shell**: `powershell` on every step
- **Python**: hardcoded `C:\gitea\runner\toolcache\Python\3.13.13\x64\python.exe`
- **Jobs**: `test`, `install-smoke`, `lint`, `arbiter-governance`, `coverage-matrix-validate`, `ci-aggregate`
- **Dependencies**: zero runtime deps; test extras are `build`, `pytest`, `pytest-cov`, `ruff`, `cryptography`

### Constraints

- **Zero third-party runtime dependencies** (stdlib only in production code) — the container must not introduce runtime deps
- **Test extras only** — `build`, `pytest`, `pytest-cov`, `ruff`, `cryptography` are test-only
- **Python 3.11+** required
- **Gitea Actions** (not GitHub Actions) — uses `act_runner` with Gitea's workflow format, which is largely compatible with GitHub Actions syntax
- **No `[skip ci]`** allowed on any commit (per AGENTS.md)

## 3. Options

### Option A: Linux container with act_runner (full runner containerization)

**Approach**: Run `gitea/act_runner` inside a Linux Docker container with Python 3.13 pre-installed. Rewrite workflow shells from `powershell` to `bash`.

**Container image**:
```dockerfile
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates docker.io && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://gitea.com/gitea/act_runner/raw/branch/main/act_runner \
    -o /usr/local/bin/act_runner && chmod +x /usr/local/bin/act_runner
WORKDIR /runner
COPY runner-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

**Workflow changes**: every `shell: powershell` → `shell: bash`; `& "$env:PYTHON" -m pytest` → `python -m pytest`; `runs-on` labels change to `[self-hosted, linux, python-ci, container]`.

**Pros**:
- Standard, well-documented pattern; `gitea/act_runner` has official Docker support
- Lightest image (~150MB base)
- Portable across any Linux host with Docker
- Isolation per job (container ephemeral)
- Developers can `docker run` the same image locally to reproduce CI
- Enables future Linux/macOS runners without workflow changes
- Docker-in-Docker or Docker socket mount enables container-based jobs

**Cons**:
- **Breaking change**: all workflow shells must change from `powershell` to `bash`
- PowerShell-specific scripts in `scripts/` (e.g., `build_wheel_from_sdist.py`, `verify_ci_jobs.py`) may have Windows-path assumptions that need auditing
- Requires Docker installed on Anvil (or a new Linux host)
- Gitea `act_runner` Docker mode requires careful config (registration token, labels, container network)
- Windows-specific tests (if any) would need conditional skips or a separate Windows runner

**Effort**: Medium. ~1 day for Dockerfile + entrypoint + workflow rewrite + testing.

---

### Option B: Windows Server Core container with act_runner

**Approach**: Run `gitea/act_runner` inside a Windows Server Core container with Python 3.13 pre-installed. Keep PowerShell workflows unchanged.

**Container image**:
```dockerfile
FROM mcr.microsoft.com/windows/servercore:ltsc2022
RUN powershell -Command \
    Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.13/python-3.13.13-amd64.exe' -OutFile 'python-installer.exe'; \
    Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait; \
    Remove-Item python-installer.exe
RUN powershell -Command \
    Invoke-WebRequest -Uri 'https://gitea.com/gitea/act_runner/releases/latest/download/act_runner_windows_amd64.exe' -OutFile 'C:\act_runner.exe'
WORKDIR C:\runner
COPY runner-entrypoint.ps1 C:\entrypoint.ps1
ENTRYPOINT ["powershell", "-File", "C:\\entrypoint.ps1"]
```

**Workflow changes**: minimal — `runs-on` labels change to include `container`; the hardcoded `PYTHON` env var can be replaced with `python` (since Python is in PATH in the container).

**Pros**:
- **No workflow shell changes** — PowerShell preserved
- Matches current Windows environment exactly
- Isolation per job (container ephemeral)
- Developers on Windows can reproduce CI locally

**Cons**:
- **Heavy image**: Windows Server Core base is ~5GB; with Python, ~6GB
- **Windows host required**: only runs on Windows hosts with Docker Desktop or Windows Server with Containers role
- **Slower pulls**: 6GB image pull on every runner start (unless cached)
- **Less community support**: `act_runner` Docker mode is primarily tested on Linux; Windows container mode is less documented
- **Licensing**: Windows Server Core base image requires a valid Windows Server license for production use
- **No portability**: cannot run on Linux/macOS hosts
- Windows containers have known networking quirks with Docker-in-Docker

**Effort**: Medium. ~1 day for Dockerfile + entrypoint + runner config + testing. But image size makes iteration slow.

---

### Option C: Python environment Dockerfile only (no runner containerization)

**Approach**: Create a `Dockerfile` in the `hummbl-governance` repo that reproduces the CI Python environment. Developers run `docker build -t hummbl-ci . && docker run hummbl-ci pytest tests/` to reproduce CI locally. The runner itself stays bare-metal.

**Container image** (lives in `hummbl-governance/Dockerfile`):
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[test]"
COPY . .
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=hummbl_governance", "--cov-report=term", "--cov-fail-under=80"]
```

**Workflow changes**: none. The runner stays as-is.

**Pros**:
- **Smallest scope** — no runner changes, no workflow changes, no risk to existing CI
- **Immediate value** — developers can reproduce CI locally today
- **Linux-based** — portable, lightweight (~150MB)
- **First step toward full containerization** — the Dockerfile can later be extended into a runner image (Option A)
- No breaking changes

**Cons**:
- **Does not solve isolation** — the runner still runs jobs in the same bare-metal session
- **Does not solve SPOF** — one runner, one host
- **Does not solve environment drift on the runner itself** — only solves local reproducibility
- Developers still need Docker installed locally
- The Dockerfile may diverge from the actual runner environment if not kept in sync

**Effort**: Low. ~2 hours for Dockerfile + docker-compose (optional) + documentation.

---

### Option D: Hybrid — Option C now, Option A later

**Approach**: Implement Option C immediately (Python environment Dockerfile for local reproducibility). Track Option A as a follow-up in the roadmap with a prerequisite of auditing all `scripts/*.py` for Windows-path assumptions.

**Pros**:
- Delivers immediate value without risk
- Creates the Dockerfile foundation that Option A will extend
- Defers the breaking workflow change to a planned migration
- Allows time to audit PowerShell/path assumptions before the cutover

**Cons**:
- Two phases instead of one
- The runner isolation problem remains until Option A lands

**Effort**: Low now (2 hours) + Medium later (1 day).

## 4. Recommendation

**Option D (Hybrid)** is recommended.

**Rationale**:
1. Option C delivers immediate value (local reproducibility) with zero risk to existing CI
2. The Dockerfile created in Option C becomes the base image for Option A
3. Option A's workflow rewrite (powershell→bash) is a breaking change that deserves a planned migration, not a surprise
4. The `scripts/` directory has Windows-specific Python scripts (`build_wheel_from_sdist.py`, `install_wheel_from_sdist.py`, `smoke_installed_wheel.py`, `verify_ci_jobs.py`, `arbiter_audit.py`, `validate_coverage_matrices.py`, `build_evidence_validation_report.py`) that need auditing for path and shell assumptions before the cutover
5. Nodezero is DORMANT — there's no urgency to enable cross-platform runners today

**If the operator wants maximum isolation now**: Option A is the right choice, but budget 1-2 days for the workflow rewrite and script audit.

**If the operator wants to preserve PowerShell at all costs**: Option B, but accept the 6GB image and Windows-only constraint.

## 5. Prerequisites (for any option)

- [ ] Docker installed on the target host (Anvil for A/B, developer machines for C)
- [ ] Gitea runner registration token (for A/B — available in Gitea UI: Site Administration → Actions → Runners → Create Runner)
- [ ] Audit `scripts/*.py` for Windows-path assumptions (required for A, recommended for C)
- [ ] Confirm `arbiter-dev[analyzers]==0.2.0` is installable in the target container (it's a third-party package used in the `arbiter-governance` job)

## 6. Open questions

1. Does Anvil have Docker installed? (Determines whether A/B can run there or need a new host)
2. Is there a Linux host available in the fleet, or does Anvil need to run Docker Desktop?
3. Should the container image be stored in the Gitea container registry or built on-the-fly?
4. Is `arbiter-dev[analyzers]==0.2.0` compatible with Linux? (It's used in the `arbiter-governance` job)
5. Are there Windows-specific tests in the suite that would need conditional skips under Linux?

## 7. Decision

**Operator decision required.** Select A, B, C, or D. If D, confirm that Option C should be implemented now and Option A tracked as a follow-up.
