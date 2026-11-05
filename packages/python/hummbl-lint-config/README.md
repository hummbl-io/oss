# hummbl-lint-config

Shared ruff lint configuration for the HUMMBL fleet.

## Usage

### As a package (recommended)

Not on PyPI as of 2026-11-01. From the monorepo root, install the source:

```bash
pip install -e packages/python/hummbl-lint-config
```

In your repo's `ruff.toml`:
```toml
extend = "hummbl_lint_config/ruff.toml"
```

### As a direct reference

Clone this repo and reference the config:
```toml
extend = "../hummbl-lint-config/ruff.toml"
```

## Rules

| Rule | Purpose |
|------|---------|
| `B904` | `raise ... from err` in except blocks |
| `SIM` | Code simplifications |
| `I` | Import ordering (isort) |
| `UP` | Pyupgrade — deprecated Python patterns |

`PLW1514` (missing `encoding=` on `open()`) was removed: it is preview-gated in ruff and silently unenforced without `preview = true`, which would activate unrelated preview rules. Revisit per-package if the rule stabilizes.

## License

MIT OR Apache-2.0 — see [LICENSE](LICENSE).
