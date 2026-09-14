"""Schema validation for scripts/lenses.json lens and synthesist entries.

Ensures every lens has the required keys (school, system) with the correct
shape, and that system prompts contain the JSON return specification.
Guards against silent regression when lenses are added or edited.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
for _p in (str(SCRIPTS), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LENSES_PATH = SCRIPTS / "lenses.json"

EXPECTED_LENS_COUNT = 115
# Lenses that pre-date the "Return JSON with keys:" convention.
# New lenses MUST include the return spec; this list should not grow.
LENSES_WITHOUT_RETURN_SPEC = {"baudrillard"}


def _load_lenses() -> dict:
    """Load and return the lenses.json data structure."""
    assert LENSES_PATH.exists(), f"missing lenses file: {LENSES_PATH}"
    with LENSES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_lenses_json_is_valid_json():
    """lenses.json must parse without error."""
    _load_lenses()  # raises on invalid JSON


def test_top_level_keys():
    """Top-level must contain 'lenses', 'synthesist', 'presets', 'synthesists'."""
    data = _load_lenses()
    for key in ("lenses", "synthesist", "presets", "synthesists"):
        assert key in data, f"missing top-level key: '{key}'"
    assert isinstance(data["lenses"], dict), "'lenses' must be an object"
    assert isinstance(data["synthesist"], dict), "'synthesist' must be an object"
    assert isinstance(data["presets"], dict), "'presets' must be an object"
    assert isinstance(data["synthesists"], dict), "'synthesists' must be an object"


def test_lens_count():
    """Lens count must match EXPECTED_LENS_COUNT.

    Update EXPECTED_LENS_COUNT when lenses are intentionally added or removed.
    This catches accidental deletion or duplication.
    """
    data = _load_lenses()
    assert len(data["lenses"]) == EXPECTED_LENS_COUNT, (
        f"expected {EXPECTED_LENS_COUNT} lenses, got {len(data['lenses'])}; "
        f"update EXPECTED_LENS_COUNT if this change is intentional"
    )


def test_every_lens_has_school_and_system():
    """Each lens must have 'school' and 'system' string keys."""
    data = _load_lenses()
    for name, entry in data["lenses"].items():
        assert isinstance(entry, dict), f"lens '{name}' must be an object"
        assert "school" in entry, f"lens '{name}' missing 'school'"
        assert "system" in entry, f"lens '{name}' missing 'system'"
        assert isinstance(entry["school"], str), f"lens '{name}' school must be string"
        assert isinstance(entry["system"], str), f"lens '{name}' system must be string"
        assert len(entry["school"]) > 0, f"lens '{name}' school is empty"
        assert len(entry["system"]) > 0, f"lens '{name}' system is empty"


def test_every_lens_school_has_valid_prefix():
    """Each lens school must start with 'ARCANA /' or 'PRAXIS /'."""
    data = _load_lenses()
    valid_prefixes = ("ARCANA /", "PRAXIS /", "POIESIS /", "PRAWN /", "NOMOS /", "LINGUA /", "EVIDENCE /", "RELEASE /", "SYNTHESIS /", "CANON /")
    for name, entry in data["lenses"].items():
        school = entry["school"]
        assert school.startswith(valid_prefixes), (
            f"lens '{name}' school '{school}' must start with one of {valid_prefixes}"
        )


def test_every_new_lens_system_has_json_return_spec():
    """Each lens system prompt (except known legacy exceptions) must contain
    the JSON return specification."""
    data = _load_lenses()
    for name, entry in data["lenses"].items():
        if name in LENSES_WITHOUT_RETURN_SPEC:
            continue
        assert "Return JSON with keys:" in entry["system"], (
            f"lens '{name}' system prompt missing 'Return JSON with keys:' spec; "
            f"if this is a legacy lens, add it to LENSES_WITHOUT_RETURN_SPEC"
        )


def test_synthesist_has_school_and_system():
    """The singular 'synthesist' entry must have 'school' and 'system' keys."""
    data = _load_lenses()
    syn = data["synthesist"]
    assert "school" in syn, "synthesist missing 'school'"
    assert "system" in syn, "synthesist missing 'system'"
    assert isinstance(syn["school"], str)
    assert isinstance(syn["system"], str)


def test_every_synthesist_variant_has_description_and_system():
    """Each synthesist variant must have 'description' and 'system' keys."""
    data = _load_lenses()
    for name, entry in data["synthesists"].items():
        assert isinstance(entry, dict), f"synthesist variant '{name}' must be an object"
        assert "description" in entry, f"synthesist variant '{name}' missing 'description'"
        assert "system" in entry, f"synthesist variant '{name}' missing 'system'"
        assert isinstance(entry["system"], str)
        assert len(entry["system"]) > 0


def test_no_duplicate_lens_names():
    """Lens names must be unique (case-insensitive check for clarity)."""
    data = _load_lenses()
    names = list(data["lenses"].keys())
    lower_names = [n.lower() for n in names]
    assert len(lower_names) == len(set(lower_names)), (
        f"case-variant duplicate lens names detected: {names}"
    )


def test_new_philosophy_of_language_lenses_present():
    """Verify the 9 philosophy-of-language lenses added in the
    feat/philosophy-of-language-lenses branch are present."""
    data = _load_lenses()
    expected = {
        "humboldt", "herder", "wittgenstein", "heidegger",
        "sapir", "whorf", "nietzsche", "gadamer", "levinas",
    }
    actual = set(data["lenses"].keys())
    missing = expected - actual
    assert not missing, f"missing philosophy-of-language lenses: {missing}"


def test_arcana_wave_members_have_prompts():
    """Every member named in ecosystem_contracts.ARCANA_WAVES must have a
    runnable prompt in lenses.json. 'synthesist' is the synthesis agent
    (covered by the top-level 'synthesist' key), not a lens, so it is
    exempt. Guards against the wave structure referencing personas that
    cannot actually run in overnight_v0.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    wave_members: set[str] = set()
    for _label, members in ec.ARCANA_WAVES:
        wave_members.update(members)
    missing = sorted((wave_members - lens_ids) - {"synthesist"})
    assert not missing, (
        f"ARCANA_WAVES references {len(missing)} member(s) with no lens prompt "
        f"in lenses.json: {missing}. Either add the prompt or drop the member "
        f"from ARCANA_WAVES.")


