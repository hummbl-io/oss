# hummbl-lint-config

Shared ruff lint configuration for the HUMMBL fleet.

## Usage

### As a package (recommended)

```bash
pip install hummbl-lint-config
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
| `PLW1514` | Missing `encoding` on `open()` calls |
| `B904` | `raise ... from err` in except blocks |
| `SIM` | Code simplifications |
| `I` | Import ordering (isort) |
| `UP` | Pyupgrade — deprecated Python patterns |

## License

Apache 2.0
