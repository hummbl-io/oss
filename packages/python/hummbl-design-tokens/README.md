# hummbl-design-tokens

Single source of truth for HUMMBL fleet visual identity. Authors design tokens
in YAML, generates outputs for every rendering surface: Base24 terminal themes,
CSS custom properties, Python/TypeScript color modules, livery configs, and
documentation swatches.

## Quick start

```bash
pip install -e ".[test]"
python -m hummbl_design_tokens generate --all --outdir ./output
```

## Token source

All tokens are authored in `hummbl_design_tokens/data/tokens.json`. This is the
canonical source — every output format is derived from it. JSON is used instead
of YAML to maintain zero third-party runtime dependencies (stdlib only).

## Outputs

| Output | File | Surface |
|--------|------|---------|
| Base24 terminal theme | `base24-hummbl.yml` | foot, Alacritty, Kitty, iTerm2 |
| CSS custom properties | `hummbl-tokens.css` | Web dashboards |
| Python color module | `colors.py` | Python applications |
| TypeScript color module | `colors.ts` | TypeScript/JavaScript applications |
| Livery configs | `liveries/<agent>.json` | Per-agent livery definitions |
| Documentation swatches | `swatches.html` | Visual reference page |

## Design decisions

See `docs/2026-09-02-swarm-synthesis-master-design-decisions.md` in the
`hummbl-io/design-reference` repo for the full research basis and resolved
contradictions.