def test_prawn_stages_have_prompts():
    """Every stage named in ecosystem_contracts.PRAWN_STAGES must have a
    runnable lens prompt in lenses.json. PRAXIS and POIESIS stages are
    already treated as runnable lenses; PRAWN must match, so a run can
    analyze a system *through* a PRAWN stage (e.g. the Account gate as a
    lens). Guards against PRAWN having contracts but no prompts.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    missing = sorted(set(ec.PRAWN_STAGES) - lens_ids)
    assert not missing, (
        f"PRAWN_STAGES references {len(missing)} stage(s) with no lens prompt "
        f"in lenses.json: {missing}. PRAWN must match PRAXIS/POIESIS: every "
        f"stage gets a runnable prompt.")


def test_synthesist_styles_all_present():
    """Every style named in generate_synthesis_variants.STYLE_DESCRIPTIONS
    must have a runnable prompt in lenses.json.synthesists. The generator
    can produce 7 styles; the live config must carry all 7 so --synthesist
    can select any of them. Guards against the generator and the lens store
    drifting out of sync. ('default' is the legacy synthesist, not a style,
    so it is not required to be in STYLE_DESCRIPTIONS.)
    """
    import generate_synthesis_variants as gsv
    data = _load_lenses()
    synth_ids = set(data["synthesists"].keys())
    missing = sorted(set(gsv.STYLE_DESCRIPTIONS) - synth_ids)
    assert not missing, (
        f"generate_synthesis_variants defines {len(missing)} style(s) with no "
        f"prompt in lenses.json.synthesists: {missing}. Add the variant or "
        f"drop the style from STYLE_DESCRIPTIONS.")


def test_praxis_archetypes_have_prompts():
    """Every archetype in ecosystem_contracts.PRAXIS_ARCHETYPES must have a
    runnable lens prompt in lenses.json. PRAXIS archetypes are treated as
    runnable lenses (school 'PRAXIS / ...'); the canonical roster and the
    lens store must not drift. Locks in the existing 11/11 completeness.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    missing = sorted(set(ec.PRAXIS_ARCHETYPES) - lens_ids)
    assert not missing, (
        f"PRAXIS_ARCHETYPES references {len(missing)} archetype(s) with no "
        f"lens prompt in lenses.json: {missing}. Add the prompt or drop the "
        f"archetype from PRAXIS_ARCHETYPES.")


