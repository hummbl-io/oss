# ARCANA Ecosystem Roadmap

This roadmap keeps the platform expansion disciplined now that sibling modules
exist as contract surfaces. The goal is to move from named modules to useful
governed behavior without creating parallel systems that drift from ARCANA core.

## Current State

The ecosystem has matured significantly. All nine modules now have personas
inlined in `scripts/lenses.json`, and most have SOUL.md files in
`~/.agents/agents/souls/`. The current persona count:

| Module | Personas | Status |
|--------|----------|--------|
| **ARCANA** | 60 theoretical lenses | Mature — generation, synthesis, article contracts, CLI/runtime |
| **PRAXIS** | 11 archetypes (all in lenses.json) | Mature — all 11 have system prompts + SOUL.md files |
| **POIESIS** | 5 stage personas (all in lenses.json) | v0.2 — all 5 have system prompts + SOUL.md files |
| **PAIDEIA** | 9 scorer personas (all in lenses.json under `paideia_scorers`) | v0.2 — all 9 have system prompts in lenses.json |
| **NOMOS** | 3 personas (all in lenses.json) | v0.2 — hammurabi, grotius, kant; all have SOUL.md files |
| **LINGUA** | 3 personas (all in lenses.json) | v0.2 — orwell, borges, rhetoric_aristotle; all have SOUL.md files |
| **EVIDENCE** | 3 personas (all in lenses.json) | v0.2 — sherlock, bohr, foucault_panopticon; all have SOUL.md files |
| **RELEASE** | 3 personas (all in lenses.json) | v0.2 — hermes_gatekeeper, prometheus, pandora; all have SOUL.md files |
| **PRAWN** | 5 stage personas (all in lenses.json) | v0.1-draft, pressure-tested against 5 ARCANA lenses; stage-lenses landed |
| **SYNTHESIS** | 3 orchestration-role personas (all in lenses.json) | ROADMAP — contracts + personas scaffolded; runtime out of scope this phase |
| **CANON** | 3 registry-stage personas (all in lenses.json) | ROADMAP — contracts + personas scaffolded; registry out of scope this phase |
| **Total** | **103 personas across 11 modules** | |

The critical constraint is that every new sibling must first produce reusable
contracts and receipts before it grows custom runtime behavior.

## Near-Term Enhancements

~~Personas for NOMOS, LINGUA, EVIDENCE, and RELEASE~~ — **Done**. All four
modules now have 3 personas each inlined in `scripts/lenses.json` with SOUL.md
files. The remaining near-term work is contract and runtime:

1. Contract receipts
   - Add minimal receipt dataclasses or dict schemas for NOMOS, EVIDENCE,
     RELEASE, and LINGUA.
   - Keep receipts stdlib-only and JSON-serializable.
   - Ensure every receipt records module name, version, source artifact,
     timestamp, decision/status, and evidence references.

2. Artifact manifest
   - Define a single manifest shape for generated articles, scores, variants,
     and release outputs.
   - Let sibling receipts attach to the manifest instead of each sibling
     inventing a different index.

3. Cross-module validation
   - Extend `make test` with checks that all sibling modules remain importable,
     all README contract references are current, and every contract surface has
     at least one receipt schema test before runtime code lands.

4. Release gate skeleton
   - Implement RELEASE as the first executable sibling because it composes the
     others naturally: PAIDEIA score, NOMOS standards note, EVIDENCE audit
     summary, LINGUA editorial check.
   - Keep the first gate read-only: it reports `pass`, `hold`, or `blocked`
     without publishing.

## Medium-Term Enhancements

1. NOMOS mapping tables
   - Start with stable internal mapping tables for NIST AI RMF, ISO 42001, and
     EU AI Act categories.
   - Avoid policy interpretation beyond mapping and evidence trace until the
     receipt model is stable.

2. EVIDENCE history index
   - Add append-only JSONL or TSV evidence history for score drift, generator
     failures, retries, and release holds.
   - Keep history local and deterministic before any dashboard integration.

3. LINGUA variant policy
   - Define channel policies for human article, LLM article, summary, and
     metadata variants.
   - Add citation/paraphrase checks before adding style-heavy generation.

4. PAIDEIA scorer hardening
   - Replace remaining hard-axis stubs with evidence-backed detector paths.
   - Preserve v0.1 behavior as a compatibility mode.

## What Not To Build Yet

- No separate sibling runtime daemons.
- No external publication automation until RELEASE has read-only gates.
- No dashboard-first EVIDENCE work before file-level evidence records exist.
- No policy/legal claims in NOMOS that cannot be traced to a mapping table or
  explicit human-authored note.
- No stylistic rewrite engine in LINGUA before citation integrity checks exist.

> **Note**: The persona layer is now complete across all modules (97 personas
> in lenses.json). The remaining "not yet" items are about runtime behavior and
> contract enforcement, not about persona or system-prompt coverage.

## First Executable Slice

The first useful cross-module workflow should be:

```
article.md
  -> PAIDEIA score
  -> LINGUA citation/style check
  -> NOMOS standards note
  -> EVIDENCE audit summary
  -> RELEASE read-only gate decision
```

The output should be one JSON receipt bundle plus a short Markdown summary. This
keeps the system reviewable, deterministic, and easy to test before any
publishing action is authorized.

## Lane Split

1. Contract/schema lane
   - Owns receipt schemas, manifest export, and contract/doc drift checks.
   - Avoids runtime policy changes except where needed for validation.

2. RELEASE lane
   - Owns the read-only gate and future configurable policy thresholds.
   - Must remain side-effect-free until explicit publication automation is
     authorized.

3. PAIDEIA lane
   - Owns detector quality and scorer compatibility.
   - Replaces v0.1 hard-axis stubs incrementally while keeping existing score
     outputs readable.
