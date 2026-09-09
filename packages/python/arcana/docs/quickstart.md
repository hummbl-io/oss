# arcana quickstart

From zero to one generated article in ~20 minutes, assuming you have Ollama
running on at least one reachable endpoint.

## Prerequisites

- **Python 3.11+** (3.12 tested)
- **Ollama** running somewhere reachable with a capable model.
  Current default in `scripts/endpoints.json`: `qwen3.5:9b` on `127.0.0.1`.
  Override with:
  - `ARCANA_OLLAMA_URL`
  - `ARCANA_OLLAMA_MODEL`
  - `ARCANA_OLLAMA_NAME`
  - `ARCANA_ENDPOINTS_PATH` (to a custom JSON file with one or more endpoints)
- **Git Bash or POSIX shell** on Windows (for the `PROJECTS/arcana/` path)
- **uv** is optional; plain `python` works fine — there are no third-party
  runtime deps (stdlib only).

## First run (generate one article on a topic you pick)

```bash
cd PROJECTS/arcana/scripts

# 1. Sanity check — endpoint is reachable
curl -sS "$(python -c 'import _gen_common as g; e=g.load_endpoint(); print(e["url"])')/api/tags" | head -c 200

# 2. Dry-run to see what lenses will be dispatched (no Ollama calls)
python overnight_v0.py --topic "your topic here" --dry-run

# 3. Pick a preset for a focused 3-lens run (faster than all 27)
python overnight_v0.py --topic "your topic here" \
    --preset state_of_exception_vs_constitutional_floor

# OR: full-roster run (27 lenses, ~20-30 min on qwen3.5:9b on M4 Pro)
python overnight_v0.py --topic "your topic here"

# 4. Inspect the result
ls outputs/$(date -u +%Y-%m-%d)/*/
cat outputs/$(date -u +%Y-%m-%d)/*/article.md
```

The output directory contains:
- `article.md` — canonical human-readable output
- `synthesis.json` — structured synthesis (title, convergences, divergences, etc.)
- `perspective_<lens>.json` — one per lens that ran
- `run.log` — timestamps + token counts per call

## Add agent-optimized variants (CPU-only post-processor)

```bash
python generate_article_variants.py --all
```

Creates `article.llm.md`, `meta.json`, `schema.jsonld`, `summary.txt`,
`reflection.md` in each output dir.

## Publish to llms.txt

```bash
python generate_llms_txt.py
# writes ../llms.txt + ../llms-full.txt at repo root
```

## Common recipes

### Recover from a synthesis failure
When synthesis times out or errors but perspectives landed:

```bash
python overnight_v0.py --resynth outputs/2026-04-24/my-topic-slug/ \
    --synthesist minimalist
```

### Run a batch with safety net
```bash
python overnight_v0.py \
    --topics-file topics/my-list.txt \
    --fallback-synthesist minimalist
```

If primary synthesist times out or errors on any topic, auto-retries with
the minimalist synthesist (produces shorter output, rarely times out).

### Use a PAIDEIA-9 target contract
```bash
# Generate a target plan
python generate_paideia_plan.py --topic "rate limiters" \
    --expertise-stage competent --target-solo relational

# Run with plan as contract; delta written to paideia_delta.json after
python overnight_v0.py --topic "rate limiters" \
    --plan paideia/plans/plan-2026-04-24-rate-limiters.json
```

## Generate more material (brainstorm generators)

Each of these follows the same pattern: `--theme THEME --count N --seed N`,
plus generator-specific flags. All produce staging files + TSV log rows.
Merge into `lenses.json` with `--merge lenses.json`.

```bash
# Topics for a batch run
python generate_topics.py --theme "AI governance" --count 10

# New lens profiles
python generate_agents.py --theme "political theology" --count 4 \
    --require-primary-texts 2

# Lens pairings (tension groups)
python generate_pairings.py --theme "enterprise agents" --count 4 --size 3

# Synthesist style variants
python generate_synthesis_variants.py --styles tension,socratic,minimalist

# Paradigm scenarios per lens (documentation)
python generate_scenarios.py --lens all --count 3
```

## Debugging

### "endpoint refused connection"
Ollama isn't running or the URL/port in `endpoints.json` is wrong. Check
`curl <url>/api/tags`.

### "synthesist timed out"
Default timeout is 900s. For heavy topics, add `--fallback-synthesist minimalist`.

### "primary-text signals"
`generate_agents.py --require-primary-texts 2` rejects lens profiles that
don't name actual books/years/thinkers. Drop to 0 to disable; raise to 3
for stricter academic grounding.

### Tests
```bash
python -m pytest tests/ -v      # 225 tests across 12 files
```

No Ollama calls during tests.

## When the model is busy

If a local GPU is doing something else (training, image gen), the Ollama
endpoint may be slow or contended. Running arcana against a remote endpoint
via Tailscale keeps GPU contention off the primary workstation.

## Next steps

- [paideia-9.md](paideia-9.md) — design your content's target vector
- [generator-family.md](generator-family.md) — write a new generator
- [llm-content-templates.md](llm-content-templates.md) — per-article output contract