def test_poiesis_stages_have_prompts():
    """Every stage in ecosystem_contracts.POIESIS_STAGES must have a runnable
    lens prompt in lenses.json. POIESIS stages are treated as runnable lenses
    (school 'POIESIS / ...'); the canonical roster and the lens store must not
    drift. Locks in the existing 5/5 completeness.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    missing = sorted(set(ec.POIESIS_STAGES) - lens_ids)
    assert not missing, (
        f"POIESIS_STAGES references {len(missing)} stage(s) with no lens "
        f"prompt in lenses.json: {missing}. Add the prompt or drop the stage "
        f"from POIESIS_STAGES.")


def test_paideia_scorers_cover_all_axes():
    """Every axis in ecosystem_contracts.PAIDEIA_AXES must have a matching
    scorer persona in lenses.json.paideia_scorers (matched on the scorer's
    'axis' field). Locks the v0.1 9-axis -> 9-scorer mapping so the contract
    and the scorer registry cannot drift. Superset entries for not-yet-adopted
    axes (e.g. emotion_scorer with axis 'Em' for the v0.2 EMOTION proposal)
    are allowed and ignored until the axis is added to PAIDEIA_AXES.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    scored_axes = {s["axis"] for s in data.get("paideia_scorers", {}).values()}
    missing = sorted(set(ec.PAIDEIA_AXES) - scored_axes)
    assert not missing, (
        f"PAIDEIA_AXES has {len(missing)} axis/axes with no scorer in "
        f"lenses.json.paideia_scorers: {missing}. Add the scorer persona or "
        f"drop the axis from PAIDEIA_AXES.")


def test_synthesis_roles_have_prompts():
    """Every role in ecosystem_contracts.SYNTHESIS_ROLES must have a runnable
    lens prompt in lenses.json (school 'SYNTHESIS / ...'). SYNTHESIS is a
    ROADMAP sibling; its roles are scaffolded as runnable lenses so the
    contract roster and the lens store cannot drift before runtime lands.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    missing = sorted(set(ec.SYNTHESIS_ROLES) - lens_ids)
    assert not missing, (
        f"SYNTHESIS_ROLES references {len(missing)} role(s) with no lens "
        f"prompt in lenses.json: {missing}. Add the prompt or drop the role "
        f"from SYNTHESIS_ROLES.")


def test_canon_stages_have_prompts():
    """Every stage in ecosystem_contracts.CANON_STAGES must have a runnable
    lens prompt in lenses.json (school 'CANON / ...'). CANON is a ROADMAP
    sibling; its stages are scaffolded as runnable lenses so the contract
    roster and the lens store cannot drift before runtime lands.
    """
    import ecosystem_contracts as ec
    data = _load_lenses()
    lens_ids = set(data["lenses"].keys())
    missing = sorted(set(ec.CANON_STAGES) - lens_ids)
    assert not missing, (
        f"CANON_STAGES references {len(missing)} stage(s) with no lens "
        f"prompt in lenses.json: {missing}. Add the prompt or drop the stage "
        f"from CANON_STAGES.")


def _run_standalone():

    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
