# Golden Corpus Snapshots

This directory contains versioned snapshots of golden corpus validation outputs used for semantic drift detection.

## Purpose

Snapshots capture the deterministic validation behavior of Base120 at specific points in time. They serve as baselines for detecting unintentional changes in validation logic, ensuring corpus stability even within frozen schema versions.

## Structure

Each snapshot is a JSON file with the following naming convention:
```
snapshot-<commit-sha-8-chars>.json
```

Example: `snapshot-5b9ab408.json`

## Snapshot Format

```json
{
  "snapshot_id": "5b9ab408",
  "git_sha": "5b9ab4088f286507c6f1f9a16d89278a73baa7bd",
  "timestamp": "2026-01-04T18:20:00Z",
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
      "invalid-schema-missing-field.json": {
        "artifact_id": "artifact-invalid-001",
        "errors": ["ERR-SCHEMA-001"]
      }
    }
  }
}
```

## Usage

### Capture New Baseline

```bash
python -m base120.drift.capture_baseline
```

This is automatically done by CI on main branch commits.

### Compare Snapshots

```bash
python -m base120.drift.compare \
  artifacts/golden_corpus_snapshots/snapshot-abc1234.json \
  artifacts/golden_corpus_snapshots/snapshot-def5678.json
```

This is automatically done by CI on pull requests.

## Maintenance

- **Automatic Updates**: Snapshots are captured automatically on main branch changes
- **Manual Updates**: Can be triggered via workflow dispatch
- **Retention**: All snapshots are retained indefinitely (may add rotation in future)
- **Drift Reports**: Temporary drift report JSON files are gitignored (see `.gitignore`)

## Related Documentation

- [Drift Detection Guide](../docs/drift-detection.md)
- [Golden Corpus Contract](../docs/corpus-contract.md)
