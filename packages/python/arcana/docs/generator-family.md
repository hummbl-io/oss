# Generator Family Pattern

The arcana pipeline has a family of brainstorm-and-merge generators. This doc
captures the shared pattern so adding a new generator is mechanical.

## Current members

| Generator | Produces | Merges into | Runner flag |
|-----------|----------|-------------|------------|
| `generate_topics.py` | topic strings | `topics-*.txt` (feeds `--topics-file`) | — |
| `generate_agents.py` | lens profiles (id/school/system) | `lenses.json.lenses` | `--lenses` |
| `generate_pairings.py` | named lens bundles | `lenses.json.presets` | `--preset` |
| `generate_synthesis_variants.py` | alternative synthesist prompts | `lenses.json.synthesists` | `--synthesist` |
| `generate_scenarios.py` | per-lens paradigm cases | `lens_docs/<id>.md` | — (docs only) |
| `generate_paideia_plan.py` | PAIDEIA-9 content plan | `paideia/plans/` (no merge) | (future: `--plan`) |
| `kstar_diagnostic.py` | TF-IDF K* proxy on lens outputs or `lenses.json` prompts | stdout / JSON report | — |
| `arcana_praxis_poiesis_crosswalk.py` | ARCANA×PRAXIS×POIESIS synthesis | dated research artifact | — (overnight) |
| `prawn_arcana_praxis_crosswalk.py` | PRAWN×ARCANA×PRAXIS synthesis | dated research artifact | — (overnight) |

## Shared shape

```
┌─────────────────┐
│  --theme/input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    endpoints.json → Ollama /api/generate
│   brainstorm()  │    (format=json, think=false)
└────────┬────────┘
         │ raw JSON response
         ▼
┌─────────────────┐    optional: --self-review pass
│    validate()   │    (each generator's custom validator)
└────────┬────────┘
         │ list of accepted items
         ▼
┌─────────────────┐
│  staging file   │ (gitignored per-day JSON in <type>/ dir)
└────────┬────────┘
         │
         ▼
┌─────────────────┐    TSV log (git-tracked)
│ append_log()    │    columns: timestamp, source, theme, model,
└────────┬────────┘             seed, prompt_version, + domain fields
         │
         │ optional: --merge
         ▼
┌─────────────────┐
│ lenses.json or  │ live config consumed by overnight_v0.py
│ topics file     │
└─────────────────┘
```

## Adding a new generator

1. **Decide the output shape** — list of structured items vs. single plan vs. per-id file. Be explicit about what merges where.
2. **Pick the shared-library surface** from `_gen_common.py`:
   - `load_endpoint()` — always
   - `ollama_generate()` — always
   - `self_review()` — opt-in on `--self-review`
   - `TsvLog` — always (append-only logging)
   - `validate_required_string_fields()` — reuse for basic shape checks
   - `standard_argparse()` — base CLI flags (--model, --endpoint, --seed, --output, --dry-run, --self-review)
   - `provenance_row()` — standard log row with prompt_version
3. **Write the generator** following the conventions:
   - Module-level `PROMPT_VERSION = "<name>-v1"` (bump on schema-changing prompt edits)
   - `build_prompt(...)` returning `(system, user)` tuple; keep prompts inline (but versioned) for now
   - `validate_<item>()` returning `(ok, reason)` tuple
   - If `--merge` applies: `merge_into_<target>(items, path) -> int`
   - `main()` uses `gc.standard_argparse()` and extends with generator-specific flags
4. **Add log columns** — generator log TSV columns should include the common provenance fields plus anything domain-specific
5. **Write tests** — at minimum: validator happy/sad paths. Use `test_gen_common.py` as template.
6. **Update `.gitignore`** — per-day staging files should be gitignored; logs stay tracked.

## Conventions

