# Semantic Drift Detection

## Overview

Base120 implements automated **semantic drift detection** to ensure golden corpus stability over time. This infrastructure monitors validation outputs for unintentional changes, even within frozen schema/release versions (e.g., v1.x).

Drift detection provides infrastructure-enforced guarantees that validation behavior remains deterministic and stable across:
- Code refactorings
- Dependency updates
- Runtime environment changes
- Time-based variations

## Architecture

### Components

1. **Baseline Snapshots** (`artifacts/golden_corpus_snapshots/`)
   - Versioned snapshots of golden corpus validation outputs
   - Stored with metadata: commit SHA, timestamp, Base120 version, schema version
   - Captured automatically on main branch changes

2. **Drift Detection Module** (`base120/drift/`)
   - `capture_baseline.py`: Captures snapshots of current validation outputs
   - `compare.py`: Compares snapshots and generates drift reports

3. **CI Workflow** (`.github/workflows/drift-detection.yml`)
   - Runs on PRs to detect drift before merge
   - Runs on main branch to capture new baselines
   - Runs periodically (daily) to monitor for unexpected drift

### Drift Types

The system detects four types of drift:

1. **Encoding Changes** (Breaking) ⚠️
   - Same input produces different output
   - Error codes changed for existing test cases
   - **Action Required:** Investigation and justification

2. **Semantic Changes** (Breaking) ⚠️
   - Structural differences in validation outputs
   - Different error ordering or formatting
   - **Action Required:** Restore deterministic behavior

3. **New Corpus Files** (Non-breaking) ℹ️
   - New test cases added to golden corpus
   - **Action:** Review and merge if appropriate

4. **Removed Corpus Files** (Non-breaking) ℹ️
   - Test cases removed from golden corpus
   - **Action:** Review and justify removal

## Workflows

### On Pull Requests

When a PR is opened or updated:

1. CI fetches latest baseline snapshot from main branch
2. CI captures current snapshot with PR code
3. CI compares snapshots and generates drift report
4. Drift report posted as PR comment
5. PR blocked if breaking drift detected

**Example PR Comment:**

```markdown
## 🔍 Semantic Drift Detection Report

**Baseline:** `abc12345`
**Current:** `def67890`

⚠️ **Breaking drift detected** - corpus outputs have changed!

### Drift Summary

- ⚠️ Encoding Change: 1

### Detailed Changes

#### valid/valid-basic.json
**Type:** encoding_change
**Description:** Validation output changed: baseline=[], current=['ERR-TEST-001']
**Baseline errors:** `[]`
**Current errors:** `['ERR-TEST-001']`
```

### On Main Branch

When code is merged to main:

1. CI captures new baseline snapshot
2. Snapshot committed to repository with message `[skip ci]`
3. Snapshot becomes new baseline for future comparisons

### Periodic Monitoring

Daily at 00:00 UTC:

1. CI captures current snapshot
2. CI compares with previous snapshot
3. If unexpected drift detected, issue created automatically

## Recovery Protocols

### Intentional Changes (Expected Drift)

If your change intentionally modifies validation behavior:

1. **Document the change** in PR description
2. **Explain the justification** (bug fix, feature enhancement)
3. **Update governance classification** to reflect impact level
4. **Merge the PR** - CI will capture new baseline automatically
5. **Verify baseline** was updated in follow-up main branch build

### Unintentional Changes (Unexpected Drift)

If drift is detected but was not intended:

1. **Investigate root cause:**
   - Non-deterministic code (timestamps, random values)
   - Environment dependencies (OS, Python version)
   - Dependency version changes
   - Floating-point arithmetic issues

2. **Restore deterministic behavior:**
   - Use `BASE120_FIXED_TIMESTAMP` for time-based values
   - Sort collections before comparison
   - Pin dependency versions
   - Avoid environment-specific logic

3. **Verify fix:**
   - Capture new snapshot locally
   - Compare with baseline
   - Ensure no drift detected

4. **Update PR** with fixes

### False Positives

If drift is flagged incorrectly:

1. **Check baseline snapshot** is from correct branch
2. **Verify deterministic execution** with `BASE120_FIXED_TIMESTAMP`
3. **Review comparison logic** in `base120/drift/compare.py`
4. **Report issue** if drift detection logic is faulty

## Manual Operations

### Capture Baseline Locally

```bash
python -m base120.drift.capture_baseline
```

Output: `artifacts/golden_corpus_snapshots/snapshot-<commit>.json`

### Compare Snapshots

```bash
python -m base120.drift.compare \
  artifacts/golden_corpus_snapshots/snapshot-abc1234.json \
  artifacts/golden_corpus_snapshots/snapshot-def5678.json
```

Output:
- Markdown report to stdout
- JSON report to `artifacts/golden_corpus_snapshots/drift-report-<current>.json`
- Exit code 0 (no breaking drift) or 1 (breaking drift detected)

### Deterministic Testing

Use fixed timestamp for reproducible snapshots:

```bash
BASE120_FIXED_TIMESTAMP="2026-01-01T00:00:00Z" \
  python -m base120.drift.capture_baseline
```

## Integration with Governance

Drift detection integrates with the governance classifier (PR #26):

- **Trivial/Editorial changes:** Drift detection skipped
- **Corpus changes:** Drift expected and reviewed
- **Schema/FM changes:** Breaking drift requires justification
- **Potential breaking changes:** Drift detection mandatory

## Threshold Configuration

Currently, drift detection uses **zero-tolerance** for breaking drift:

- Any encoding/semantic change triggers alert
- New/removed corpus files generate warnings only
- No automatic baseline updates on drift

Future enhancements may add configurable thresholds for:
- Acceptable drift percentage
- Drift severity levels
- Auto-update policies for non-breaking drift

## Maintenance

### Baseline Storage

- Baselines stored in `artifacts/golden_corpus_snapshots/`
- Committed to repository for version control
- Retained indefinitely (may add rotation policy in future)

### Snapshot Format

```json
{
  "snapshot_id": "abc12345",
  "git_sha": "abc1234567890...",
  "timestamp": "2026-01-04T00:00:00Z",
  "base120_version": "1.0.0",
  "schema_version": "v1.0.0",
  "results": {
    "valid": {
      "valid-basic.json": {
        "artifact_id": "artifact-valid-001",
        "errors": []
      }
    },
    "invalid": {
      "invalid-schema.json": {
        "artifact_id": "artifact-invalid-001",
        "errors": ["ERR-SCHEMA-001"]
      }
    }
  }
}
```

## Troubleshooting

### Drift detected in CI but not locally

- Ensure same Python version (3.13)
- Check for environment-specific dependencies
- Use `BASE120_FIXED_TIMESTAMP` in both environments

### Snapshot not captured on main

- Check workflow logs for errors
- Verify write permissions for `github-actions[bot]`
- Ensure `[skip ci]` in commit message to avoid loops

### Periodic monitoring creating false issues

- Review recent main branch changes
- Check for non-deterministic test execution
- Investigate dependency updates

## Future Enhancements

Planned improvements:

1. **Performance drift tracking** - measure and alert on validation time increases
2. **Configurable thresholds** - allow acceptable drift ranges
3. **Snapshot retention policy** - rotate old baselines
4. **Cross-version drift detection** - compare v1.0 vs v1.1 behavior
5. **Regression testing** - detect reintroduced bugs

## References

- [Golden Corpus Contract](corpus-contract.md)
- [Base120 Specification](spec-v1.0.0.md)
