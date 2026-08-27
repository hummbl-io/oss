# Gap-10: Air-Gap Demo Runbooks (Level 2-3)

**Issue:** #415 (gap-10)
**Federal standards:** S9 Air-Gap Proof Track, DoD Zero Trust
**Date:** 2026-08-27
**Status:** PREP ONLY ΓÇö operator decision (2026-08-27): prep, no demo run

## 1. Purpose

This document provides runbooks for demonstrating the HUMMBL governance
kernel's air-gap capability at S9 Level 2 (Offline Capable) and Level 3
(Air-Gapped). These are prep artifacts ΓÇö the operator chose not to run
demos in this phase.

## 2. Level 2: Offline Capable Demonstration

### Objective

Verify that the `hummbl-governance` package can be installed, imported,
and its test suite passes in an environment with no internet access,
using only pre-cached dependencies.

### Prerequisites

- Python 3.11+ installed
- pip cache populated with test dependencies (pytest, pytest-cov, ruff,
  build, cryptography) ΓÇö see `AIR_GAPPED_DEPS.md` for download procedure
- `hummbl-governance` source code available (git clone or tarball)
- Network egress disabled (firewall block or disconnected NIC)

### Runbook

```bash
# 1. Pre-cache dependencies (ON NETWORKED HOST, before air-gap)
mkdir -p /media/sneakernet/deps/pypi
pip download -d /media/sneakernet/deps/pypi pytest pytest-cov ruff build cryptography

# 2. Transfer to air-gapped host via sneakernet
# (Copy /media/sneakernet/deps/ to air-gapped host)

# 3. On air-gapped host: verify no internet
ping -c 1 8.8.8.8  # Should fail
curl -s https://pypi.org  # Should fail

# 4. Install from local cache
pip install --no-index --find-links /media/sneakernet/deps/pypi \
    pytest pytest-cov ruff build cryptography

# 5. Install governance package (editable, no deps)
cd /path/to/hummbl-governance
pip install -e . --no-deps

# 6. Run test suite
python -m pytest tests/ -v --cov=hummbl_governance --cov-report=term

# 7. Verify all tests pass
# Expected: 100% pass rate, coverage >= 80%

# 8. Run linting
ruff check hummbl_governance/ tests/

# 9. Run SBOM generation (gap-5)
python scripts/gap5-generate-sbom.py --output sbom.cdx.json

# 10. Run CI pinning audit (gap-5)
python scripts/gap5-audit-ci-pinning.py
```

### Expected results

| Check | Expected | Evidence |
|-------|----------|----------|
| Internet access | None | `ping` and `curl` fail |
| pip install (deps) | Success from local cache | No PyPI access needed |
| pip install (governance) | Success, zero deps | `dependencies = []` |
| Test suite | 100% pass, coverage >= 80% | pytest output |
| Linting | 0 errors | ruff output |
| SBOM generation | Success | `sbom.cdx.json` created |
| CI pinning audit | 0 violations | Script output |

### Evidence to capture

- Terminal transcript showing no internet + successful install + tests
- `sbom.cdx.json` generated offline
- pytest coverage report
- Add to evidence package as S8 #14 (air-gap test results)

## 3. Level 3: Air-Gapped Demonstration

### Objective

Verify that the governance kernel operates on a fully air-gapped host
with no network path to the internet, including git operations via
local Gitea mirror.

### Prerequisites

- Air-gapped host (Anvil or dedicated air-gap machine)
- Gitea v1.26+ running locally (port 3030) with governance repos mirrored
- Local Docker registry (port 5000) with base images
- Local PyPI index (port 8080) with cached wheels
- Ollama (port 11434) for local LLM inference
- Sneakernet transfer media (USB drive or similar)
- Coordination bus local mirror (C:/FM or equivalent)

### Runbook

```bash
# 1. Verify isolation (on air-gapped host)
python /path/to/platform/tools/scripts/test_air_gapped_environment.py
# Expected: all isolation checks pass

# 2. Verify no internet path
ping -c 1 8.8.8.8  # Should fail
curl -s https://github.com  # Should fail
curl -s https://pypi.org  # Should fail

# 3. Verify local services
curl -s http://localhost:3030/api/v1/user  # Gitea
curl -s http://localhost:5000/v2/_catalog  # Registry
curl -s http://localhost:11434/api/tags    # Ollama
curl -s http://localhost:8080              # PyPI index

# 4. Clone governance repo from local Gitea
git clone http://localhost:3030/governance/hummbl-governance.git
cd hummbl-governance

# 5. Install from local PyPI index
pip install --index-url http://localhost:8080/simple/ \
    pytest pytest-cov ruff build cryptography
pip install -e . --no-deps

# 6. Run full test suite
python -m pytest tests/ -v --cov=hummbl_governance --cov-report=term

# 7. Run governance primitives smoke test
python -c "
from hummbl_governance.kernel.mutation_gate import PreMutationGate
from hummbl_governance.kernel.auth_provider import EnvVarAuthProvider
from hummbl_governance.primitives.merkle_anchor import MerkleTree
print('All governance primitives imported successfully (air-gapped)')
"

# 8. Run Merkle anchoring on local bus (gap-6)
python scripts/gap6-merkle-anchor.py anchor --dry-run --machine airgapped

# 9. Run SBOM generation (gap-5)
python scripts/gap5-generate-sbom.py --output sbom.cdx.json

# 10. Run CI pinning audit (gap-5)
python scripts/gap5-audit-ci-pinning.py

# 11. Commit test results to local Gitea
git add sbom.cdx.json
git commit -m "test: air-gap Level 3 demonstration results"
git push origin main  # Pushes to local Gitea, not GitHub
```

### Expected results

| Check | Expected | Evidence |
|-------|----------|----------|
| Isolation verification | All checks pass | `test_air_gapped_environment.py` output |
| Internet access | None | `ping`, `curl` to external fail |
| Local services | All running | Gitea, registry, Ollama, PyPI |
| Git clone (local) | Success | From local Gitea mirror |
| pip install (local) | Success | From local PyPI index |
| Test suite | 100% pass, coverage >= 80% | pytest output |
| Governance primitives import | Success | Smoke test output |
| Merkle anchor (dry-run) | Success | STH generated |
| SBOM generation | Success | `sbom.cdx.json` created |
| CI pinning audit | 0 violations | Script output |
| Git push (local) | Success | To local Gitea, not GitHub |

### Evidence to capture

- `test_air_gapped_environment.py` output (isolation verification)
- Terminal transcript showing all steps
- `sbom.cdx.json` generated offline
- pytest coverage report
- Local Gitea commit log showing results committed
- Add to evidence package as S8 #14 (air-gap test results)

## 4. Data transfer procedures

For transferring results FROM the air-gapped host to the networked
environment (for evidence package submission), follow
`AIR_GAPPED_DATA_TRANSFER.md`:

1. Write results to sneakernet media (USB drive)
2. On networked host, scan media for malware
3. Copy results to evidence package directory
4. Commit to GitHub from networked host

**Never connect the air-gapped host to the internet to transfer results.**

## 5. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-27 | Initial demo runbooks (gap-10 prep) | devin |