- **Prompt version**: every generator has `PROMPT_VERSION` logged per-row. Bump when the prompt schema changes. Lets you re-run analysis on "only rows produced by paideia-plan-v1 vs v2."
- **Referent clarity**: when the generator produces scored/classified content (like PAIDEIA), every score specifies a `referent` (artifact | reader_state | reader_demand) to avoid silent category slips.
- **Scope flag**: `instructional_intent: bool` for content-design generators. Non-instructional artifacts score some axes as advisory rather than deficient.
- **Hit-rate visibility**: rejection reasons go to stderr. Future: log rejections as TSV rows with `source="rejected"` for mineable failure analysis.
- **Timeout tolerance**: `gc.ollama_generate` catches `TimeoutError | OSError | URLError` — a hung model call returns `OllamaResult.parse_error`, not an uncaught exception.
- **Fallback chain**: when possible, offer a lighter synthesist/model path on timeout (cf. overnight_v0.py's minimalist synthesist pattern).
- **Generated artifacts**: scoring outputs like `scripts/paideia/scores/*.json` are runtime sidecars and must stay untracked; `scripts/paideia/history.tsv` is the canonical tracked log.
- **Retention option**: run `make archive-scores` to snapshot generated score JSONs into an ignored archive directory for occasional audit/review; canonical score history remains `scripts/paideia/history.tsv`.

## Hardening roadmap

| # | Item | Status | Where |
|---|------|--------|-------|
| 1 | Extract shared library | DONE | `_gen_common.py` |
| 2 | Prompt versioning | DONE | `PROMPT_VERSION` per module + log column |
| 3 | Self-review pass option | DONE | `--self-review` via standard_argparse |
| 4 | Tests for shared library | DONE | `test_gen_common.py` (32 tests) |
| 5 | Timeout/OSError catch in Ollama calls | DONE | `gc.ollama_generate` |
| 6 | Refactor 5 existing generators | DONE | topics/agents/pairings/synth/scenarios |
| 7 | Log rejection reasons to TSV | DONE | `source=rejected` rows w/ `reason` col |
| 8 | Retry on validation failure | DONE | `gc.run_brainstorm` (all 4 generators) + `--min-accepted`/`--max-retries` |
| 9 | Move prompts to versioned template files | DONE (5/6) | `prompts/<name>_v<N>.txt` |
| 10 | TSV schema migration helper | DONE | `migrate_logs.py` |
| 11 | Hit-rate analytics | DONE | `analyze_logs.py` |
| 12 | `--preview-merge` diff flag | DONE | `--preview-merge` on agents/pairings/synthesis_variants |
| 13 | Central `generators` CLI | PENDING | — |
| 14 | LLM detectors for score_paideia D/V/L axes | BLOCKED pending human calibration set | `score_paideia.py --use-llm` requires `--allow-uncalibrated` |
| 15 | Synthesist claims-only input | DONE | `overnight_v0.py --synth-input claims` |
| 16 | K* diagnostic on lens outputs | DONE (TF-IDF proxy) | `kstar_diagnostic.py` |

## Retry pattern

Opt-in for any generator that has variance (hit rate below ~80%). All four
brainstorm generators (agents, pairings, scenarios, synthesis_variants) call
`gc.run_brainstorm`, which encapsulates ollama → optional self-review →
list extraction → per-item validation → optional retry-with-bumped-seed.

```python
seen: set[str] = set()

def validator(item: dict) -> tuple[bool, str]:
    ok, reason = validate(item, excluded | seen)
    if ok:
        seen.add(item["id"])
    return ok, reason

accepted, rejected, last_result = gc.run_brainstorm(
    endpoint=endpoint,
    build_prompt=lambda: build_prompt(args.theme, args.count),
    list_key="lenses",                 # key inside the parsed JSON
    item_validator=validator,          # closure over seen-set
    base_seed=args.seed,
    self_review=args.self_review,
    schema_hint="...",                 # only used when self_review=True
    timeout=900,
    min_accepted=args.min_accepted,
    max_retries=args.max_retries,
    log_fn=lambda m: print(m, file=sys.stderr))
```

CLI:
```bash
python generate_agents.py --theme X --count 5                    # single attempt
python generate_agents.py --theme X --count 5 \
    --min-accepted 4 --max-retries 3                             # up to 4 attempts
```

Cross-attempt dedup is done by the validator closure — it owns its `seen`
set and rejects any item whose id is already in it. `run_brainstorm` itself
is stateless about content; it only stages the bumped seed and the retry
loop. Exceptions raised inside an attempt are caught and recorded as
rejection rows with `attempt_error: <cls>: <msg>` reasons.

## Prompt-file pattern

Each generator loads its versioned prompt from `prompts/<name>_v<N>.txt`:

```python
system, user_tmpl = gc.load_prompt("topics", "v1")
user = user_tmpl.safe_substitute(theme=theme, count=count)
```

File format:
```
---SYSTEM---
System prompt text.
---USER---
User prompt template with $variables.
```

Prompt version lives in the filename (`topics_v1.txt` → `topics_v2.txt`). The
generator's `PROMPT_VERSION = "topics-v1"` constant should match; bumping =
creating a new file, never editing v1.

## Migration / destructive-edit safety

Any tool that rewrites a TSV log, merges into a config file, or deletes
generator artifacts must follow the dry-run-first rule:

1. **Always run with `--dry-run` first.** The runner must print the planned
   diff (rows added/removed/changed, files affected) without touching disk.
2. **Inspect the planned diff against the source-of-truth columns.** For
   schema migrations on TSV logs, the canonical column list lives in each
   generator's `LOG_COLUMNS` constant — read those, do not hand-roll.
3. **Only after a clean dry-run output, re-run without `--dry-run`.**

Why: a prior `migrate_logs.py` run added a `reason` column but missed
`prompt_version`, producing a schema mismatch with the refactored
generators. Backups saved the data, but the lesson is: planned-vs-actual
diffs should be visible before bytes are written, and the column source
must be the generator module, not a copy in the migration script.

Tools that must support `--dry-run`:

- `migrate_logs.py` — TSV schema migrations
- `score_all.py` — sidecar JSON writes (already supports `--dry-run`)
- `overnight_v0.py --plan` — preview without running
- Any future `--preview-merge` flag on generators with `--merge`

A merge or migration tool without `--dry-run` is treated the same as one
without `--help`: incomplete and not landable.

For generators with `--merge`, the equivalent flag is `--preview-merge`:

```bash
python generate_agents.py --theme X --merge lenses.json --preview-merge
# stderr: "would merge 3 new lens(es) into lenses.json"
#         "  + new_lens_1"
#         "  = existing_lens (already present)"
# (no write)
```

The merge function returns `(added_ids, skipped_ids)` so any future tooling
can drive the same diff without re-implementing the planning logic.

## Anti-patterns

- **Inline prompts that change silently** — without `PROMPT_VERSION` bump, quality regressions are invisible. Bump when you edit.
- **Generators that write directly to `lenses.json` without staging** — the staging → merge pattern lets you review before committing.
- **Validators that hide rejection reasons** — every reject should surface *why*, for future hit-rate analysis.
- **Logging as stdout prose** — stdout is for human runners; all structured signal goes to the TSV log.
- **Hit-rate theater** — an 80% "accept" that ships 40% garbage is worse than a 50% accept that ships 50% good. Tighten validators before relaxing them.
- **Destructive runs without `--dry-run` first** — migrations and merges must preview before writing. See "Migration / destructive-edit safety" above.
- **Migration scripts that hand-roll column lists** — read `LOG_COLUMNS` from the generator module so the source of truth is in one place.
