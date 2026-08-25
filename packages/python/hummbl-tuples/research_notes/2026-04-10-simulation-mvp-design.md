# Governance Simulation MVP — Design Note

Date: 2026-04-10
Companion to: ADR-003

## Question

What is the minimum rule-based governance simulator that (a) exercises the existing tuple schemas as an execution surface, (b) demonstrably models the Gemini Probation Incident shape, and (c) leaves a clean interface point for Stage 2 validation, sensitivity analysis, and uncertainty quantification?

## Evidence (Stage 1, this commit)

`hummbl_tuples/simulation/` implements a deterministic rule-based simulator. Running

```
python3 -m hummbl_tuples.simulation --summary
```

against the synthetic `gemini-probation` scenario produces:

```json
{
  "contracts": 3,
  "evidence_events": 3,
  "probation_entries": 1,
  "probation_exits": 1,
  "scope_denials": 2,
  "total_events": 29
}
```

`test_simulation.py` asserts that:

1. every emitted event validates against the JSON Schemas in `schemas/`
   (reusing `reference_impl/validate_examples.py`),
2. the scenario shape matches the Gemini Probation Incident categories
   (violations → probation → restricted DCT → recovery → restored DCT),
3. the simulator is bitwise-deterministic under `seed=0`,
4. the restricted DCT reduces the executor's `ops_allowed` to
   `['read:research']` and the restored DCT returns the full original scope.

## Inference

The tuple schemas (`CONTRACT`, `DCT`, `DCTX`, `SYSTEM`, `EVIDENCE`) are
sufficient as an execution surface for a rule-based governance simulator at
the MVP scale. No new tuple classes were required. This is tentative support
for Hypothesis 2 in `2026-03-27-initial-hypotheses.md` ("`CONTRACT`, `DCT`,
`DCTX`, `SYSTEM`, and `EVIDENCE` may be enough for a practical first
taxonomy").

One mild pressure: `DCTX.event` carried a much wider vocabulary
(`contract_bound`, `probation_entered`, `probation_exited`) than any checked-in
example uses. The schema's `additionalProperties: true` accommodated this
without edits, but the event vocabulary is now a de-facto part of the
simulation contract and should be formalized before Stage 2 if any external
consumer parses it.

## Staged Roadmap

### Stage 1 — Shipped in this commit
- Rule-based deterministic core: `Environment`, `TrustModel`, `ProbationPolicy`,
  `SimulationClock`.
- Schema-conformant event constructors (`events.py`).
- Synthetic Gemini-probation scenario (`scenarios.py`).
- CLI runner (`python -m hummbl_tuples.simulation`).
- Regression test with schema validation + determinism check.
- `LLMAdapter` protocol defined but unused.

### Stage 2 — Required to call this a scientific instrument
- **Validation strategy.** Replace `metadata['source'] = 'synthetic'` with
  `'empirical'` plus a structured log dropped in from the Gemini Probation
  Incident corpus. The scenario's contract categories and action vocabulary
  are the migration contract.
- **Sensitivity analysis.** Sweep `TrustModel.violation_penalty`,
  `TrustModel.success_reward`, `ProbationPolicy.entry_threshold`,
  `ProbationPolicy.exit_threshold`, and
  `ProbationPolicy.consecutive_clean_required`. Morris elementary effects are
  the cheapest first pass; Sobol indices if budget allows. Reduce each trace
  via `trace_summary` so the analysis surface stays stable.
- **Uncertainty quantification.** Report distributions over scalar
  observables (denials, probation entries, time-to-recovery), not point
  estimates. Stage 1 is deterministic so UQ only becomes meaningful once
  either (a) the rule-based core admits stochastic components, or (b) the
  LLM adapter is wired in. Plumb `Environment.rng` through `TrustModel` for
  (a).

### Stage 3 — Research artifact
- Falsifiable claims about tuple-mediated execution governance grounded in
  traces from the empirical corpus.
- Comparisons against event-stream baselines per `comparisons/`.
- Candidate novelty claims lifted from `novelty_quest/`.

## Known Limitations

1. **Hallucination propagation.** Once an LLM-backed agent is introduced via
   `LLMAdapter`, denied ops must be hard errors rather than retry loops;
   otherwise the adapter can amplify hallucinated scope violations. The
   protocol docstring states this explicitly. Any external writeup must
   re-state it.
2. **Plain-language → simulation config.** Program synthesis from natural
   language into scenario config has unsolved reliability issues (cf. Yin &
   Neubig 2017). The MVP is scripted by hand; do not present any NL → config
   pipeline as production-ready without empirical evaluation.
3. **Sim-to-real gap.** Without domain randomization or explicit
   parameter sweeps, the simulator will overfit to whichever scenario shape
   it was tuned against (Zhao et al. 2020). Stage 2 sensitivity analysis is
   the minimum mitigation.
4. **Trust scalar.** `TrustModel` is a single bounded scalar with additive
   updates. This is sufficient for the MVP and matches the incident's
   categorical shape, but real agent trust is high-dimensional (tool-scope,
   recency, counterfactual risk). Flagged as a Stage 2 refactor point.
5. **No empirical ground truth in this branch.** Stage 1 validates the
   simulator's *internal consistency* (schemas, determinism, scenario
   shape), not its *external validity* against the Gemini Probation Incident
   logs. Treat Stage 1 as a demonstration, not a scientific finding.

## Uncertainty

- Medium confidence that the rule-based core generalizes to other
  synthetic governance incidents. Not yet tested beyond `gemini-probation`.
- Low confidence that the trust scalar will survive contact with the
  empirical corpus unmodified. Expect Stage 2 to demand a richer state.
- High confidence in the schema posture: emitting plain dicts that validate
  against `schemas/` is cheap and has already caught one latent
  `tuple_data.event` vocabulary drift during implementation.

## Confidence

- ADR-003's "prototype for hummbl-governance" framing is the right carve-out
  for ADR-002, **conditional on** Stage 2 staying bounded. If Stage 2 grows
  into a workflow engine or runtime, the package must migrate out of this
  repo.
- Stage 1 is honestly labeled: a demonstrable MVP, not a research finding.
  External writeups must not cite this commit as empirical evidence without
  Stage 2's validation harness.
