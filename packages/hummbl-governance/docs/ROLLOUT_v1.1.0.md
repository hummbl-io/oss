# hummbl-governance v1.1.0 Rollout Plan

> Post-publish dependency upgrade and migration guide for all repos consuming `hummbl-governance`.

## Summary

`hummbl-governance==1.1.0` is now live on PyPI. This release adds the **Governance Kernel** (26th primitive) with 12 runtime modules, 136 tests, and full CLI support. Zero breaking changes to existing primitives.

## Repos Requiring Upgrade

The following 10 repos declare a dependency on `hummbl-governance` and need their `pyproject.toml` (or `requirements.txt`) updated to `>=1.1.0`:

| # | Repo | Current Spec | Target Spec | Migration Notes |
|---|------|-------------|-------------|-----------------|
| 1 | `hummbl-governance` | `>=0.3.0` | `>=1.1.0` | **CRITICAL** — also migrate `hummbl_governance.kernel` imports to `hummbl_governance.kernel` |
| 2 | `adversary-emulation-playbook` | `>=1.0.0` | `>=1.1.0` | None — additive change |
| 3 | `hummbl-governance-showcase` | `>=1.0.0` | `>=1.1.0` | None — additive change |
| 4 | `hummbl-agent-sdk` | unpinned | `>=1.1.0` | Pin for reproducibility |
| 5 | `hummbl-cli` | unpinned | `>=1.1.0` | Pin for reproducibility |
| 6 | `hummbl-dashboard` | unpinned | `>=1.1.0` | Pin for reproducibility |
| 7 | `hummbl-foundry` | unpinned | `>=1.1.0` | Pin for reproducibility |
| 8 | `hummbl-py` | `>=1.0.0` | `>=1.1.0` | None — additive change |
| 9 | `hummbl-scheduler` | unpinned | `>=1.1.0` | Pin for reproducibility |
| 10 | `hummbl-scripts` | unpinned | `>=1.1.0` | Pin for reproducibility |

## hummbl-governance Migration (Critical Path)

`hummbl-governance` is the only repo with a **breaking migration** — it has an in-repo copy of the Kernel at `hummbl_governance/kernel/` that must be replaced with the PyPI package.

### Step 1: Upgrade dependency

```bash
cd ~/projects/PROJECTS/hummbl-governance
# Update pyproject.toml in both package roots
sed -i 's/hummbl-governance>=0.3.0/hummbl-governance>=1.1.0/g' \
    pyproject.toml hummbl-governance/pyproject.toml hummbl_governance/pyproject.toml
```

### Step 2: Rewrite imports

```bash
cd ~/projects/PROJECTS/hummbl-governance
# Replace all hummbl_governance.kernel imports with hummbl_governance
find hummbl_governance -name "*.py" -exec sed -i '' 's/from hummbl_governance.kernel import/from hummbl_governance import/g' {} +
find hummbl_governance -name "*.py" -exec sed -i '' 's/from hummbl_governance.kernel.invariants import/from hummbl_governance import/g' {} +
find hummbl_governance -name "*.py" -exec sed -i '' 's/from hummbl_governance.kernel.law_engine import/from hummbl_governance import/g' {} +
```

**Files confirmed to import from `hummbl_governance.kernel`:**
- `hummbl_governance/services/compliance_daemon.py` — `Kernel`, `KernelPanic`
- `hummbl_governance/bus/bus_writer_core.py` — `Kernel`, `KernelPanic`

### Step 3: Set environment variables

```bash
# Maintain backward-compatible paths
export HUMMBL_KERNEL_STATE_DIR="hummbl_governance/_state/kernel"
export HUMMBL_KERNEL_ATLAS_DIR="_internal/research/2026-06-17-scaling-law-atlas/records"
```

### Step 4: Remove in-repo kernel

```bash
cd ~/projects/PROJECTS/hummbl-governance
# WARNING: Only do this after all imports are verified to work with hummbl_governance
git rm -r hummbl_governance/kernel/
```

**Note:** `hummbl_governance/kernel/` has NEVER been committed to git (`git log --all -- hummbl_governance/kernel/` returns empty). It exists only in the working tree. The portability fixes applied during this session (`HUMMBL_KERNEL_STATE_DIR` support in `kernel.py` and `law_engine.py`) will be lost unless committed first.

### Step 5: Verify

```bash
cd ~/projects/PROJECTS/hummbl-governance
python -m pytest hummbl_governance/tests/unit/test_compliance_daemon.py -v
python -m pytest hummbl_governance/tests/unit/test_bus_writer.py -v
python -c "from hummbl_governance import Kernel; k = Kernel.boot(); print(k.health())"
```

## Non-Critical Repos (Simple Upgrade)

For repos 2-10, the upgrade is a one-line dependency bump with no code changes:

```bash
# Example for hummbl-py
cd ~/projects/PROJECTS/hummbl-py
sed -i 's/hummbl-governance>=1.0.0/hummbl-governance>=1.1.0/g' pyproject.toml
pip install -e ".[test]"
python -m pytest tests/ -v
```

## Optional: New Kernel Adoption

Repos that do NOT currently depend on `hummbl-governance` but would benefit from the Kernel:

| Repo | Use Case | Adoption Effort |
|------|----------|-----------------|
| `hummbl-bus` | Governance receipts on every bus post | Low — add `Kernel.create_receipt()` call |
| `hummbl-cognition` | Evidence grading for ledger entries | Low — use `EvidenceEngine.grade()` |
| `hummbl-foundry` | Agent identity registry + role claims | Medium — wire `IdentityEngine` into agent lifecycle |
| `hummbl-autonomy` | Scaling-law evaluation for autonomous decisions | Low — use `LawEngine.evaluate()` |

## Verification Checklist

Before declaring rollout complete:

- [ ] `hummbl-governance` pyproject.toml updated to `>=1.1.0`
- [ ] `hummbl-governance` imports migrated from `hummbl_governance.kernel` to `hummbl_governance`
- [ ] `hummbl-governance` in-repo kernel removed (or committed if keeping)
- [ ] All 10 repos' test suites pass after upgrade
- [ ] `pip install hummbl-governance>=1.1.0` works in a fresh venv
- [ ] `python -m hummbl_governance.kernel health` returns 17 laws loaded
- [ ] PyPI page shows v1.1.0 as latest

## Rollback

If any repo breaks:

```bash
# Pin back to last known good version
pip install "hummbl-governance<1.1.0"
# Or in pyproject.toml:
# "hummbl-governance>=0.8.0,<1.1.0"
```

The v1.1.0 release is **additive only** — no existing primitive APIs were changed. The only risk is the new `kernel` package adding ~230 KB to the wheel size.

---

**Published:** 2026-06-17
**Package:** https://pypi.org/project/hummbl-governance/1.1.0/
**Docs:** `hummbl-governance/docs/KERNEL_DOCTRINE.md`, `KERNEL_IaC.md`
