"""Validator tests for each generator's custom validation logic.

Each generator defines a `validate()` function that checks domain-specific
rules on LLM output. These tests don't call Ollama — they construct synthetic
dicts that match or violate the schema and confirm validate() accepts/rejects
them correctly.

Run with: python -m pytest scripts/test_generators.py -v
Or:       python scripts/test_generators.py

Coverage target: every rejection reason surfaced in production this week.
"""
from __future__ import annotations

import json as _json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_agents
import generate_pairings
import generate_scenarios
import generate_synthesis_variants as generate_sv

# --------------------- generate_agents ---------------------------------- #

def _agent(id_="schmitt", school="ARCANA / political-theology",
           system=None) -> dict:
    if system is None:
        system = ("You are Carl Schmitt, focusing on friend-enemy distinctions "
                  "and the state of exception. Your key terms include "
                  "sovereignty, decision, and concrete order. ") * 5
    return {"id": id_, "school": school, "system": system}


def test_agent_validate_happy():
    ok, _ = generate_agents.validate(_agent(), existing=set())
    assert ok


def test_agent_validate_missing_field():
    a = _agent()
    del a["school"]
    ok, why = generate_agents.validate(a, existing=set())
    assert not ok and "school" in why


def test_agent_validate_duplicate_id():
    ok, why = generate_agents.validate(_agent(), existing={"schmitt"})
    assert not ok and "duplicate" in why.lower()


def test_agent_validate_bad_snake_case():
    ok, why = generate_agents.validate(_agent(id_="Schmitt"), existing=set())
    assert not ok and "snake_case" in why


def test_agent_validate_system_too_short():
    ok, why = generate_agents.validate(_agent(system="too short"), existing=set())
    assert not ok and "too short" in why


def test_agent_validate_id_not_in_prompt():
    # Content is about Newman, id is 'bennett' — the real 2026-04 failure mode
    ok, why = generate_agents.validate(_agent(
        id_="bennett",
        system=("You are John Henry Newman, explicating the secular as a "
                "sphere with quasi-theological structures. ") * 7),
        existing=set())
    assert not ok and "does not appear" in why


def test_agent_id_appears_in_prompt_snake_case_components():
    # leto_ii should match on "leto"
    assert generate_agents.id_appears_in_prompt(
        "leto_ii",
        "Frank Herbert's Leto II Atreides merged with sandtrout...")


def test_agent_count_primary_texts():
    text = "Schmitt, *Political Theology* (1932), distinguishes friend and enemy."
    assert generate_agents.count_primary_text_signals(text) >= 2


# --------------------- generate_pairings -------------------------------- #

def _pairing(name="tension_pair", lenses=("schmitt", "arendt", "hayek"),
             why_tension=None, example_topic="emergency powers during a pandemic") -> dict:
    if why_tension is None:
        why_tension = ("Schmitt reads this through the friend-enemy distinction; "
                       "Arendt through plural action; Hayek through spontaneous order. "
                       "They disagree about who decides and whether decision is possible.")
    return {"name": name, "lenses": list(lenses),
            "why_tension": why_tension, "example_topic": example_topic}


