# Repository Health Contract

## Identity

- **Repository**: `HUMMBL/governed-compression`
- **Canonical host**: `https://<FLEET_HOST_1>.<TAILSCALE_TAILNET>.<TAILSCALE_TAILNET>/HUMMBL/governed-compression`
- **Public mirror**: `https://github.com/hummbl-io/governed-compression`
- **Default branch**: `main`
- **Visibility**: Public
- **Owner**: HUMMBL Team

## Lifecycle

- **Status**: Active experimental implementation surface
- **Purpose**: Reference implementation for governed vector/KV compression methods and benchmarks.

## Canonical Relationship

- **Source of truth**: This Gitea repo.
- **Audience**: Internal HUMMBL experimentation and benchmark sharing.

## Validation Contract

From repository root:

```bash
python -m pip install -e .
pytest
```

```bash
ruff check .
```

## Branch Protection Expectation

- `main` should be PR-protected.
- Required checks for change-heavy PRs should include test/validation and benchmark sanity checks where added in CI.