def test_pairing_validate_happy():
    ok, _ = generate_pairings.validate(
        _pairing(), roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert ok


def test_pairing_validate_unknown_lens():
    ok, why = generate_pairings.validate(
        _pairing(lenses=("schmitt", "arendt", "nonexistent")),
        roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert not ok and "unknown" in why


def test_pairing_validate_wrong_size():
    ok, why = generate_pairings.validate(
        _pairing(lenses=("schmitt", "arendt")),
        roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert not ok and "exactly 3" in why


def test_pairing_validate_duplicate_lenses():
    ok, why = generate_pairings.validate(
        _pairing(lenses=("schmitt", "schmitt", "arendt")),
        roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert not ok and "duplicate" in why


def test_pairing_validate_bad_name():
    ok, why = generate_pairings.validate(
        _pairing(name="BadName"),
        roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert not ok and "snake_case" in why


def test_pairing_validate_short_tension():
    ok, why = generate_pairings.validate(
        _pairing(why_tension="too short"),
        roster_ids={"schmitt", "arendt", "hayek"},
        existing_names=set(), size=3)
    assert not ok and "50 chars" in why


# --------------------- generate_synthesis_variants ---------------------- #

def _synth(id_="tension", description="surfaces divergences",
           system=None) -> dict:
    if system is None:
        system = ("You are the tension-synthesist. You read per-lens perspectives "
                  "and produce a synthesis that refuses to smooth irreducible "
                  "disagreements. ") * 3 + "Return JSON with keys: title, summary, convergences, divergences, synthesis, live_questions, tags, confidence_score."
    return {"id": id_, "description": description, "system": system}


def test_synth_validate_happy():
    ok, _ = generate_sv.validate(_synth(), existing=set())
    assert ok


def test_synth_validate_missing_schema_sentence():
    ok, why = generate_sv.validate(_synth(
        system=("x" * 250)),   # long enough but no "Return JSON"
        existing=set())
    assert not ok and "Return JSON" in why


def test_synth_validate_bad_id():
    ok, why = generate_sv.validate(_synth(id_="BadID"), existing=set())
    assert not ok and "snake_case" in why


def test_synth_validate_duplicate():
    ok, why = generate_sv.validate(_synth(), existing={"tension"})
    assert not ok and "duplicate" in why.lower()


# --------------------- generate_scenarios ------------------------------- #

def _scenario(title="Border Closure Protocol",
              setup=None,
              what_lens_sees="The sovereign performs the decision to declare an enemy.",
              what_lens_misses="It overlooks how exclusion radicalizes domestic populations.") -> dict:
    if setup is None:
        setup = ("In early 2023, a sovereign nation halts cross-border travel "
                 "and seizes foreign tech firm assets, citing an undefined "
                 "digital contagion that threatens national existence. The "
                 "legislature's attempt to debate is overruled by the executive. "
                 "This is a classic suspension of legal order in the name of concrete order.")
    return {"title": title, "setup": setup,
            "what_lens_sees": what_lens_sees,
            "what_lens_misses": what_lens_misses}


def test_scenario_validate_happy():
    ok, _ = generate_scenarios.validate(_scenario())
    assert ok


def test_scenario_validate_missing_field():
    sc = _scenario()
    del sc["what_lens_misses"]
    ok, why = generate_scenarios.validate(sc)
    assert not ok and "what_lens_misses" in why


def test_scenario_validate_setup_too_short():
    ok, why = generate_scenarios.validate(_scenario(setup="Too short."))
    assert not ok and "too short" in why


def test_scenarios_run_one_lens_dry_run_skips_write(tmp_path, monkeypatch):
    """Regression test: --dry-run on generate_scenarios must not write
    lens_docs/<id>.md or append to the SCENARIOS_LOG TSV."""
    import _gen_common as gc
    fake_lens_def = {"school": "test", "system": "test"}
    fake_accepted = [_scenario()]
    fake_result = gc.OllamaResult(
        parsed={"scenarios": fake_accepted}, raw="", elapsed_s=0.1,
        prompt_tokens=10, completion_tokens=5,
        model="fake", endpoint_name="fake")

    def fake_brainstorm(**kwargs):
        return fake_accepted, [], fake_result
    def fake_load_lens(lens_id):
        return fake_lens_def

    docs_dir = tmp_path / "lens_docs"
    log_path = tmp_path / "scenarios.tsv"
    monkeypatch.setattr(gc, "run_brainstorm", fake_brainstorm)
    monkeypatch.setattr(generate_scenarios, "load_lens", fake_load_lens)
    monkeypatch.setattr(generate_scenarios, "LENS_DOCS_DIR", docs_dir)
    monkeypatch.setattr(generate_scenarios, "SCENARIOS_LOG", log_path)

    endpoint = {"name": "fake", "model": "fake-model", "url": "http://x"}
    ok = generate_scenarios.run_one_lens(
        endpoint, "test_lens", count=1, force=False, seed=1,
        self_review=False, dry_run=True)
    assert ok is True
    # Critical assertions: no disk side effects under dry_run
    assert not (docs_dir / "test_lens.md").exists()
    assert not log_path.exists()


def test_scenarios_run_one_lens_writes_when_not_dry_run(tmp_path, monkeypatch):
    """Counterpart to the dry-run test: confirms the writer code path is
    intact (i.e. the dry-run fix didn't accidentally short-circuit production
    writes)."""
    import _gen_common as gc
    fake_lens_def = {"school": "test", "system": "test"}
    fake_accepted = [_scenario()]
    fake_result = gc.OllamaResult(
        parsed={"scenarios": fake_accepted}, raw="", elapsed_s=0.1,
        prompt_tokens=10, completion_tokens=5,
        model="fake", endpoint_name="fake")

    def fake_brainstorm(**kwargs):
        return fake_accepted, [], fake_result

    docs_dir = tmp_path / "lens_docs"
    log_path = tmp_path / "scenarios.tsv"
    monkeypatch.setattr(gc, "run_brainstorm", fake_brainstorm)
    monkeypatch.setattr(generate_scenarios, "load_lens", lambda lid: fake_lens_def)
    monkeypatch.setattr(generate_scenarios, "LENS_DOCS_DIR", docs_dir)
    monkeypatch.setattr(generate_scenarios, "SCENARIOS_LOG", log_path)

    endpoint = {"name": "fake", "model": "fake-model", "url": "http://x"}
    ok = generate_scenarios.run_one_lens(
        endpoint, "test_lens", count=1, force=True, seed=1,
        self_review=False, dry_run=False)
    assert ok is True
    assert (docs_dir / "test_lens.md").exists()
    assert log_path.exists()


# ---- merge_into_lenses_json (agents/pairings/synthesis) ---------------- #


def test_agents_merge_writes_and_reports_diff(tmp_path):
    target = tmp_path / "lenses.json"
    target.write_text(_json.dumps({"lenses": {"existing": {"school": "x", "system": "y"}}}),
                      encoding="utf-8")
    new = [{"id": "new_one", "school": "S", "system": "Sys text long enough"},
           {"id": "existing", "school": "S2", "system": "would-collide"}]
    added, skipped = generate_agents.merge_into_lenses_json(new, target)
    assert added == ["new_one"]
    assert skipped == ["existing"]
    data = _json.loads(target.read_text(encoding="utf-8"))
    assert "new_one" in data["lenses"]
    # Existing entry is preserved (not overwritten)
    assert data["lenses"]["existing"]["school"] == "x"


def test_agents_merge_dry_run_does_not_write(tmp_path):
    target = tmp_path / "lenses.json"
    original = {"lenses": {"keep": {"school": "x", "system": "y"}}}
    target.write_text(_json.dumps(original), encoding="utf-8")
    new = [{"id": "would_add", "school": "S", "system": "T"}]
    added, skipped = generate_agents.merge_into_lenses_json(
        new, target, dry_run=True)
    assert added == ["would_add"]
    assert skipped == []
    # File on disk is untouched
    on_disk = _json.loads(target.read_text(encoding="utf-8"))
    assert on_disk == original


def test_pairings_merge_writes_and_skips_existing(tmp_path):
    target = tmp_path / "lenses.json"
    target.write_text(_json.dumps({"presets": {"preset_a": {}}}),
                      encoding="utf-8")
    new = [{"name": "preset_a", "lenses": ["x", "y"], "why_tension": "t" * 60,
            "example_topic": "topic example"},
           {"name": "preset_b", "lenses": ["x", "y"], "why_tension": "t" * 60,
            "example_topic": "topic example"}]
    added, skipped = generate_pairings.merge_into_lenses_json(new, target)
    assert added == ["preset_b"]
    assert skipped == ["preset_a"]


def test_pairings_merge_dry_run_does_not_write(tmp_path):
    target = tmp_path / "lenses.json"
    original = {"presets": {}}
    target.write_text(_json.dumps(original), encoding="utf-8")
    new = [{"name": "p1", "lenses": ["a", "b"], "why_tension": "t" * 60,
            "example_topic": "topic example"}]
    added, skipped = generate_pairings.merge_into_lenses_json(
        new, target, dry_run=True)
    assert added == ["p1"] and skipped == []
    assert _json.loads(target.read_text(encoding="utf-8")) == original


def test_synth_merge_promotes_legacy_synthesist_key(tmp_path):
    target = tmp_path / "lenses.json"
    legacy = {"synthesist": {"system": "old-system-prompt"}}
    target.write_text(_json.dumps(legacy), encoding="utf-8")
    new = [{"id": "new_s", "description": "d", "system": "s"}]
    generate_sv.merge_into_lenses_json(new, target)
    data = _json.loads(target.read_text(encoding="utf-8"))
    # Legacy auto-promotion to synthesists.default
    assert "default" in data["synthesists"]
    assert data["synthesists"]["default"]["system"] == "old-system-prompt"
    # New synthesist also added
    assert "new_s" in data["synthesists"]


def test_synth_merge_dry_run(tmp_path):
    target = tmp_path / "lenses.json"
    target.write_text(_json.dumps({"synthesists": {"default": {}}}),
                      encoding="utf-8")
    new = [{"id": "default", "description": "d", "system": "s"},
           {"id": "fresh", "description": "d", "system": "s"}]
    added, skipped = generate_sv.merge_into_lenses_json(
        new, target, dry_run=True)
    assert added == ["fresh"]
    assert skipped == ["default"]


# --------------------- standalone runner -------------------------------- #

class _SimpleMonkeypatch:
    """Minimal monkeypatch shim for the standalone runner. Tracks attribute
    sets per (object, name) and restores them on undo()."""
    def __init__(self):
        self._restore: list = []

    def setattr(self, obj, name, value):
        self._restore.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, original in reversed(self._restore):
            setattr(obj, name, original)
        self._restore.clear()


def _run_standalone():
    """Fallback runner when pytest isn't available."""
    import inspect
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        mp = _SimpleMonkeypatch()
        try:
            sig = inspect.signature(fn)
            kwargs: dict = {}
            if "tmp_path" in sig.parameters:
                td = tempfile.mkdtemp()
                kwargs["tmp_path"] = Path(td)
            if "monkeypatch" in sig.parameters:
                kwargs["monkeypatch"] = mp
            fn(**kwargs)
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
        finally:
            mp.undo()
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
